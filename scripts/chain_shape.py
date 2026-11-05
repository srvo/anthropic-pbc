"""Chain shape: read the argument as beats joined by THEREFORE, BUT or AND THEN.

The storyteller's rule (Parker and Stone): beats joined by "and then" are a list, not a story;
each beat should follow from the last (therefore) or turn against it (but). Logic is the same:
a conclusion is earned only through therefores, and a "but" must be answered.

For each theme (and each lens of a lensed theme) the beats are the cards in sequence order,
one per slot (the slot's default). Each link from beat i to beat i+1 is classified:

    therefore  beat i+1 rests on beat i, directly or through cards earlier in the run
    but        beat i+1 is an objection or a reply (the argument turns)
    and        beat i+1 does not rest on beat i, but a later beat rests on both (a conjunction
               gathering premises for an inference: fine, but not yet earned)
    and-then   nothing later in the run rests on beat i: it dangles, a list item

The PROPOSED shape is these links as authored. The PROVEN shape keeps a beat only at circle >= 1
(every quote under it passes Descartes) and a link only when both ends are proven; otherwise the
link is a gap. Pure functions over check_cards.Deck; render_chain.py turns them into HTML.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import check_cards as cc

THEREFORE, BUT, AND, AND_THEN = "therefore", "but", "and", "and-then"
TURN_ROLES = {"objection", "reply"}


@dataclass
class Beat:
    card: str
    role: str
    title: str
    circle: int
    statement: str
    rests_on: list[str]
    alternatives: list[str] = field(default_factory=list)

    @property
    def proven(self) -> bool:
        return self.circle >= 1


@dataclass
class Link:
    kind: str
    proven: bool  # both ends proven (and, for therefore, the support is proven)


@dataclass
class Run:
    theme: str
    lens: str  # "-" for an unlensed theme
    question: str
    beats: list[Beat]
    links: list[Link]  # len(beats) - 1
    point: str | None  # the run's last conclusion, if any

    def shape(self, proven_only: bool = False) -> str:
        """Compact glyph string: '■ ∴ ■ but ■ & ■ … ■'. Unproven beats are '□' and their links '·'."""
        out = []
        for i, b in enumerate(self.beats):
            if i:
                lk = self.links[i - 1]
                if proven_only and not lk.proven:
                    out.append("·")
                else:
                    out.append({THEREFORE: "∴", BUT: "but", AND: "&", AND_THEN: "…"}[lk.kind])
            out.append("□" if proven_only and not b.proven else "■")
        return " ".join(out)


def _closure(card: str, deps: dict[str, list[str]], inside: set[str]) -> set[str]:
    """Everything inside the run that `card` rests on, transitively (through cards outside the run too)."""
    seen: set[str] = set()
    stack = list(deps.get(card, []))
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        seen.add(x)
        stack.extend(deps.get(x, []))
    return seen & inside if inside else seen


def runs(d: cc.Deck) -> list[Run]:
    circ = cc.circles(d)
    themes = {t["theme"]: t for t in d.themes}
    # slot -> default card (first in sequence order) and its alternatives
    slot_default: dict[str, str] = {}
    slot_alts: dict[str, list[str]] = {}
    for r in d.sequence:
        slot_default.setdefault(r["slot"], r["card"])
        slot_alts.setdefault(r["slot"], []).append(r["card"])
    alias = {r["card"]: slot_default[r["slot"]] for r in d.sequence}

    def deps_of(c: str) -> list[str]:
        return [alias.get(x, x) for x in d.cards.get(c, [])]

    deps = {c: deps_of(c) for c in d.cards}

    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for r in d.sequence:
        if slot_default[r["slot"]] != r["card"]:
            continue
        lt = cc.lens_of(r["card"], d.themes)
        lens = lt[1] if lt else "-"
        grouped.setdefault((r["theme"], lens), []).append(r)

    # Unlensed cards of a lensed theme (framing, conclusion) join the default lens run.
    out: list[Run] = []
    theme_order = [t["theme"] for t in d.themes]
    for theme in theme_order:
        t = themes[theme]
        lenses = [x for x in t["lenses"].split(",") if x != "-"] or ["-"]
        shared = grouped.get((theme, "-"), []) if lenses != ["-"] else []
        for lens in lenses:
            rows = grouped.get((theme, lens), [])
            if lens != "-":
                head = [r for r in shared if r["role"] != "conclusion"]
                tail = [r for r in shared if r["role"] == "conclusion"] if lens == t["default_lens"] else []
                rows = head + rows + tail
            rows = sorted(rows, key=lambda r: int(r["order"]))
            if not rows:
                continue
            beats = [Beat(r["card"], r["role"], r["title"], circ.get(r["card"], 0), d.statements.get(r["card"], ""),
                          d.cards.get(r["card"], []), [a for a in slot_alts[r["slot"]] if a != r["card"]])
                     for r in rows]
            inside = {b.card for b in beats}
            support = {b.card: _closure(b.card, deps, inside) for b in beats}
            links = []
            for i in range(1, len(beats)):
                prev, cur = beats[i - 1], beats[i]
                if cur.role in TURN_ROLES:
                    kind = BUT
                elif prev.card in support[cur.card]:
                    kind = THEREFORE
                elif any(prev.card in support[b.card] for b in beats[i + 1:]):
                    kind = AND
                else:
                    kind = AND_THEN
                links.append(Link(kind, prev.proven and cur.proven))
            concl = [b.card for b in beats if b.role == "conclusion"]
            out.append(Run(theme, lens, t["question"], beats, links, concl[-1] if concl else None))
    return out


def used_by(d: cc.Deck) -> dict[str, list[str]]:
    """card -> cards that rest on it directly (any theme)."""
    out: dict[str, list[str]] = {c: [] for c in d.cards}
    for c, deps in d.cards.items():
        for x in deps:
            if x in out:
                out[x].append(c)
    return out


def weak_points(d: cc.Deck, circ: dict[str, int]) -> dict[str, list[str]]:
    """card -> what keeps it at circle 0: failing quotes (Q) and pending sources (P), found transitively."""
    out: dict[str, list[str]] = {}
    for c in d.cards:
        bad: list[str] = []
        seen: set[str] = set()
        stack = list(d.cards[c])
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            if x in d.cards:
                stack.extend(d.cards[x])
            elif x in d.pending or (x in d.q_labels and (d.descartes_ok is None or x not in d.descartes_ok)):
                bad.append(x)
        out[c] = sorted(bad)
    return out


def spine(d: cc.Deck, rs: list[Run]) -> list[tuple[str, str, str, bool]]:
    """Theme-to-theme links: (from_theme, to_theme, kind, proven). THEREFORE when any card of the later
    theme rests (transitively) on a card of the earlier one; BUT when the later
    theme's first beat is an objection or reply; else AND THEN. Proven when some proven card carries the dependency."""
    circ = cc.circles(d)
    by_theme: dict[str, set[str]] = {}
    for r in d.sequence:
        by_theme.setdefault(r["theme"], set()).add(r["card"])
    order = [t["theme"] for t in d.themes]
    out = []
    for a, b in zip(order, order[1:]):
        earlier = by_theme.get(a, set())
        carriers = [c for c in by_theme.get(b, set()) if _closure(c, d.cards, set()) & earlier]
        first = next((r for r in rs if r.theme == b), None)
        if first and first.beats and first.beats[0].role in TURN_ROLES:
            kind = BUT
        elif carriers:
            kind = THEREFORE
        else:
            kind = AND_THEN
        proven = any(circ.get(c, 0) >= 1 for c in carriers) if carriers else all(
            circ.get(c, 0) >= 1 for c in by_theme.get(b, set()))
        out.append((a, b, kind, proven))
    return out


def tally(rs: list[Run]) -> dict[str, dict[str, int]]:
    t = {k: {"proposed": 0, "proven": 0} for k in (THEREFORE, BUT, AND, AND_THEN)}
    for r in rs:
        for lk in r.links:
            t[lk.kind]["proposed"] += 1
            t[lk.kind]["proven"] += int(lk.proven)
    return t
