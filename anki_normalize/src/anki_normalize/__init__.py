"""Normalize editor-generated HTML in an Anki collection."""

import argparse
import re
from pathlib import Path

from anki.collection import Collection

DB = Path.home() / ".local/share/Anki2/User 1/collection.anki2"
NBSP = r"(?:&nbsp;|&#0*160;|&#x0*a0;|\u00a0)"
SINGLE_NBSP = re.compile(NBSP, re.I)
SPACE_RUN = re.compile(rf"(?:(?: |{NBSP}){{2,}}|{NBSP})", re.I)
LATEX = re.compile(r"\\\(.*?\\\)|\\\[.*?\\\]", re.S)
BARE_DIV_OPEN = re.compile(r"<div\s*>", re.I)
TAG = re.compile(r'''<!--.*?-->|<(?:[^>"']|"[^"]*"|'[^']*')*>''', re.S)
TAG_NAME = re.compile(r"<\s*(/?)\s*([\w:-]+)")
VERBATIM = {"code", "kbd", "pre", "samp", "script", "style"}
BLOCK = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "div",
    "dl",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "ul",
}


def transform(
    chunk: str,
    offset: int,
    whole: str,
    pattern: re.Pattern,
    action: str,
):
    decisions = [
        (action, pattern.match(whole, offset + match.start()))
        for match in pattern.finditer(chunk)
    ]
    cleaned = chunk if action.startswith("KEEP") else pattern.sub(" ", chunk)
    return cleaned, decisions


def clean_chunk(chunk: str, offset: int, whole: str, normalize: bool):
    if not normalize:
        return transform(chunk, offset, whole, SPACE_RUN, "KEEP (verbatim)")

    output, decisions, position = [], [], 0
    for latex in LATEX.finditer(chunk):
        normal, found = transform(
            chunk[position : latex.start()],
            offset + position,
            whole,
            SPACE_RUN,
            "NORMALIZE",
        )
        math, math_found = transform(
            latex.group(),
            offset + latex.start(),
            whole,
            SINGLE_NBSP,
            "NBSP → SPACE (LaTeX)",
        )
        output += [normal, math]
        decisions += found + math_found
        position = latex.end()

    tail, found = transform(
        chunk[position:], offset + position, whole, SPACE_RUN, "NORMALIZE"
    )
    return "".join(output) + tail, decisions + found


def adjacent_to_block_or_edge(text: str, start: int, end: int) -> bool:
    before, after = text[:start].rstrip(), text[end:].lstrip()
    if not before or not after:
        return True
    previous = re.search(r"</?\s*([\w:-]+)[^>]*>$", before)
    following = re.match(r"</?\s*([\w:-]+)\b", after)
    return bool(
        (previous and previous[1].lower() in BLOCK)
        or (following and following[1].lower() in BLOCK)
    )


def clean_field(text: str, include_verbatim: bool = False):
    output, decisions, position, depth, div_stack = [], [], 0, 0, []
    latex_spans = list(LATEX.finditer(text))

    for tag in TAG.finditer(text):
        chunk, found = clean_chunk(
            text[position : tag.start()],
            position,
            text,
            include_verbatim or depth == 0,
        )
        output.append(chunk)
        decisions += found

        value = tag.group()
        name = TAG_NAME.match(value)
        closing = bool(name and name[1])
        tag_name = name[2].lower() if name else ""
        bare_div, empty_div = False, False

        if tag_name == "div":
            if closing:
                bare_div, open_end = (
                    div_stack.pop() if div_stack else (False, None)
                )
                empty_div = bare_div and not text[open_end : tag.start()].strip()
            else:
                bare_div = bool(BARE_DIV_OPEN.fullmatch(value))
                div_stack.append((bare_div, tag.end()))

        if bare_div:
            protected = (depth and not include_verbatim) or any(
                match.start() <= tag.start() < match.end()
                for match in latex_spans
            )
            if protected:
                replacement, action = value, "KEEP DIV (protected)"
            else:
                if empty_div:
                    output[-1] = ""
                    if found:
                        del decisions[-len(found) :]
                next_is_div = bool(
                    closing and BARE_DIV_OPEN.match(text[tag.end() :].lstrip())
                )
                use_break = not empty_div and (
                    next_is_div
                    or not adjacent_to_block_or_edge(
                        text, tag.start(), tag.end()
                    )
                )
                replacement = "<br>" if use_break else ""
                action = (
                    "BARE DIV → <br>" if use_break else "REMOVE BARE DIV"
                )
            output.append(replacement)
            decisions.append((action, tag))
        else:
            output.append(value)

        if tag_name in VERBATIM:
            if closing:
                depth = max(0, depth - 1)
            elif not value.rstrip().endswith("/>"):
                depth += 1
        position = tag.end()

    chunk, found = clean_chunk(
        text[position:], position, text, include_verbatim or depth == 0
    )
    return "".join(output) + chunk, decisions + found


def context(text: str, match: re.Match, radius: int = 35) -> str:
    start, end = match.span()
    return (
        text[max(0, start - radius) : start]
        + f"⟦{match.group()}⟧"
        + text[end : end + radius]
    ).replace("\n", " ")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument(
        "--dry-run", action="store_true", help="show every decision"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="also normalize verbatim elements",
    )
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error(f"database not found: {args.db}")

    collection = Collection(str(args.db))
    changed_notes, spaces, divs, replaced_nbsp, kept = [], 0, 0, 0, 0
    try:
        for note_id in collection.find_notes(""):
            note, dirty = collection.get_note(note_id), False
            for index, text in enumerate(note.fields):
                new, decisions = clean_field(text, args.all)
                for action, match in decisions:
                    changed = not action.startswith("KEEP")
                    divs += changed and "DIV" in action
                    spaces += changed and "DIV" not in action
                    kept += not changed
                    replaced_nbsp += (
                        len(SINGLE_NBSP.findall(match.group()))
                        if changed
                        else 0
                    )
                    if args.dry_run:
                        print(
                            f"{action:22} note {note_id}, "
                            f"field {index + 1}: {context(text, match)}"
                        )
                if new != text:
                    note.fields[index], dirty = new, True
            if dirty:
                changed_notes.append(note)

        print(
            f"Will normalize {spaces} whitespace runs containing "
            f"{replaced_nbsp} NBSPs and simplify {divs} bare div "
            f"boundaries in {len(changed_notes)} notes; preserving "
            f"{kept} protected items."
        )
        if args.dry_run or not changed_notes:
            return
        answer = input("Apply these changes? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            return

        backup_dir = args.db.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        collection.create_backup(
            backup_folder=str(backup_dir),
            force=True,
            wait_for_completion=True,
        )
        collection.update_notes(changed_notes)
        print("Updated through Anki's API. You can also undo it in Anki.")
    finally:
        collection.close()
