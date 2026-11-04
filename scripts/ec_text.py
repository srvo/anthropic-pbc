"""Where earnings-call text lives: the gitignored bulk dir, never the repository.

The committed tables in corpus/earnings-calls/ hold ids, metadata, character
offsets and BLAKE3 hashes only (maintainer decision, 2026-11-04: quotes may be
published, whole transcripts and the whole corpus may not). The text is rebuilt
from the pinned source into .eccorpus/ by

    uv run scripts/ec_extract.py build     # .eccorpus/ai-paragraphs.parquet, .eccorpus/ai-windows.parquet
    uv run scripts/ec_questions.py build   # .eccorpus/ai-questions.parquet

Each bulk file is the full table, text included, byte-identical to the table
that was committed before the text came out (so the BLAKE3 recorded in every
witness run-*.json still names it). Scripts read metadata from the committed
table and text from the bulk file, joined by id. No third-party imports here,
so any script can use it whatever its own dependencies.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus" / "earnings-calls"
BULK = ROOT / ".eccorpus"

PARAGRAPHS = CORPUS / "ai-paragraphs.parquet"
WINDOWS = CORPUS / "ai-windows.parquet"
QUESTIONS = CORPUS / "ai-questions.parquet"
PARAGRAPHS_TEXT = BULK / "ai-paragraphs.parquet"
WINDOWS_TEXT = BULK / "ai-windows.parquet"
QUESTIONS_TEXT = BULK / "ai-questions.parquet"

_BUILD = {PARAGRAPHS_TEXT: "scripts/ec_extract.py build", WINDOWS_TEXT: "scripts/ec_extract.py build",
          QUESTIONS_TEXT: "scripts/ec_questions.py build"}


def need(p: Path) -> Path:
    """The bulk text file, or exit naming the command that rebuilds it."""
    if not p.exists():
        sys.exit(f"{p.relative_to(ROOT)} missing: text is not committed; rebuild it with "
                 f"`uv run scripts/ec_extract.py fetch` then `uv run {_BUILD[p]}`")
    return p


def windows_sql() -> str:
    """Committed window metadata with its text joined on window_id; same columns, same order,
    as the full table."""
    return (f"(SELECT w.*, t.text FROM '{WINDOWS}' w "
            f"JOIN (SELECT window_id, text FROM '{need(WINDOWS_TEXT)}') t USING (window_id))")


def questions_sql() -> str:
    """Committed question metadata with its text joined on question_id."""
    return (f"(SELECT q.*, t.text FROM '{QUESTIONS}' q "
            f"JOIN (SELECT question_id, text FROM '{need(QUESTIONS_TEXT)}') t USING (question_id))")
