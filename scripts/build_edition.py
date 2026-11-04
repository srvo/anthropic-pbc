#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "blake3==1.0.11",
#   "duckdb==2.0.0",
#   "matplotlib==3.10.7",
# ]
# ///
"""Build DECK.md as an edition of one source commit and one risk codebook.

    uv run scripts/build_edition.py --codebook v0.2-draft    # write DECK.md, deck/*.svg, deck/STAMP.json
    uv run scripts/build_edition.py --codebook v0.2-draft --check   # exit 1 if a rebuild would change anything

The build is the review step. It writes into the working tree and never
commits. Review `git diff`, then commit the edition yourself. The stamp names
the source commit (HEAD at build time), so the edition commit's parent is the
commit it was built from.

Rules (docs/report-build.md):
  - every dag.yml step must be `ok` (Praxis dag.py status);
  - every input the build reads must be committed and unmodified;
  - one risk codebook for every risk chart and number;
  - every number in the deck comes from a binding computed here; a digit in
    the template outside {{...}} on a caption line fails the build;
  - quotes from the paper are checked against edition v0 at PAPER_V0.
Positive = both witnesses (DeBERTa, ModernBERT) >= 0.5, everywhere.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

import blake3
import duckdb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import deck_charts  # noqa: E402

TEMPLATE = ROOT / "deck" / "deck.template.md"
OUT_MD = ROOT / "DECK.md"
OUT_DIR = ROOT / "deck"
STAMP = OUT_DIR / "STAMP.json"
EC = ROOT / "corpus" / "earnings-calls"
PAPER = "docs/anthropic-contrapunctus.md"
PAPER_V0 = "1afb042"
DAG_TOOL = ROOT.parent / "praxis" / "datasets" / "dag.py"
FIRST_YEAR = 2013
RISK_WORD = r"(?i)\brisk(s|y|ier|iest)?\b"

# Risk codebooks this build supports: codebook file, score folder for earnings-call windows,
# the cross-source chart for that codebook, and a status shown on every slide.
CODEBOOKS = {
    "v0.2-draft": {
        "file": "corpus/codebooks/codebook-v0.2-draft.tsv",
        "ec_scores": "proposals/earnings-calls/codebook-v0.2-draft",
        "dialogue": "proposals/cross-source/codebook-v0.2-draft/report/dialogue-space.tsv",
        "status": " (DRAFT: wording awaits review)",
    },
}
# Fixed inputs read whatever the codebook (their own codebooks are recorded in the stamp).
FIXED = {
    "question_intents": "proposals/earnings-calls/codebook-questions-v0.1/report/ttm.tsv",
    "question_chart": "proposals/earnings-calls/codebook-questions-v0.1/report/intent-ttm.svg",
    "dialogue_chart": "proposals/cross-source/codebook-v0.2-draft/report/dialogue-space.svg",
    "cve_monthly_ai": "corpus/cve/monthly-ai.tsv",
}
LABELS = {"regulation": "Regulation", "cyber": "Cybersecurity", "privacy": "Data privacy",
          "accuracy": "Accuracy / hallucination", "bias": "Bias / fairness", "labor": "Jobs / labor",
          "disruption": "Disruption of the business", "capex": "Overspending / capex return",
          "energy": "Energy / power", "supply": "Chip & supply constraints", "ip": "Intellectual property",
          "safety_ethics": "Safety / ethics / misuse"}
QUOTES = {  # binding -> exact text in edition v0 (markdown emphasis and line breaks removed before matching)
    "q_toothless": "Anthropic's charter is legally real and legally toothless.",
    "q_365b": "§365(b) gives directors no duty to any person on account of a public-benefit interest",
}


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def b3(p: Path) -> str:
    return blake3.blake3(p.read_bytes()).hexdigest()


def label(t: str) -> str:
    return LABELS.get(t, t + " *")


# ---------------------------------------------------------------- preconditions
def preflight(cb: dict, inputs: list[str]) -> list[str]:
    errs = []
    r = subprocess.run(["uv", "run", "--quiet", str(DAG_TOOL), "status"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        errs.append("dag.py status is not all ok:\n" + "\n".join(l for l in r.stdout.splitlines() if not l.startswith("ok")))
    for p in inputs:
        if not git("ls-files", "--", p).strip():
            errs.append(f"input not committed: {p}")
    dirty = git("status", "--porcelain", "--", *inputs).strip()
    if dirty:
        errs.append("inputs modified since the last commit:\n" + dirty)
    return errs


# ---------------------------------------------------------------- bindings + charts
def flags_sql(scores: Path, h: str) -> str:
    return (f"SELECT d.window_id FROM '{scores / 'deberta.parquet'}' d JOIN '{scores / 'modernbert.parquet'}' m "
            f"USING (window_id, hypothesis_id) WHERE d.hypothesis_id = '{h}' AND d.p_entail >= .5 AND m.p_entail >= .5")


def earnings(cb: dict, b: dict) -> tuple[list[tuple], list[tuple]]:
    con = duckdb.connect()
    scores = ROOT / cb["ec_scores"]
    as_of = str(con.execute(f"SELECT max(report_date) FROM read_csv('{EC / 'calls.tsv'}')").fetchone()[0])
    types = [r["id"] for r in csv.DictReader((ROOT / cb["file"]).open(), delimiter="\t") if r["group"] == "risk_type"]
    con.execute(f"""CREATE TABLE calls AS SELECT symbol, fiscal_year, fiscal_quarter, report_date
        FROM read_csv('{EC / "calls.tsv"}')
        WHERE (duplicate_of IS NULL OR duplicate_of = '') AND n_paragraphs > 2 AND report_date <= DATE '{as_of}'""")
    con.execute(f"""CREATE TABLE w AS SELECT window_id, symbol, fiscal_year, fiscal_quarter, report_date::DATE AS report_date,
            regexp_matches(text, '{RISK_WORD}') AS lex,
            window_id IN ({flags_sql(scores, 'ai_risk')}) AS ai_risk
        FROM '{EC / "ai-windows.parquet"}'""")
    con.execute("""CREATE TABLE cw AS SELECT c.*, bool_or(w.lex) AS lex, bool_or(w.ai_risk) AS nli
        FROM calls c LEFT JOIN w USING (symbol, fiscal_year, fiscal_quarter) GROUP BY ALL""")
    series = con.execute(f"""SELECT year(report_date) AS year, count(*) AS calls,
            round(100.0 * count(*) FILTER (WHERE lex) / count(*), 2), round(100.0 * count(*) FILTER (WHERE nli) / count(*), 2)
        FROM cw WHERE year(report_date) >= {FIRST_YEAR} GROUP BY 1 ORDER BY 1""").fetchall()
    since = f"DATE '{as_of}' - INTERVAL 1 YEAR"
    con.execute(f"CREATE TABLE ttm AS SELECT * FROM w WHERE report_date > {since} AND report_date <= DATE '{as_of}' AND ai_risk")
    ranking = []
    for t in types:
        firms = con.execute(f"SELECT count(DISTINCT symbol) FROM ttm WHERE window_id IN ({flags_sql(scores, t)})").fetchone()[0]
        ranking.append((t, label(t), firms))
    ranking.sort(key=lambda r: (-r[2], r[0]))
    b.update(as_of=as_of, ec_year_last=str(series[-1][0]), ec_pct_witness_last=f"{series[-1][3]:.1f}",
             ec_pre2023_max=f"{max(r[3] for r in series if r[0] < 2023):.1f}",
             ec_ttm_risk_firms=str(con.execute("SELECT count(DISTINCT symbol) FROM ttm").fetchone()[0]),
             ec_top3=", ".join(f"{r[1].rstrip(' *')} ({r[2]})" for r in ranking[:3]))
    return series, ranking


def plot_earnings(series, ranking, b: dict, codebook: str) -> None:
    matplotlib, plt = deck_charts.setup()
    S = deck_charts
    fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=S.SURFACE)
    S.style(ax)
    years = [r[0] for r in series]
    for col, color, name in ((2, S.S1, 'Mentions "risk" next to AI (no model)'), (3, S.S2, f"Both models: AI framed as a risk ({codebook})")):
        ys = [float(r[col]) for r in series]
        ax.plot(years, ys, color=color, lw=2, marker="o", ms=4.5, mec=S.SURFACE, mew=1.5, label=name)
        ax.annotate(f"{ys[-1]:.1f}%", (years[-1], ys[-1]), xytext=(8, 0), textcoords="offset points",
                    va="center", color=S.INK, fontsize=10, fontweight="bold")
    ax.set_xticks(years, [str(y) if y != years[-1] else f"{y}\n(to {b['as_of'][5:]})" for y in years], fontsize=9)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_ylim(0, None)
    ax.set_title("Share of S&P 500 earnings calls where AI is discussed as a risk", loc="left",
                 color=S.INK, fontsize=12, fontweight="bold", pad=22)
    ax.text(0, 1.02, "Calls per calendar year; denominator is every unique, non-stub S&P 500 call in the corpus",
            transform=ax.transAxes, color=S.INK2, fontsize=9)
    ax.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=S.INK)
    fig.text(0.01, 0.01, f"Source: defeatbeta/yahoo-finance-data transcripts (ODC-BY). Model line: risk codebook {codebook}, "
             "witness proposal, not hand-verified.", color=S.INK2, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT_DIR / "ai-risk-by-year.svg", facecolor=S.SURFACE, metadata={"Date": None, "Creator": None})
    plt.close(fig)

    shown = [r for r in ranking if r[2] > 0][::-1]
    fig, ax = plt.subplots(figsize=(8, 0.36 * len(shown) + 1.5), facecolor=S.SURFACE)
    ax.set_facecolor(S.SURFACE)
    ax.barh([r[1] for r in shown], [r[2] for r in shown], color=S.S1, height=0.62)
    for i, r in enumerate(shown):
        ax.text(r[2] + 0.4, i, str(r[2]), va="center", color=S.INK, fontsize=9)
    for s in ("top", "right", "bottom"):
        ax.spines[s].set_visible(False)
    ax.set_xticks([])
    ax.tick_params(length=0, labelsize=9.5, labelcolor=S.INK)
    ax.set_title(f"AI risks raised on S&P 500 calls, 12 months to {b['as_of']}", loc="left",
                 color=S.INK, fontsize=12, fontweight="bold", pad=18)
    ax.text(0, 1.01, f"Number of companies; both models must propose the window. Risk codebook {codebook}; * = new in v0.2.",
            transform=ax.transAxes, color=S.INK2, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "risk-ranking-ttm.svg", facecolor=S.SURFACE, metadata={"Date": None, "Creator": None})
    plt.close(fig)


def table(path: str) -> list[dict]:
    with (ROOT / path).open() as f:
        return list(csv.DictReader((l for l in f if not l.startswith("#")), delimiter="\t"))


def other_bindings(cb: dict, b: dict) -> None:
    qi = {r["intent"]: r for r in table(FIXED["question_intents"])}
    b.update(q_revenue_pct=f"{float(qi['q_revenue']['pct_of_ai_questions']):.1f}",
             q_controls_pct=f"{float(qi['q_controls']['pct_of_ai_questions']):.1f}")
    ds = {r["risk_type"]: r for r in table(cb["dialogue"])}
    b.update(ds_exec_safety=f"{float(ds['safety_ethics']['executives_pct']):.0f}",
             ds_hn_safety=f"{float(ds['safety_ethics']['hn_anthropic_pct']):.0f}",
             ds_wp_safety=f"{float(ds['safety_ethics']['wikipedia_pct']):.0f}",
             ds_sec_cyber=f"{float(ds['cyber']['hn_security_pct']):.0f}")
    cve = table(FIXED["cve_monthly_ai"])
    b.update(cve_claude_total=f"{sum(int(r['n_credit_claude']) for r in cve):,}",
             cve_ai_total=f"{sum(int(r['n_ai_credited']) for r in cve):,}",
             cve_first=cve[0]["month"], cve_last=cve[-1]["month"])


def quotes(b: dict) -> list[str]:
    text = re.sub(r"\s+", " ", git("show", f"{PAPER_V0}:{PAPER}").replace("**", "").replace("*", ""))
    errs = []
    for k, q in QUOTES.items():
        if q not in text:
            errs.append(f"quote {k} not found in {PAPER}@{PAPER_V0}: {q}")
        b[k] = q
    return errs


# ---------------------------------------------------------------- render
CAPTION_OK = re.compile(r"\{\{\w+\}\}|v0\.\d+(-draft)?|S&P 500|12 months|33,000\+|≥ 0\.5|edition v0")


def render(b: dict) -> tuple[str, list[str]]:
    tpl = TEMPLATE.read_text()
    errs = []
    for i, line in enumerate(tpl.splitlines(), 1):
        if 'class="src"' in line and re.search(r"\d", CAPTION_OK.sub("", line)):
            errs.append(f"deck.template.md:{i}: unbound number in caption")
    missing = sorted(set(re.findall(r"\{\{(\w+)\}\}", tpl)) - set(b))
    errs += [f"unresolved binding {{{{{m}}}}}" for m in missing]
    return re.sub(r"\{\{(\w+)\}\}", lambda m: b.get(m.group(1), m.group(0)), tpl), errs


def build(codebook: str) -> tuple[dict[str, bytes], list[str]]:
    cb = CODEBOOKS[codebook]
    inputs = [cb["file"], cb["ec_scores"], cb["dialogue"], *FIXED.values(), "corpus/earnings-calls/calls.tsv",
              "corpus/earnings-calls/ai-windows.parquet", "deck/deck.template.md", "scripts/build_edition.py",
              "scripts/deck_charts.py", "dag.lock.tsv"]
    errs = preflight(cb, inputs)
    if errs:
        return {}, errs
    head = git("rev-parse", "HEAD").strip()
    b = {"codebook": codebook, "codebook_status": cb["status"], "source_commit": head[:12], "paper_v0": PAPER_V0,
         "generated_notice": f"<!-- GENERATED by scripts/build_edition.py --codebook {codebook} from {head}. "
                             "Edit deck/deck.template.md, not this file. -->"}
    errs += quotes(b)
    OUT_DIR.mkdir(exist_ok=True)
    series, ranking = earnings(cb, b)
    plot_earnings(series, ranking, b, codebook)
    deck_charts.OUT = OUT_DIR
    deck_charts.cve(*deck_charts.setup())
    other_bindings(cb, b)
    md, rerrs = render(b)
    errs += rerrs
    outs = {"DECK.md": md.encode()}
    for n in ("ai-risk-by-year.svg", "risk-ranking-ttm.svg", "cve-ai-credit.svg"):
        outs[f"deck/{n}"] = (OUT_DIR / n).read_bytes()
    stamp = {
        "edition_of": head,
        "codebook": {"risk": codebook, "risk_file": cb["file"], "risk_blake3": b3(ROOT / cb["file"]),
                     "question_intents": "corpus/earnings-calls/codebook-questions-v0.1.tsv"},
        "rule": "positive = DeBERTa and ModernBERT both >= 0.5",
        "dag_lock_blake3": b3(ROOT / "dag.lock.tsv"),
        "paper_v0": f"{PAPER}@{PAPER_V0}",
        "tools": {"python": "duckdb==2.0.0 matplotlib==3.10.7 blake3==1.0.11",
                  "render": "npx @marp-team/marp-cli@4.1.2 DECK.md --pptx --allow-local-files"},
        "bindings": {k: v for k, v in sorted(b.items()) if k != "generated_notice"},
        "inputs": {p: b3(ROOT / p) for p in sorted(inputs) if (ROOT / p).is_file()},
        "outputs": {k: blake3.blake3(v).hexdigest() for k, v in sorted(outs.items())},
        "references": {p: b3(ROOT / p) for p in (FIXED["question_chart"], FIXED["dialogue_chart"])},
    }
    outs["deck/STAMP.json"] = (json.dumps(stamp, indent=2, ensure_ascii=False) + "\n").encode()
    return outs, errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--codebook", required=True, choices=sorted(CODEBOOKS))
    ap.add_argument("--check", action="store_true", help="rebuild and compare; write nothing that differs")
    a = ap.parse_args()
    before = {p: (ROOT / p).read_bytes() for p in ("DECK.md", "deck/ai-risk-by-year.svg", "deck/risk-ranking-ttm.svg",
                                                   "deck/cve-ai-credit.svg", "deck/STAMP.json") if (ROOT / p).exists()}
    outs, errs = build(a.codebook)
    if errs:
        for p, v in before.items():   # leave the tree as it was
            (ROOT / p).write_bytes(v)
        print("build failed:\n  " + "\n  ".join(errs), file=sys.stderr)
        return 1
    if a.check:
        diff = [p for p, v in outs.items() if before.get(p) != v]
        for p, v in before.items():
            (ROOT / p).write_bytes(v)
        print("edition is current" if not diff else "edition would change: " + ", ".join(diff))
        return 1 if diff else 0
    for p, v in outs.items():
        (ROOT / p).write_bytes(v)
    print(f"built edition of {outs and json.loads(outs['deck/STAMP.json'])['edition_of'][:12]} "
          f"with risk codebook {a.codebook}. Review `git diff`, then commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
