#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "duckdb==2.0.0",
#   "matplotlib==3.10.7",
# ]
# ///
"""What sell-side analysts ask S&P 500 companies about AI: selling it, or governing it?

Units: corpus/earnings-calls/ai-questions.parquet (scripts/ec_questions.py).
Intent: codebook-questions-v0.1, scored by the two NLI witnesses
(scripts/ec_classify.py). A question is proposed for an intent when BOTH witnesses
score >= 0.5: a witness proposal (docs/bert-enrichment-spec.md §5), no gold set yet.

Groups (from the codebook's `group` column):
  commercial  q_revenue, q_efficiency       "how much can you sell / save?"
  capital     q_spend                       "what are you spending, and the return?"
  threat      q_competition                 "does AI hurt your business?"
  workforce   q_workforce
  oversight   q_risk, q_controls, q_regulation, q_harm, q_security
  controls    q_controls alone: the direct "how do you govern/control your AI risk?"

Beside the witnesses, a deterministic word measure (COMMERCIAL_WORDS,
OVERSIGHT_WORDS) anyone can re-check from the verbatim text. It is noisy in both
directions (e.g. "regulatory capital" on a bank call), so it is a cross-check
on direction, not a precise rate.

    uv run scripts/ec_question_report.py [--as-of YYYY-MM-DD]

Outputs (proposals/earnings-calls/codebook-questions-v0.1/report/): agreement.tsv,
by-year.tsv, ttm.tsv, oversight-questions.tsv (every flagged question, verbatim),
intent-ttm.svg. --as-of defaults to the latest call date; no clock enters.
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
PROP = ROOT / "proposals" / "earnings-calls" / "codebook-questions-v0.1"
REPORT = PROP / "report"
QUESTIONS = CORPUS / "ai-questions.parquet"
CODEBOOK = CORPUS / "codebook-questions-v0.1.tsv"

OVERSIGHT = ["q_risk", "q_controls", "q_regulation", "q_harm", "q_security"]
COMMERCIAL = ["q_revenue", "q_efficiency"]
OVERSIGHT_WORDS = (r"(?i)\b(governance|govern|governing|oversight|guardrails?|safeguards?|responsible ai|"
                   r"safety|ethics?|ethical|hallucinat\w*|liabilit\w*|regulat\w*|compliance|privacy|bias|"
                   r"misuse|accountab\w*)\b")
COMMERCIAL_WORDS = (r"(?i)\b(revenues?|monetiz\w*|monetis\w*|pricing|prices?|demand|orders?|bookings|backlog|"
                    r"sales|units?|shipments?|margins?|attach|upsell|arr|tam|market share|growth)\b")
LABELS = {"q_revenue": "Revenue, demand, pricing", "q_spend": "AI spending & its return",
          "q_efficiency": "Cost savings, efficiency", "q_competition": "AI as a threat to the business",
          "q_security": "Security, privacy", "q_risk": "Risks / downsides (any)",
          "q_workforce": "Jobs, headcount", "q_controls": "How do you control / govern AI risk?",
          "q_regulation": "Regulation, liability", "q_harm": "Harm to customers or society"}

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
S1, S2, MUTED = "#2a78d6", "#eb6834", "#a8a69f"


def tsv(con, sql: str, path: Path, note: str = "", derived: dict | None = None) -> None:
    """Write a table. Columns starting with `_` are counts for `derived` (column -> function
    of the row) and are not written. No SQL rounding: display.py formats from exact counts."""
    rel = con.execute(sql)
    cols = [d[0] for d in rel.description]
    keep = [c for c in cols if not c.startswith("_")]
    out = []
    for r in rel.fetchall():
        row = dict(zip(cols, r))
        for c, fn in (derived or {}).items():
            row[c] = fn(row)
        out.append("\t".join(display.cell(row[c]) for c in keep) + "\n")
    path.write_text((f"# {note}\n" if note else "") + "\t".join(keep) + "\n" + "".join(out))


def kappa(r: dict) -> str | None:
    k = display.kappa(r["_n"], r["_pos_a"], r["_pos_b"], r["_agree"])
    return None if k is None else display.round_half_up(k, 3)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--as-of", default="")
    a = ap.parse_args()
    con = duckdb.connect()
    as_of = a.as_of or str(con.execute(f"SELECT max(report_date) FROM read_csv('{CORPUS / 'calls.tsv'}')").fetchone()[0])
    REPORT.mkdir(parents=True, exist_ok=True)

    hyps = [r[0] for r in con.execute(f"SELECT id FROM read_csv('{CODEBOOK}', delim='\t', header=true)").fetchall()]
    con.execute(f"""CREATE TABLE s AS SELECT d.question_id, d.hypothesis_id, d.p_entail >= 0.5 AS d, m.p_entail >= 0.5 AS m
        FROM '{PROP / 'deberta.parquet'}' d JOIN '{PROP / 'modernbert.parquet'}' m USING (question_id, hypothesis_id)""")
    agg = ", ".join(f"bool_or(hypothesis_id = '{h}' AND d AND m) AS {h}" for h in hyps)
    con.execute(f"""CREATE TABLE q AS SELECT x.*, f.* EXCLUDE (question_id),
            regexp_matches(x.text, '{OVERSIGHT_WORDS}') AS w_oversight,
            regexp_matches(x.text, '{COMMERCIAL_WORDS}') AS w_commercial,
            year(x.report_date::DATE) AS year
        FROM '{QUESTIONS}' x JOIN (SELECT question_id, {agg} FROM s GROUP BY 1) f USING (question_id)""")
    con.execute(f"ALTER TABLE q ADD COLUMN oversight BOOLEAN; UPDATE q SET oversight = {' OR '.join(OVERSIGHT)}")
    con.execute(f"ALTER TABLE q ADD COLUMN commercial BOOLEAN; UPDATE q SET commercial = {' OR '.join(COMMERCIAL)}")

    tsv(con, """SELECT hypothesis_id, count(*) AS n_questions, count(*) FILTER (WHERE d) AS pos_deberta,
            count(*) FILTER (WHERE m) AS pos_modernbert, count(*) FILTER (WHERE d AND m) AS pos_both,
            NULL AS cohen_kappa, count(*)::INT AS _n, (count(*) FILTER (WHERE d))::INT AS _pos_a,
            (count(*) FILTER (WHERE m))::INT AS _pos_b, (count(*) FILTER (WHERE d = m))::INT AS _agree
        FROM s GROUP BY 1 ORDER BY pos_both DESC, 1""", REPORT / "agreement.tsv", derived={"cohen_kappa": kappa})

    pcts = ["commercial", "q_spend", "q_competition", "q_workforce", "oversight", "q_controls", "w_commercial", "w_oversight"]
    share_counts = ", ".join(f"(count(*) FILTER (WHERE {c}))::INT AS _n_{c}" for c in pcts) + ", count(*)::INT AS _n_all"
    names = {"pct_commercial": "commercial", "pct_capital": "q_spend", "pct_threat": "q_competition",
             "pct_workforce": "q_workforce", "pct_oversight": "oversight", "pct_controls": "q_controls",
             "pct_words_commercial": "w_commercial", "pct_words_oversight": "w_oversight"}
    year_derived = {k: (lambda c: lambda r: display.pct(r[f"_n_{c}"], r["_n_all"], 2))(c) for k, c in names.items()}
    cols = ("count(*) AS ai_questions, NULL AS pct_commercial, NULL AS pct_capital, NULL AS pct_threat, "
            "NULL AS pct_workforce, NULL AS pct_oversight, NULL AS pct_controls, "
            "count(*) FILTER (WHERE oversight) AS n_oversight, count(*) FILTER (WHERE q_controls) AS n_controls, "
            f"NULL AS pct_words_commercial, NULL AS pct_words_oversight, {share_counts}")
    tsv(con, f"""SELECT q.year, c.questioner_turns, {cols} FROM q
            JOIN (SELECT year(report_date) AS year, sum(n_questioner_turns) AS questioner_turns
                  FROM read_csv('{CORPUS / 'calls.tsv'}') JOIN read_csv('{CORPUS / 'question-calls.tsv'}')
                  USING (symbol, fiscal_year, fiscal_quarter) GROUP BY 1) c USING (year)
            WHERE q.report_date <= '{as_of}' GROUP BY ALL ORDER BY 1""",
        REPORT / "by-year.tsv",
        f"calendar year of call date, to {as_of}. pct_* = share of AI questions; both witnesses >= 0.5 "
        "(witness proposals, no gold set); pct_words_* = deterministic word match.", derived=year_derived)

    ttm = f"report_date > CAST(DATE '{as_of}' - INTERVAL 1 YEAR AS VARCHAR) AND report_date <= '{as_of}'"
    n_ttm, n_firms, n_analysts = con.execute(
        f"SELECT count(*), count(DISTINCT symbol), count(DISTINCT speaker) FROM q WHERE {ttm}").fetchone()
    union = " UNION ALL ".join(f"SELECT '{h}' AS intent, count(*) FILTER (WHERE {h}) AS n FROM q WHERE {ttm}" for h in hyps)
    tsv(con, f"""SELECT intent, n::INT AS questions, NULL AS pct_of_ai_questions FROM ({union})
            ORDER BY n DESC, intent""", REPORT / "ttm.tsv",
        f"12 months to {as_of}: {n_ttm} AI questions from {n_analysts} questioners on {n_firms} S&P 500 firms. "
        "A question can carry several intents. Witness proposals, no gold set.",
        derived={"pct_of_ai_questions": lambda r: display.pct(r["questions"], n_ttm, 2)})

    flags = " || ".join(f"CASE WHEN {h} THEN '{h};' ELSE '' END" for h in OVERSIGHT)
    con.execute(f"""COPY (SELECT report_date, symbol, speaker, rtrim({flags}, ';') AS oversight_intents,
            w_oversight AS oversight_words, question_id, replace(replace(text, chr(10), ' '), chr(9), ' ') AS question
        FROM q WHERE oversight ORDER BY report_date DESC, symbol, question_id)
        TO '{REPORT / 'oversight-questions.tsv'}' (HEADER, DELIMITER '\t')""")

    rows = [(h, int(k)) for h, k in con.execute(f"SELECT intent, questions FROM read_csv('{REPORT / 'ttm.tsv'}', "
                                                 "comment='#', delim='\t', header=true)").fetchall()]
    plot(rows, n_ttm, as_of)
    print(open(REPORT / "ttm.tsv").read())
    return 0


def plot(rows: list[tuple], n: int, as_of: str) -> None:
    import matplotlib
    matplotlib.use("svg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"svg.hashsalt": "ec-questions", "font.family": "DejaVu Sans", "font.size": 10})
    group = {h: ("oversight" if h in OVERSIGHT else "commercial" if h in COMMERCIAL + ["q_spend"] else "other")
             for h, _ in rows}
    color = {"commercial": S1, "oversight": S2, "other": MUTED}
    shown = rows[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.42 * len(shown) + 1.6), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    pos = [float(Fraction(100 * k, n)) for _, k in shown]   # bar lengths; labels come from display.pct
    ax.barh([LABELS[h] for h, _ in shown], pos, color=[color[group[h]] for h, _ in shown], height=0.62)
    for i, ((h, k), x) in enumerate(zip(shown, pos)):
        ax.text(x + 0.3, i, f"{display.pct(k, n, 1)}%  ({display.count(k)})", va="center", color=INK, fontsize=9)
    for s in ("top", "right", "bottom"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(INK2)
    ax.set_xticks([])
    ax.tick_params(length=0, labelsize=9.5, labelcolor=INK)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=S1, label="Selling it / spending on it"), Patch(color=S2, label="Governing its risks"),
                       Patch(color=MUTED, label="Other")], loc="lower right", frameon=False, fontsize=9, labelcolor=INK)
    ax.set_title("What analysts ask S&P 500 companies about AI", loc="left", color=INK, fontsize=12,
                 fontweight="bold", pad=20)
    ax.text(0, 1.01, f"Share of {display.count(n)} analyst questions on AI, 12 months to {as_of}",
            transform=ax.transAxes, color=INK2, fontsize=9)
    fig.text(0.01, 0.01, "A question can count under several topics. Both NLI models must agree; not hand-verified. "
             "Source: defeatbeta/yahoo-finance-data (ODC-BY).", color=INK2, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(REPORT / "intent-ttm.svg", facecolor=SURFACE, metadata={"Date": None, "Creator": None})
    plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())
