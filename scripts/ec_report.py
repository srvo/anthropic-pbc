#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb==2.0.0"]
# ///
"""Deterministic tables over the two NLI witnesses. Counts, never verdicts.

A window is a *proposed* positive for a hypothesis only when BOTH witnesses
(DeBERTa-v3-large and ModernBERT-large) score P(entailment) >= THRESHOLD.
Each witness's own count and Cohen's kappa between them are reported beside
it, so disagreement is visible rather than averaged away. Rates use the
calls.tsv denominator (unique, non-stub S&P 500 calls), never AI windows alone.

    uv run scripts/ec_report.py            # writes proposals/earnings-calls/codebook-v0.1/report/*.tsv

Speaker role is a heuristic (a speaker heard on >= 3 issuers' calls is treated
as a sell-side analyst); it is reported as such.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus" / "earnings-calls"
PROP = ROOT / "proposals" / "earnings-calls" / "codebook-v0.1"
REPORT = PROP / "report"
THRESHOLD = 0.5


def main() -> int:
    for m in ("deberta", "modernbert"):
        if not (PROP / f"{m}.parquet").exists():
            sys.exit(f"missing {m}.parquet: run scripts/ec_classify.py --model {m}")
    REPORT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"CREATE VIEW w AS SELECT * FROM '{CORPUS / 'ai-windows.parquet'}'")
    con.execute(f"""CREATE VIEW calls AS SELECT * FROM read_csv('{CORPUS / 'calls.tsv'}', delim='\t', header=true)
                    WHERE coalesce(duplicate_of, '') = '' AND n_paragraphs > 2""")
    con.execute(f"CREATE TABLE cb AS SELECT row_number() OVER () AS ord, * FROM read_csv('{CORPUS / 'codebook-v0.1.tsv'}', delim='\t', header=true)")
    con.execute(f"""
      CREATE TABLE s AS
      SELECT d.window_id, d.hypothesis_id, d.p_entail AS p_deb, m.p_entail AS p_mod,
             d.p_entail >= {THRESHOLD} AS pos_deb, m.p_entail >= {THRESHOLD} AS pos_mod,
             (d.p_entail >= {THRESHOLD} AND m.p_entail >= {THRESHOLD}) AS pos
      FROM '{PROP / 'deberta.parquet'}' d JOIN '{PROP / 'modernbert.parquet'}' m USING (window_id, hypothesis_id)""")
    # Wide per-window flags (both-agree), joined to metadata.
    hyps = [r[0] for r in con.execute("SELECT id FROM cb ORDER BY ord").fetchall()]
    flags = ", ".join(f"bool_or(pos) FILTER (WHERE hypothesis_id = '{h}') AS {h}" for h in hyps)
    con.execute(f"""CREATE TABLE f AS SELECT w.*, x.* EXCLUDE (window_id)
                    FROM w JOIN (SELECT window_id, {flags} FROM s GROUP BY 1) x USING (window_id)""")

    def out(name: str, sql: str) -> None:
        con.execute(f"COPY ({sql}) TO '{REPORT / name}' (HEADER, DELIMITER '\t')")

    # 1. Witness agreement per hypothesis.
    out("agreement.tsv", """
      SELECT cb."group", hypothesis_id, count(*) AS n_windows,
             sum(pos_deb::INT) AS pos_deberta, sum(pos_mod::INT) AS pos_modernbert, sum(pos::INT) AS pos_both,
             round(( avg((pos_deb = pos_mod)::INT)
                     - (avg(pos_deb::INT) * avg(pos_mod::INT) + (1 - avg(pos_deb::INT)) * (1 - avg(pos_mod::INT))) )
                   / nullif(1 - (avg(pos_deb::INT) * avg(pos_mod::INT) + (1 - avg(pos_deb::INT)) * (1 - avg(pos_mod::INT))), 0), 3)
               AS cohen_kappa
      FROM s JOIN cb ON cb.id = s.hypothesis_id GROUP BY ALL ORDER BY min(cb.ord)""")

    # 2. By fiscal year, with the all-calls denominator.
    out("by-year.tsv", """
      WITH c AS (SELECT fiscal_year, count(*) AS calls FROM calls GROUP BY 1),
      k AS (SELECT fiscal_year, count(DISTINCT (symbol, fiscal_quarter)) AS calls_ai,
                   count(DISTINCT (symbol, fiscal_quarter)) FILTER (WHERE about_ai AND ai_risk) AS calls_ai_risk,
                   count(DISTINCT (symbol, fiscal_quarter)) FILTER (WHERE about_ai AND governance) AS calls_ai_governance,
                   count(*) FILTER (WHERE about_ai) AS windows_ai,
                   count(*) FILTER (WHERE about_ai AND ai_risk) AS windows_risk,
                   count(*) FILTER (WHERE about_ai AND ai_opportunity) AS windows_opportunity
            FROM f GROUP BY 1)
      SELECT c.fiscal_year, c.calls, coalesce(calls_ai, 0) AS calls_mentioning_ai,
             coalesce(calls_ai_risk, 0) AS calls_with_ai_risk,
             round(coalesce(calls_ai_risk, 0) / c.calls, 4) AS share_calls_ai_risk,
             coalesce(calls_ai_governance, 0) AS calls_with_ai_governance,
             coalesce(windows_ai, 0) AS windows_ai, coalesce(windows_risk, 0) AS windows_risk,
             coalesce(windows_opportunity, 0) AS windows_opportunity
      FROM c LEFT JOIN k USING (fiscal_year) ORDER BY 1""")

    # 3. Risk types by year (window counts; type and ai_risk both both-agree).
    types = [r[0] for r in con.execute("SELECT id FROM cb WHERE \"group\" = 'risk_type' ORDER BY ord").fetchall()]
    cols = ", ".join(f"count(*) FILTER (WHERE {t}) AS {t}" for t in types)
    out("risk-types-by-year.tsv", f"SELECT fiscal_year, count(*) AS risk_windows, {cols} FROM f "
                                  f"WHERE about_ai AND ai_risk GROUP BY 1 ORDER BY 1")

    # 4. Who raises risk: analyst vs issuer (heuristic role).
    out("by-role.tsv", """
      SELECT role, count(*) FILTER (WHERE about_ai) AS windows_ai,
             count(*) FILTER (WHERE about_ai AND ai_risk) AS windows_risk,
             count(*) FILTER (WHERE about_ai AND ai_opportunity) AS windows_opportunity,
             round(count(*) FILTER (WHERE about_ai AND ai_risk) / nullif(count(*) FILTER (WHERE about_ai), 0), 4) AS share_risk,
             round(count(*) FILTER (WHERE about_ai AND ai_opportunity) / nullif(count(*) FILTER (WHERE about_ai), 0), 4) AS share_opportunity
      FROM f GROUP BY 1 ORDER BY 1""")

    # 5. Per firm, for the join to the Risk-Governance Index (Appendix E).
    tcols = ", ".join(f"count(*) FILTER (WHERE about_ai AND ai_risk AND {t}) AS {t}" for t in types)
    out("by-firm.tsv", f"""
      WITH c AS (SELECT symbol, count(*) AS calls FROM calls GROUP BY 1)
      SELECT c.symbol, c.calls,
             count(DISTINCT (f.fiscal_year, f.fiscal_quarter)) FILTER (WHERE about_ai) AS calls_mentioning_ai,
             min(f.fiscal_year) FILTER (WHERE about_ai) AS first_ai_fy,
             min(f.fiscal_year) FILTER (WHERE about_ai AND ai_risk) AS first_ai_risk_fy,
             count(*) FILTER (WHERE about_ai) AS windows_ai,
             count(*) FILTER (WHERE about_ai AND ai_risk) AS windows_risk,
             count(*) FILTER (WHERE about_ai AND ai_opportunity) AS windows_opportunity,
             count(*) FILTER (WHERE about_ai AND governance) AS windows_governance,
             {tcols}
      FROM c LEFT JOIN f USING (symbol) GROUP BY c.symbol, c.calls ORDER BY c.symbol""")

    # 6. Window-level both-agree flags (ids + metadata only; text lives in the corpus).
    out("window-flags.tsv", f"SELECT window_id, symbol, fiscal_year, fiscal_quarter, paragraph_number, role, "
                            f"{', '.join(hyps)} FROM f ORDER BY symbol, fiscal_year, fiscal_quarter, paragraph_number, window_id")
    for p in sorted(REPORT.glob("*.tsv")):
        print(f"wrote {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
