#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["blake3==1.0.11"]
# ///
"""Derive plain text from the pinned sources, for Descartes quote checks.

    uv run scripts/source_text.py            # write sources/<file>.txt for every row of sources/MANIFEST.tsv
    uv run scripts/source_text.py --check    # also re-hash every pinned source against the manifest first

Descartes checks that a quote occurs exactly once in a file. A PDF or an HTML filing is not text, so
each source gets one derived text file beside it (gitignored, like the source: P1). The derivation is
fixed and deterministic, so anyone can rebuild the same bytes:

- PDF: `pdftotext -enc UTF-8 -nopgbrk`, the recipe Descartes itself uses (derived/recipes.tsv).
- HTML: every tag replaced by a space, entities decoded.
- Then, for both: zero-width spaces (U+200B, which the RSP's PDF puts around every run of text)
  removed, and every run of whitespace collapsed to one space, so a quote that crosses a line break
  in the layout still matches the sentence as written.

A quote that passes is present, word for word, in the source as its publisher laid it out; the
normalisation above is the only difference, and it is the same for every quote.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import re
import subprocess
import sys
from pathlib import Path

import blake3

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources"


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u200b", "")).strip() + "\n"


def derive(path: Path) -> str:
    if path.suffix == ".pdf":
        out = subprocess.run(["pdftotext", "-enc", "UTF-8", "-nopgbrk", str(path), "-"],
                             capture_output=True, check=True)
        return normalise(out.stdout.decode("utf-8"))
    if path.suffix in (".htm", ".html"):
        raw = path.read_text(encoding="utf-8", errors="strict")
        return normalise(html.unescape(re.sub(r"<[^>]+>", " ", raw)))
    raise ValueError(f"{path.name}: no derivation for {path.suffix}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="verify each source's BLAKE3 against the manifest")
    a = ap.parse_args()
    rows = list(csv.DictReader((SOURCES / "MANIFEST.tsv").open(encoding="utf-8"), delimiter="\t"))
    bad = 0
    for row in rows:
        src = SOURCES / row["path"]
        if not src.is_file():
            print(f"missing\t{row['path']}\t(fetch {row['url']})")
            bad += 1
            continue
        if a.check:
            if blake3.blake3(src.read_bytes()).hexdigest() != row["blake3"]:
                print(f"changed\t{row['path']}\tBLAKE3 differs from the manifest")
                bad += 1
                continue
        try:
            text = derive(src)
        except ValueError as e:
            print(f"skipped\t{e}")
            continue
        out = src.with_name(src.name + ".txt")
        out.write_text(text, encoding="utf-8")
        print(f"ok\t{out.relative_to(ROOT)}\t{hashlib.sha256(text.encode()).hexdigest()[:16]}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
