#!/usr/bin/env -S uv run
# /// script
# dependencies = ["anki==26.8.1", "codespell"]
# ///
"""Interactively find and fix codespell typos in an Anki collection."""

import argparse
import html
import re
import subprocess
import tempfile
from pathlib import Path

from anki.collection import Collection

DB = Path.home() / ".local/share/Anki2/User 1/collection.anki2"
IGNORE = Path(__file__).with_name("ignore.txt")
RESULT = re.compile(r"^.+?:(\d+): (.+?) ==> (.+?)(?: \| .*)?$")


def plain(text: str) -> str:
    text = re.sub(r"\{\{c\d+::(.*?)(?:::.*?)?\}\}", r"\1", text, flags=re.S)
    for pattern in (
        r"```.*?```|~~~.*?~~~|`[^`]+`",
        r"<(pre|code|script|style)\b[^>]*>.*?</\1>",
        r"\\\[.*?\\\]|\\\(.*?\\\)|\$\$.*?\$\$|\$.*?\$",
        r"\{\{.*?\}\}",
    ):
        text = re.sub(pattern, " ", text, flags=re.S | re.I)
    text = re.sub(r"!?\[([^]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>|https?://\S+", " ", html.unescape(text))
    return re.sub(r"\s+", " ", text).strip()


def run_codespell(lines: list[str], ignore: Path):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as file:
        file.write("\n".join(lines))
        path = Path(file.name)
    command = ["codespell"]
    if ignore.exists():
        command += ["--ignore-words", str(ignore)]
    result = subprocess.run(command + [str(path)], text=True, capture_output=True)
    path.unlink()
    if result.returncode not in (0, 65):
        raise SystemExit(result.stderr)
    return [
        (int(match[1]) - 1, match[2], match[3].split(", "))
        for line in result.stdout.splitlines()
        if (match := RESULT.match(line))
    ]


def scan(collection: Collection, ignore: Path):
    fields = []
    for note_id in collection.find_notes(""):
        for field in collection.get_note(note_id).fields:
            if text := plain(field):
                fields.append((note_id, text))
    typos = {}
    for line, word, suggestions in run_codespell([text for _, text in fields], ignore):
        note_id, text = fields[line]
        entry = typos.setdefault(word, {"suggestions": suggestions, "notes": set(), "contexts": []})
        entry["notes"].add(note_id)
        if len(entry["contexts"]) < 3:
            start = max(0, text.find(word) - 40)
            entry["contexts"].append(text[start : start + 80])
    return typos


def review(typos):
    fixes, ignored = {}, []
    items = sorted(typos.items(), key=lambda item: len(item[1]["notes"]), reverse=True)
    for index, (word, entry) in enumerate(items, 1):
        suggestions = entry["suggestions"][:9]
        print(f"\n[{index}/{len(items)}] {word} ({len(entry['notes'])} notes)")
        for context in entry["contexts"]:
            print(f"  {context}")
        print("  " + "  ".join(f"{n}:{value}" for n, value in enumerate(suggestions, 1)))
        while True:
            answer = input("[#] accept, [e]dit, [i]gnore, [s]kip, [q]uit: ").strip()
            if answer.isdigit() and 1 <= int(answer) <= len(suggestions):
                fixes[word] = suggestions[int(answer) - 1]
                break
            if answer == "e" and (replacement := input("replacement: ").strip()):
                fixes[word] = replacement
                break
            if answer == "i":
                ignored.append(word)
                break
            if answer == "s":
                break
            if answer == "q":
                return fixes, ignored
    return fixes, ignored


def apply(collection: Collection, fixes, typos):
    patterns = {word: re.compile(rf"\b{re.escape(word)}\b") for word in fixes}
    note_ids = set().union(*(typos[word]["notes"] for word in fixes))
    changed, replacements = [], 0
    for note_id in note_ids:
        note = collection.get_note(note_id)
        for index, field in enumerate(note.fields):
            for word, pattern in patterns.items():
                field, count = pattern.subn(lambda _: fixes[word], field)
                replacements += count
            note.fields[index] = field
        changed.append(note)
    collection.update_notes(changed)
    return len(changed), replacements


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--ignore-file", type=Path, default=IGNORE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error(f"database not found: {args.db}")

    collection = Collection(str(args.db))
    try:
        typos = scan(collection, args.ignore_file)
        print(f"Found {len(typos)} unique possible typos.")
        fixes, ignored = review(typos)
        if ignored and not args.dry_run:
            with args.ignore_file.open("a") as file:
                file.writelines(f"{word}\n" for word in ignored)
        if not fixes or args.dry_run:
            return
        if input(f"Apply {len(fixes)} fixes? [y/N] ").lower() not in {"y", "yes"}:
            return

        backup_dir = args.db.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        collection.create_backup(backup_folder=str(backup_dir), force=True, wait_for_completion=True)
        changed, replacements = apply(collection, fixes, typos)
        print(f"Made {replacements} replacements in {changed} notes through Anki's API.")
    finally:
        collection.close()


if __name__ == "__main__":
    main()
