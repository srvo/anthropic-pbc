#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "duckdb==2.0.0",
#   "matplotlib==3.10.7",
# ]
# ///
"""AI-as-a-risk on S&P 500 earnings calls: the time series and the current ranking.

Two measures, side by side, because neither is clean on its own:

  lexical   a call has an AI window (sentence +-1) containing the word "risk"
            (risk, risks, risky, riskier, riskiest). Deterministic and
            re-checkable from verbatim text by anyone. Over-counts: AI used *for*
            risk management (insurers, banks, brokers) matches too.
  witnesses both NLI witnesses score the window >= 0.5 on `ai_risk`
            (codebook v0.1). A model proposal under docs/bert-enrichment-spec.md
            §5; no human gold set yet, so its precision is unknown.

The citable claim is the *shape* the two share, not either level.

The ranking covers the trailing 12 months to --as-of (default: the latest call
date in the corpus, so no clock enters). A firm counts toward a risk type when
at least one of its windows is proposed as both `ai_risk` and that type. Every
counted window is written verbatim to risk-quotes-ttm.tsv with its window_id.

    uv run scripts/ec_risk_series.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import display  # noqa: E402  (the one number-to-text path)
from fractions import Fraction  # noqa: E402
CORPUS = ROOT / "corpus" / "earnings-calls"
REPORT = ROOT / "proposals" / "earnings-calls" / "codebook-v0.1" / "report"
RISK_WORD = r"(?i)\brisk(s|y|ier|iest)?\b"
TYPES = ["regulation", "cyber", "privacy", "accuracy", "bias", "labor", "disruption",
         "capex", "energy", "supply", "ip", "safety_ethics"]
LABELS = {"regulation": "Regulation", "cyber": "Cybersecurity", "privacy": "Data privacy",
          "accuracy": "Accuracy / hallucination", "bias": "Bias / fairness", "labor": "Jobs / labor",
          "disruption": "Disruption of the business", "capex": "Overspending / capex return",
          "energy": "Energy / power", "supply": "Chip & supply constraints", "ip": "Intellectual property",
          "safety_ethics": "Safety / ethics / misuse"}
FIRST_YEAR = 2013

# Reference palette (dataviz skill, light mode): slots 1-2, chart surface, inks.
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
S1, S2 = "#2a78d6", "#eb6834"


def build(con: duckdb.DuckDBPyConnection, as_of: str) -> None:
    con.execute(f"""CREATE TABLE calls AS SELECT symbol, fiscal_year, fiscal_quarter, report_date
        FROM read_csv('{CORPUS / "calls.tsv"}')
        WHERE (duplicate_of IS NULL OR duplicate_of = '') AND n_paragraphs > 2 AND report_date <= DATE '{as_of}'""")
    con.execute(f"""CREATE TABLE w AS SELECT w.window_id, w.symbol, w.fiscal_year, w.fiscal_quarter,
            w.report_date::DATE AS report_date,
            w.speaker, w.role, w.text, regexp_matches(w.text, '{RISK_WORD}') AS lex, f.* EXCLUDE (window_id, symbol,
            fiscal_year, fiscal_quarter, paragraph_number, role)
        FROM '{CORPUS / "ai-windows.parquet"}' w
        JOIN read_csv('{REPORT / "window-flags.tsv"}') f USING (window_id)""")
    con.execute("""CREATE TABLE cw AS SELECT c.*, bool_or(w.lex) AS lex, bool_or(w.ai_risk) AS nli
        FROM calls c LEFT JOIN w USING (symbol, fiscal_year, fiscal_quarter) GROUP BY ALL""")


def write_series(con, as_of: str) -> list[tuple]:
    counts = con.execute(f"""SELECT year(report_date)::INT AS year, count(*)::INT AS calls,
            (count(*) FILTER (WHERE lex))::INT AS calls_lexical, (count(*) FILTER (WHERE nli))::INT AS calls_witnesses
        FROM cw WHERE year(report_date) >= {FIRST_YEAR} GROUP BY 1 ORDER BY 1""").fetchall()
    rows = [(y, n, lx, nl, display.pct(lx, n, 2), display.pct(nl, n, 2)) for y, n, lx, nl in counts]
    head = "year\tcalls\tcalls_lexical\tcalls_witnesses\tpct_lexical\tpct_witnesses\n"
    body = "".join("\t".join(display.cell(x) for x in r) + "\n" for r in rows)
    note = f"# calendar year of call date; {as_of[:4]} runs to {as_of}. Denominator: unique, non-stub S&P 500 calls.\n"
    (REPORT / "ai-risk-by-year.tsv").write_text(note + head + body)
    return rows


def write_ranking(con, as_of: str) -> list[tuple]:
    since = f"DATE '{as_of}' - INTERVAL 1 YEAR"
    con.execute(f"CREATE TABLE ttm AS SELECT * FROM w WHERE report_date > {since} AND report_date <= DATE '{as_of}' AND ai_risk")
    n_firms = con.execute(f"SELECT count(DISTINCT symbol) FROM calls WHERE report_date > {since}").fetchone()[0]
    rows = []
    for t in TYPES:
        firms, wins = con.execute(f"SELECT count(DISTINCT symbol), count(*) FROM ttm WHERE {t}").fetchone()
        rows.append((t, LABELS[t], firms, wins))
    rows.sort(key=lambda r: (-r[2], -r[3], r[0]))
    risk_firms, risk_wins = con.execute("SELECT count(DISTINCT symbol), count(*) FROM ttm").fetchone()
    note = (f"# trailing 12 months to {as_of}: {n_firms} S&P 500 firms held calls; {risk_firms} had >= 1 window "
            f"proposed as ai_risk by both witnesses ({risk_wins} windows). Witness proposals, no gold set.\n")
    (REPORT / "risk-ranking-ttm.tsv").write_text(
        note + "rank\trisk_type\tlabel\tfirms\twindows\n"
        + "".join(f"{i}\t{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\n" for i, r in enumerate(rows, 1)))
    types_expr = " || ".join(f"CASE WHEN {t} THEN '{t};' ELSE '' END" for t in TYPES)
    con.execute(f"""COPY (SELECT report_date, symbol, speaker, role, rtrim({types_expr}, ';') AS risk_types,
            window_id, replace(replace(text, chr(10), ' '), chr(9), ' ') AS quote
        FROM ttm ORDER BY report_date DESC, symbol, window_id)
        TO '{REPORT / "risk-quotes-ttm.tsv"}' (HEADER, DELIMITER '\t')""")
    return rows


def plot(series: list[tuple], ranking: list[tuple], as_of: str) -> None:
    import matplotlib
    matplotlib.use("svg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"svg.hashsalt": "ec-risk", "font.family": "DejaVu Sans", "font.size": 10,
                         "axes.edgecolor": INK2, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
    meta = {"Date": None, "Creator": None}

    years = [r[0] for r in series]
    fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    for col, color, label in ((4, S1, 'Mentions "risk" next to AI'), (5, S2, "Both models: AI framed as a risk")):
        ys = [float(Fraction(100 * r[col - 2], r[1])) for r in series]   # positions; the label is exact
        ax.plot(years, ys, color=color, lw=2, marker="o", ms=4.5, mec=SURFACE, mew=1.5, label=label)
        ax.annotate(f"{display.pct(series[-1][col - 2], series[-1][1], 1)}%", (years[-1], ys[-1]), xytext=(8, 0), textcoords="offset points",
                    va="center", color=INK, fontsize=10, fontweight="bold")
    ax.set_xticks(years, [str(y) if y != years[-1] else f"{y}\n(to {as_of[5:]})" for y in years], fontsize=9)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_ylim(0, None)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)
    ax.set_title("Share of S&P 500 earnings calls where AI is discussed as a risk", loc="left",
                 color=INK, fontsize=12, fontweight="bold", pad=22)
    ax.text(0, 1.02, "Calls per calendar year; denominator is every unique S&P 500 call in the corpus",
            transform=ax.transAxes, color=INK2, fontsize=9)
    ax.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=INK)
    fig.text(0.01, 0.01, "Source: defeatbeta/yahoo-finance-data transcripts (ODC-BY). Model line is a witness "
             "proposal, not hand-verified.", color=INK2, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(REPORT / "ai-risk-by-year.svg", facecolor=SURFACE, metadata=meta)
    plt.close(fig)

    shown = [r for r in ranking if r[2] > 0][::-1]
    fig, ax = plt.subplots(figsize=(8, 0.42 * len(shown) + 1.3), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.barh([r[1] for r in shown], [r[2] for r in shown], color=S1, height=0.62)
    for i, r in enumerate(shown):
        ax.text(r[2] + 0.4, i, str(r[2]), va="center", color=INK, fontsize=9)
    for s in ("top", "right", "bottom"):
        ax.spines[s].set_visible(False)
    ax.set_xticks([])
    ax.tick_params(length=0, labelsize=9.5, labelcolor=INK)
    ax.set_title(f"AI risks raised on S&P 500 calls, 12 months to {as_of}", loc="left",
                 color=INK, fontsize=12, fontweight="bold", pad=18)
    ax.text(0, 1.01, "Number of companies; a window counts when both models propose it", transform=ax.transAxes,
            color=INK2, fontsize=9)
    fig.tight_layout()
    fig.savefig(REPORT / "risk-ranking-ttm.svg", facecolor=SURFACE, metadata=meta)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--as-of", default="", help="YYYY-MM-DD; default = latest call date in the corpus")
    a = ap.parse_args()
    con = duckdb.connect()
    as_of = a.as_of or str(con.execute(
        f"SELECT max(report_date) FROM read_csv('{CORPUS / 'calls.tsv'}')").fetchone()[0])
    build(con, as_of)
    series = write_series(con, as_of)
    ranking = write_ranking(con, as_of)
    plot(series, ranking, as_of)
    for r in series[-5:]:
        print(f"{r[0]}: lexical {r[4]}%  witnesses {r[5]}%  ({r[1]} calls)")
    for i, r in enumerate(ranking, 1):
        print(f"{i:2}. {r[1]:28} {r[2]:3} firms  {r[3]:4} windows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
