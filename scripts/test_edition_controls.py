#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "blake3==1.0.11",
#   "duckdb==2.0.0",
#   "matplotlib==3.10.7",
# ]
# ///
"""Negative tests: each display control in build_edition.py must fail on a bad input.

    uv run scripts/test_edition_controls.py

Nothing in the repository is written: templates are temporary files, charts go to
a temporary directory.
"""

from __future__ import annotations

import sys
import tempfile
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_edition as be  # noqa: E402
import display  # noqa: E402

FAILS: list[str] = []


def expect(name: str, cond: bool) -> None:
    print(("ok    " if cond else "FAIL  ") + name)
    if not cond:
        FAILS.append(name)


def raises(fn, exc) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


def build_with(template: str) -> be.Build:
    b = be.Build("v0.2-draft")
    b.reg.put("as_of", "2026-11-04", source="test", how="test")
    b.reg.put("q_ok", "33,000+", source="test", how="test")
    b.reg.put("n", "137", source="test", how="test")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(template)
    old = be.TEMPLATE
    be.TEMPLATE = Path(f.name)
    try:
        b.render("0" * 40)
    finally:
        be.TEMPLATE = old
    return b


FM = "---\nmarp: true\nsize: 16:9\n---\n\n"

# 1-2. exact inputs and one rounding rule
display.selftest()
expect("float input refused", raises(lambda: display.pct(0.5, 1), TypeError))
expect("rounded-column float refused", raises(lambda: display.round_half_up(60.5, 0), TypeError))
expect("half up at a tie (1/8 -> 13)", display.pct(1, 8, 0) == "13")
expect("exact fraction, not the rounded column (504/833 -> 61)", display.pct(504, 833, 0) == "61")
expect("numerator above denominator refused", raises(lambda: display.pct(9, 8), ValueError))
reg = display.Registry()
reg.put("x", "12.2", source="t", how="t")
expect("one binding cannot carry two texts", raises(lambda: reg.put("x", "12.3", source="t", how="t"), ValueError))

# 5. no unbound numerals
b = build_with(FM + "There were 42 firms.\n")
expect("hand-typed numeral in template fails", any("hand-typed numerals ['42']" in e for e in b.errs))
b = build_with(FM + "{{n}} firms in S&P 500 calls, to {{as_of}}.\n")
expect("bound numerals and the S&P 500 name pass", not b.errs)
b = build_with(FM + "Missing {{nope}}.\n")
expect("unresolved binding fails", any("unresolved binding" in e for e in b.errs))
b = be.Build("v0.2-draft")
b.check_text("chart", "peak 0.31%")
expect("unregistered numeral in chart text fails", any("unregistered numerals" in e for e in b.errs))

# 6. quotes
b = build_with(FM + 'They said "a paraphrase".\n')
expect("quoted text that is not a quote binding fails", any("quote binding" in e for e in b.errs))
b = build_with(FM + 'The headline "{{q_ok}}" stands.\n')
expect("quote binding passes", not b.errs)

# 7. clipping and XML
with tempfile.TemporaryDirectory() as d:
    be.OUT_DIR = Path(d)
    b = be.Build("v0.2-draft")
    matplotlib, plt = b.mpl()
    fig, ax = plt.subplots(figsize=(4, 3))
    fig.text(0.9, 0.5, "this label runs off the right edge")
    b.save_fig(fig, "clip.svg")
    expect("text past the figure edge fails", any("clipped" in e for e in b.errs))
    expect("malformed SVG fails", raises(lambda: b.save_svg("<svg><text>a & b</text></svg>", "bad.svg"), Exception))

# M1. the source commit is the last commit touching an input, so committing the outputs keeps --check passing
with tempfile.TemporaryDirectory() as d:
    g = Path(d)
    def commit(name: str, body: str) -> str:
        (g / name).write_text(body)
        be.git("add", name, cwd=g)
        be.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", name, cwd=g)
        return be.git("rev-parse", "HEAD", cwd=g).strip()
    be.git("init", "-q", cwd=g)
    src = commit("input.txt", "a")
    out = commit("output.txt", "b")
    expect("committing an output does not move the source commit", be.source_commit(["input.txt"], cwd=g) == src != out)
    src2 = commit("input.txt", "c")
    expect("committing an input moves the source commit", be.source_commit(["input.txt"], cwd=g) == src2)

print(f"\n{len(FAILS)} failure(s)")
sys.exit(1 if FAILS else 0)
