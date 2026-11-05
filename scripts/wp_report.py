#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb==2.0.0"]
# ///
"""How much of Wikipedia's AI-risk discourse the codebook-v0.1 risk types can name.

codebook-v0.1 was written for company speech. Scoring Wikipedia's AI-risk articles
with it shows which parts of the public "dialogue space" it has no type for:
windows both witnesses propose as `ai_risk` but that get no specific risk type
other than the catch-all `safety_ethics`. Witness proposals, no gold set.

    uv run scripts/wp_report.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import display  # noqa: E402  (the one number-to-text path)


def csv_field(v: str) -> str:
    """Quote a text field the way DuckDB's COPY (DELIMITER '\\t') does, so the table bytes do not change."""
    return '"' + v.replace('"', '""') + '"' if any(c in v for c in '\t"\n\r') else v


P = ROOT / "proposals" / "wikipedia-ai-risk" / "codebook-v0.1"
W = ROOT / "corpus" / "wikipedia-ai-risk" / "windows.parquet"
SPECIFIC = ["regulation", "cyber", "privacy", "accuracy", "bias", "labor", "disruption",
            "capex", "energy", "supply", "ip"]


def main() -> int:
    rep = P / "report"
    rep.mkdir(exist_ok=True)
    con = duckdb.connect()
    con.execute(f"""CREATE TABLE f AS SELECT d.window_id, d.hypothesis_id AS h,
        d.p_entail >= .5 AND m.p_entail >= .5 AS b, d.p_entail >= .5 AS bd, m.p_entail >= .5 AS bm
        FROM '{P / 'deberta.parquet'}' d JOIN '{P / 'modernbert.parquet'}' m USING (window_id, hypothesis_id)""")
    con.execute(f"CREATE TABLE w AS SELECT window_id, title FROM '{W}'")
    spec = ", ".join(f"'{t}'" for t in SPECIFIC)
    con.execute(f"""CREATE TABLE r AS SELECT window_id,
        window_id NOT IN (SELECT window_id FROM f WHERE h IN ({spec}) AND b) AS untyped
        FROM f WHERE h = 'ai_risk' AND b""")
    con.execute(f"""COPY (SELECT h AS hypothesis, count(*) AS n_windows,
          count(*) FILTER (WHERE bd) AS n_deberta, count(*) FILTER (WHERE bm) AS n_modernbert,
          count(*) FILTER (WHERE b) AS n_both FROM f GROUP BY 1 ORDER BY n_both DESC, 1)
        TO '{rep / 'hypotheses.tsv'}' (HEADER, DELIMITER '\t')""")
    art = con.execute("""SELECT title, count(*)::INT AS n_ai_risk_windows,
          (count(*) FILTER (WHERE untyped))::INT AS n_no_specific_type
        FROM r JOIN w USING (window_id) GROUP BY 1 ORDER BY n_no_specific_type DESC, title""").fetchall()
    with (rep / "untyped-by-article.tsv").open("w") as fh:   # no SQL rounding: display.py formats from counts
        fh.write("title\tn_ai_risk_windows\tn_no_specific_type\tpct_no_specific_type\n")
        for title, n_w, n_u in art:
            fh.write("\t".join(display.cell(v) for v in (csv_field(title), n_w, n_u, display.pct(n_u, n_w, 1))) + "\n")
    n, u = con.execute("SELECT count(*), count(*) FILTER (WHERE untyped) FROM r").fetchone()
    tot = con.execute("SELECT count(*) FROM w").fetchone()[0]
    (rep / "summary.tsv").write_text(
        "windows\tai_risk_windows\tno_specific_type\tpct_no_specific_type\n"
        f"{tot}\t{n}\t{u}\t{display.pct(u, n, 1)}\n")
    print(f"{tot} windows; {n} proposed ai_risk; {u} ({display.pct(u, n, 1)}%) with no specific risk type")
    return 0


if __name__ == "__main__":
    sys.exit(main())
