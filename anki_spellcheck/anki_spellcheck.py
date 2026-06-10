#!/usr/bin/env python3
"""Interactive spell-checker for an Anki collection.

Scans every note's fields, strips the Markdown/HTML/LaTeX/Cloze markup, runs the
plain text through `codespell`, and lets you review each unique misspelling once:
accept a suggestion, type your own fix, or mark it a permanent false-positive.
Accepted fixes are written straight back into the SQLite database (a backup is
taken first).

codespell flags only known misspellings, so — unlike a dictionary-based checker
— it does not drown you in false positives on technical jargon or proper nouns.
The trade-off is recall: it will miss novel typos that are not on its list.
"""

from __future__ import annotations

import html
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

import click

DEFAULT_DB = Path.home() / ".local/share/Anki2/User 1/collection.anki2"
# Words codespell should never flag (the rare case where one of its corrections
# is wrong for you). Kept beside the script so it is easy to find and edit.
DEFAULT_IGNORE = Path(__file__).with_name("ignore.txt")
FIELD_SEP = "\x1f"
MAX_SUGGESTIONS = 9
MAX_CONTEXTS = 3
CONTEXT_RADIUS = 40


# --------------------------------------------------------------------------- #
# Markup stripping
#
# Fields are a mix of Markdown, raw HTML, and LaTeX. The peeling order matters:
# code spans/blocks go first (their contents are never prose), and HTML
# entities are unescaped *before* tags are stripped — otherwise escaped markup
# such as `&lt;a href="…"&gt;` only becomes a tag *after* the tag regex has run,
# leaking attribute/tag names like `href` and `pre` into the spell-checker.
# --------------------------------------------------------------------------- #

_CLOZE = re.compile(r"\{\{c\d+::(.*?)(?:::.*?)?\}\}", re.DOTALL)
_FENCED_CODE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`]+`")
_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_MD_INLINE_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MD_REF_LINK = re.compile(r"\[([^\]]*)\]\[[^\]]*\]")
_TEMPLATE = re.compile(r"\{\{.*?\}\}", re.DOTALL)
_LATEX_BLOCKS = re.compile(
    r"\\\[.*?\\\]|\\\(.*?\\\)|\$\$.*?\$\$|\$.*?\$"
    r"|\\begin\{.*?\}.*?\\end\{.*?\}",
    re.DOTALL,
)
_LATEX_CMD = re.compile(r"\\[a-zA-Z]+\*?|\\[^a-zA-Z]")
_URL = re.compile(r"https?://\S+|\bwww\.\S+")
# Whole HTML elements whose contents are code/markup, not prose.
_CODE_ELEMENT = re.compile(
    r"<(pre|code|kbd|samp|script|style)\b[^>]*>.*?</\1>",
    re.DOTALL | re.IGNORECASE,
)
_TAG = re.compile(r"<[^>]+>")
# Markdown emphasis/heading/list/blockquote punctuation left at the margins.
_MD_MARKERS = re.compile(r"(?m)^\s{0,3}(?:#{1,6}|>|[-*+])\s+|[*~]{1,2}")
_WHITESPACE = re.compile(r"\s+")


def strip_markup(field_text: str) -> str:
    """Reduce one Anki field (Markdown + HTML + LaTeX) to plain prose."""
    text = field_text
    # 1. Cloze: keep the answer text, drop the hint and wrapper.
    text = _CLOZE.sub(r"\1", text)
    # 2. Code spans/blocks first — their contents are identifiers, never prose.
    text = _FENCED_CODE.sub(" ", text)
    text = _INLINE_CODE.sub(" ", text)
    # 3. Markdown links/images: keep the visible text, drop the target.
    text = _MD_IMAGE.sub(" ", text)
    text = _MD_INLINE_LINK.sub(r"\1", text)
    text = _MD_REF_LINK.sub(r"\1", text)
    # 4. Anki/handlebars templating and LaTeX math.
    text = _TEMPLATE.sub(" ", text)
    text = _LATEX_BLOCKS.sub(" ", text)
    text = _LATEX_CMD.sub(" ", text)
    # 5. Unescape entities *before* stripping tags, then drop code elements and
    #    remaining tags. This catches both real and previously-escaped markup.
    text = html.unescape(text)
    text = _CODE_ELEMENT.sub(" ", text)
    text = _TAG.sub(" ", text)
    # 6. Bare URLs left in prose. This MUST run after tag-stripping: a greedy
    #    URL match inside `<a href="…">` would otherwise swallow the closing
    #    `">`, leaving a dangling `<a href="` that the tag regex can't remove.
    text = _URL.sub(" ", text)
    # 7. Leftover Markdown emphasis/heading/list punctuation.
    text = _MD_MARKERS.sub(" ", text)
    return _WHITESPACE.sub(" ", text).strip()


# --------------------------------------------------------------------------- #
# codespell driver
#
# codespell flags only *known* misspellings (a curated list) rather than every
# word missing from a dictionary, so it does not trip over the jargon and
# proper nouns that flood a not-in-dictionary checker like aspell. We feed it
# the whole collection in one batch — one stripped field per line — and map its
# `path:line: word ==> corrections` output back to the originating note.
# --------------------------------------------------------------------------- #

_CODESPELL_LINE = re.compile(r"^.+?:(\d+): (.+?) ==> (.+?)(?: \| .*)?$")


@dataclass
class Flag:
    """One codespell hit located back to its source line."""

    line: int  # 1-based index into the corpus handed to codespell
    word: str  # the misspelled token, original case
    suggestions: list[str]  # codespell's suggested correction(s)


class Codespell:
    """Batch driver for the `codespell` CLI."""

    def __init__(self, ignore_file: Path | None) -> None:
        self._ignore_file = ignore_file

    def check(self, corpus: list[str]) -> list[Flag]:
        """Run codespell over one stripped field per line; return every hit."""
        # codespell's stdin mode emits a two-line-per-hit format; pointing it at
        # a real file gives the simpler one-line `path:line: word ==> corr`.
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", encoding="utf-8", delete=False
        ) as tmp:
            tmp.write("\n".join(corpus))
            corpus_path = tmp.name
        cmd = ["codespell", corpus_path]
        if self._ignore_file is not None and self._ignore_file.exists():
            cmd[1:1] = ["--ignore-words", str(self._ignore_file)]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8"
            )
        except FileNotFoundError:
            raise SystemExit(
                "codespell not found on PATH. Install it with "
                "`uv tool install codespell` or `pip install codespell`."
            ) from None
        finally:
            Path(corpus_path).unlink(missing_ok=True)
        # Exit 0 = clean, 65 = typos found; anything else is a real failure.
        if proc.returncode not in (0, 65):
            raise SystemExit(f"codespell failed:\n{proc.stderr.strip()}")

        flags: list[Flag] = []
        for out in proc.stdout.splitlines():
            match = _CODESPELL_LINE.match(out)
            if match is None:
                continue
            suggestions = [s.strip() for s in match.group(3).split(",") if s.strip()]
            flags.append(
                Flag(
                    line=int(match.group(1)),
                    word=match.group(2),
                    suggestions=suggestions,
                )
            )
        return flags


# --------------------------------------------------------------------------- #
# Scan
# --------------------------------------------------------------------------- #


@dataclass
class Misspelling:
    word: str
    suggestions: list[str]
    note_ids: set[int] = field(default_factory=set)
    contexts: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.note_ids)


def make_context(plain: str, word: str) -> str:
    """A short snippet of `plain` around the first occurrence of `word`."""
    idx = plain.find(word)
    if idx < 0:
        return plain[: 2 * CONTEXT_RADIUS]
    start = max(0, idx - CONTEXT_RADIUS)
    end = min(len(plain), idx + len(word) + CONTEXT_RADIUS)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(plain) else ""
    snippet = plain[start:idx] + f"[{word}]" + plain[idx + len(word) : end]
    return prefix + snippet.replace("\n", " ") + suffix


def scan_notes(
    conn: sqlite3.Connection,
    codespell: Codespell,
    limit: int | None,
) -> dict[str, Misspelling]:
    """Build a map of unique misspelled word -> aggregated occurrences."""
    query = "SELECT id, flds FROM notes"
    if limit is not None:
        query += f" LIMIT {int(limit)}"

    # Flatten every non-empty stripped field into one corpus line, remembering
    # which note it came from so codespell's hits can be attributed back.
    fields: list[tuple[int, str]] = []  # parallel to the corpus: (note_id, plain)
    scanned = 0
    for note_id, flds in conn.execute(query):
        scanned += 1
        for field_text in str(flds).split(FIELD_SEP):
            plain = strip_markup(field_text)
            if plain:
                fields.append((int(note_id), plain))
    print(f"Scanned {scanned} notes ({len(fields)} fields).", file=sys.stderr)

    found: dict[str, Misspelling] = OrderedDict()
    for flag in codespell.check([plain for _, plain in fields]):
        note_id, plain = fields[flag.line - 1]
        entry = found.get(flag.word)
        if entry is None:
            entry = Misspelling(word=flag.word, suggestions=flag.suggestions)
            found[flag.word] = entry
        entry.note_ids.add(note_id)
        if len(entry.contexts) < MAX_CONTEXTS:
            entry.contexts.append(make_context(plain, flag.word))
    return found


# --------------------------------------------------------------------------- #
# Interactive review
# --------------------------------------------------------------------------- #


@dataclass
class Review:
    """Outcome of the interactive session."""

    fixes: dict[str, str] = field(default_factory=dict)  # word -> replacement
    new_ignores: list[str] = field(default_factory=list)
    quit_early: bool = False


def review_misspellings(found: dict[str, Misspelling], min_count: int) -> Review:
    review = Review()
    candidates = sorted(
        (m for m in found.values() if m.count >= min_count),
        key=lambda m: m.count,
        reverse=True,
    )
    total = len(candidates)
    if total == 0:
        print("No misspellings to review. 🎉")
        return review

    print(f"\n{total} unique word(s) to review.\n")
    for index, miss in enumerate(candidates, start=1):
        _print_entry(index, total, miss)
        decision = _prompt(miss)
        if decision is None:
            review.quit_early = True
            break
        kind, value = decision
        if kind == "fix":
            review.fixes[miss.word] = value
        elif kind == "ignore":
            review.new_ignores.append(miss.word)
        # "skip" -> record nothing
    return review


def _print_entry(index: int, total: int, miss: Misspelling) -> None:
    plural = "cards" if miss.count != 1 else "card"
    print("─" * 72)
    print(f"[{index}/{total}]  «{miss.word}»  — {miss.count} {plural}")
    for ctx in miss.contexts:
        print(f"    {ctx}")
    if miss.suggestions:
        shown = miss.suggestions[:MAX_SUGGESTIONS]
        listing = "   ".join(f"{i}:{s}" for i, s in enumerate(shown, start=1))
        print(f"  suggestions: {listing}")
    else:
        print("  suggestions: (none)")


def _prompt(miss: Misspelling) -> tuple[str, str] | None:
    """Return (kind, value) or None to quit. kind in {fix, ignore, skip}."""
    shown = miss.suggestions[:MAX_SUGGESTIONS]
    while True:
        choice = input(
            "  [#]=accept  e=edit  i=false-positive  s=skip  q=quit > "
        ).strip()
        if choice == "":
            continue
        if choice == "q":
            return None
        if choice == "s":
            return ("skip", "")
        if choice == "i":
            return ("ignore", "")
        if choice == "e":
            custom = input("    replacement: ").strip()
            if custom:
                return ("fix", custom)
            continue
        if choice.isdigit():
            num = int(choice)
            if 1 <= num <= len(shown):
                return ("fix", shown[num - 1])
        print("    ? not a valid choice")


# --------------------------------------------------------------------------- #
# Apply
# --------------------------------------------------------------------------- #



def backup_db(db_path: Path) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = db_path.with_name(f"{db_path.stem}.{stamp}.bak")
    shutil.copy2(db_path, backup)
    wal = db_path.with_name(db_path.name + "-wal")
    if wal.exists():
        shutil.copy2(wal, backup.with_name(backup.name + "-wal"))
    return backup


def apply_fixes(
    conn: sqlite3.Connection,
    fixes: dict[str, str],
    note_ids: set[int],
) -> tuple[int, int]:
    """Apply word fixes to the given notes. Returns (notes_changed, replacements)."""
    patterns = {word: re.compile(rf"\b{re.escape(word)}\b") for word in fixes}
    now = int(time.time())
    notes_changed = 0
    replacements = 0

    cur = conn.cursor()
    placeholders = ",".join("?" * len(note_ids))
    rows = cur.execute(
        f"SELECT id, flds FROM notes WHERE id IN ({placeholders})",
        tuple(note_ids),
    ).fetchall()

    for note_id, flds in rows:
        fields = str(flds).split(FIELD_SEP)
        changed = False
        for i, field_text in enumerate(fields):
            new_text = field_text
            for word, repl in fixes.items():
                new_text, n = patterns[word].subn(repl, new_text)
                replacements += n
            if new_text != field_text:
                fields[i] = new_text
                changed = True
        if not changed:
            continue
        new_flds = FIELD_SEP.join(fields)
        sfld = strip_markup(fields[0])
        cur.execute(
            "UPDATE notes SET flds=?, sfld=?, mod=?, usn=-1 WHERE id=?",
            (new_flds, sfld, now, note_id),
        )
        notes_changed += 1

    cur.execute("UPDATE col SET mod=? WHERE id=(SELECT id FROM col LIMIT 1)", (now,))
    conn.commit()
    return notes_changed, replacements


# --------------------------------------------------------------------------- #
# Ignore-list persistence
# --------------------------------------------------------------------------- #


def load_ignore(path: Path) -> set[str]:
    """Load a word-list file. Blank lines and `#` comments are skipped."""
    if not path.exists():
        return set()
    words: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        token = line.strip()
        if not token or token.startswith("#"):
            continue
        words.add(token.lower())
    return words


def append_ignore(path: Path, words: list[str]) -> None:
    if not words:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for word in words:
            fh.write(word + "\n")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


@click.command(help=__doc__)
@click.option(
    "--db",
    type=click.Path(path_type=Path),
    default=DEFAULT_DB,
    show_default=True,
    help="Path to the Anki collection SQLite database.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Review and report fixes without writing to the database.",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Only scan the first N notes (for quick test runs).",
)
@click.option(
    "--min-count",
    type=int,
    default=1,
    show_default=True,
    help="Only review words appearing on at least this many cards.",
)
@click.option(
    "--ignore-file",
    type=click.Path(path_type=Path),
    default=DEFAULT_IGNORE,
    show_default=True,
    help="File of words to treat as permanent false-positives.",
)
def main(
    db: Path,
    dry_run: bool,
    limit: int | None,
    min_count: int,
    ignore_file: Path,
) -> None:
    if not db.exists():
        click.echo(f"Database not found: {db}", err=True)
        raise SystemExit(1)

    ignored = load_ignore(ignore_file)
    if ignored:
        click.echo(f"Ignoring {len(ignored)} false-positive(s) from {ignore_file}")

    codespell = Codespell(ignore_file)
    # Read-only connection for the scan; we reopen read-write only to apply.
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        found = scan_notes(conn, codespell, limit)
    finally:
        conn.close()

    review = review_misspellings(found, min_count)
    append_ignore(ignore_file, review.new_ignores)
    if review.new_ignores:
        click.echo(f"Added {len(review.new_ignores)} word(s) to {ignore_file}")

    if not review.fixes:
        click.echo("No fixes to apply.")
        return

    click.echo(f"\n{len(review.fixes)} word(s) marked for fixing:")
    for word, repl in review.fixes.items():
        click.echo(f"  «{word}» → «{repl}»")

    if dry_run:
        click.echo("\n[dry-run] No changes written.")
        return

    confirm = input("\nWrite these fixes to the database? [y/N] ").strip().lower()
    if confirm != "y":
        click.echo("Aborted; nothing written.")
        return

    backup = backup_db(db)
    click.echo(f"Backed up to {backup}")

    note_ids: set[int] = set()
    for word in review.fixes:
        note_ids |= found[word].note_ids

    conn = sqlite3.connect(db)
    try:
        notes_changed, replacements = apply_fixes(conn, review.fixes, note_ids)
    finally:
        conn.close()

    click.echo(f"Done: {replacements} replacement(s) across {notes_changed} note(s).")
    click.echo("Open Anki and sync to upload the changes.")


if __name__ == "__main__":
    main()
