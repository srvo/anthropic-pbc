"""Argument workbench: parties, coverage, quantities and barriers on top of the card deck.

Primitives (all TSV under argument/):
    claims     cards.tsv (Descartes format), sequence.tsv, themes.tsv     -> check_cards.Deck
    links      therefore / but / and / and-then                            -> chain_shape.runs (never typed)
    sources    claims/anthropic-contrapunctus.tsv quotes + descartes-check.txt circles
    parties    parties.tsv   who holds a lever or bears the effects, and what establishes it
    coverage   coverage.tsv  party x theme: missing < identified < located < secondhand < voiced
    quantities quantities.tsv observed (verbatim in a pinned quote) | applied (reader slider) | implied (=formula)
    sides      sides.tsv     cards that carry Anthropic's case, for the effect-size bars

Pure functions; render_workbench.py turns them into the page. Nothing here reads the clock.
"""
from __future__ import annotations

import ast
import dataclasses
import hashlib
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import chain_shape as cs
import check_cards as cc

ARG = cc.ARG
PARTY_KINDS = ("enforcer", "affected", "both")
STATES = ("missing", "identified", "located", "secondhand", "voiced")  # weakest to strongest
BASES = ("observed", "applied", "implied")
SIDES = ("defence",)
STARTS = ("mid", "low")
FUNCS = {"min": min, "max": max}
INPUTS = ["claims/anthropic-contrapunctus.tsv", "argument/cards.tsv", "argument/sequence.tsv", "argument/themes.tsv",
          "argument/pending-sources.tsv", "argument/merges.tsv", "argument/descartes-check.txt",
          "argument/parties.tsv", "argument/coverage.tsv", "argument/quantities.tsv", "argument/sides.tsv"]


@dataclass
class Workbench:
    deck: cc.Deck
    quotes: dict[str, dict[str, str]]  # Q label -> {path, quote, statement}
    parties: list[dict[str, str]]
    coverage: list[dict[str, str]]
    quantities: list[dict[str, str]]
    sides: dict[str, str]
    errors: list[str] = field(default_factory=list)

    @property
    def qty(self) -> dict[str, dict[str, str]]:
        return {q["id"]: q for q in self.quantities}


def _rows(path: Path) -> list[dict[str, str]]:
    return cc.read_tsv(path) if path.exists() else []


def load(root: Path = cc.ROOT) -> Workbench:
    d = cc.check(cc.load(root))
    quotes = {}
    for r in cc.read_tsv(root / cc.CLAIMS, header=False):
        if len(r) == 6:
            quotes[r[0]] = {"statement": r[3], "path": r[4], "quote": r[5].replace("\\n", " ").replace("\\t", " ")}
    sides = {r["card"]: r["side"] for r in _rows(root / ARG / "sides.tsv")}
    return Workbench(d, quotes, _rows(root / ARG / "parties.tsv"), _rows(root / ARG / "coverage.tsv"),
                     _rows(root / ARG / "quantities.tsv"), sides)


def split(v: str) -> list[str]:
    return [] if v.strip() in ("", "-") else [x.strip() for x in v.split(",") if x.strip()]


# ---------------------------------------------------------------- formulas

def formula_names(expr: str) -> list[str]:
    """Identifiers an implied formula uses; raises ValueError on anything but numbers, ids, + - * / **, min, max."""
    tree = ast.parse(expr, mode="eval")
    names: list[str] = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            if n.id not in FUNCS:
                names.append(n.id)
        elif isinstance(n, ast.Call):
            if not (isinstance(n.func, ast.Name) and n.func.id in FUNCS) or n.keywords:
                raise ValueError("only min() and max() may be called")
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub) and isinstance(n.operand, ast.BinOp) \
                and isinstance(n.operand.op, ast.Pow):
            raise ValueError("write -(a**b), not -a**b (JavaScript rejects it)")
        elif not isinstance(n, (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Load, ast.Add, ast.Sub,
                                ast.Mult, ast.Div, ast.Pow, ast.USub)):
            raise ValueError(f"{type(n).__name__} is not allowed")
        if isinstance(n, ast.Constant) and not isinstance(n.value, (int, float)):
            raise ValueError("only numeric constants")
    return sorted(set(names), key=names.index)


def _eval(node: ast.AST, env: dict[str, float]) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body, env)
    if isinstance(node, ast.Constant):
        return float(node.value)
    if isinstance(node, ast.Name):
        return env[node.id]
    if isinstance(node, ast.UnaryOp):
        return -_eval(node.operand, env)
    if isinstance(node, ast.Call):
        return FUNCS[node.func.id](*(_eval(a, env) for a in node.args))
    a, b = _eval(node.left, env), _eval(node.right, env)
    op = type(node.op)
    if op is ast.Add:
        return a + b
    if op is ast.Sub:
        return a - b
    if op is ast.Mult:
        return a * b
    if op is ast.Div:
        return a / b if b else math.inf if a > 0 else -math.inf if a < 0 else math.nan
    return a ** b


def formula_js(expr: str) -> str:
    """The same formula as a JavaScript expression over an object `v` (validated by formula_names first)."""
    formula_names(expr)
    ops = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}

    def js(n: ast.AST) -> str:
        if isinstance(n, ast.Expression):
            return js(n.body)
        if isinstance(n, ast.Constant):
            return repr(float(n.value)) if isinstance(n.value, float) else str(n.value)
        if isinstance(n, ast.Name):
            return f'v["{n.id}"]'
        if isinstance(n, ast.UnaryOp):
            return f"(-{js(n.operand)})"
        if isinstance(n, ast.Call):
            return f"Math.{n.func.id}({', '.join(js(a) for a in n.args)})"
        if isinstance(n.op, ast.Pow):
            return f"Math.pow({js(n.left)}, {js(n.right)})"
        return f"({js(n.left)} {ops[type(n.op)]} {js(n.right)})"

    return js(ast.parse(expr, mode="eval"))


def implied_order(quantities: list[dict[str, str]]) -> list[str]:
    """Implied ids in dependency order (inputs first)."""
    by = {q["id"]: q for q in quantities}
    out: list[str] = []
    busy: set[str] = set()

    def visit(i: str) -> None:
        if i in out or i in busy or by[i]["basis"] != "implied":
            return
        busy.add(i)
        for n in split(by[i]["rests_on"]):
            if n in by:
                visit(n)
        out.append(i)

    for q in quantities:
        visit(q["id"])
    return out


def start_value(q: dict[str, str]) -> float:
    lo, hi = float(q["low"]), float(q["high"])
    return lo if q.get("start") == "low" else (lo + hi) / 2


def evaluate(quantities: list[dict[str, str]], overrides: dict[str, float] | None = None) -> dict[str, float | None]:
    """Value of every quantity: observed and normative as written, applied at its slider start (or override),
    implied by formula in dependency order. Pending observed values are None, and so is anything built on them."""
    overrides = overrides or {}
    by = {q["id"]: q for q in quantities}
    out: dict[str, float | None] = {}

    def val(i: str, seen: frozenset = frozenset()) -> float | None:
        if i in out:
            return out[i]
        q = by[i]
        if i in overrides:
            v: float | None = overrides[i]
        elif q["basis"] == "implied":
            # check() reports bad formulas, unknown names and cycles; here they just evaluate to None
            expr = q["value"][1:]
            try:
                names = formula_names(expr)
            except (SyntaxError, ValueError):
                names = None
            if i in seen or names is None or any(n not in by for n in names):
                return None
            env = {n: val(n, seen | {i}) for n in names}
            v = None if any(x is None for x in env.values()) else _eval(ast.parse(expr, mode="eval"), env)
        elif q["value"] != "-":
            v = float(q["value"])
        elif q["basis"] == "applied":
            v = start_value(q)
        else:
            v = None
        out[i] = v
        return v

    for q in quantities:
        val(q["id"])
    return out


def basis_of(wb: Workbench) -> dict[str, dict[str, object]]:
    """id -> {basis, effective (weakest of inputs: applied < observed), pending: blockers it inherits}."""
    by = wb.qty
    circ = cc.circles(wb.deck)
    memo: dict[str, dict[str, object]] = {}

    def blockers(labels: list[str]) -> list[str]:
        out = []
        for x in labels:
            if x in wb.deck.pending:
                out.append(x)
            elif x in wb.deck.q_labels and (wb.deck.descartes_ok is None or x not in wb.deck.descartes_ok):
                out.append(x)
            elif x in wb.deck.cards and circ.get(x, 0) < 1:
                out.append(x)
        return out

    def of(i: str) -> dict[str, object]:
        if i in memo:
            return memo[i]
        q = by[i]
        if q["basis"] == "implied":
            memo[i] = {"basis": "implied", "effective": "applied", "pending": []}  # provisional: breaks cycles
            ins = [of(n) for n in split(q["rests_on"]) if n in by]
            eff = "applied" if any(x["effective"] == "applied" for x in ins) else "observed"
            pend = sorted({p for x in ins for p in x["pending"]})
        else:
            eff = q["basis"]
            pend = sorted(blockers(split(q["rests_on"])))
        memo[i] = {"basis": q["basis"], "effective": eff, "pending": pend}
        return memo[i]

    return {q["id"]: of(q["id"]) for q in wb.quantities}


# ---------------------------------------------------------------- checks

def _number_forms(v: str) -> list[str]:
    forms = [v]
    try:
        f = float(v)
    except ValueError:
        return forms
    if f == int(f) and abs(f) >= 1000:
        forms.append(f"{int(f):,}")
    return forms


def value_in_quote(value: str, quote: str) -> bool:
    return any(re.search(r"(?<![\d.,])" + re.escape(form) + r"(?![\d])", quote) for form in _number_forms(value))


def check(wb: Workbench) -> Workbench:
    d = wb.deck
    themes = [t["theme"] for t in d.themes]
    known = d.q_labels | set(d.cards) | d.pending
    err = wb.errors.append

    pids = [p["id"] for p in wb.parties]
    for p in sorted({x for x in pids if pids.count(x) > 1}):
        err(f"parties.tsv: {p}: duplicate id")
    for p in wb.parties:
        if p["kind"] not in PARTY_KINDS:
            err(f"parties.tsv: {p['id']}: kind {p['kind']!r} is not one of {PARTY_KINDS}")
        if not p["standing"].strip():
            err(f"parties.tsv: {p['id']}: empty standing (write 'none established')")
        for x in split(p["rests_on"]):
            if x not in known:
                err(f"parties.tsv: {p['id']}: rests on {x}, which is not a Q-label, card or pending source")

    seq_theme = {r["card"]: r["theme"] for r in d.sequence}
    seen = set()
    for r in wb.coverage:
        key = (r["party"], r["theme"])
        if key in seen:
            err(f"coverage.tsv: {key[0]} x {key[1]}: duplicate")
        seen.add(key)
        if r["party"] not in pids:
            err(f"coverage.tsv: unknown party {r['party']}")
        if r["theme"] not in themes:
            err(f"coverage.tsv: unknown theme {r['theme']}")
        if r["state"] not in STATES:
            err(f"coverage.tsv: {key[0]} x {key[1]}: state {r['state']!r} is not one of {STATES}")
        cards = split(r["cards"])
        if r["state"] == "missing" and cards:
            err(f"coverage.tsv: {key[0]} x {key[1]}: missing but cites {', '.join(cards)}")
        if r["state"] != "missing" and not cards:
            err(f"coverage.tsv: {key[0]} x {key[1]}: {r['state']} needs at least one card")
        for c in cards:
            if c not in d.cards:
                err(f"coverage.tsv: {key[0]} x {key[1]}: {c} is not a card")
            elif seq_theme.get(c) != r["theme"]:
                err(f"coverage.tsv: {key[0]} x {key[1]}: {c} is in theme {seq_theme.get(c)}, not {r['theme']}")
    for p in pids:
        for t in themes:
            if (p, t) not in seen:
                err(f"coverage.tsv: {p} x {t}: no row (write 'missing')")

    by = wb.qty
    ids = [q["id"] for q in wb.quantities]
    for i in sorted({x for x in ids if ids.count(x) > 1}):
        err(f"quantities.tsv: {i}: duplicate id")
    for q in wb.quantities:
        i, b, v = q["id"], q["basis"], q["value"]
        if b not in BASES:
            err(f"quantities.tsv: {i}: basis {b!r} is not one of {BASES}")
            continue
        refs = split(q["rests_on"])
        if b == "observed":
            if not refs:
                err(f"quantities.tsv: {i}: observed but rests on nothing")
            for x in refs:
                if x not in d.q_labels and x not in d.pending:
                    err(f"quantities.tsv: {i}: observed must rest on Q-labels or pending sources; {x} is neither")
            if v == "-":
                if not any(x in d.pending for x in refs):
                    err(f"quantities.tsv: {i}: no value, but no pending source explains why")
            else:
                try:
                    float(v)
                except ValueError:
                    err(f"quantities.tsv: {i}: value {v!r} is not a number")
                    continue
                qs = [x for x in refs if x in wb.quotes]
                if not any(value_in_quote(v, wb.quotes[x]["quote"]) for x in qs):
                    err(f"quantities.tsv: {i}: value {v} does not appear in the quote of {', '.join(refs)}")
        elif b == "applied":
            for x in refs:
                if x not in known:
                    err(f"quantities.tsv: {i}: rests on {x}, which is not a Q-label, card or pending source")
            if v != "-":
                if not q["note"].startswith("normative:"):
                    err(f"quantities.tsv: {i}: an applied value needs a note beginning 'normative:'; else give a range")
            else:
                try:
                    lo, hi = float(q["low"]), float(q["high"])
                    if not lo < hi:
                        err(f"quantities.tsv: {i}: low must be below high")
                except ValueError:
                    err(f"quantities.tsv: {i}: applied needs numeric low and high")
                if q.get("start") not in STARTS:
                    err(f"quantities.tsv: {i}: start must be one of {STARTS}")
        else:
            if not v.startswith("="):
                err(f"quantities.tsv: {i}: implied value must be '=formula'")
                continue
            try:
                names = formula_names(v[1:])
            except (SyntaxError, ValueError) as e:
                err(f"quantities.tsv: {i}: bad formula: {e}")
                continue
            for n in names:
                if n not in by:
                    err(f"quantities.tsv: {i}: formula uses {n}, which is not a quantity")
            if sorted(names) != sorted(refs):
                err(f"quantities.tsv: {i}: rests_on must list exactly the formula's inputs ({', '.join(names)})")
    graph = {q["id"]: [n for n in split(q["rests_on"]) if n in by] for q in wb.quantities if q["basis"] == "implied"}
    for cyc in cc.find_cycles(graph):
        err("quantities.tsv: cycle: " + " -> ".join(cyc))

    for c, s in wb.sides.items():
        if c not in d.cards:
            err(f"sides.tsv: {c} is not a card")
        if s not in SIDES:
            err(f"sides.tsv: {c}: side {s!r} is not one of {SIDES}")
    return wb


# ---------------------------------------------------------------- analysis

def proven_links(d: cc.Deck) -> int:
    return sum(lk.proven for r in cs.runs(d) for lk in r.links)


def with_fixed(d: cc.Deck, labels: set[str]) -> cc.Deck:
    """The deck as it would be if these Q-labels passed Descartes and these pending sources were pinned and passed."""
    ok = set(d.descartes_ok or set()) | labels
    return dataclasses.replace(d, q_labels=d.q_labels | labels, descartes_ok=ok, pending=d.pending - labels,
                               errors=[], notes=[])


@dataclass
class Barrier:
    kind: str  # failing quote | pending source | missing link | unsupported standing | unsourced assumption
    item: str
    links: int  # proven links the fix alone would add
    lifts: int  # cards the fix alone lifts to circle >= 1
    blocks: int  # cards (or quantities, for an assumption) that depend on it
    detail: str
    fix: str


KIND_ORDER = ["failing quote", "pending source", "missing link", "unsupported standing", "unsourced assumption"]


def barriers(wb: Workbench) -> list[Barrier]:
    d = wb.deck
    circ = cc.circles(d)
    weak = cs.weak_points(d, circ)
    base = proven_links(d)
    out: list[Barrier] = []

    labels = sorted({x for ws in weak.values() for x in ws}
                    | {x for p in wb.parties for x in split(p["rests_on"]) if x in d.pending}
                    | {x for q in wb.quantities for x in split(q["rests_on"]) if x in d.pending})
    for x in labels:
        d2 = with_fixed(d, {x})
        c2 = cc.circles(d2)
        lifts = sum(1 for c in d.cards if circ[c] < 1 <= c2[c])
        blocks = sum(1 for ws in weak.values() if x in ws)
        if x in d.pending:
            kind, fix = "pending source", "pin the source and select the quote"
        else:
            kind, fix = "failing quote", "repair the quote so Descartes finds it once, byte for byte"
        users = sorted(c for c in d.cards if x in d.cards[c])
        extra = [p["id"] for p in wb.parties if x in split(p["rests_on"])] + \
                [q["id"] for q in wb.quantities if x in split(q["rests_on"])]
        detail = "cited by " + (", ".join(users) or "no card") + (f"; also {', '.join(extra)}" if extra else "")
        out.append(Barrier(kind, x, proven_links(d2) - base, lifts, blocks, detail, fix))

    used = cs.used_by(d)
    for r in cs.runs(d):
        for i, lk in enumerate(r.links):
            if lk.kind != cs.AND_THEN:
                continue
            a, b = r.beats[i], r.beats[i + 1]
            run = r.theme + ("/" + r.lens if r.lens != "-" else "")
            out.append(Barrier("missing link", f"{a.card} → {b.card}", int(lk.proven), 0, len(used.get(a.card, [])),
                               f"{run}: nothing later in the run rests on {a.card}",
                               "rest a later card on it, turn it into an objection, or move it"))

    for p in wb.parties:
        refs = split(p["rests_on"])
        bad = [x for x in refs if (x in d.cards and circ[x] < 1) or x in d.pending]
        if not refs or bad:
            why = "nothing in the deck establishes it" if not refs else "rests on unproven " + ", ".join(bad)
            fix = "find a source for this party's standing, or for its absence" if not refs else \
                "fix: " + ", ".join(sorted({w for x in bad for w in (weak.get(x) or [x])}))
            out.append(Barrier("unsupported standing", p["id"], 0, 0, 0, f"{p['name']}: {why}", fix))

    deps: dict[str, set[str]] = {}

    def downstream(i: str) -> set[str]:
        if i not in deps:
            deps[i] = set()
            for q in wb.quantities:
                if q["basis"] == "implied" and i in split(q["rests_on"]):
                    deps[i] |= {q["id"]} | downstream(q["id"])
        return deps[i]

    for q in wb.quantities:
        if q["basis"] == "applied" and not q["note"].startswith("normative:"):
            refs = split(q["rests_on"])
            out.append(Barrier("unsourced assumption", q["id"], 0, 0, len(downstream(q["id"])),
                               q["name"] + (f" (rests on {', '.join(refs)})" if refs else ""),
                               "pin a source for the value, or keep it as a stated assumption"))
    out.sort(key=lambda b: (-b.links, -b.lifts, -b.blocks, KIND_ORDER.index(b.kind), b.item))
    return out


def side_weights(wb: Workbench) -> list[dict[str, object]]:
    """Per theme: cards carrying the complaint vs Anthropic's case (defence), counted as written and weighted by circle.
    Cards with role lens or budget that sides.tsv does not list are method and count on neither side."""
    d = wb.deck
    circ = cc.circles(d)
    out = []
    for t in d.themes:
        rows = [r for r in d.sequence if r["theme"] == t["theme"]]
        acc = {"complaint": [0, 0, []], "defence": [0, 0, []], "method": [0, 0, []]}
        for r in rows:
            c = r["card"]
            side = wb.sides.get(c) or ("method" if r["role"] in ("lens", "budget") else "complaint")
            acc[side][0] += 1
            acc[side][1] += circ.get(c, 0)
            acc[side][2].append(c)
        out.append({"theme": t["theme"], "question": t["question"],
                    **{k: {"written": v[0], "proven": v[1], "cards": v[2]} for k, v in acc.items()}})
    return out


def theme_stats(d: cc.Deck) -> dict[str, dict[str, int]]:
    circ = cc.circles(d)
    out: dict[str, dict[str, int]] = {}
    for r in d.sequence:
        s = out.setdefault(r["theme"], {"cards": 0, "proven": 0})
        s["cards"] += 1
        s["proven"] += int(circ.get(r["card"], 0) >= 1)
    return out


def best_state(wb: Workbench) -> dict[str, str]:
    out = {p["id"]: "missing" for p in wb.parties}
    for r in wb.coverage:
        if r["state"] in STATES and r["party"] in out and STATES.index(r["state"]) > STATES.index(out[r["party"]]):
            out[r["party"]] = r["state"]
    return out


def verdict(wb: Workbench) -> dict[str, object]:
    d = wb.deck
    circ = cc.circles(d)
    rs = cs.runs(d)
    tal = cs.tally(rs)
    total = sum(v["proposed"] for v in tal.values())
    proven = sum(v["proven"] for v in tal.values())
    answer = next((r.beats[-1].card for r in rs if r.theme == "answer" and r.beats), None)
    weak = cs.weak_points(d, circ)
    return {"answer": answer, "statement": d.statements.get(answer, ""), "circle": circ.get(answer, 0),
            "links": total, "proven": proven, "therefore": tal[cs.THEREFORE]["proposed"],
            "therefore_proven": tal[cs.THEREFORE]["proven"], "and_then": tal[cs.AND_THEN]["proposed"],
            "blockers": weak.get(answer, [])}


# ---------------------------------------------------------------- survivorship (mirrored in the page's script)

def survival(h: float, t: float) -> float:
    return (1 - h) ** t


def hazard_for(target: float, years: float) -> float:
    return 1 - target ** (1 / years)


def lever_hazard(h: float, shares: list[float]) -> float:
    for s in shares:
        h *= 1 - s
    return h


# ---------------------------------------------------------------- sphere layout and bundle

def ring(n: int, r: float, cx: float = 0, cy: float = 0, phase: float = -90) -> list[tuple[float, float, float]]:
    """n points evenly on a circle, starting at the top; (x, y, angle in degrees), rounded for stable output."""
    out = []
    for i in range(n):
        a = phase + 360 * i / max(n, 1)
        out.append((round(cx + r * math.cos(math.radians(a)), 2), round(cy + r * math.sin(math.radians(a)), 2),
                    round(a, 4)))
    return out


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(root: Path = cc.ROOT) -> list[tuple[str, str, int]]:
    return [(p, sha256(root / p), (root / p).stat().st_size) for p in INPUTS if (root / p).exists()]


def inputs_digest(rows: list[tuple[str, str, int]]) -> str:
    return hashlib.sha256("".join(f"{p}\t{h}\n" for p, h, _ in rows).encode()).hexdigest()
