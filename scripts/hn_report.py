#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb==2.0.0"]
# ///
"""Hacker News focused sets: witness agreement, AI-risk share by month, and the
12-month risk-type ranking set beside the earnings-call ranking. IDs only.

Reads corpus/hacker-news/{months.tsv,windows.parquet} and the two witnesses'
scores in proposals/hacker-news/<set>/. Writes to proposals/hacker-news/report/.
No comment text or username is written; examples are item ids with their HN URL.
A positive is a witness proposal (both >= 0.5), not a finding: there is no gold set.

    uv run scripts/hn_report.py
"""

from __future__ import annotations

import re
import sys
from html import escape
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus" / "hacker-news"
PROP = ROOT / "proposals" / "hacker-news"
REPORT = PROP / "report"
EC_RANK = ROOT / "proposals" / "earnings-calls" / "codebook-v0.1" / "report" / "risk-ranking-ttm.tsv"
SETS = ["anthropic", "ai_security"]
TTM = ("2025-09-01", "2026-08-31")   # the archive's last 12 months (it ends 2026-08)
sys.path.insert(0, str(ROOT / "scripts"))
from fractions import Fraction  # noqa: E402

import display  # noqa: E402  (the one number-to-text path)
from ec_risk_series import LABELS, TYPES  # noqa: E402


def load(con: duckdb.DuckDBPyConnection) -> None:
    parts = []
    for s in SETS:
        parts.append(f"""SELECT '{s}' AS "set", d.window_id, d.hypothesis_id AS h, d.p_entail AS pd, m.p_entail AS pm
            FROM '{PROP / s / 'deberta.parquet'}' d JOIN '{PROP / s / 'modernbert.parquet'}' m USING (window_id, hypothesis_id)""")
    con.execute("CREATE TABLE s AS " + " UNION ALL ".join(parts))
    con.execute(f"""CREATE TABLE w AS SELECT * FROM '{CORPUS / 'windows.parquet'}'""")
    con.execute("""CREATE TABLE f AS SELECT "set", window_id, h, pd >= .5 AND pm >= .5 AS b FROM s""")
    con.execute("""CREATE TABLE wf AS SELECT w.*, f.h, f.b FROM w JOIN f USING ("set", window_id)""")
    # comment-level: a comment carries hypothesis h if any of its windows in the set does
    con.execute("""CREATE TABLE c AS SELECT "set", item_id, any_value(day) AS day, h, bool_or(b) AS b
        FROM wf GROUP BY ALL""")


def tsv(path: Path, header: str, rows) -> None:
    with path.open("w") as f:
        f.write(header + "\n")
        for r in rows:
            f.write("\t".join(display.cell(v) for v in r) + "\n")


def agreement(con) -> None:
    rows = con.execute("""SELECT "set", h, count(*)::INT n,
        (count(*) FILTER (WHERE pd >= .5))::INT n_deberta, (count(*) FILTER (WHERE pm >= .5))::INT n_modernbert,
        (count(*) FILTER (WHERE pd >= .5 AND pm >= .5))::INT n_both,
        (count(*) FILTER (WHERE (pd >= .5) = (pm >= .5)))::INT agree
        FROM s GROUP BY 1, 2 ORDER BY 1, 2""").fetchall()
    out = []
    for st, h, n, nd, nm, nb, agree in rows:
        k = display.kappa(n, nd, nm, agree)
        out.append((st, h, n, nd, nm, nb, None if k is None else display.round_half_up(k, 3)))
    tsv(REPORT / "agreement.tsv", "set\thypothesis\tn_windows\tn_deberta\tn_modernbert\tn_both\tkappa", out)


def by_month(con) -> None:
    con.execute(f"CREATE TABLE m AS SELECT * FROM read_csv('{CORPUS / 'months.tsv'}', delim='\t', header=true)")
    rows = con.execute("""SELECT m.month, m.n_comments::INT,
        (count(DISTINCT c.item_id) FILTER (WHERE c."set" = 'anthropic'))::INT anth,
        (count(DISTINCT c.item_id) FILTER (WHERE c."set" = 'anthropic' AND c.h = 'ai_risk' AND c.b))::INT anth_risk,
        (count(DISTINCT c.item_id) FILTER (WHERE c."set" = 'ai_security'))::INT sec,
        (count(DISTINCT c.item_id) FILTER (WHERE c."set" = 'ai_security' AND c.h = 'ai_risk' AND c.b))::INT sec_risk
        FROM m LEFT JOIN c ON strftime(c.day, '%Y-%m') = m.month GROUP BY 1, 2 ORDER BY 1""").fetchall()
    out = [(mo, n, a, ar, display.pct(a, n, 3), display.pct(ar, a, 1) if a else None, s_, sr,
            display.pct(s_, n, 3)) for mo, n, a, ar, s_, sr in rows]
    tsv(REPORT / "by-month.tsv", "month\tn_comments\tn_anthropic\tn_anthropic_ai_risk\tpct_comments_anthropic"
        "\tpct_anthropic_ai_risk\tn_ai_security\tn_ai_security_ai_risk\tpct_comments_ai_security", out)


def ranking(con) -> list[tuple]:
    """Per set: comments with ai_risk AND type (both witnesses), TTM. Share of ai_risk comments."""
    res = []
    for st in SETS:
        base = con.execute(f"""SELECT count(DISTINCT item_id) FROM c WHERE "set" = '{st}' AND h = 'ai_risk' AND b
            AND day BETWEEN '{TTM[0]}' AND '{TTM[1]}'""").fetchone()[0]
        for t in TYPES:
            n = con.execute(f"""SELECT count(DISTINCT x.item_id) FROM c x JOIN c r USING ("set", item_id)
                WHERE x."set" = '{st}' AND x.h = '{t}' AND x.b AND r.h = 'ai_risk' AND r.b
                AND x.day BETWEEN '{TTM[0]}' AND '{TTM[1]}'""").fetchone()[0]
            res.append((st, t, int(n), int(base)))
    ec = {}
    with EC_RANK.open() as f:
        raw = f.read().splitlines()
    tot = int(re.search(r"\((\d+) windows\)", raw[0]).group(1))   # windows proposed ai_risk
    lines = [x.split("\t") for x in raw if not x.startswith("#")]
    hdr, body = lines[0], lines[1:]
    for r in body:
        ec[r[hdr.index("risk_type")]] = (int(r[hdr.index("windows")]), tot)
    out = []
    bases = {st: next(b for s_, _, _, b in res if s_ == st) for st in SETS}
    for t in TYPES:
        row = [t, LABELS[t], ec[t][0], display.pct(ec[t][0], ec[t][1], 1)]
        for st in SETS:
            n, base = next((n, b) for s_, t_, n, b in res if s_ == st and t_ == t)
            row += [n, display.pct(n, base, 1) if base else None]
        out.append(tuple(row))
    out.sort(key=lambda r: (-Fraction(r[4], bases["anthropic"]), r[0]))   # exact share, not the rounded text
    with (REPORT / "risk-ranking-ttm.tsv").open("w") as f:
        f.write(f"# {TTM[0]}..{TTM[1]}. Share of AI-risk units naming each type (a unit can name several). "
                f"Earnings calls: {ec[TYPES[0]][1]} risk windows, trailing 12 months to 2026-11-04. "
                f"HN: comments proposed ai_risk by both witnesses (anthropic {bases['anthropic']}, "
                f"ai_security {bases['ai_security']}). Witness proposals, no gold set.\n")
        f.write("risk_type\tlabel\tcalls_windows\tcalls_pct\tanthropic_comments\tanthropic_pct"
                "\tai_security_comments\tai_security_pct\n")
        for r in out:
            f.write("\t".join(display.cell(v) for v in r) + "\n")
    return [(*r, {"calls": ec[TYPES[0]][1], **bases}) for r in out]


def examples(con) -> None:
    """Item ids (no text) of the most confidently risk-typed comments, per set and type, TTM."""
    rows = con.execute(f"""WITH x AS (
          SELECT s."set", w.item_id, s.h, least(s.pd, s.pm) AS p
          FROM s JOIN w USING ("set", window_id)
          WHERE s.h IN ({", ".join(f"'{t}'" for t in TYPES)}) AND s.pd >= .5 AND s.pm >= .5
            AND w.day BETWEEN '{TTM[0]}' AND '{TTM[1]}'
            AND (s."set", s.window_id) IN (SELECT "set", window_id FROM f WHERE h = 'ai_risk' AND b))
        SELECT "set", h, item_id, max(p)::DOUBLE p FROM x GROUP BY 1, 2, 3
        QUALIFY row_number() OVER (PARTITION BY "set", h ORDER BY max(p) DESC, item_id) <= 10
        ORDER BY 1, 2, 4 DESC, 3""").fetchall()
    tsv(REPORT / "examples-ttm.tsv", "set\trisk_type\titem_id\tmin_witness_p\turl",
        [(st, h, item, display.score(p, 4), f"https://news.ycombinator.com/item?id={item}") for st, h, item, p in rows])


def plot(rank: list[tuple]) -> None:
    """Three panels, same row order, one bar per risk type: share of AI-risk units naming it."""
    panels = [("Earnings calls (executives)", 3, "calls"), ("HN: Anthropic", 5, "anthropic"), ("HN: AI security", 7, "ai_security")]
    exact = lambda r, idx, key: Fraction(100 * r[idx - 1], r[-1][key]) if r[-1][key] else Fraction(0)
    W, rowh, top, left, pw, gap = 920, 26, 92, 190, 210, 42
    H = top + rowh * len(rank) + 56
    vmax = max(float(exact(r, i, key)) for r in rank for _, i, key in panels)
    vmax = (int(vmax // 10) + 1) * 10
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="system-ui,-apple-system,sans-serif" role="img" aria-labelledby="t d">',
         '<style>text{fill:#1b1b1b}.m{fill:#5f6368}.g{stroke:#e3e3e3}.b{fill:#2a6f97}</style>',
         f'<rect width="{W}" height="{H}" fill="#fcfcfb"/>',
         '<title id="t">What kind of AI risk: executives vs Hacker News</title>',
         '<desc id="d">Share of AI-risk passages naming each risk type, in three sources, trailing 12 months.</desc>',
         '<text x="16" y="30" font-size="18" font-weight="600">What kind of AI risk? Executives vs Hacker News</text>',
         f'<text x="16" y="52" font-size="13" class="m">Share of AI-risk units naming each type. Calls: 12 months to 2026-11-04. HN: {TTM[0][:7]} to {TTM[1][:7]}.</text>']
    for k, (name, idx, key) in enumerate(panels):
        x0 = left + k * (pw + gap)
        o.append(f'<text x="{x0}" y="{top - 12}" font-size="13" font-weight="600">{name}</text>')
        for v in (0, vmax // 2, vmax):
            gx = x0 + pw * v / vmax
            o.append(f'<line x1="{gx:.1f}" x2="{gx:.1f}" y1="{top - 4}" y2="{top + rowh * len(rank)}" class="g"/>')
            o.append(f'<text x="{gx:.1f}" y="{top + rowh * len(rank) + 16}" font-size="11" class="m" text-anchor="middle">{v}%</text>')
        for j, r in enumerate(rank):
            y = top + j * rowh
            v = exact(r, idx, key)
            bw = max(pw * float(v) / vmax, 0.0)
            d = r[-1][key]
            t1 = display.pct(r[idx - 1], d, 1) if d else "0.0"
            t0 = display.pct(r[idx - 1], d, 0) if d else "0"
            o.append(f'<g><title>{name}: {escape(r[1])}, {t1}% ({display.count(r[idx - 1])} units)</title>'
                     f'<rect x="{x0}" y="{y + 5}" width="{bw:.1f}" height="{rowh - 10}" rx="2" class="b"/>'
                     f'<text x="{x0 + bw + 4:.1f}" y="{y + rowh / 2 + 4}" font-size="11" class="m">{t0}</text></g>')
    for j, r in enumerate(rank):
        o.append(f'<text x="{left - 10}" y="{top + j * rowh + rowh / 2 + 4}" font-size="12" text-anchor="end">{escape(r[1])}</text>')
    o.append(f'<text x="16" y="{H - 12}" font-size="11" class="m">Ordered by HN: Anthropic. Two NLI witnesses must both score ≥ 0.5; a unit can name several types. Witness proposals, no gold set.</text>')
    o.append("</svg>")
    (REPORT / "risk-ranking-ttm.svg").write_text("\n".join(o) + "\n")


def main() -> int:
    REPORT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    load(con)
    agreement(con)
    by_month(con)
    plot(ranking(con))
    examples(con)
    for p in sorted(REPORT.iterdir()):
        print(p.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
