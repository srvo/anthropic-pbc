#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb==2.0.0"]
# ///
"""The dialogue space under codebook-v0.2-draft: which sources discuss which AI risks.

For each source, the share of its AI-risk units (both witnesses >= 0.5 on
`ai_risk`) that also carry each risk type (both witnesses >= 0.5). Sources:
  executives   earnings-call windows not spoken by an analyst or the operator, 12 months to 2026-11-04
  analysts     analyst questions on calls, 12 months to 2026-11-04
  hn_anthropic Hacker News Anthropic/Claude windows, 2025-09..2026-08
  hn_security  Hacker News AI-security windows, 2025-09..2026-08
  wikipedia    Wikipedia AI-risk article windows, revisions as of 2026-11-04
DRAFT codebook, witness proposals, no gold set. Writes
proposals/cross-source/codebook-v0.2-draft/report/.

    uv run scripts/v02_map.py
"""

from __future__ import annotations

import csv
import sys
from html import escape
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import display  # noqa: E402  (the one number-to-text path)
from fractions import Fraction  # noqa: E402
CB = ROOT / "corpus" / "codebooks" / "codebook-v0.2-draft.tsv"
OUT = ROOT / "proposals" / "cross-source" / "codebook-v0.2-draft" / "report"
EC, HN, WP = ROOT / "corpus" / "earnings-calls", ROOT / "corpus" / "hacker-news", ROOT / "corpus" / "wikipedia-ai-risk"
P = ROOT / "proposals"
# Each source's window. The sources cover different periods; the output table records them ("# window" lines)
# so a reader of the table, and the edition build, can say so.
CALLS = ("2025-11-04", "2026-11-04")    # report_date after the first, through the second
HN_DAYS = ("2025-09-01", "2026-08-31")  # comment day, inclusive
WP_AS_OF = "2026-11-04"                 # the article revisions pinned in corpus/wikipedia-ai-risk/MANIFEST.tsv
WINDOWS = {"executives": f"calls dated after {CALLS[0]} through {CALLS[1]}",
           "analysts": f"calls dated after {CALLS[0]} through {CALLS[1]}",
           "hn_anthropic": f"comments dated {HN_DAYS[0]} to {HN_DAYS[1]}",
           "hn_security": f"comments dated {HN_DAYS[0]} to {HN_DAYS[1]}",
           "wikipedia": f"article revisions as of {WP_AS_OF}"}
SOURCES = [  # (key, label, scores dir, id col, unit filter SQL over table u)
    ("executives", "Executives (calls)", P / "earnings-calls/codebook-v0.2-draft", "window_id",
     f"SELECT window_id AS id FROM '{EC / 'ai-windows.parquet'}' WHERE role NOT IN ('analyst_heuristic', 'operator') "
     f"AND report_date::DATE > DATE '{CALLS[0]}' AND report_date::DATE <= DATE '{CALLS[1]}'"),
    ("analysts", "Analyst questions", P / "earnings-calls/codebook-v0.2-draft-questions", "question_id",
     f"SELECT question_id AS id FROM '{EC / 'ai-questions.parquet'}' "
     f"WHERE report_date::DATE > DATE '{CALLS[0]}' AND report_date::DATE <= DATE '{CALLS[1]}'"),
    ("hn_anthropic", "HN: Anthropic", P / "hacker-news/anthropic-v0.2-draft", "window_id",
     f"""SELECT window_id AS id FROM '{HN / 'windows.parquet'}' WHERE "set" = 'anthropic' AND day BETWEEN '{HN_DAYS[0]}' AND '{HN_DAYS[1]}'"""),
    ("hn_security", "HN: AI security", P / "hacker-news/ai_security-v0.2-draft", "window_id",
     f"""SELECT window_id AS id FROM '{HN / 'windows.parquet'}' WHERE "set" = 'ai_security' AND day BETWEEN '{HN_DAYS[0]}' AND '{HN_DAYS[1]}'"""),
    ("wikipedia", "Wikipedia", P / "wikipedia-ai-risk/codebook-v0.2-draft", "window_id",
     f"SELECT window_id AS id FROM '{WP / 'windows.parquet'}'"),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cb = list(csv.DictReader(CB.open(), delimiter="\t"))
    types = [r for r in cb if r["group"] == "risk_type"]
    con = duckdb.connect()
    shares: dict[str, dict[str, tuple[int, int]]] = {}
    for key, _, d, idc, units in SOURCES:
        con.execute(f"""CREATE OR REPLACE TABLE f AS
            SELECT x.{idc} AS id, x.hypothesis_id AS h, x.p_entail >= .5 AND y.p_entail >= .5 AS b
            FROM '{d / 'deberta.parquet'}' x JOIN '{d / 'modernbert.parquet'}' y USING ({idc}, hypothesis_id)
            WHERE x.{idc} IN ({units})""")
        risk = int(con.execute("SELECT count(*) FROM f WHERE h = 'ai_risk' AND b").fetchone()[0])
        shares[key] = {}
        for t in types:
            n = con.execute(f"""SELECT count(*) FROM f a JOIN f r USING (id)
                WHERE a.h = '{t['id']}' AND a.b AND r.h = 'ai_risk' AND r.b""").fetchone()[0]
            n = int(n)
            shares[key][t["id"]] = (n, risk)
    new = {r["id"] for r in cb if r["status"].startswith("v0.2")}
    rows = sorted(types, key=lambda t: -max(Fraction(shares[k][t["id"]][0], max(shares[k][t["id"]][1], 1)) for k, *_ in SOURCES))
    with (OUT / "dialogue-space.tsv").open("w") as f:
        f.write("# Share (%) of each source's AI-risk units naming each risk type; both witnesses >= 0.5. "
                "codebook-v0.2-draft (DRAFT wording), witness proposals, no gold set.\n")
        for k, *_ in SOURCES:
            f.write(f"# window {k}: {WINDOWS[k]}\n")
        f.write("risk_type\tnew_in_v0.2\t" + "\t".join(f"{k}_pct\t{k}_n" for k, *_ in SOURCES) + "\n")
        f.write("ai_risk_units\t\t" + "\t".join(f"\t{shares[k][types[0]['id']][1]}" for k, *_ in SOURCES) + "\n")
        for t in rows:
            cells = []
            for k, *_ in SOURCES:
                n, base = shares[k][t["id"]]
                cells += [display.pct(n, base, 1) if base else "", str(n)]
            f.write(f"{t['id']}\t{'yes' if t['id'] in new else ''}\t" + "\t".join(cells) + "\n")
    plot(rows, shares, new)
    print(f"wrote {OUT.relative_to(ROOT)}/dialogue-space.tsv and .svg")
    return 0


def plot(rows, shares, new) -> None:
    """Heatmap: risk types x sources, cell = share; one sequential hue, value printed."""
    cw, rh, left, top = 128, 24, 210, 108
    W, H = left + cw * len(SOURCES) + 24, top + rh * len(rows) + 64
    def fill(v: float) -> str:  # light -> dark blue, sequential
        t = min(v / 50.0, 1.0)
        lo, hi = (236, 243, 249), (16, 70, 120)
        return "#%02x%02x%02x" % tuple(round(a + (b - a) * t) for a, b in zip(lo, hi))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="system-ui,-apple-system,sans-serif" role="img">',
         '<style>text{fill:#1b1b1b}.m{fill:#5f6368}</style>', f'<rect width="{W}" height="{H}" fill="#fcfcfb"/>',
         '<text x="16" y="30" font-size="18" font-weight="600">Who talks about which AI risks</text>',
         '<text x="16" y="52" font-size="12" class="m">Share of each source\'s AI-risk passages naming each type. '
         'Codebook v0.2 DRAFT; * = new in v0.2.</text>']
    for j, (k, label, *_r) in enumerate(SOURCES):
        base = shares[k][rows[0]["id"]][1]
        o.append(f'<text x="{left + j * cw + cw / 2}" y="{top - 24}" font-size="12" font-weight="600" text-anchor="middle">{escape(label)}</text>')
        o.append(f'<text x="{left + j * cw + cw / 2}" y="{top - 9}" font-size="11" class="m" text-anchor="middle">n = {display.count(base)}</text>')
    for i, t in enumerate(rows):
        y = top + i * rh
        o.append(f'<text x="{left - 8}" y="{y + rh / 2 + 4}" font-size="12" text-anchor="end">{escape(t["id"])}{" *" if t["id"] in new else ""}</text>')
        for j, (k, label, *_r) in enumerate(SOURCES):
            n, base = shares[k][t["id"]]
            v = 100 * n / base if base else 0.0   # colour only; every printed value comes from display.pct
            ink = "#ffffff" if v >= 25 else "#1b1b1b"
            o.append(f'<g><title>{escape(label)}: {escape(t["id"])} {display.pct(n, base, 1) if base else "0.0"}% ({n} of {base})</title>'
                     f'<rect x="{left + j * cw + 1}" y="{y + 1}" width="{cw - 2}" height="{rh - 2}" rx="2" fill="{fill(v)}"/>'
                     f'<text x="{left + j * cw + cw / 2}" y="{y + rh / 2 + 4}" font-size="11" text-anchor="middle" style="fill:{ink}">{display.pct(n, base, 0) if base else "0"}</text></g>')
    o.append(f'<text x="16" y="{H - 30}" font-size="11" class="m">n = passages both NLI witnesses score ≥ 0.5 on ai_risk; a cell needs both ≥ 0.5 on the type too. A passage can name several types.</text>')
    o.append(f'<text x="16" y="{H - 14}" font-size="11" class="m">Calls and questions: 12 months to 2026-11-04. HN: 2025-09 to 2026-08. Wikipedia: revisions as of 2026-11-04. Witness proposals, no gold set.</text>')
    o.append("</svg>")
    (OUT / "dialogue-space.svg").write_text("\n".join(o) + "\n")


if __name__ == "__main__":
    sys.exit(main())
