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
expect("unregistered numeral in chart text fails", any("not supplied by its bindings" in e for e in b.errs))

# 5 (M2). a numeral is checked against the bindings its string was built from, not against every binding
b = be.Build("v0.2-draft")
b.reg.put("a", "12.2", source="t", how="t")
b.reg.put("b", "0.6", source="t", how="t")
b.check_text("chart", b.say("{a}% against 0.6%"))
expect("numeral of another binding fails (identity, not membership)", any("['0.6']" in e for e in b.errs))
b = be.Build("v0.2-draft")
b.reg.put("a", "12.2", source="t", how="t")
b.reg.put("b", "0.6", source="t", how="t")
b.check_text("chart", b.say("{a}% against {b}%"))
expect("numerals from the string's own bindings pass", not b.errs)
expect("minus sign kept in tokens", be.tokens("fell to -5 and \u22123") == {"-5", "\u22123"})
b = be.Build("v0.2-draft")
b.reg.put("five", "5", source="t", how="t")
b.check_text("chart", b.say("change -{five}"))
expect("a bound 5 does not license -5", any("-5" in e for e in b.errs))
expect("500 passes only inside the name S&P 500", be.tokens("S&P 500 firms") == set() and be.tokens("500 firms") == {"500"})
b = build_with(FM + "Some 500 firms.\n")
expect("bare 500 in the template fails", any("hand-typed numerals ['500']" in e for e in b.errs))
b = be.Build("v0.2-draft")
b.reg.put("a", "12", source="t", how="t")
b.compose("c", "{a} and 13", source="t", how="t")
expect("composite binding with a hand-typed numeral fails", any("binding c" in e and "13" in e for e in b.errs))

# 5 (M3). every channel that ships is checked
b = build_with(FM + "<!-- presenter note: 42 firms -->\n")
expect("numeral in an HTML comment (presenter note) fails", any("['42']" in e for e in b.errs))
b = build_with(FM + "![w:900 chart of 42 firms](deck/x.svg)\n")
expect("numeral in image alt text fails", any("['42']" in e for e in b.errs))
b = build_with(FM + "![w:900 h:400 {{n}} firms](deck/x2.svg)\n")
expect("image size keywords and a bound alt pass", not b.errs)
b = build_with('---\nmarp: true\ntitle: "Top 42 risks"\nsize: 16:9\n---\n\nx\n')
expect("numeral in the front-matter title fails", any("['42']" in e for e in b.errs))
for svg, what in (("<svg><text>ok<tspan>42</tspan></text></svg>", "tspan text"),
                  ("<svg><g><text>a</text>42 firms</g></svg>", "tail text"),
                  ('<svg aria-label="42 firms"><text>a</text></svg>', "aria-label"),
                  ("<svg><!-- 42 --><text>a</text></svg>", "SVG comment"),
                  ("<svg><style>text{fill:#000}</style>42<text>a</text></svg>", "text after a style element")):
    with tempfile.TemporaryDirectory() as d:
        be.OUT_DIR = Path(d)
        b = be.Build("v0.2-draft")
        b.save_svg(svg, "t.svg")
        expect(f"numeral in SVG {what} fails", any("['42']" in e for e in b.errs))
with tempfile.TemporaryDirectory() as d:
    be.OUT_DIR = Path(d)
    b = be.Build("v0.2-draft")
    matplotlib, plt = b.mpl()
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([0, 1], [0, 1])
    ax.set_xticks([0, 1], ["2025", "2026\n(to 11-04)"])
    b.save_fig(fig, "ticks.svg")
    expect("unbound data in a fixed tick label fails", any("11" in e for e in b.errs))
    b = be.Build("v0.2-draft")
    b.reg.put("y", "2026", source="t", how="t")
    b.reg.put("md", "11-04", source="t", how="t")
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([0, 1], [0, 1])
    ax.set_yticks([0.5])
    ax.set_xticks([1], [b.say("{y}\n(to {md})")])
    fig.tight_layout()
    b.save_fig(fig, "ticks2.svg")
    expect("bound tick label and scale ticks pass", not b.errs)

# 6. quotes
b = build_with(FM + 'They said "a paraphrase".\n')
expect("quoted text that is not a quote binding fails", any("quote binding" in e for e in b.errs))
b = build_with(FM + 'The headline "{{q_ok}}" stands.\n')
expect("quote binding passes", not b.errs)
for line, what in (("They said \u201ca paraphrase\u201d.", "curly double quotes"),
                   ("They said 'a paraphrase'.", "straight single quotes"),
                   ("They said \u2018a paraphrase\u2019.", "curly single quotes"),
                   ("> a paraphrase set as a blockquote", "a markdown blockquote"),
                   ("<blockquote>a paraphrase</blockquote>", "an HTML blockquote")):
    b = build_with(FM + line + "\n")
    expect(f"quoted text in {what} that is not a quote binding fails", any("quote binding" in e for e in b.errs))
b = build_with(FM + "Anthropic's charter and the executives' passages, in \u2018{{q_ok}}\u2019.\n> {{q_ok}}\n")
expect("apostrophes, a bound single quote and a bound blockquote pass", not b.errs)
b = be.Build("v0.2-draft")
old_quotes = be.QUOTES
be.QUOTES = {**old_quotes, "q_fake": "words edition v0 never printed"}
try:
    b.register_static("0" * 40)
finally:
    be.QUOTES = old_quotes
expect("a quote not verbatim in edition v0 fails", any("q_fake" in e for e in b.errs))
expect("q_33k carries the status the paper gives it", b.reg.values["q_33k_status"]["text"].startswith("UNVERIFIED"))

# 4 (M4). a binding that copies another carries its n and d
reg = display.Registry()
reg.pct("src", 214, 1760, 1, source="t", how="t")
reg.copy("dup", "src")
expect("copied binding carries n/d", (reg.values["dup"].get("n"), reg.values["dup"].get("d")) == (214, 1760))

# M6. the CVE baseline date comes from the CVE manifest, never from another source's as-of
with tempfile.TemporaryDirectory() as d:
    m = Path(d) / "MANIFEST.tsv"
    m.write_text("id\trole\tpinned\nother\tsource\t2026-01-01\n")
    expect("CVE manifest without a baseline row fails", raises(lambda: be.cve_baseline(m), ValueError))
expect("CVE baseline read from the committed manifest",
       bool(__import__("re").fullmatch(r"\d{4}-\d{2}-\d{2}", be.cve_baseline(be.ROOT / be.CVE_MANIFEST))))

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

# H1. firm counts use company speakers only: analysts and the operator are excluded
import duckdb  # noqa: E402
kept = duckdb.connect().execute(f"SELECT count(*) FROM (VALUES ('issuer_heuristic'), ('analyst_heuristic'), ('operator'), (NULL)) "
                  f"t(role) WHERE {be.COMPANY_SPEAKERS}").fetchone()[0]
expect("company-speaker filter drops analysts, the operator and unknown roles", kept == 1)

# M5. the question-group totals must come from the same window as ttm.tsv's header
with tempfile.TemporaryDirectory() as d:
    comments, rows = be.table(be.QUESTIONS["ttm"])
    m = __import__("re").fullmatch(r"# (\d+) months to (\S+): (\d+) AI questions from (.*)", comments[0])
    bad = Path(d) / "ttm.tsv"
    lines = (be.ROOT / be.QUESTIONS["ttm"]).read_text().splitlines()
    lines[0] = f"# {m.group(1)} months to {m.group(2)}: {int(m.group(3)) + 1} AI questions from {m.group(4)}"
    bad.write_text("\n".join(lines) + "\n")
    old_q = be.QUESTIONS
    be.QUESTIONS = {**old_q, "ttm": str(bad)}
    be.OUT_DIR = Path(d)
    b = be.Build("v0.2-draft")
    b.reg.put("as_of", m.group(2), source="t", how="t")
    b.reg.put("ttm_months", m.group(1), source="t", how="t")
    b.reg.put("question_codebook", old_q["codebook"], source="t", how="t")
    try:
        b.questions()
    finally:
        be.QUESTIONS = old_q
    expect("question total that disagrees with ttm.tsv's header fails", any("AI questions in the window" in e for e in b.errs))

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
