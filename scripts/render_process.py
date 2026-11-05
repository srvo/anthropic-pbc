"""The argument in process: one page for the operator and for anyone we show it to.

Beliefs first, then what is moving now (points, search queue, leads, barriers,
weight-bearing steps, slide queue), a walk through the complaint sphere, the
ten stops, the proof tree, the map, and every chart with its stage.

Reads only committed inputs through the repository's own check scripts, so
every count on the page is the repository's.

    python3 scripts/render_process.py OUT_DIR    # writes OUT_DIR/index.html and OUT_DIR/fig/
"""
from __future__ import annotations

import csv
import html
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTDIR = Path(sys.argv[1] if len(sys.argv) > 1 else "_site/process").expanduser().resolve()
OUT = OUTDIR / "index.html"
sys.path.insert(0, str(REPO / "scripts"))

import chain_shape as cs  # noqa: E402
import workbench as w  # noqa: E402

e = html.escape
wb = w.check(w.load(REPO))
d = wb.deck
runs = cs.runs(d)
commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
branch = subprocess.run(["git", "-C", str(REPO), "branch", "--show-current"], capture_output=True, text=True).stdout.strip()

# ---------- cards, sides, proof state ----------
seq = d.sequence
theme_order = [t["theme"] for t in d.themes] if isinstance(d.themes, list) else list(d.themes)
themes = {r["theme"]: r for r in csv.DictReader(open(REPO / "argument/themes.tsv"), delimiter="\t")}
beats = {b.card: b for r in runs for b in r.beats}
# Alternatives that share a slot (e.g. budget allocation rules) are not beats of a run; carry them too.
for s in d.sequence:
    if s["card"] not in beats:
        beats[s["card"]] = cs.Beat(s["card"], s["role"], s["title"], int(s["circle"]),
                                   d.statements.get(s["card"], ""), list(d.cards.get(s["card"], [])))
title = {s["card"]: s["title"] for s in seq}
theme_of = {s["card"]: s["theme"] for s in seq}
role_of = {s["card"]: s["role"] for s in seq}
side = dict(wb.sides)
proven = {c: beats[c].proven for c in beats}
deps = {c: beats[c].rests_on for c in beats}
failing_q = {x for c in deps for x in deps[c] if x.startswith("Q") and x not in d.descartes_ok}
pending = set(d.pending)
weak = cs.weak_points(d, {c: beats[c].circle for c in beats})
pending_rows = {r["id"]: r for r in csv.DictReader(open(REPO / "argument/pending-sources.tsv"), delimiter="\t")}


def side_of(c: str) -> str:
    if side.get(c) == "defence":
        return "defence"
    return "method" if role_of.get(c) in ("lens", "budget") else "complaint"


n_cards = len(beats)
n_proven = sum(proven.values())
tally = cs.tally(runs)
links_total = sum(v["proposed"] for v in tally.values())
ther = tally["therefore"]
answer_card = "A063"
answer_blockers = weak.get(answer_card, [])
cited_q = {x for c in deps for x in deps[c] if x.startswith("Q")}
q_pass = len([q for q in cited_q if q in d.descartes_ok])
parties = wb.parties
best = w.best_state(wb)


def standing_proven(p: dict) -> bool:
    ids = w.split(p["rests_on"])
    return bool(ids) and all((proven.get(i) if i in beats else i in d.descartes_ok) for i in ids)


n_standing = sum(standing_proven(p) for p in parties)
affected = [p for p in parties if p["kind"] in ("affected", "both")]
voiced_affected = sum(best.get(p["id"]) == "voiced" for p in affected)
sides_rows = w.side_weights(wb)
def_written = sum(r["defence"]["written"] for r in sides_rows)
def_proven = sum(r["defence"]["proven"] for r in sides_rows)
barriers = w.barriers(wb)

# ---------- plain-language bridges (our editorial framing; the cards carry the claims) ----------
BRIDGE = {
    "promise": "Start where Anthropic starts: it is a public benefit corporation. What does that label promise, and to whom?",
    "best-case": "Before we judge, state their case at its strongest, in their own terms.",
    "enforce": "A promise is worth what it costs to break. Who can make Anthropic keep this one?",
    "lens": "We need a yardstick Anthropic cannot call unfair. We use its own: the Constitution it wrote for Claude.",
    "record": "What public benefit did it provide, and what harm, held to the same standard of proof?",
    "pillars": "The board set five pillars. Does each survive Anthropic's own admissions?",
    "planet": "What does the buildout cost the planet, and can anyone check? Five yardsticks, including the one kindest to Anthropic.",
    "answer": "Put it together.",
    "remedy": "If no one can enforce the promise, what would make it enforceable?",
    "falsifiers": "What would change our mind, and are we held to the same test?",
}
PLAIN = {
    "promise": "The promise", "best-case": "Their best case", "enforce": "Who can enforce it",
    "lens": "The yardstick", "record": "The record", "pillars": "The five pillars", "planet": "The planet",
    "answer": "The answer", "remedy": "What would bind", "falsifiers": "What would change our mind",
}
GLYPH = {"therefore": "therefore", "but": "but", "and": "and", "and-then": "and then"}


def chip(c: str, big: bool = False) -> str:
    s = side_of(c)
    state = "proven" if proven.get(c) else "open"
    return (f'<a class="chip {s} {state}{" big" if big else ""}" href="#c-{e(c)}" data-card="{e(c)}" '
            f'title="{e(beats[c].statement)}"><span class="mk" aria-hidden="true"></span>{e(title.get(c, c))}'
            f'<span class="sr"> ({s}, {"proven" if proven.get(c) else "not yet proven"})</span></a>')


def leaf(x: str) -> str:
    if x in beats:
        return chip(x)
    if x.startswith("P-"):
        r = pending_rows.get(x, {})
        return f'<span class="leaf pend" title="{e(r.get("needed_for", ""))}">source not yet pinned: {e(x[2:])}</span>'
    ok = x in d.descartes_ok
    q = wb.quotes.get(x, {}) if isinstance(wb.quotes, dict) else {}
    return (f'<span class="leaf {"qok" if ok else "qbad"}" title="{e(q.get("quote", ""))}">'
            f'quote {e(x)} {"checked byte for byte" if ok else "fails the byte check"}</span>')


def landing(t: str, trs) -> str | None:
    """The stop's conclusion; else its last inference (a stop that sets a yardstick ends on one)."""
    if t == "planet":
        return "A061"
    pt = next((r.point for r in trs if r.point), None)
    if pt:
        return pt
    inf = [b.card for r in trs for b in r.beats if b.role == "inference"]
    return inf[-1] if inf else None


# ---------- section: scorecard ----------
def tile(big: str, label: str, note: str, tone: str = "") -> str:
    return f'<div class="tile {tone}"><div class="big">{big}</div><div class="lab">{label}</div><div class="note">{note}</div></div>'


score = "".join([
    tile("Not yet", "Our answer is proven", f"“PBC in law, not in the sense the category promises” waits on {len(answer_blockers)} items", "warn"),
    tile(f"{n_proven}<small>/{n_cards}</small>", "steps proven", "every quote beneath them passes the byte check"),
    tile(f"{ther['proven']}<small>/{ther['proposed']}</small>", "“therefore” links proven", f"of {links_total} links; {tally['and-then']['proposed']} are only “and then”"),
    tile(f"{def_written}", "steps state Anthropic's case", f"{def_proven} of them proven so far"),
    tile(f"{n_standing}<small>/{len(parties)}</small>", "parties with proven standing", "who can actually make Anthropic act"),
    tile(f"{voiced_affected}<small>/{len(affected)}</small>", "affected parties heard directly", "everyone else is named or described secondhand", "warn"),
])

rows = []
for t in theme_order:
    st = w.theme_stats(d)[t]
    trs = [r for r in runs if r.theme == t]
    point = landing(t, trs)
    pp = proven.get(point) if point else None
    status = ("holds", "Proven") if pp else (("part", "Partly checked") if st["proven"] else ("none", "Not yet checked"))
    sr = next(r for r in sides_rows if r["theme"] == t)
    rows.append(
        f'<tr><td><a href="#t-{t}">{e(PLAIN[t])}</a><div class="q">{e(themes[t]["question"])}</div></td>'
        f'<td>{e(beats[point].statement) if point else "–"}</td>'
        f'<td class="num">{sr["defence"]["written"]}</td>'
        f'<td class="num">{st["proven"]}/{st["cards"]}</td>'
        f'<td><span class="badge {status[0]}"><span aria-hidden="true">{"●" if status[0]=="holds" else ("◐" if status[0]=="part" else "○")}</span> {status[1]}</span></td></tr>')
scoretable = "".join(rows)

# ---------- section: the walk ----------
walk = []
for i, t in enumerate(theme_order, 1):
    trs = [r for r in runs if r.theme == t]
    parts = []
    for r in trs:
        seqhtml = []
        for j, b in enumerate(r.beats):
            if j:
                lk = r.links[j - 1]
                seqhtml.append(f'<span class="lk {lk.kind} {"p" if lk.proven else "o"}">{GLYPH[lk.kind]}</span>')
            seqhtml.append(f'<span id="c-{e(b.card)}" class="beat">{chip(b.card)}</span>')
        lens = f'<h4>Lens: {e(r.lens.replace("-", " "))}</h4>' if r.lens not in ("-", "", None) else ""
        parts.append(f'{lens}<div class="run">{"".join(seqhtml)}</div>')
    defence = [c for r in trs for c in [b.card for b in r.beats] if side_of(c) == "defence"]
    point = landing(t, trs)
    why = ""
    if point:
        blockers = weak.get(point, [])
        why = (f'<div class="because"><div class="lbl">Where this stop lands</div>{chip(point, True)}'
               f'<p>{e(beats[point].statement)}</p><div class="lbl">because</div><div class="leaves">'
               + "".join(leaf(x) for x in beats[point].rests_on) + "</div>"
               + (f'<div class="lbl">still waiting on</div><div class="leaves">{"".join(leaf(x) for x in blockers)}</div>' if blockers else
                  '<div class="lbl ok">nothing: this step is proven end to end</div>')
               + "</div>")
    steel = ""
    if defence:
        steel = ('<div class="steel"><div class="lbl">Their strongest case here</div>'
                 + "".join(f'<p>{chip(c)} {e(beats[c].statement)}</p>' for c in defence) + "</div>")
    walk.append(
        f'<section class="stop" id="t-{t}"><div class="stopno">{i}</div><div class="stopbody">'
        f'<h3>{e(PLAIN[t])}</h3><p class="bridge">{e(BRIDGE[t])}</p>{steel}{why}'
        f'<details><summary>Every step in this stop ({sum(len(r.beats) for r in trs)})</summary>{"".join(parts)}</details>'
        f'</div></section>')

# ---------- section: the why tree ----------
seen: set[str] = set()


def tree(c: str, depth: int = 0) -> str:
    if c not in beats:
        return f"<li>{leaf(c)}</li>"
    if c in seen:
        return f'<li>{chip(c)} <span class="muted">(shown above)</span></li>'
    seen.add(c)
    kids = beats[c].rests_on
    inner = "".join(tree(k, depth + 1) for k in kids)
    op = " open" if depth < 1 else ""
    return (f'<li><details{op}><summary>{chip(c)} <span class="stmt">{e(beats[c].statement)}</span></summary>'
            f'<ul>{inner}</ul></details></li>')


whytree = f'<ul class="tree">{tree(answer_card)}</ul>'

# ---------- section: the map (layered DAG) ----------
col_w, row_h, top, left = 150, 15, 40, 10
pos: dict[str, tuple[float, float]] = {}
cols = {t: [s["card"] for s in seq if s["theme"] == t] for t in theme_order}
for ci, t in enumerate(theme_order):
    for ri, c in enumerate(cols[t]):
        pos[c] = (left + ci * col_w + 18, top + ri * row_h)
H = top + max(len(v) for v in cols.values()) * row_h + 20
W = left + len(theme_order) * col_w
edges = []
for c, ds in deps.items():
    for x in ds:
        if x in pos and c in pos:
            (x1, y1), (x2, y2) = pos[x], pos[c]
            mx = (x1 + x2) / 2
            edges.append(f'<path class="edge {"ep" if proven.get(c) and proven.get(x) else "eo"}" data-a="{e(x)}" data-b="{e(c)}" '
                         f'd="M{x1:.0f},{y1:.0f} C{mx + 30:.0f},{y1:.0f} {mx - 30:.0f},{y2:.0f} {x2:.0f},{y2:.0f}"/>')
nodes = []
for c, (x, y) in pos.items():
    s = side_of(c)
    nodes.append(f'<g class="node {s} {"proven" if proven.get(c) else "open"}" data-card="{e(c)}" tabindex="0">'
                 f'<title>{e(title[c])}: {e(beats[c].statement)}</title>'
                 f'<circle cx="{x}" cy="{y}" r="{7 if c == answer_card else 4.5}"/>'
                 f'<text x="{x + 8}" y="{y + 3.5}">{e(title[c][:22])}</text></g>')
heads = "".join(f'<text class="colh" x="{left + i * col_w + 12}" y="18">{e(PLAIN[t])}</text>' for i, t in enumerate(theme_order))
dag = (f'<svg class="dag" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
       f'aria-label="Every step of the argument as a dot, columns by stop, lines from what a step rests on to the step">'
       f'{heads}<g>{"".join(edges)}</g><g>{"".join(nodes)}</g></svg>')

# ---------- section: barriers ----------
top_b = barriers[:15]
mx = max(b.lifts for b in top_b) or 1
bar_rows = "".join(
    f'<div class="brow" title="{e(b.detail)}"><div class="bl">{e(b.item.replace("P-", ""))}<span>{e(b.kind)}</span></div>'
    f'<div class="bt"><div class="bb" style="width:{b.lifts / mx * 100:.0f}%"></div></div>'
    f'<div class="bn">{b.lifts} link{"s" if b.lifts != 1 else ""} · {b.blocks} steps downstream</div></div>'
    for b in top_b)

# ---------- section: sides ----------
smax = max(max(r["defence"]["written"], r["complaint"]["written"]) for r in sides_rows) or 1
side_rows = []


def seg(kind: str, n: int) -> str:
    return f'<div class="seg {kind}" style="width:{n / smax * 100:.1f}%"></div>' if n else ""


for r in sides_rows:
    dw, dp = r["defence"]["written"], r["defence"]["proven"]
    cw, cp = r["complaint"]["written"], r["complaint"]["proven"]
    side_rows.append(
        f'<div class="srow"><div class="sl">{e(PLAIN[r["theme"]])}</div>'
        f'<div class="sd" title="Anthropic\'s case: {dp} proven of {dw}">{seg("open", dw - dp)}{seg("fill", dp)}</div>'
        f'<div class="sc" title="Our complaint: {cp} proven of {cw}">{seg("fill", cp)}{seg("open", cw - cp)}</div>'
        f'<div class="sn">{dp}/{dw} · {cp}/{cw}</div></div>')

# ---------- section: parties ----------
STATES = ["missing", "identified", "located", "secondhand", "voiced"]
cov = {(r["party"], r["theme"]): r["state"] for r in wb.coverage}
ph = "".join(f'<th scope="col"><span>{e(PLAIN[t])}</span></th>' for t in theme_order)
prow = []
for p in parties:
    cells = "".join(
        f'<td class="cv s{STATES.index(cov.get((p["id"], t), "missing"))}" title="{e(cov.get((p["id"], t), "missing"))}">'
        f'{e(cov.get((p["id"], t), "missing")[0].upper()) if cov.get((p["id"], t), "missing") != "missing" else ""}</td>'
        for t in theme_order)
    sp = standing_proven(p)
    prow.append(f'<tr><th scope="row">{e(p["name"])}<div class="q">{e(p["kind"])}</div></th>'
                f'<td class="stand">{"<b>proven</b>: " if sp else ""}{e(p["standing"])}</td>{cells}</tr>')

# ---------- section: evidence base (datasets and charts) ----------
def tsv(path: str) -> list[dict]:
    return list(csv.DictReader((l for l in open(REPO / path) if not l.startswith("#")), delimiter="\t"))


ttm = tsv("proposals/earnings-calls/codebook-questions-v0.1/report/ttm.tsv")
qn = round(float(ttm[0]["questions"]) / float(ttm[0]["pct_of_ai_questions"]) * 100)
qi = {r["intent"]: r for r in ttm}
byyear = tsv("proposals/earnings-calls/codebook-v0.1/report/ai-risk-by-year.tsv")
last = byyear[-1]
rank = tsv("proposals/earnings-calls/codebook-v0.1/report/risk-ranking-ttm.tsv")
hn = tsv("proposals/hacker-news/report/risk-ranking-ttm.tsv")
wp = tsv("proposals/wikipedia-ai-risk/codebook-v0.1/report/summary.tsv")[0]
cve = tsv("corpus/cve/monthly-ai.tsv")
cve12 = cve[-12:]
cve_ai = sum(int(r["n_ai_credited"]) for r in cve12)
cve_claude = sum(int(r["n_credit_claude"]) for r in cve12)
cve_all = sum(int(r["n_published"]) for r in cve12)
agree = {r["hypothesis_id"]: r for r in tsv("proposals/earnings-calls/codebook-v0.1/report/agreement.tsv")}

EVID = [
    ("Wall Street analysts", "S&P 500 earnings calls", "fig/analysts.svg",
     f"Of about {qn:,} analyst questions about AI in the last twelve months, {qi['q_revenue']['pct_of_ai_questions']}% ask about revenue; "
     f"{qi['q_harm']['questions']} ({qi['q_harm']['pct_of_ai_questions']}%) ask about harm.",
     "Who checks the buildout? The people pricing it ask how much it earns.", "classified", "A007 (scrutiny runs backwards)"),
    ("Executives on AI risk", "S&P 500 earnings calls", "fig/ai-risk-year.svg",
     f"In {last['year']}, {last['pct_lexical']}% of calls mention AI risk by keyword ({last['pct_witnesses']}% when both models agree), up from under 1% before 2017.",
     "AI risk has entered the companies' own talk, so silence on it is a choice.", "classified", "pillars, record"),
    ("Which risks executives name", "S&P 500 earnings calls", "fig/risk-rank.svg",
     f"Top AI risk named in the last twelve months: {rank[0]['label'].lower()} ({rank[0]['firms']} firms); {rank[1]['label'].lower()} second ({rank[1]['firms']}).",
     "Sets the background for Anthropic's own risk disclosure.", "classified", "record"),
    ("What the public argues about", "Hacker News comments", "fig/hn-rank.svg",
     f"In comments about Anthropic, {hn[0]['label'].lower()} leads at {hn[0]['anthropic_pct']}%; executives give it {hn[0]['calls_pct']}% of their AI-risk talk.",
     "A secondhand public voice, until affected people speak for themselves.", "classified", "coverage of the public"),
    ("Where the conversation splits", "calls, Hacker News and Wikipedia together", "fig/dialogue.svg",
     "One codebook applied to executives, analysts, the public and Wikipedia, so their emphases can be set side by side.",
     "Shows who talks about which risk, and who does not.", "draft codebook", "lens"),
    ("Who gets checked", "the paper", "fig/who-checked.svg",
     "Wood Cache, a small benefit with a mild worst case, is verified end to end; Anthropic, with serious worst cases, is checked by its own report.",
     "The opening contrast of the argument.", "in the argument (hand-drawn)", "A007, A008"),
    ("Security-benefit claims", "CVE records, monthly", None,
     f"Last twelve months: {cve_all:,} CVEs published; {cve_ai:,} credit AI-assisted discovery, and {cve_claude:,} of those credits name Claude.",
     "The audit Anthropic's 33,000-flaw figure lacks starts here.", "pinned", "A040, A071"),
    ("Wikipedia on AI risk", "151 articles", None,
     f"{wp['pct_no_specific_type']}% of AI-risk passages name no specific risk type.",
     "Feeds the codebook's risk dimensions.", "classified", "codebook"),
    ("Health of democracy", "GDELT news and TV; Rooney Reports", None,
     "Attention to democracy and stated democratic attitudes. Measures the background only, never Anthropic's effect.",
     "The denominator any claim that Anthropic helps democracy has to beat.", "pinned", "pillar 3"),
    ("Compute, chips, spend", "Epoch AI datasets", None,
     "Chips, data centres, company spend and revenue, as published by Epoch AI.",
     "Context for the $895.4 billion of committed spend.", "pinned", "A052, planet"),
    ("10-K risk factors", "SEC filings, Item 1A", None,
     "Disclosed risks set against the governance that would control each one: the Risk–Governance Index.",
     "Not yet reproducible: no manifest, data held locally.", "local only", "remedy"),
]
charts = tsv("argument/charts.tsv")
by_path = {c["where"]: c["id"] for c in charts}
FIGS = {c["id"]: c["where"] for c in charts if c["where"].endswith(".svg") and (REPO / c["where"]).exists()}
PAGES = {"workbench": "https://srvo.github.io/anthropic-pbc/", "process": ""}


def chart_link(c: dict) -> str:
    wh = c["where"]
    if c["id"] in FIGS:
        return f'<a href="fig/{e(c["id"])}.svg">{e(c["title"])}</a>'
    if "#" in wh and wh.split("#")[0] in PAGES:
        pg, anc = wh.split("#", 1)
        return f'<a href="{e(PAGES[pg])}#{e(anc)}">{e(c["title"])}</a>'
    return e(c["title"])


chart_rows = "".join(
    f'<tr><td>{chart_link(c)}<div class="q">{e(c["where"])}</div></td><td>{e(c["shows"])}</td><td class="q">{e(c["data"])}</td>'
    f'<td>{e(c["wired"])}</td><td><span class="pill">{e(c["stage"])}</span></td><td class="q">{e(c["feeds"])}</td></tr>' for c in charts)
STAGE = ["local only", "pinned", "classified", "draft codebook", "in the argument (hand-drawn)"]
ev = []
for name, src, fig, finding, why_it, stage, feeds in EVID:
    img = f'<img src="{fig}" alt="{e(name)} chart" loading="lazy">' if fig else ""
    ev.append(f'<article class="ev">{img}<h4>{e(name)}</h4><div class="q">{e(src)}</div><p>{e(finding)}</p>'
              f'<p class="muted">{e(why_it)}</p><div class="evf"><span class="stage">{e(stage)}</span><span>would feed: {e(feeds)}</span></div></article>')

# ---------- section: process funnel ----------
FUN = [
    ("Primary sources pinned", len(tsv("sources/MANIFEST.tsv")), "filings, the PBC Report, the Constitution, the RSP, law, lens papers; each held by its hash"),
    ("Sources still to pin", len(pending), "named in the deck, not yet held"),
    ("Quotes cited by steps", len(cited_q), "each a short excerpt that must appear once, byte for byte"),
    ("Quotes passing", q_pass, "Descartes found them exactly"),
    ("Steps (cards)", n_cards, "one short claim each, naming what it rests on"),
    ("Steps proven", n_proven, "every quote beneath them passes"),
    ("“Therefore” links", ther["proposed"], "the links that make it an argument rather than a list"),
    ("“Therefore” links proven", ther["proven"], ""),
    ("Author sign-off (circle 4)", 0, "a person vouching for what no check can settle; none yet"),
]
fmax = max(v for _, v, _ in FUN)
funnel = "".join(f'<div class="frow"><div class="fl">{e(a)}</div><div class="ft"><div class="fb" style="width:{max(v / fmax * 100, 0.6):.1f}%"></div></div>'
                 f'<div class="fn">{v}</div><div class="fd">{e(n)}</div></div>' for a, v, n in FUN)

# ---------- chain shapes ----------
shapes = []
for r in runs:
    g = []
    for j, b in enumerate(r.beats):
        if j:
            lk = r.links[j - 1]
            g.append(f'<i class="g {lk.kind} {"p" if lk.proven else "o"}" title="{GLYPH[lk.kind]}"></i>')
        g.append(f'<b class="d {side_of(b.card)} {"p" if b.proven else "o"}" title="{e(b.title)}"></b>')
    nm = PLAIN[r.theme] + (f" · {r.lens.replace('-', ' ')}" if r.lens not in ("-", None, "") else "")
    shapes.append(f'<div class="shape"><div class="sl">{e(nm)}</div><div class="gl">{"".join(g)}</div></div>')

# ---------- beliefs (the primitive the argument starts from) ----------
def rows_of(path: str) -> list[dict]:
    p = REPO / path
    return tsv(path) if p.exists() else []


beliefs = rows_of("argument/beliefs.tsv")
belief_html = "".join(f'<li><b>{e(b["id"])}</b> {e(b["belief"])} <span class="q">— {e(b["source"])} · {e(b["state"])}</span></li>'
                      for b in beliefs)

# ---------- in process: points, search queue, leads ----------
points = rows_of("argument/points.tsv")
queries = rows_of("research/queries.tsv")
leads = rows_of("research/leads.tsv")


def count(rows: list[dict], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rows:
        out[r.get(key, "")] = out.get(r.get(key, ""), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def pills(c: dict[str, int]) -> str:
    return " ".join(f'<span class="pill">{e(k or "–")} <b>{v}</b></span>' for k, v in c.items()) or '<span class="muted">none yet</span>'


lead_pts = {l["point_id"] for l in leads}
primary = {"filing", "statute", "court", "agency", "paper", "data", "subject"}
prim_pts = {l["point_id"] for l in leads if l["source_class"] in primary}
STAGES = [
    ("Points explored", len(points), "every claim, question, missing source and falsifier, one row each"),
    ("Searches queued", len(queries), "two or three web queries per point, generated mechanically"),
    ("Searches run", sum(q["state"] in ("searched", "normalized") for q in queries), "raw responses pinned by hash"),
    ("Points with leads", len(lead_pts), "at least one result came back"),
    ("Points with a primary-source lead", len(prim_pts), "a filing, statute, ruling, agency, paper or dataset to pin next"),
    ("Sources pinned", len(tsv("sources/MANIFEST.tsv")), "held by hash; quotes can now be checked"),
]
smax2 = max([v for _, v, _ in STAGES] + [1])
pipeline = "".join(f'<div class="frow"><div class="fl">{e(a)}</div><div class="ft"><div class="fb acc" style="width:{max(v / smax2 * 100, 0.6):.1f}%"></div></div>'
                   f'<div class="fn">{v}</div><div class="fd">{e(n)}</div></div>' for a, v, n in STAGES)
def ans(p: dict) -> str:
    a = p.get("best_answer", "-")
    return "" if a in ("", "-") else f'<div class="ans"><b>Their answer:</b> {e(a[:280])}{"…" if len(a) > 280 else ""}</div>'


point_rows = "".join(
    f'<tr><td>{e(p["id"])}</td><td>{e(p["point"])}{ans(p)}</td><td>{e(p["kind"])}</td><td>{e(p["status"])}</td>'
    f'<td class="num">{sum(l["point_id"] == p["id"] for l in leads)}</td></tr>' for p in points)

# ---------- weight-bearing queue ----------
down: dict[str, set[str]] = {}
for c, ds in deps.items():
    for x in ds:
        down.setdefault(x, set()).add(c)


def downstream(c: str) -> set[str]:
    seen2, stack = set(), [c]
    while stack:
        for k in down.get(stack.pop(), ()):
            if k not in seen2:
                seen2.add(k)
                stack.append(k)
    return seen2


answer_path = {answer_card} | {x for x in beats if answer_card in downstream(x)}
weight = sorted(((len(downstream(c)), c) for c in beats), reverse=True)
wb_rows = "".join(
    f'<tr><td>{chip(c)}</td><td class="num">{n}</td><td>{"yes" if c in answer_path else "–"}</td>'
    f'<td>{"proven" if proven[c] else "<b>open</b>: " + ", ".join(e(x) for x in weak.get(c, [])[:4]) + ("…" if len(weak.get(c, [])) > 4 else "")}</td></tr>'
    for n, c in weight[:15])

# ---------- slide queue ----------
slides = rows_of("argument/slides.tsv")


def slide_item(s: dict) -> str:
    c = s["card"]
    if c in beats:
        what = chip(c) + f' <span class="q">{"proven" if proven[c] else "not yet proven: a slide would outrun its proof"}</span>'
    elif c.startswith("fig:"):
        cid = by_path.get(c[4:], Path(c[4:]).stem)
        what = f'<a href="fig/{e(cid)}.svg">{e(cid)}</a> <span class="q">chart</span>'
    else:
        what = '<span class="q">open question, no card yet</span>'
    return f'<tr><td class="num">{e(s["order"])}</td><td>{what}<div>{e(s["why"])}</div></td><td>{e(s["added_by"])}</td><td><span class="pill">{e(s["state"])}</span></td></tr>'


slide_rows = "".join(slide_item(s) for s in sorted(slides, key=lambda r: int(r["order"])))

# ---------- open lines: where we push next ----------
olines = rows_of("argument/open-lines.tsv")
BUDGET = ["L-planet-planetary-boundaries-01", "L-planet-planetary-boundaries-03", "L-planet-planetary-boundaries-04",
          "L-planet-planetary-boundaries-05", "L-planet-planetary-boundaries-06", "L-planet-planetary-boundaries-07",
          "L-planet-planetary-boundaries-08", "L-planet-planetary-boundaries-09", "L-planet-planetary-boundaries-10",
          "L-planet-planetary-boundaries-11", "L-planet-planetary-boundaries-12", "L-planet-planetary-boundaries-13"]
EXTRA = {
    "L1": '<p class="muted">Ask of any purpose: what population, measured how, over what time, and what would count as crossing the line? The charter answers none of the four.</p>',
    "L2": ('<div class="lbl">The budget chain, step by step: Earth limit → allocation rule → sector share → operator share → compute</div><div class="run">'
           + '<span class="lk and-then o">then</span>'.join(chip(c) for c in BUDGET if c in beats)
           + '</div><p class="muted">Every step past the first rests on a choice someone must state; the workbench <a href="https://srvo.github.io/anthropic-pbc/#carry">carry-forward panel</a> lets you set each one and watch the number move.</p>'),
    "L3": '<p class="muted">Set the hazard yourself in the workbench <a href="https://srvo.github.io/anthropic-pbc/#survive">survival curves</a>: the line to avoid is one in ten a year, and no governance lever is yet proven.</p>',
    "L4": '<p class="muted">A survey draft and organisation list are held privately for review. Nothing is sent without the author\'s approval and a compliance read.</p>',
}


def line_cards(v: str) -> str:
    out = []
    for x in [y.strip() for y in v.replace(" and ", ",").split(",")]:
        if x in beats:
            out.append(chip(x))
    return "".join(out)


oline_html = "".join(
    f'<article class="oline" id="line-{e(l["id"])}"><div class="lbl">{e(l["id"])} · {e(l["claim_by"])} · {e(l["state"])} · leads {sum(x["point_id"] == l["id"] for x in leads)}</div>'
    f'<h3>{e(l["question"])}</h3><div class="claim"><div class="lbl">At its strongest</div><p>{e(l["best_version"])}</p></div>'
    f'<div class="steel"><div class="lbl">Anthropic\'s best answer</div><p>{e(l["best_answer"])}</p></div>'
    f'{EXTRA.get(l["id"], "")}<p><b>Yardsticks:</b> {e(l["lenses"])}</p><div class="leaves">{line_cards(l["cards"])}</div>'
    f'<p class="q">Sources needed: {e(l["sources_needed"])}</p></article>' for l in olines)

# ---------- how others govern lethal risk ----------
peer = rows_of("research/peer-governance.tsv")
MECH = []
for r in peer:
    if r["mechanism"] not in MECH:
        MECH.append(r["mechanism"])
FIRMS = []
for r in peer:
    if r["firm"] not in FIRMS:
        FIRMS.append(r["firm"])
pcell = {(r["firm"], r["mechanism"]): r for r in peer}
MARK = {"yes": ("Y", "holds"), "partial": ("P", "part"), "no": ("N", "none"), "unknown": ("?", "none")}


def pc(f: str, m: str) -> str:
    r = pcell.get((f, m))
    if not r:
        return '<td class="pg">–</td>'
    mk, cls = MARK.get(r["present"], ("?", "none"))
    return (f'<td class="pg {cls}"><a href="{e(r["url"])}" title="{e(r["finding"])}">{mk}</a></td>')


peer_head = "".join(f'<th scope="col"><span>{e(m.split("-", 1)[-1].replace("-", " "))}</span></th>' for m in MECH)
peer_rows = "".join(f'<tr{" class=\"me\"" if f == "Anthropic" else ""}><th scope="row">{e(f)}</th>{"".join(pc(f, m) for m in MECH)}</tr>' for f in FIRMS)
anth = [r for r in peer if r["firm"] == "Anthropic"]
anth_html = "".join(f'<li><b>{e(r["mechanism"].split("-", 1)[-1].replace("-", " "))}</b> ({e(r["present"])}): {e(r["finding"])}</li>' for r in anth)

# ---------- risk regimes, other economies, people not in the room ----------
regimes = rows_of("research/risk-regimes.tsv")
PK = {"fixed": "none", "scaled": "holds", "uncapped": "holds", "mixed": "part"}
reg_rows = "".join(
    f'<tr><td><b>{e(r["category"])}</b><div class="q">{e(r["risk"])}</div></td><td>{e(r["regulator"])}<div class="q">{e(r["instrument"])}</div></td>'
    f'<td>{e(r["licence"])}</td><td>{e(r["premarket"])}</td><td>{e(r["stop_authority"])}</td>'
    f'<td><span class="pg {PK.get(r["penalty_kind"], "none")}">{e(r["penalty_kind"])}</span><div class="q">{e(r["penalty_detail"])}</div></td>'
    f'<td>{e(r["backstop"])}</td><td><a href="{e(r["url"])}">source</a></td></tr>' for r in regimes)
alts = rows_of("research/alt-economics.tsv")
alt_html = "".join(
    f'<article class="ev"><h4><a href="{e(a["url"])}">{e(a["model"])}</a></h4><p>{e(a["core_idea"])}</p>'
    f'<p class="q"><b>Who enforces the purpose:</b> {e(a["enforcer"])}</p><p class="q"><b>Limits:</b> {e(a["limits"])}</p>'
    f'<p class="q"><b>Applied to frontier AI:</b> {e(a["ai_governance"])}</p><p class="q"><b>Working example:</b> {e(a["example"])}</p>'
    f'<div class="steel"><div class="lbl">Strongest criticism</div><p>{e(a["strongest_criticism"])}</p></div></article>' for a in alts)
unad = rows_of("research/unaddressed.tsv")
un_rows = "".join(
    f'<tr><td><b>{e(u["group"])}</b></td><td>{e(u["effects"])}</td><td>{e(u["voice_today"])}</td>'
    f'<td>{e(u["in_parties"]) if u["in_parties"] not in ("", "-") else "<b>missing</b>"}</td><td><a href="{e(u["url"])}">source</a></td></tr>' for u in unad)

# ---------- who will discipline them? Wall Street ----------
QDIR = "proposals/earnings-calls/codebook-questions-v0.1/report/"
ttm_head = open(REPO / QDIR / "ttm.tsv").readline().lstrip("# ").strip()
kap = {r["hypothesis_id"]: r["cohen_kappa"] for r in tsv(QDIR + "agreement.tsv")}
yrs = [r for r in tsv(QDIR + "by-year.tsv") if int(r["year"]) >= 2022]
OVERSIGHT = {"q_risk", "q_controls", "q_harm", "q_regulation"}
LABEL = {"q_revenue": "AI revenue, demand, pricing", "q_spend": "AI spending and its return", "q_efficiency": "cost savings",
         "q_security": "security", "q_competition": "competition", "q_risk": "risks or downsides", "q_workforce": "jobs, headcount",
         "q_controls": "how the company controls AI risk", "q_regulation": "regulation", "q_harm": "harm to customers or society"}
qmax = max(int(r["questions"]) for r in ttm)
ws_bars = "".join(
    f'<div class="brow"><div class="bl">{e(LABEL.get(r["intent"], r["intent"]))}<span>κ {e(kap.get(r["intent"], "–"))}</span></div>'
    f'<div class="bt"><div class="bb {"ov" if r["intent"] in OVERSIGHT else "cm"}" style="width:{int(r["questions"]) / qmax * 100:.1f}%"></div></div>'
    f'<div class="bn">{r["questions"]} questions · {r["pct_of_ai_questions"]}%</div></div>' for r in ttm)
n_rev = int(qi["q_revenue"]["questions"])
n_gov = sum(int(qi[k]["questions"]) for k in ("q_controls", "q_harm", "q_regulation"))
n_ovs = sum(int(qi[k]["questions"]) for k in OVERSIGHT)
ws_years = "".join(f'<tr><td>{e(r["year"])}</td><td class="num">{e(r["ai_questions"])}</td><td class="num">{e(r["pct_commercial"])}%</td>'
                   f'<td class="num">{e(r["pct_oversight"])}%</td><td class="num">{e(r["pct_words_commercial"])}%</td><td class="num">{e(r["pct_words_oversight"])}%</td></tr>' for r in yrs)
last_y = yrs[-1]

# ---------- walk the flower (complaint sphere), step by step ----------
import math  # noqa: E402

R1, R2 = 175, 330
tpos = {t: (R1 * math.cos(2 * math.pi * i / len(theme_order) - math.pi / 2), R1 * math.sin(2 * math.pi * i / len(theme_order) - math.pi / 2))
        for i, t in enumerate(theme_order)}
ppos = {p["id"]: (R2 * math.cos(2 * math.pi * (i + .5) / len(parties) - math.pi / 2), R2 * math.sin(2 * math.pi * (i + .5) / len(parties) - math.pi / 2))
        for i, p in enumerate(parties)}
fl = ['<svg class="flower" viewBox="-470 -400 940 800" role="img" aria-label="Complaint sphere: the question, ten dimensions, seventeen parties and how each is heard">']
fl.append('<g class="L4">')
for (pid, th), stt in cov.items():
    if stt == "missing" or pid not in ppos or th not in tpos:
        continue
    (x1, y1), (x2, y2) = ppos[pid], tpos[th]
    fl.append(f'<line class="cl {e(stt)}" x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}"><title>{e(pid)} · {e(th)}: {e(stt)}</title></line>')
fl.append('</g><g class="L2">')
for t, (x, y) in tpos.items():
    st = w.theme_stats(d)[t]
    frac = st["proven"] / st["cards"] if st["cards"] else 0
    fl.append(f'<line class="spoke" x1="0" y1="0" x2="{x:.0f}" y2="{y:.0f}"/>'
              f'<circle class="petal" cx="{x:.0f}" cy="{y:.0f}" r="30"/><circle class="petalfill" cx="{x:.0f}" cy="{y:.0f}" r="{30 * math.sqrt(frac):.1f}"/>'
              f'<text class="tl" x="{x:.0f}" y="{y + 46:.0f}">{e(PLAIN[t])}</text><text class="ts" x="{x:.0f}" y="{y + 60:.0f}">{st["proven"]}/{st["cards"]} proven</text>')
fl.append('</g><g class="L3">')
for p in parties:
    x, y = ppos[p["id"]]
    stt = best.get(p["id"], "missing")
    anchor = "start" if x > 5 else ("end" if x < -5 else "middle")
    dx = 14 if x > 5 else (-14 if x < -5 else 0)
    fl.append(f'<g class="pp {e(p["kind"])} {e(stt)}"><rect x="{x - 8:.0f}" y="{y - 8:.0f}" width="16" height="16" rx="{8 if p["kind"] != "enforcer" else 2}"/>'
              f'<text x="{x + dx:.0f}" y="{y + 4:.0f}" text-anchor="{anchor}">{e(p["name"][:30])}</text><title>{e(p["name"])}: best coverage {e(stt)}; lever: {e(p["standing"])}</title></g>')
fl.append('</g><g class="L1"><circle class="core" r="72"/><text class="ct" y="-8">Is Anthropic a public</text><text class="ct" y="12">benefit corporation?</text></g></svg>')
flower = "".join(fl)
cov_counts = count([{"s": best.get(p["id"], "missing")} for p in parties], "s")
FLOWER_STEPS = [
    ("The question", "Everything hangs from one question at the centre. The argument is a set of answers to it, each checkable on its own."),
    ("Ten dimensions", f"Each petal is one dimension of the question: what the label promises, their best case, who can enforce it, the yardstick, the record, the pillars, the planet, the answer, the remedy, and what would change our mind. Each petal fills as its steps are proven."),
    ("Seventeen parties", "Around the edge: who holds a lever over the promise (squares) and who bears its effects (circles). A party with no lever and real exposure is the gap the whole argument is about."),
    ("How each is heard", f"A line joins a party to each dimension where it appears: dotted when only named, solid when located or told secondhand, thick when heard in its own words. Best coverage now: {', '.join(f'{v} {k}' for k, v in cov_counts.items())}."),
    ("The gap", f"Read the edge, not the centre: {len(affected) - voiced_affected} of the {len(affected)} parties who bear the effects are only named or described by others, and {n_standing} of {len(parties)} parties have a lever the cards prove. That asymmetry is the finding before any number is."),
]
flower_steps = "".join(f'<li data-step="{i}"><b>{e(a)}</b> {e(b)}</li>' for i, (a, b) in enumerate(FLOWER_STEPS, 1))

# ---------- views index ----------
VIEWS = [
    ("Workbench", "https://srvo.github.io/anthropic-pbc/", "complaint sphere, every chain, barriers, carried-forward numbers, survival scenarios"),
    ("Chain view", "https://srvo.github.io/anthropic-pbc/chain/", "each stop as therefore / but / and then, proposed beside proven"),
    ("Card deck (claims index)", "https://srvo.github.io/anthropic-pbc/cards/", "every step by stop, with its quotes"),
    ("Workbench on EC1C", "https://ec1c.com/workbench/#sphere", "the preserved, reviewed edition on the development portal"),
    ("Repository", f"https://github.com/srvo/anthropic-pbc/tree/{commit}", f"branch {branch}; argument/ holds the cards"),
    ("Oversight directory", "../anthropic-oversight/directory.html", "public groups and oversight routes (internal)"),
    ("Constituency bundles", "../anthropic-oversight/bundles.html", "resources, an ask and an offer per affected group (internal)"),
    ("Market-data pilot", "../anthropic-market-pilot/index.html", "building the dataset map with a data partner (internal)"),
    ("v0 paper commentary", "../anthropic-pbc-working-paper-154d864-commentary.html", "the fixed first edition, annotated (internal)"),
]
views = "".join(f'<li><a href="{e(u)}">{e(n)}</a> <span class="muted">— {e(t)}</span></li>' for n, u, t in VIEWS)

CSS = r"""
:root{--bg:#f9f9f7;--surf:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--mut:#6f6e69;--rule:#e2e1dc;--def:#2a78d6;--com:#eb6834;--met:#8a8984;
--ok:#0ca30c;--warn:#c98500;--bad:#d03b3b;--s0:#f0efec;--s1:#cde2fb;--s2:#9ec5f4;--s3:#5598e7;--s4:#1c5cab;}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0d0d0d;--surf:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--mut:#9a998f;--rule:#383835;
--def:#3987e5;--com:#d95926;--met:#8a8984;--s0:#262624;--s1:#184f95;--s2:#256abf;--s3:#3987e5;--s4:#86b6ef;}}
:root[data-theme=dark]{--bg:#0d0d0d;--surf:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--mut:#9a998f;--rule:#383835;--def:#3987e5;--com:#d95926;--s0:#262624;--s1:#184f95;--s2:#256abf;--s3:#3987e5;--s4:#86b6ef;}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:24px 16px 80px}h1{font-size:30px;line-height:1.2;margin:8px 0}h2{font-size:22px;margin:56px 0 6px;padding-top:12px;border-top:1px solid var(--rule)}
h3{margin:0 0 4px;font-size:19px}h4{margin:12px 0 4px;font-size:15px}a{color:inherit}.muted,.q{color:var(--mut)}.q{font-size:13px}p{margin:6px 0}
nav.toc{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:14px;margin:14px 0;color:var(--ink2)}nav.toc a{text-decoration:none;border-bottom:1px solid var(--rule)}
.lede{font-size:18px;color:var(--ink2);max-width:760px}.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:13px;color:var(--ink2);margin:10px 0}
.sr{position:absolute;left:-9999px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0}.tile{background:var(--surf);border:1px solid var(--rule);border-radius:8px;padding:12px}
.tile .big{font-size:28px;font-weight:700}.tile .big small{font-size:16px;color:var(--mut)}.tile .lab{font-weight:600;font-size:14px}.tile .note{font-size:12.5px;color:var(--mut)}.tile.warn{border-left:4px solid var(--warn)}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;vertical-align:top;padding:7px 8px;border-bottom:1px solid var(--rule)}td.num{text-align:right;font-variant-numeric:tabular-nums}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.badge{white-space:nowrap;font-weight:600;font-size:13px}.badge.holds{color:var(--ok)}.badge.part{color:var(--warn)}.badge.none{color:var(--mut)}
.chip{display:inline-flex;max-width:100%;white-space:normal;align-items:center;gap:5px;text-decoration:none;font-size:13px;border:1px solid var(--rule);background:var(--surf);border-radius:999px;padding:1px 9px 1px 6px;margin:2px 0;line-height:1.5}
.chip .mk{width:10px;height:10px;border-radius:50%;border:2px solid var(--com);flex:none}.chip.defence .mk{border-color:var(--def)}.chip.method .mk{border-color:var(--met)}
.chip.proven .mk{background:var(--com)}.chip.defence.proven .mk{background:var(--def)}.chip.method.proven .mk{background:var(--met)}.chip.big{font-size:15px;font-weight:600}
.chip.hl{outline:2px solid var(--ink)}
.stop{display:grid;grid-template-columns:44px minmax(0,1fr);gap:12px;margin:0;padding:18px 0;border-left:2px solid var(--rule);margin-left:20px;padding-left:0}
.stopno{width:36px;height:36px;border-radius:50%;background:var(--ink);color:var(--bg);display:grid;place-items:center;font-weight:700;margin-left:-19px}
.bridge{font-size:17px;color:var(--ink2)}.steel{border-left:4px solid var(--def);background:var(--surf);padding:8px 12px;margin:10px 0;border-radius:0 8px 8px 0}
.because{border-left:4px solid var(--com);background:var(--surf);padding:8px 12px;margin:10px 0;border-radius:0 8px 8px 0}
.lbl{font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);margin-top:8px}.lbl.ok{color:var(--ok)}
.leaves{display:flex;flex-wrap:wrap;gap:4px 6px}.leaf{font-size:12.5px;border-radius:4px;padding:1px 7px;border:1px dashed var(--rule)}.leaf.pend{border-color:var(--warn)}.leaf.qbad{border-color:var(--bad)}.leaf.qok{border-style:solid}
details summary{cursor:pointer;color:var(--ink2);font-size:14px;margin-top:8px}.run{display:flex;flex-wrap:wrap;align-items:center;gap:2px 4px;margin:6px 0}
.lk{font-size:11.5px;font-style:italic;color:var(--mut)}.lk.therefore.p,.lk.but.p{color:var(--ink);font-weight:700}
.tree,.tree ul{list-style:none;padding-left:18px;margin:0}.tree{padding-left:0}.tree li{margin:3px 0;border-left:1px solid var(--rule);padding-left:8px}.tree .stmt{font-size:13.5px;color:var(--ink2)}
.dagwrap{overflow:auto;border:1px solid var(--rule);border-radius:8px;background:var(--surf);max-height:640px}
.dag .edge{fill:none;stroke-width:1}.dag .eo{stroke:var(--rule)}.dag .ep{stroke:var(--mut)}.dag .edge.hl{stroke:var(--ink);stroke-width:2}
.dag .node circle{stroke-width:2;stroke:var(--com);fill:var(--surf)}.dag .node.defence circle{stroke:var(--def)}.dag .node.method circle{stroke:var(--met)}
.dag .node.proven circle{fill:var(--com)}.dag .node.defence.proven circle{fill:var(--def)}.dag .node.method.proven circle{fill:var(--met)}
.dag text{font-size:9.5px;fill:var(--ink2)}.dag .colh{font-size:11px;font-weight:700;fill:var(--ink)}.dag .node{cursor:pointer}.dag .node.dim{opacity:.18}
.brow,.srow,.frow{display:grid;align-items:center;gap:8px;margin:5px 0;font-size:13.5px}.brow{grid-template-columns:200px 1fr 190px}.bl span{display:block;font-size:11.5px;color:var(--mut)}
.bt,.ft{height:14px}.bb{height:14px;background:var(--com);border-radius:0 4px 4px 0}.bn,.fn{color:var(--ink2);font-variant-numeric:tabular-nums}
.srow{grid-template-columns:150px 1fr 1fr 90px}.sd{display:flex;justify-content:flex-end;gap:2px;border-right:1px solid var(--ink2);height:16px}.sc{display:flex;gap:2px;height:16px}
.sd .seg.fill{background:var(--def);border-radius:4px 0 0 4px}.sd .seg.open{border:1.5px solid var(--def);border-radius:4px 0 0 4px}
.sc .seg.fill{background:var(--com);border-radius:0 4px 4px 0}.sc .seg.open{border:1.5px solid var(--com);border-radius:0 4px 4px 0}.sn{font-size:12px;color:var(--mut)}
.frow{grid-template-columns:210px 1fr 50px;}.fd{grid-column:1/-1;font-size:12px;color:var(--mut);margin-top:-4px}.fb{height:14px;background:var(--ink2);border-radius:0 4px 4px 0}
.cv{text-align:center;font-size:11px;font-weight:700;min-width:30px}.cv.s0{background:var(--s0)}.cv.s1{background:var(--s1)}.cv.s2{background:var(--s2)}.cv.s3{background:var(--s3);color:#fff}.cv.s4{background:var(--s4);color:#fff}
.stand{font-size:12.5px;color:var(--ink2);min-width:200px}th[scope=col] span{writing-mode:vertical-rl;transform:rotate(180deg);font-size:12px;white-space:nowrap}
.shape{display:grid;grid-template-columns:230px 1fr;gap:8px;align-items:center;margin:4px 0;font-size:13px}.gl{display:flex;flex-wrap:wrap;align-items:center;gap:1px}
.gl .d{width:11px;height:11px;border-radius:50%;border:2px solid var(--com);display:inline-block}.gl .d.defence{border-color:var(--def)}.gl .d.method{border-color:var(--met)}
.gl .d.p{background:var(--com)}.gl .d.defence.p{background:var(--def)}.gl .d.method.p{background:var(--met)}
.gl .g{display:inline-block;width:14px;height:2px;background:var(--rule)}.gl .g.therefore{height:4px;background:var(--ink2)}.gl .g.therefore.p{background:var(--ink)}.gl .g.but{height:4px;background:repeating-linear-gradient(90deg,var(--ink2) 0 3px,transparent 3px 5px)}
.evs{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(300px,100%),1fr));gap:12px}.ev{background:var(--surf);border:1px solid var(--rule);border-radius:8px;padding:12px;font-size:14px}
.ev img{width:100%;background:#fff;border-radius:4px;border:1px solid var(--rule)}.evf{display:flex;justify-content:space-between;gap:8px;font-size:12px;color:var(--mut);margin-top:8px}.stage{font-weight:700;color:var(--ink2)}
.steps{counter-reset:s;list-style:none;padding:0}.steps li{counter-increment:s;padding:6px 0 6px 40px;position:relative}.steps li:before{content:counter(s);position:absolute;left:0;top:6px;width:28px;height:28px;border-radius:50%;border:2px solid var(--ink2);display:grid;place-items:center;font-weight:700;font-size:13px}
.claim{border-left:4px solid var(--com);background:var(--surf);padding:12px 16px;border-radius:0 8px 8px 0;margin:10px 0}.big-c{font-size:20px;font-weight:700;line-height:1.35}.bb.ov{background:var(--def)}.bb.cm{background:var(--com)}
.oline{border-top:1px solid var(--rule);padding:14px 0}.oline h3{font-size:19px;margin:4px 0 8px}
.ans{font-size:12.5px;color:var(--ink2);border-left:3px solid var(--def);padding-left:8px;margin-top:4px}
.pg{text-align:center;font-weight:700}.pg a{text-decoration:none}.pg.holds{color:var(--ok)}.pg.part{color:var(--warn)}.pg.none{color:var(--bad)}tr.me th,tr.me td{background:var(--surf)}
.kicker{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--com);font-weight:700;margin-top:10px}
.beliefs{padding-left:18px}.beliefs li{margin:6px 0}
.white{border:2px dashed var(--rule);border-radius:12px;padding:28px 24px;min-height:220px;background:var(--surf)}.big-q{font-size:24px;line-height:1.3;font-weight:700;max-width:720px}
.pill{display:inline-block;border:1px solid var(--rule);border-radius:999px;padding:0 8px;font-size:12.5px;margin:2px 2px}.pillrow{margin:6px 0}.fb.acc{background:var(--com)}
.fwrap{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:16px;align-items:start}
.flower{width:100%;height:auto;max-height:640px}.flower text{fill:var(--ink);font-size:13px}.flower .ct{text-anchor:middle;font-size:15px;font-weight:700}
.flower .core{fill:var(--surf);stroke:var(--com);stroke-width:3}.flower .spoke{stroke:var(--rule)}.flower .petal{fill:var(--surf);stroke:var(--com);stroke-width:2}.flower .petalfill{fill:var(--com)}
.flower .tl{text-anchor:middle;font-weight:600;font-size:12.5px}.flower .ts{text-anchor:middle;fill:var(--mut);font-size:11px}
.flower .pp rect{fill:var(--s0);stroke:var(--ink2);stroke-width:1.5}.flower .pp.voiced rect{fill:var(--s4)}.flower .pp.secondhand rect{fill:var(--s3)}.flower .pp.located rect{fill:var(--s2)}.flower .pp.identified rect{fill:var(--s1)}
.flower .pp text{font-size:11.5px}.flower .cl{stroke:var(--def);opacity:.5;stroke-width:1.2}.flower .cl.identified{stroke-dasharray:3 3}.flower .cl.voiced{stroke-width:3;opacity:.9}
.fwrap .L2,.fwrap .L3,.fwrap .L4{opacity:.06;transition:opacity .4s}.fwrap[data-step="2"] .L2,.fwrap[data-step="3"] .L2,.fwrap[data-step="3"] .L3,.fwrap[data-step="4"] .L2,.fwrap[data-step="4"] .L3,.fwrap[data-step="4"] .L4,.fwrap[data-step="5"] .L2,.fwrap[data-step="5"] .L3,.fwrap[data-step="5"] .L4{opacity:1}
.fwrap[data-step="5"] .pp.enforcer{opacity:.35}.fsteps li{opacity:.4;margin:8px 0}.fsteps li.on{opacity:1}.fbtns{display:flex;gap:8px;align-items:center}
.fbtns button{font:inherit;border:1px solid var(--rule);background:var(--surf);color:var(--ink);border-radius:6px;padding:4px 12px;cursor:pointer}
@media (max-width:700px){.fwrap{grid-template-columns:1fr}.brow{grid-template-columns:1fr}.srow{grid-template-columns:90px 1fr 1fr}.sn{display:none}.shape{grid-template-columns:1fr}.frow{grid-template-columns:130px 1fr 40px}}
"""

JS = r"""
const fw=document.querySelector('.fwrap');
if(fw){const n=fw.querySelectorAll('.fsteps li').length;const set=k=>{fw.dataset.step=k;fw.querySelectorAll('.fsteps li').forEach(li=>li.classList.toggle('on',+li.dataset.step===k));fw.querySelector('.fstep').textContent=k+' of '+n};
set(1);fw.querySelectorAll('[data-go]').forEach(b=>b.addEventListener('click',()=>set(Math.min(n,Math.max(1,+fw.dataset.step+ +b.dataset.go)))));
fw.querySelectorAll('.fsteps li').forEach(li=>li.addEventListener('click',()=>set(+li.dataset.step)))}
const svg=document.querySelector('.dag');
if(svg){const edges=[...svg.querySelectorAll('.edge')];const nodes=[...svg.querySelectorAll('.node')];
const up={},down={};edges.forEach(p=>{(down[p.dataset.a]??=[]).push(p.dataset.b);(up[p.dataset.b]??=[]).push(p.dataset.a)});
function reach(c,m,s=new Set()){(m[c]||[]).forEach(x=>{if(!s.has(x)){s.add(x);reach(x,m,s)}});return s}
function focus(c){const k=new Set([c,...reach(c,up),...reach(c,down)]);nodes.forEach(n=>n.classList.toggle('dim',!k.has(n.dataset.card)));
edges.forEach(p=>p.classList.toggle('hl',k.has(p.dataset.a)&&k.has(p.dataset.b)))}
function clear(){nodes.forEach(n=>n.classList.remove('dim'));edges.forEach(p=>p.classList.remove('hl'))}
nodes.forEach(n=>{n.addEventListener('mouseenter',()=>focus(n.dataset.card));n.addEventListener('focus',()=>focus(n.dataset.card));
n.addEventListener('click',()=>{const t=document.getElementById('c-'+n.dataset.card);if(t){const det=t.closest('details');if(det)det.open=true;t.scrollIntoView({behavior:'smooth',block:'center'});t.querySelector('.chip')?.classList.add('hl');setTimeout(()=>t.querySelector('.chip')?.classList.remove('hl'),2500)}})});
svg.addEventListener('mouseleave',clear)}
document.querySelectorAll('a.chip').forEach(a=>a.addEventListener('click',ev=>{const t=document.getElementById('c-'+a.dataset.card);if(t){ev.preventDefault();const det=t.closest('details');if(det)det.open=true;t.scrollIntoView({behavior:'smooth',block:'center'})}}));
"""

page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Argument in process</title><style>{CSS}</style></head><body><main>
<div class="q">Ethical Capital · anthropic-pbc @ {e(commit)} ({e(branch)}) · every count is computed from the committed files; the editorial text (bridges, beliefs, open lines) is ours and marked as such</div>
<div class="kicker">The argument, in process</div>
<h1>Is Anthropic a public benefit corporation?</h1>
<p class="lede">One page, one path. We start from Anthropic's own claim, state its strongest case, then keep asking the next question: what benefit, measured how, governed by whom, at what risk, and who is in control. Every step is a small checkable card. Our answer is written down; it is <b>not yet proven</b>, and this page shows exactly what it waits on.</p>
<nav class="toc"><a href="#beliefs">What we believe</a><a href="#open">The open question</a><a href="#next">Where we push next</a><a href="#now">In process now</a><a href="#weight">Weight-bearing</a><a href="#slides">Slide queue</a><a href="#street">Not Wall Street</a><a href="#peers">How others govern</a><a href="#regimes">Risk regimes</a><a href="#others">Other ways to build it</a><a href="#absent">Who is not in the room</a><a href="#flower">Walk the flower</a><a href="#score">Scorecard</a><a href="#walk">The walk</a><a href="#why">Why, all the way down</a><a href="#map">The map</a><a href="#sides">Both sides</a><a href="#shapes">Argument or list?</a><a href="#stuck">Where it is stuck</a><a href="#who">Who can act</a><a href="#evidence">Every chart</a><a href="#process">How we prove it</a><a href="#views">All views</a></nav>
<div class="legend"><span><span class="chip defence proven"><span class="mk"></span>Anthropic's case</span></span><span><span class="chip complaint proven"><span class="mk"></span>our complaint</span></span><span><span class="chip method proven"><span class="mk"></span>method / yardstick</span></span><span>filled = proven · hollow = not yet proven</span></div>

<h2 id="beliefs">What we believe</h2>
<p class="muted">The premises everything else is read against. They are lines the author draws, not facts a quote can prove, so they wait on the author's sign-off (circle 4). Reject one and you can see which conclusions go with it.</p>
<ul class="beliefs">{belief_html}</ul>

<h2 id="open">The open question</h2>
<div class="white"><p class="big-q">What would the solution be if we really cared about the environment, the world and flourishing?</p>
<p class="muted">This space is empty on purpose. A critique earns the right to ask this, not to answer it. What already points here: the remedy stop (governance others can invoke, an irrevocable mission lock, standing to contest, a metered externality bond), the doughnut's floor test (does the benefit lift anyone above the floor?), and the falsifiers (what Anthropic could publish that would change our mind). It is in the slide queue.</p></div>

<h2 id="next">Where we push next</h2>
<p class="muted">The lines the argument has not yet built, each stated at its strongest beside Anthropic's best answer. Each becomes points and searches before it becomes cards (<code>argument/open-lines.tsv</code>).</p>
{oline_html}

<h2 id="now">In process now</h2>
<p class="muted">What is moving, so nothing in progress is invisible. Every point we have explored becomes two or three web searches, generated mechanically; results come back as leads, sorted by whether they reach a primary source. A lead is not evidence until its source is pinned and a quote from it passes the byte check.</p>
{pipeline}
<div class="pillrow"><span class="q">points by status</span> {pills(count(points, "status"))}</div>
<div class="pillrow"><span class="q">points by kind</span> {pills(count(points, "kind"))}</div>
<div class="pillrow"><span class="q">searches</span> {pills(count(queries, "state"))}</div>
<div class="pillrow"><span class="q">leads by source</span> {pills(count(leads, "source_class"))}</div>
<details><summary>Every point ({len(points)})</summary><div class="scroll"><table><thead><tr><th>id</th><th>Point</th><th>Kind</th><th>Status</th><th class="num">Leads</th></tr></thead><tbody>{point_rows}</tbody></table></div></details>

<h2 id="weight">Weight-bearing steps</h2>
<p class="muted">The steps the most other steps rest on, counted through the whole graph. If one of these falls, everything below it falls; so these get proven, and stress-tested, first.</p>
<div class="scroll"><table><thead><tr><th>Step</th><th class="num">Steps resting on it</th><th>On the answer's path</th><th>State</th></tr></thead><tbody>{wb_rows}</tbody></table></div>

<h2 id="slides">Slide queue</h2>
<p class="muted">One central queue: when an argument is interesting, it goes here (<code>argument/slides.tsv</code>). Each row shows its proof state, so no slide claims more than the cards prove.</p>
<div class="scroll"><table><thead><tr><th class="num">#</th><th>Argument</th><th>Added by</th><th>State</th></tr></thead><tbody>{slide_rows}</tbody></table></div>

<h2 id="street">Who will hold them to it? Not Wall Street</h2>
<div class="claim"><p class="big-c">The people who will price Anthropic ask about AI revenue, not AI control. Expect no market pressure on alignment until revenue disappoints.</p>
<p>In the last twelve months, analysts on S&amp;P 500 earnings calls asked <b>{n_rev}</b> questions about AI revenue against <b>{n_ovs}</b> about any AI risk or oversight: <b>{n_rev / max(n_ovs, 1):.0f} to 1</b>. Against questions on how a company controls AI, regulation and harm alone ({n_gov}), it is <b>{n_rev / max(n_gov, 1):.0f} to 1</b>. Once Anthropic lists, only stockholders holding the lesser of 2% or $2 million can sue to enforce its public benefit (A018); analysts ask on behalf of those investors. The second sentence above is an inference, not yet tested.</p></div>
{ws_bars}
<p class="q">{e(ttm_head)} Orange: commercial and capital questions; blue: oversight questions. κ is the agreement between the two models that labelled each question; below 0.4 (harm, regulation) the count is soft.</p>
<h3>The trend, and a check that uses no model</h3>
<div class="scroll"><table><thead><tr><th>Year</th><th class="num">AI questions</th><th class="num">Commercial (models)</th><th class="num">Oversight (models)</th><th class="num">Commercial words</th><th class="num">Oversight words</th></tr></thead><tbody>{ws_years}</tbody></table></div>
<p class="muted">The word columns are a plain word match, no model involved: in {e(last_y["year"])}, {e(last_y["pct_words_commercial"])}% of analysts' AI questions use commercial words and {e(last_y["pct_words_oversight"])}% use oversight words.</p>
<div class="steel"><div class="lbl">The strongest reply</div><p>Oversight questions are rising fast: {e(yrs[-2]["pct_oversight"])}% of AI questions in {e(yrs[-2]["year"])}, {e(last_y["pct_oversight"])}% in {e(last_y["year"])}. Analysts follow what moves a stock, and an AI incident would move one. These are S&amp;P 500 analysts; Anthropic's will cover an AI company and may ask differently. Our reply: the share is rising from almost nothing, and it is still a small share. The query queue is searching for how analysts behave after revenue misses.</p></div>
<p class="q">Status: two-model proposal, not yet checked against a gold sample; it does not yet carry a card. Source: <code>{QDIR}</code>.</p>

<h2 id="peers">How others govern work that can kill</h2>
<p class="muted">Firms whose work can kill people or cause systemic harm, checked on eight governance mechanisms from their filings, proxies and regulators. Each cell links to its source; hover for the finding. Leads, not pinned evidence (<code>research/peer-governance.tsv</code>).</p>
<div class="scroll"><table class="peer"><thead><tr><th>Firm</th>{peer_head}</tr></thead><tbody>{peer_rows}</tbody></table></div>
<div class="claim"><p><b>What the comparison shows.</b> Every firm here, Anthropic included, has a board committee for its gravest risk. The difference is who can stop the work: the NRC can revoke a reactor licence, the FAA must approve any increase in 737 production, the CPUC can push PG&amp;E toward receivership. No regulator can halt an Anthropic training run or deployment, and we found no fund sized to the harm it warns of.</p></div>
<div class="steel"><div class="lbl">A correction this forces on us</div><p>California's SB 53 is a binding outside check: the Attorney General can fine up to $1 million per violation, including for not following Anthropic's own safety framework, and critical incidents must be reported to the state within 15 days. Cards A050 (“no mandatory independent check”) and A057 (“no law backstops it”) overstate the case and need qualifying: a binding check exists, but it holds Anthropic to a standard Anthropic writes.</p></div>
<details><summary>Anthropic, mechanism by mechanism</summary><ul>{anth_html}</ul></details>

<h2 id="regimes">How society already governs lethal risk</h2>
<p class="muted">Every major high-risk industry, by regime: who licenses it, who approves it before sale, who can stop it, and whether its maximum penalty is a fixed sum or scales with the firm. A fixed cap is a price; a scaled one can deter (open line L5). Leads, not pinned evidence (<code>research/risk-regimes.tsv</code>).</p>
{('<div class="scroll"><table><thead><tr><th>Industry</th><th>Regulator</th><th>Licence</th><th>Pre-market</th><th>Who can stop it</th><th>Penalty</th><th>Backstop</th><th></th></tr></thead><tbody>' + reg_rows + '</tbody></table></div>') if regimes else '<p class="q">In progress.</p>'}

<h2 id="others">Other ways to build it</h2>
<p class="muted">Economic and organisational models that start from limits and from who holds the purpose, beginning with permacomputing. Each at its strongest, with its strongest criticism. They feed open line L2 (<code>research/alt-economics.tsv</code>).</p>
{('<div class="evs">' + alt_html + '</div>') if alts else '<p class="q">In progress.</p>'}

<h2 id="absent">Who is not in the room</h2>
<p class="muted">Everyone who bears the effects of frontier AI, set against the parties the argument names. “Missing” means the argument does not yet name them at all (<code>research/unaddressed.tsv</code>).</p>
{('<div class="scroll"><table><thead><tr><th>Who</th><th>Effects, as documented</th><th>Who speaks for them today</th><th>In the argument</th><th></th></tr></thead><tbody>' + un_rows + '</tbody></table></div>') if unad else '<p class="q">In progress.</p>'}

<h2 id="flower">Walk the flower</h2>
<p class="muted">The complaint sphere, one layer at a time. Step through it.</p>
<div class="fwrap" data-step="1"><div>{flower}</div><div><div class="fbtns"><button type="button" data-go="-1">Back</button><button type="button" data-go="1">Next</button><span class="fstep q"></span></div><ol class="fsteps">{flower_steps}</ol></div></div>

<h2 id="score">Scorecard</h2>
<div class="tiles">{score}</div>
<div class="scroll"><table><thead><tr><th>Stop</th><th>Where it lands</th><th class="num">Their case</th><th class="num">Proven</th><th>Status</th></tr></thead><tbody>{scoretable}</tbody></table></div>

<h2 id="walk">The walk</h2>
<p class="muted">Ten stops, in order. Each opens with the plain question, then Anthropic's strongest case where the deck states one, then where the stop lands, what that rests on, and what is still missing. Hover a step for its full claim.</p>
{"".join(walk)}

<h2 id="why">Why, all the way down</h2>
<p class="muted">The answer, opened one “because” at a time until it reaches a quote checked against a primary source, a quote that fails the check, or a source not yet pinned. The answer is proven when every branch ends in a passing quote.</p>
{whytree}

<h2 id="map">The map</h2>
<p class="muted">Every step as a dot, one column per stop, a line from each step to the step that rests on it. Point at a dot to light up everything it depends on and everything that depends on it; click to jump to it in the walk.</p>
<div class="dagwrap">{dag}</div>

<h2 id="sides">Both sides, stop by stop</h2>
<p class="muted">Steps stating Anthropic's case (left) and our complaint (right). Filled is proven, outlined is written but not yet proven. Method steps, the yardsticks, count on neither side. Most of Anthropic's case is still unproven because we have not yet pinned its sources: the work owes that first.</p>
{"".join(side_rows)}
<div class="q" style="margin-top:6px">numbers: Anthropic proven/written · ours proven/written</div>

<h2 id="shapes">Argument or list?</h2>
<p class="muted">Each stop drawn as its chain: a thick line is <i>therefore</i>, a dashed line is <i>but</i>, a thin line is <i>and then</i>. A long run of thin lines is a list of facts, not yet an argument. Of {links_total} links, {ther['proposed']} are <i>therefore</i> and {ther['proven']} of those are proven.</p>
{"".join(shapes)}

<h2 id="stuck">Where it is stuck</h2>
<p class="muted">The repairs that would prove the most, ranked by how many links each would turn from proposed to proven. These are the to-do list.</p>
{bar_rows}

<h2 id="who">Who can act, and who has been heard</h2>
<p class="muted">Who holds a lever over the promise or bears its effects, and how each appears in each stop: I named, L located, S told secondhand, V in their own words. {n_standing} of {len(parties)} have standing the cards prove. No affected party has yet been heard in their own words.</p>
<div class="scroll"><table class="cov"><thead><tr><th>Party</th><th>Lever</th>{ph}</tr></thead><tbody>{"".join(prow)}</tbody></table></div>

<h2 id="evidence">Every chart and dataset</h2>
<p class="muted">The wider record behind the argument. None of these yet carries a step in the argument: the steps rest on Anthropic's own filings, report, Constitution and policy, and on the lens papers. Each corpus is labelled with how far it has come. <b>Classified</b> means two independent models labelled the text and their agreement is measured (Cohen's κ {agree['ai_risk']['cohen_kappa']} on “is this AI risk?” in the calls); it is a proposal until a person checks a gold sample.</p>
<div class="evs">{"".join(ev)}</div>
<h3>Every visual, registered</h3>
<p class="muted">All {len(charts)} visuals made for this argument, from <code>argument/charts.tsv</code>, with what feeds them and whether their controls actually move them (<code>docs/chart-checklist.md</code>).</p>
<div class="scroll"><table><thead><tr><th>Visual</th><th>Shows</th><th>Data</th><th>Controls wired?</th><th>Stage</th><th>Feeds</th></tr></thead><tbody>{chart_rows}</tbody></table></div>

<h2 id="process">How we prove it</h2>
<ol class="steps">
<li><b>Pin the source.</b> Download the filing, report or paper and record its hash, so anyone can fetch the same bytes.</li>
<li><b>Select a quote.</b> A short excerpt that must appear exactly once in the source.</li>
<li><b>Check it byte for byte.</b> Descartes, our verifier, re-finds every quote with no outside help. A quote that fails stays in and shows as a barrier.</li>
<li><b>Write a step.</b> One short claim, naming exactly what it rests on: quotes, other steps, or a source not yet pinned.</li>
<li><b>Compute the links.</b> Whether a step follows from the last (<i>therefore</i>), turns against it (<i>but</i>), or only sits beside it (<i>and then</i>) is computed from what it rests on, never typed in.</li>
<li><b>State their case first.</b> Every stop carries Anthropic's strongest answer, held to the same proof.</li>
<li><b>Rank the barriers.</b> The workbench ranks every missing piece by how much of the argument fixing it would prove.</li>
<li><b>Sign off.</b> Circle 4: a person vouches for what no mechanical check can settle. No step has it yet.</li>
</ol>
{funnel}

<h2 id="views">All views</h2>
<ul>{views}</ul>
<p class="q">Rebuild: <code>python3 scripts/render_process.py OUT_DIR</code>. The same inputs give the same page. Checklists: <code>docs/chart-checklist.md</code>, <code>docs/data-intake-checklist.md</code>.</p>
</main><script>{JS}</script></body></html>"""

OUTDIR.mkdir(parents=True, exist_ok=True)
(OUTDIR / "fig").mkdir(exist_ok=True)
for cid, src in FIGS.items():
    shutil.copyfile(REPO / src, OUTDIR / "fig" / f"{cid}.svg")
OUT.write_text(page)
print(f"wrote {OUT} ({len(page):,} bytes) from {commit}; cards {n_cards} proven {n_proven}; answer blockers {len(answer_blockers)}")
