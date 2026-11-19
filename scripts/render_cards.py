# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Render argument/*.tsv as a self-contained HTML card deck.

    uv run scripts/render_cards.py OUT.html

Each theme reads outward: the card that makes the point first, then the rings of
cards it rests on, then (inside each card) the quotation ring, the source words.
Cards sharing a slot are swappable alternatives, shown side by side with a toggle.
No external files; light and dark follow prefers-color-scheme. Output depends only
on the inputs and the git commit, never on the clock or the host.
"""
from __future__ import annotations

import html
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_cards as cc  # noqa: E402

ROOT = cc.ROOT
E = html.escape


def claims_index(root: Path) -> dict[str, dict[str, str]]:
    out = {}
    for r in cc.read_tsv(root / cc.CLAIMS, header=False):
        if len(r) == 6:
            out[r[0]] = {"statement": r[3], "path": r[4], "quote": r[5].replace("\\n", " ").replace("\\t", " ")}
    return out


def manifest_by_derived(root: Path) -> dict[str, str]:
    """derived/x.txt -> source url, via derived/recipes.tsv and sources/MANIFEST.tsv."""
    urls = {f"sources/{r['path']}": r["url"] for r in cc.read_tsv(root / "sources/MANIFEST.tsv")}
    out = dict(urls)
    for r in cc.read_tsv(root / "derived/recipes.tsv", header=False):
        if len(r) >= 2 and r[1] in urls:
            out[r[0]] = urls[r[1]]
    return out


def git_head(root: Path) -> str:
    p = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
    d = subprocess.run(["git", "status", "--porcelain", "--", "argument", "claims", "scripts"], cwd=root,
                       capture_output=True, text=True, check=False)
    return (p.stdout.strip() or "unknown") + (" + uncommitted changes" if d.stdout.strip() else "")


def group_of(card: str, theme_rows) -> str:
    lt = cc.lens_of(card, theme_rows)
    return lt[1] if lt else "-"


def outward(cards: list[str], deps: dict[str, list[str]], order: dict[str, int], role: dict[str, str],
            alias: dict[str, str]) -> list[tuple[int, str]]:
    """Ring for each card. Ring 0 is the point: conclusions no other conclusion in the group rests on (else an
    unrested reply, inference or budget card, in that order). Rings 1.. follow rests_on breadth-first. Cards the point
    does not reach (context, limits, elaborations) go in a last ring, -1, shown as alongside.
    `alias` maps a slot alternative to its slot's default, so swapping never changes the rings."""
    inside = set(cards)
    rested = {alias.get(x, x) for c in cards for x in deps.get(c, []) if x in inside}
    concl = [c for c in cards if role[c] == "conclusion" and alias.get(c, c) == c]
    by_concl = {alias.get(x, x) for c in concl for x in deps.get(c, []) if x in inside}
    tops = [c for c in concl if c not in by_concl]
    free = [c for c in cards if c not in rested and alias.get(c, c) == c]
    for r in ("reply", "inference", "budget"):
        tops = tops or [c for c in free if role[c] == r]
    tops = tops or free or cards[:1]
    ring = {c: 0 for c in tops}
    frontier = list(tops)
    while frontier:
        nxt = []
        for c in frontier:
            for x in deps.get(c, []):
                x = alias.get(x, x)
                if x in inside and x not in ring:
                    ring[x] = ring[c] + 1
                    nxt.append(x)
        frontier = nxt
    for c in cards:
        if alias.get(c, c) != c:
            ring[c] = ring.get(alias[c], -1)
        ring.setdefault(c, -1)
    big = 10 ** 6
    return sorted(((ring[c], c) for c in cards), key=lambda t: (big if t[0] < 0 else t[0], order[t[1]]))


CSS = """
:root{--bg:#f7f6f2;--card:#fff;--ink:#1d1d1b;--muted:#5d5b55;--line:#dcd8cf;--accent:#2f5d8a;--quote:#f0ede4;
--c0:#b5462f;--c1:#2f7a4a;--c2:#2f5d8a;--c3:#7a5a2f;--c4:#5a2f7a;--alt:#fbf3dd}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--card:#21201d;--ink:#ecebe6;--muted:#a8a59c;--line:#3a3833;
--accent:#8fb6dd;--quote:#2b2a26;--c0:#e07a62;--c1:#6cc28c;--c2:#8fb6dd;--c3:#d2ae76;--c4:#c39be0;--alt:#2e2a1d}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 64px}h1{font-size:1.6rem;margin:.2em 0}
h2{font-size:1.25rem;margin:2.2em 0 .3em}.q{color:var(--muted);margin:0 0 1em}
.ring{margin:1.2em 0 .4em;font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;min-width:0}
.card.point{border-width:2px;border-color:var(--accent)}
.card h3{font-size:1rem;margin:0 0 .3em}.st{margin:0 0 .5em}
.meta{display:flex;gap:6px;flex-wrap:wrap;font-size:.72rem;color:var(--muted);margin-bottom:.4em}
.tag{border:1px solid var(--line);border-radius:999px;padding:0 7px}
.circle{color:#fff;border-radius:999px;padding:0 7px;font-weight:600}
.c0{background:var(--c0)}.c1{background:var(--c1)}.c2{background:var(--c2)}.c3{background:var(--c3)}.c4{background:var(--c4)}
details{font-size:.85rem}summary{cursor:pointer;color:var(--muted)}
ul.rests{list-style:none;padding:0;margin:.4em 0 0}ul.rests li{margin:.35em 0;overflow-wrap:anywhere}
blockquote{margin:.2em 0;padding:.3em .6em;background:var(--quote);border-left:3px solid var(--line);border-radius:4px}
.src{font-size:.75rem;color:var(--muted)}a{color:var(--accent)}
.slot{grid-column:1/-1;border:1px dashed var(--line);border-radius:12px;padding:10px;background:var(--alt)}
.slot .opts{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;font-size:.8rem}
.slot button,.tabs button,.view button{font:inherit;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:2px 10px;cursor:pointer}
.slot button[aria-pressed=true],.tabs button[aria-selected=true],.view button[aria-pressed=true]{background:var(--accent);color:var(--bg);border-color:var(--accent)}
.slot .card.off{opacity:.45}.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:.6em 0}
.lens[hidden]{display:none}.legend{font-size:.8rem;color:var(--muted)}
footer{margin-top:3em;font-size:.8rem;color:var(--muted);border-top:1px solid var(--line);padding-top:1em}
footer pre{white-space:pre-wrap;overflow-wrap:anywhere}
body.argorder .ring{display:none}
"""

JS = """
document.querySelectorAll('.slot').forEach(function(s){var bs=s.querySelectorAll('.opts button');
bs.forEach(function(b){b.addEventListener('click',function(){bs.forEach(function(x){x.setAttribute('aria-pressed',x===b)});
s.querySelectorAll('.card').forEach(function(c){c.classList.toggle('off',c.dataset.card!==b.dataset.card)})})})});
document.querySelectorAll('.tabs').forEach(function(t){var bs=t.querySelectorAll('button');
bs.forEach(function(b){b.addEventListener('click',function(){bs.forEach(function(x){x.setAttribute('aria-selected',x===b)});
document.querySelectorAll('.lens[data-theme="'+t.dataset.theme+'"]').forEach(function(l){l.hidden=l.dataset.lens!==b.dataset.lens})})})});
"""


def render(root: Path = ROOT) -> str:
    d = cc.check(cc.load(root))
    circ = cc.circles(d)
    claims = claims_index(root)
    urls = manifest_by_derived(root)
    pending = {r["id"]: r for r in cc.read_tsv(root / cc.ARG / "pending-sources.tsv")}
    seq = d.sequence
    meta = {r["card"]: r for r in seq}
    order = {r["card"]: int(r["order"]) for r in seq}
    title = {r["card"]: r["title"] for r in seq}
    slots: dict[str, list[str]] = {}
    for r in sorted(seq, key=lambda r: int(r["order"])):
        slots.setdefault(r["slot"], []).append(r["card"])

    def qcircle(q: str) -> int:
        return 1 if d.descartes_ok and q in d.descartes_ok else 0

    def rest_item(x: str) -> str:
        if x in claims:
            c = claims[x]
            url = urls.get(c["path"], "")
            src = f'<a href="{E(url)}">{E(c["path"])}</a>' if url else E(c["path"])
            return (f'<li><span class="circle c{qcircle(x)}" title="circle">{qcircle(x)}</span> <b>{E(x)}</b> '
                    f'<blockquote>{E(c["quote"])}</blockquote><span class="src">{src} · {E(c["statement"])}</span></li>')
        if x in pending:
            p = pending[x]
            link = f' <a href="{E(p["url"])}">source</a>' if p["url"] != "-" else ""
            return (f'<li><span class="circle c0">0</span> <b>{E(x)}</b> pending ({E(p["kind"])}): '
                    f'{E(p["note"])}{link}</li>')
        if x in meta:
            return (f'<li><span class="circle c{circ[x]}">{circ[x]}</span> <a href="#{E(x)}">{E(x)}</a> '
                    f'{E(title[x])}</li>')
        return f"<li><b>{E(x)}</b> unresolved</li>"

    def card_html(c: str, point: bool = False, off: bool = False) -> str:
        m = meta[c]
        cls = "card" + (" point" if point else "") + (" off" if off else "")
        rests = "".join(rest_item(x) for x in d.cards[c])
        return (f'<article class="{cls}" id="{E(c)}" data-card="{E(c)}"><div class="meta">'
                f'<span class="circle c{circ[c]}" title="highest circle verified">circle {circ[c]}</span>'
                f'<span class="tag">{E(m["role"])}</span><span class="tag">{E(c)}</span>'
                f'<span class="tag">{E(m["status"])}</span></div><h3>{E(m["title"])}</h3>'
                f'<p class="st">{E(d.statements[c])}</p><details><summary>rests on {len(d.cards[c])}</summary>'
                f'<ul class="rests">{rests}</ul></details></article>')

    def block(cards: list[str]) -> str:
        out, done = [], set()
        alias = {a: slots[meta[a]["slot"]][0] for a in cards if slots[meta[a]["slot"]][0] != a}
        rings = outward(cards, d.cards, order, {c: meta[c]["role"] for c in cards}, alias)
        last = None
        cur: list[str] = []
        for ring, c in rings:
            if c in done or c in alias:
                continue
            if ring != last:
                if cur:
                    out.append('<div class="grid">' + "".join(cur) + "</div>")
                    cur = []
                label = "point" if ring == 0 else ("alongside" if ring < 0 else f"ring {ring}")
                out.append(f'<div class="ring">{label}</div>')
                last = ring
            alts = [a for a in slots[meta[c]["slot"]] if a in cards]
            if len(alts) > 1:
                done.update(alts)
                btns = "".join(f'<button type="button" data-card="{E(a)}" aria-pressed="{str(i == 0).lower()}">'
                               f'{E(title[a])}</button>' for i, a in enumerate(alts))
                cur.append(f'<div class="slot"><div class="opts">Swappable · slot {E(meta[c]["slot"])}: {btns}</div>'
                           f'<div class="grid">' + "".join(card_html(a, off=i > 0) for i, a in enumerate(alts))
                           + "</div></div>")
            else:
                done.add(c)
                cur.append(card_html(c, point=ring == 0))
        if cur:
            out.append('<div class="grid">' + "".join(cur) + "</div>")
        return "".join(out)

    body = []
    for t in d.themes:
        tid = t["theme"]
        in_theme = [r["card"] for r in sorted(seq, key=lambda r: int(r["order"])) if r["theme"] == tid]
        body.append(f'<section id="theme-{E(tid)}"><h2>{E(t["question"])}</h2>'
                    f'<p class="q">Theme <b>{E(tid)}</b> · {len(in_theme)} cards</p>')
        base = [c for c in in_theme if group_of(c, d.themes) == "-"]
        body.append(block(base))
        lenses = [x for x in t["lenses"].split(",") if x != "-"]
        if lenses:
            body.append(f'<div class="tabs" role="tablist" data-theme="{E(tid)}">Lens: ' + "".join(
                f'<button type="button" role="tab" data-lens="{E(l)}" aria-selected="{str(l == t["default_lens"]).lower()}">'
                f'{E(l)}</button>' for l in lenses) + "</div>")
            for l in lenses:
                lc = [c for c in in_theme if group_of(c, d.themes) == l]
                hidden = "" if l == t["default_lens"] else " hidden"
                body.append(f'<div class="lens" data-theme="{E(tid)}" data-lens="{E(l)}"{hidden}>'
                            f'<p class="q">Lens <b>{E(l)}</b>: definition, what it implies for compute, '
                            f'the budget it yields, its limit.</p>{block(lc)}</div>')
        body.append("</section>")

    dist: dict[int, int] = {}
    for v in circ.values():
        dist[v] = dist.get(v, 0) + 1
    check_txt = root / cc.ARG / "descartes-check.txt"
    dsum = [l for l in check_txt.read_text(encoding="utf-8").splitlines() if l.startswith("summary")] if check_txt.exists() else ["not run"]
    alts = [f"{s}: {', '.join(cs)}" for s, cs in slots.items() if len(cs) > 1]
    foot = "\n".join([
        f"Generated from commit {git_head(root)} by scripts/render_cards.py.",
        f"Validator (scripts/check_cards.py): {len(d.cards)} cards, {len(d.themes)} themes, "
        f"{len(d.errors)} problems; circles {dict(sorted(dist.items()))}.",
        "Descartes over claims + cards (argument/descartes-check.txt): " + "; ".join(dsum),
        "Swappable slots: " + ("; ".join(alts) or "none"),
        f"Pending sources ({len(pending)}): " + ", ".join(sorted(pending)),
        "Circles (descartes docs/circles.md): 0 source bytes only, or pending; 1 one instrument "
        "(text recipe plus byte-exact quote match); 2 an independent instrument; 3 LLM proposal passing 1-2; "
        "4 a person's sign-off. A card is the minimum of what it rests on; every statement is LLM-written "
        "and no card has a sign-off.",
    ])
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "<title>Anthropic PBC argument cards</title>"
            f"<style>{CSS}</style></head><body><main><h1>Anthropic PBC: the argument as cards</h1>"
            "<p class=\"q\">One claim per card. Each theme opens with the card that makes its point; "
            "the rings below are what it rests on, out to the source words. Draft: every card is LLM testimony "
            "awaiting review.</p>"
            "<p class=\"legend\">Circle badge = highest circle the card is verified at: "
            + "".join(f'<span class="circle c{i}">{i}</span> ' for i in range(5))
            + "</p><nav class=\"legend\">"
            + " · ".join(f'<a href="#theme-{E(t["theme"])}">{E(t["theme"])}</a>' for t in d.themes)
            + "</nav>" + "".join(body)
            + f"<footer><b>Verification</b><pre>{E(foot)}</pre></footer></main><script>{JS}</script></body></html>\n")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: render_cards.py OUT.html", file=sys.stderr)
        return 2
    out = Path(argv[0])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
