#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["blake3>=1.0"]
# ///
"""Keep the paper, its rendered page, its figures and its hash pins in lockstep.

    uv run scripts/seal.py sync                              # rebuild figures, re-embed paper in index.html
    uv run scripts/seal.py check                             # fail on any drift (CI runs this)
    uv run scripts/seal.py check --allow-unsealed            # same, but a draft whose pins lag only warns
    uv run scripts/seal.py seal --version v0.1 --date 2026-11-04

`seal` = sync, then move every version/hash/date pin from the sealed version
(read from CITATION.cff) to the new one. The date is an argument, never read
from the clock: time is a recorded input (docs/primitives.md).

Zenodo is not touched. With the GitHub-Zenodo integration, publishing a GitHub
release of the sealed commit mints the new version DOI; the script prints the
command and does not run it.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import blake3

ROOT = Path(__file__).resolve().parent.parent
PAPER = ROOT / "docs" / "anthropic-contrapunctus.md"
PAGE = ROOT / "index.html"
FIG_BUILD = ROOT / "docs" / "figures" / "build.py"
CITATION = ROOT / "CITATION.cff"
EMBED_OPEN = '<script type="text/markdown" id="paperSrc">'
EMBED_CLOSE = "</script>"

# Every file that pins the sealed hash. Each holds no other 64-hex token, so
# "every 64-hex token equals the current hash" is the whole check.
PINS = [
    ROOT / "README.md",
    CITATION,
    ROOT / ".zenodo.json",
    PAGE,
    ROOT / "docs" / "contrapunctus-attest.md",
    ROOT / "docs" / "contrapunctus-attestations" / "README.md",
]
HEX64 = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")


def paper_hash() -> str:
    return blake3.blake3(PAPER.read_bytes()).hexdigest()


def sealed() -> tuple[str, str, str]:
    """(version, date, hash) of the currently sealed version, from CITATION.cff."""
    text = CITATION.read_text(encoding="utf-8")
    version = re.search(r'^version:\s*"([^"]+)"', text, re.M)
    date = re.search(r"^date-released:\s*(\S+)", text, re.M)
    digest = re.search(r'value:\s*"blake3:([0-9a-f]{64})"', text)
    if not (version and date and digest):
        sys.exit("CITATION.cff: missing version, date-released or blake3 identifier")
    return version.group(1), date.group(1), digest.group(1)


def embed_span(page: str) -> tuple[int, int]:
    start = page.index(EMBED_OPEN) + len(EMBED_OPEN)
    return start, page.index(EMBED_CLOSE, start)


def build_figures() -> None:
    subprocess.run([sys.executable, str(FIG_BUILD)], check=True, stdout=subprocess.DEVNULL)


def sync() -> None:
    build_figures()
    md = PAPER.read_text(encoding="utf-8")
    if EMBED_CLOSE in md:
        sys.exit("paper contains '</script>', which would break the embed")
    page = PAGE.read_text(encoding="utf-8")
    a, b = embed_span(page)
    if page[a:b] != md:
        PAGE.write_text(page[:a] + md + page[b:], encoding="utf-8")
        print("index.html: re-embedded paper")
    print("figures: rebuilt")


def check(allow_unsealed: bool) -> int:
    errors, warnings = [], []

    page = PAGE.read_text(encoding="utf-8")
    a, b = embed_span(page)
    if page[a:b] != PAPER.read_text(encoding="utf-8"):
        errors.append("index.html embed differs from docs/anthropic-contrapunctus.md (run: sync)")

    figdir = FIG_BUILD.parent
    before = {p.name: p.read_bytes() for p in figdir.glob("*.svg")}
    build_figures()
    after = {p.name: p.read_bytes() for p in figdir.glob("*.svg")}
    if before != after:
        errors.append("figures were stale; rebuilt them, review and stage the diff")

    current = paper_hash()
    _, _, pinned = sealed()
    stale = []
    for f in PINS:
        for tok in set(HEX64.findall(f.read_text(encoding="utf-8"))):
            if tok != pinned:
                errors.append(f"{f.relative_to(ROOT)}: pins {tok[:12]}…, CITATION.cff says {pinned[:12]}…")
            if tok != current:
                stale.append(str(f.relative_to(ROOT)))
    if stale:
        msg = (f"paper hash is {current[:12]}… but {len(set(stale))} pin file(s) carry "
               f"{pinned[:12]}… (unsealed draft; run: seal --version … --date …)")
        (warnings if allow_unsealed else errors).append(msg)

    for w in warnings:
        print(f"warn: {w}")
    for e in errors:
        print(f"FAIL: {e}")
    if not errors:
        print(f"ok: paper blake3 {current}" + (" (draft)" if warnings else " (sealed)"))
    return 1 if errors else 0


def seal(version: str, date: str) -> None:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        sys.exit("--date must be YYYY-MM-DD")
    ov, od, oh = sealed()
    sync()
    nh = paper_hash()
    if nh == oh and version == ov:
        sys.exit(f"nothing to seal: paper still hashes to {oh[:12]}… ({ov})")

    pairs = [
        (oh, nh),
        (oh[:8] + "…", nh[:8] + "…"),
        (f"{ov} · {od}", f"{version} · {date}"),
        (f"{ov} ({od})", f"{version} ({date})"),
        (f'version: "{ov}"', f'version: "{version}"'),
        (f"date-released: {od}", f"date-released: {date}"),
        (f"({ov}; provisional", f"({version}; provisional"),
        (f"Paper {ov} BLAKE3", f"Paper {version} BLAKE3"),
        (f">{ov} · blake3:", f">{version} · blake3:"),
    ]
    hits = {old: 0 for old, _ in pairs}
    for f in PINS:
        text = f.read_text(encoding="utf-8")
        for old, new in pairs:
            hits[old] += text.count(old)
            text = text.replace(old, new)
        f.write_text(text, encoding="utf-8")
    missing = [old for old, n in hits.items() if n == 0]
    if missing:
        print("warn: pin patterns not found (layout changed?):", *missing, sep="\n  ")

    if check(allow_unsealed=False):
        sys.exit("seal left drift behind; see FAIL lines above")
    print(f"\nsealed {version} ({date}) blake3:{nh}")
    print(f"previous: {ov} ({od}) blake3:{oh}")
    print("next, after you review and commit:")
    print(f"  gh release create {version} --title \"{version}\" --notes \"blake3:{nh}\"")
    print("  (with the Zenodo GitHub integration on, the release mints the new version DOI)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sync")
    c = sub.add_parser("check")
    c.add_argument("--allow-unsealed", action="store_true")
    s = sub.add_parser("seal")
    s.add_argument("--version", required=True)
    s.add_argument("--date", required=True)
    args = ap.parse_args()
    if args.cmd == "sync":
        sync()
        return 0
    if args.cmd == "check":
        return check(args.allow_unsealed)
    seal(args.version, args.date)
    return 0


if __name__ == "__main__":
    sys.exit(main())
