# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Render the argument's chain shape — proposed beside proven — as one self-contained HTML page.

    uv run scripts/render_chain.py OUT.html

Every link between adjacent beats is THEREFORE, BUT, AND (a conjunction later used) or AND THEN
(a dangling list item). The proposed lane shows the chain as authored; the proven lane keeps only
beats whose every quote passes Descartes (circle >= 1). See chain_shape.py for the rules. Output
depends only on the inputs and the git commit.
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chain_shape as cs  # noqa: E402
import check_cards as cc  # noqa: E402
from render_cards import git_head  # noqa: E402

E = html.escape
WORD = {cs.THEREFORE: "therefore", cs.BUT: "but", cs.AND: "and", cs.AND_THEN: "and then"}

CSS = """
:root{--bg:#f7f6f2;--card:#fff;--ink:#1d1d1b;--muted:#5d5b55;--line:#dcd8cf;--accent:#2f5d8a;
--th:#2f7a4a;--but:#a0661a;--and:#6b6a64;--then:#b5462f;--gap:#c9c4b8;--sel:#fbf3dd}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#161614;--card:#21201d;--ink:#ecebe6;--muted:#a8a59c;
--line:#3a3833;--accent:#8fb6dd;--th:#6cc28c;--but:#e0a85a;--and:#a8a59c;--then:#e07a62;--gap:#4a4740;--sel:#2e2a1d}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1200px;margin:0 auto;padding:24px 16px 64px}h1{font-size:1.5rem;margin:.1em 0}
h2{font-size:1.15rem;margin:2em 0 .2em}h3{font-size:.95rem;margin:1em 0 .3em;color:var(--muted);font-weight:600}
p.lede{max-width:70ch;color:var(--muted)}.legend{display:flex;gap:10px;flex-wrap:wrap;font-size:.8rem;margin:.6em 0}
.k{font-weight:700;font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;padding:1px 7px;border-radius:999px;white-space:nowrap}
.k.therefore{color:#fff;background:var(--th)}.k.but{color:#fff;background:var(--but)}
.k.and{color:var(--and);border:1px solid var(--and)}.k.and-then{color:#fff;background:var(--then)}
.k.gap{color:var(--muted);border:1px dashed var(--gap);background:none}
.tally{border-collapse:collapse;font-size:.85rem;margin:.6em 0}.tally td,.tally th{padding:3px 10px;border-bottom:1px solid var(--line);text-align:right}
.tally th:first-child,.tally td:first-child{text-align:left}
.lane{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:.3em 0 .8em}
.lab{width:72px;flex:none;font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.beat{border:1px solid var(--line);background:var(--card);border-radius:8px;padding:4px 8px;max-width:210px;cursor:pointer;font:inherit;color:inherit;text-align:left;font-size:.8rem;line-height:1.25}
.beat small{display:block;color:var(--muted);font-size:.68rem}
.beat.conclusion{border:2px solid var(--accent)}.beat.dangle{border-color:var(--then)}
.beat.ghost{border-style:dashed;border-color:var(--gap);color:var(--muted);background:none}
.beat[aria-pressed=true]{background:var(--sel)}
.spine{display:flex;flex-wrap:wrap;gap:6px;align-items:center}.spine .beat{max-width:none}
.panel{border:1px solid var(--line);border-radius:10px;background:var(--card);padding:10px 12px;font-size:.85rem;margin-top:.4em}
.panel[hidden]{display:none}.panel dt{color:var(--muted);font-size:.72rem;text-transform:uppercase;margin-top:.5em}.panel dd{margin:0}
.fix{font-size:.85rem;margin:.2em 0 0 1.1em;padding:0}.fix li{margin:.15em 0}
code{font-size:.85em}footer{margin-top:3em;font-size:.78rem;color:var(--muted);border-top:1px solid var(--line);padding-top:1em}
.shape{font-family:ui-monospace,Menlo,monospace;font-size:.8rem;color:var(--muted);overflow-wrap:anywhere}
"""

JS = """
const D=JSON.parse(document.getElementById('data').textContent);
function show(btn){const run=btn.closest('section');const p=run.querySelector('.panel');const c=D[btn.dataset.card];
run.querySelectorAll('.beat').forEach(b=>b.setAttribute('aria-pressed',b.dataset.card===btn.dataset.card));
p.hidden=false;p.innerHTML='';const h=document.createElement('strong');h.textContent=btn.dataset.card+' · '+c.title;p.append(h);
const dl=document.createElement('dl');
[['Claim',c.statement],['Role',c.role+' · circle '+c.circle],['Rests on',c.rests_on.join(', ')||'—'],
 ['Used by',c.used_by.join(', ')||'nothing — a dead end'],['Keeping it at circle 0',c.weak.join(', ')||'—'],
 ['Swappable for',c.alts.join(', ')||'—']].forEach(([k,v])=>{const t=document.createElement('dt');t.textContent=k;
 const d=document.createElement('dd');d.textContent=v;dl.append(t,d)});p.append(dl)}
document.querySelectorAll('.beat[data-card]').forEach(b=>b.addEventListener('click',()=>show(b)));
"""


def beat_html(b: cs.Beat, dangle: bool, ghost: bool = False) -> str:
    cls = ["beat", b.role] + (["dangle"] if dangle else []) + (["ghost"] if ghost else [])
    return (f'<button class="{" ".join(cls)}" data-card="{E(b.card)}" aria-pressed="false">'
            f'<small>{E(b.card)} · {E(b.role)} · c{b.circle}</small>{E(b.title)}</button>')


def lane(r: cs.Run, proven: bool, dangles: set[str]) -> str:
    parts = [f'<span class="lab">{"Proven" if proven else "Proposed"}</span>']
    for i, b in enumerate(r.beats):
        if i:
            lk = r.links[i - 1]
            if proven and not lk.proven:
                parts.append('<span class="k gap">gap</span>')
            else:
                parts.append(f'<span class="k {lk.kind}">{WORD[lk.kind]}</span>')
        parts.append(beat_html(b, b.card in dangles and not proven, ghost=proven and not b.proven))
    return f'<div class="lane">{"".join(parts)}</div>'


def repairs(r: cs.Run, used: dict[str, list[str]], weak: dict[str, list[str]]) -> list[str]:
    inside = {b.card for b in r.beats}
    out = []
    for i, lk in enumerate(r.links):
        if lk.kind != cs.AND_THEN:
            continue
        a, b = r.beats[i], r.beats[i + 1]
        users = used.get(a.card, [])
        earlier = [u for u in users if u in inside]
        elsewhere = [u for u in users if u not in inside]
        if earlier:
            why = f"used only by {', '.join(earlier)}, which comes before it: move it ahead"
        elif elsewhere:
            why = f"used outside this run ({', '.join(elsewhere)}): link it here or move it there"
        elif a.role == "conclusion":
            why = "a conclusion nothing builds on: rest the next step on it, or end the run here"
        else:
            why = "nothing rests on it: make a later card rest on it (therefore), turn it into an objection (but), or cut it"
        out.append(f"<li><b>{E(a.card)}</b> → {E(b.card)}: <i>and then</i> — {E(why)}</li>")
    gaps = [b for b in r.beats if not b.proven]
    if gaps:
        named = sorted({w for b in gaps for w in weak.get(b.card, [])})
        out.append(f"<li>{len(gaps)} of {len(r.beats)} beats unproven; fixing "
                   f"{E(', '.join(named[:14]))}{' …' if len(named) > 14 else ''} lifts them.</li>")
    return out


def render(root: Path = cc.ROOT) -> str:
    d = cc.check(cc.load(root))
    circ = cc.circles(d)
    rs = cs.runs(d)
    used = cs.used_by(d)
    weak = cs.weak_points(d, circ)
    sp = cs.spine(d, rs)
    tal = cs.tally(rs)
    seq = {r["card"]: r for r in d.sequence}
    alts = {b.card: b.alternatives for r in rs for b in r.beats}
    data = {c: {"title": seq.get(c, {}).get("title", c), "statement": d.statements[c], "role": seq.get(c, {}).get("role", "?"),
                "circle": circ.get(c, 0), "rests_on": d.cards[c], "used_by": used.get(c, []), "weak": weak.get(c, []),
                "alts": alts.get(c, [])} for c in d.cards}

    themes = [t["theme"] for t in d.themes]
    qs = {t["theme"]: t["question"] for t in d.themes}
    point = next((r for r in rs if r.theme == "answer"), None)
    answer_card = point.beats[-1].card if point and point.beats else None
    answer_reach = set()
    if answer_card:
        stack = [answer_card]
        while stack:
            x = stack.pop()
            if x in answer_reach:
                continue
            answer_reach.add(x)
            stack.extend(d.cards.get(x, []))
    theme_of = {r["card"]: r["theme"] for r in d.sequence}
    feeds = {th for c in answer_reach if (th := theme_of.get(c))}

    sp_html = []
    for i, th in enumerate(themes):
        if i:
            a, b, kind, proven = sp[i - 1]
            sp_html.append(f'<span class="k {kind}">{WORD[kind]}</span>' if proven or kind == cs.AND_THEN
                           else f'<span class="k {kind}" style="opacity:.55" title="not yet proven">{WORD[kind]}?</span>')
        mark = "conclusion" if th == "answer" else ("" if th in feeds else "dangle")
        sp_html.append(f'<span class="beat {mark}" title="{E(qs[th])}"><small>{E(th)}</small>{E(qs[th])}</span>')
    orphan_themes = [t for t in themes if t not in feeds and t not in {"answer", "remedy", "falsifiers"}]

    rows = "".join(f"<tr><td><span class='k {k}'>{WORD[k]}</span></td><td>{v['proposed']}</td><td>{v['proven']}</td></tr>"
                   for k, v in tal.items())
    body = []
    for r in rs:
        inside = {b.card for b in r.beats}
        dangles = {r.beats[i].card for i, lk in enumerate(r.links) if lk.kind == cs.AND_THEN}
        title = qs[r.theme] + (f" — lens: {r.lens}" if r.lens != "-" else "")
        fx = repairs(r, used, weak)
        body.append(
            f'<section><h2>{E(title)}</h2>'
            f'<div class="shape">proposed {E(r.shape())}<br>proven&nbsp;&nbsp; {E(r.shape(True))}</div>'
            f'{lane(r, False, dangles)}{lane(r, True, dangles)}'
            f'<div class="panel" hidden></div>'
            + (f'<h3>Repairs</h3><ul class="fix">{"".join(fx)}</ul>' if fx else "")
            + '</section>')
        del inside

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Argument Chain Shape</title>
<style>{CSS}</style></head><body><main>
<h1>Argument chain shape</h1>
<p class="lede">A story whose beats are joined by <i>and then</i> is a list. Each beat should follow from the last
(<b>therefore</b>) or turn against it (<b>but</b>). The same holds for an argument. The <b>proposed</b> lane is the chain as written.
The <b>proven</b> lane keeps only beats whose every source quote passes Descartes (circle 1 or higher). Unproven beats are dashed and their links are gaps.
Click any beat to see its claim, what it rests on, what uses it and what keeps it unproven.</p>
<div class="legend"><span class="k therefore">therefore</span> the next beat rests on this one
<span class="k but">but</span> objection or reply <span class="k and">and</span> gathered for a later inference
<span class="k and-then">and then</span> nothing later uses it <span class="k gap">gap</span> not proven</div>
<table class="tally"><tr><th>Link</th><th>Proposed</th><th>Proven</th></tr>{rows}</table>
<h2>Spine: theme to theme</h2>
<p class="lede">Each theme is one beat. The answer ({E(answer_card or '—')}) rests, through its cards, on:
{E(', '.join(t for t in themes if t in feeds and t != 'answer') or 'nothing')}.
{('Not reached by the answer: ' + E(', '.join(orphan_themes)) + '.') if orphan_themes else ''}</p>
<div class="spine">{''.join(sp_html)}</div>
{''.join(body)}
<footer>Generated by <code>scripts/render_chain.py</code> from <code>argument/*.tsv</code> and
<code>argument/descartes-check.txt</code> at {E(git_head(root))}. Link rules: <code>scripts/chain_shape.py</code>.</footer>
</main><script type="application/json" id="data">{json.dumps(data, sort_keys=True).replace("</", "<\\/")}</script>
<script>{JS}</script></body></html>
"""


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    out = Path(argv[1]).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
