#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["blake3==1.0.11", "pyyaml==6.0.2", "duckdb==2.0.0"]
# ///
"""The compute graph in dag.yml: check it, lock it, and find what is stale.

Modelled on OWID's ETL graph: a step is a node named by a URI, an edge means
"depends on", and a change anywhere makes everything downstream stale. Change
is read from content, never from a clock or file times:

  input hash   BLAKE3 over the step's scripts (from `cmd`), its extra `inputs`,
               and the output hash of every dependency
  output hash  BLAKE3 over (path, BLAKE3) of every file in `outputs`

dag.lock.tsv records both for every step at the last `lock`. `status` compares:

  ok        inputs and outputs match the lock
  rebuilt   outputs changed with the same inputs: downstream must refresh
  inputs    a script or an upstream output changed: rebuild this step
  upstream  something above it is not ok

    uv run scripts/dag.py check            # URIs, deps, cycles, outputs exist
    uv run scripts/dag.py status           # per step, in dependency order (exit 1 if any not ok)
    uv run scripts/dag.py plan [URI ...]   # rebuild commands for not-ok steps (or URI + descendants)
    uv run scripts/dag.py lock             # record current hashes, after a verified rebuild
    uv run scripts/dag.py mermaid          # the graph as a Mermaid flowchart
    uv run scripts/dag.py meta [--strict]  # metadata gaps against schema/metadata.schema.yml

A step names its metadata file with `meta:` (YAML). Columns are read from the
files themselves (parquet schema, TSV/CSV header), so every column must be
documented and every documented column must exist.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import blake3
import yaml

ROOT = Path(__file__).resolve().parent.parent
DAG = ROOT / "dag.yml"
LOCK = ROOT / "dag.lock.tsv"
URI = re.compile(r"^(snapshot://[\w.-]+/[\w.-]+/[\w.-]+|data://(meadow|garden|witness)/[\w.-]+/[\w.-]+/[\w.-]+"
                 r"|viz://static/[\w.-]+/[\w.-]+/[\w.-]+)$")


def load() -> dict[str, dict]:
    steps = yaml.safe_load(DAG.read_text())["steps"]
    for s in steps.values():
        s.setdefault("deps", [])
        s.setdefault("inputs", [])
        s.setdefault("outputs", [])
        s.setdefault("cmd", "")
    return steps


def topo(steps: dict[str, dict]) -> list[str]:
    order, state = [], {}

    def visit(u: str, path: tuple[str, ...]) -> None:
        if state.get(u) == 2:
            return
        if state.get(u) == 1:
            sys.exit("cycle: " + " -> ".join(path + (u,)))
        state[u] = 1
        for d in sorted(steps[u]["deps"]):
            visit(d, path + (u,))
        state[u] = 2
        order.append(u)

    for u in sorted(steps):
        visit(u, ())
    return order


def files(patterns: list[str]) -> list[Path]:
    out: set[Path] = set()
    for p in patterns:
        out.update(x for x in ROOT.glob(p) if x.is_file()) if any(c in p for c in "*?[") else out.add(ROOT / p)
    return sorted(out)


def fhash(paths: list[Path]) -> str:
    h = blake3.blake3()
    for p in paths:
        h.update(f"{p.relative_to(ROOT)}\0".encode())
        h.update((blake3.blake3(p.read_bytes()).hexdigest() if p.exists() else "MISSING").encode() + b"\n")
    return h.hexdigest()


def scripts(s: dict) -> list[str]:
    return sorted(set(re.findall(r"scripts/[\w./-]+\.py", s["cmd"])) | set(s["inputs"]))


def hashes(steps: dict[str, dict]) -> dict[str, tuple[str, str]]:
    res: dict[str, tuple[str, str]] = {}
    for u in topo(steps):
        s = steps[u]
        out = fhash(files(s["outputs"]))
        h = blake3.blake3(fhash(files(scripts(s))).encode())
        for d in sorted(s["deps"]):
            h.update(f"{d}={res[d][1]}\n".encode())
        res[u] = (h.hexdigest(), out)
    return res


def read_lock() -> dict[str, tuple[str, str]]:
    if not LOCK.exists():
        return {}
    rows = [x.split("\t") for x in LOCK.read_text().splitlines()[1:]]
    return {r[0]: (r[1], r[2]) for r in rows}


def statuses(steps: dict[str, dict]) -> dict[str, str]:
    cur, lock, st = hashes(steps), read_lock(), {}
    for u in topo(steps):
        if u not in lock:
            st[u] = "unlocked"
        elif cur[u][0] != lock[u][0]:
            st[u] = "inputs"
        elif cur[u][1] != lock[u][1]:
            st[u] = "rebuilt"
        else:
            st[u] = "ok"
        bad = [d for d in steps[u]["deps"] if st[d] != "ok"]
        if st[u] == "ok" and bad:
            st[u] = "upstream"
    return st


def cmd_check(steps) -> int:
    errs = []
    for u, s in steps.items():
        if not URI.match(u):
            errs.append(f"bad URI: {u}")
        errs += [f"{u}: unknown dep {d}" for d in s["deps"] if d not in steps]
        errs += [f"{u}: missing script {p}" for p in scripts(s) if not (ROOT / p).exists()]
        for p in s["outputs"]:
            if not files([p]) or not all(x.exists() for x in files([p])):
                errs.append(f"{u}: missing output {p}")
    if not errs:
        topo(steps)
    print("\n".join(errs) if errs else f"ok: {len(steps)} steps, acyclic, all scripts and outputs present")
    return 1 if errs else 0


def cmd_status(steps) -> int:
    st = statuses(steps)
    for u in topo(steps):
        print(f"{st[u]:9} {u}")
    return 0 if all(v == "ok" for v in st.values()) else 1


def descendants(steps, roots: set[str]) -> set[str]:
    out, grew = set(roots), True
    while grew:
        grew = False
        for u, s in steps.items():
            if u not in out and out & set(s["deps"]):
                out.add(u)
                grew = True
    return out


def cmd_plan(steps, uris: list[str]) -> int:
    st = statuses(steps)
    want = descendants(steps, set(uris)) if uris else {u for u, v in st.items() if v != "ok"}
    for u in topo(steps):
        if u in want:
            print(f"# {u}  [{st[u]}]\n{steps[u]['cmd'] or '(hand-edited; review, no command)'}")
    return 0


def cmd_lock(steps) -> int:
    cur = hashes(steps)
    LOCK.write_text("uri\tinput_blake3\toutput_blake3\n" + "".join(
        f"{u}\t{cur[u][0]}\t{cur[u][1]}\n" for u in topo(steps)))
    print(f"locked {len(cur)} steps -> {LOCK.relative_to(ROOT)}")
    return 0


def mermaid(steps) -> str:
    ids = {u: f"n{i}" for i, u in enumerate(topo(steps))}
    lines = ["flowchart LR"]
    for u in topo(steps):
        lines.append(f'    {ids[u]}["{u.split("://")[1]}"]')
    for u in topo(steps):
        for d in sorted(steps[u]["deps"]):
            lines.append(f"    {ids[d]} --> {ids[u]}")
    return "\n".join(lines) + "\n"


SCHEMA = ROOT / "schema" / "metadata.schema.yml"


def columns_of(p: Path) -> list[str] | None:
    """Column names read from the file, or None for a non-tabular file."""
    if p.suffix == ".parquet":
        import duckdb
        return [r[0] for r in duckdb.connect().execute(f"DESCRIBE SELECT * FROM '{p}'").fetchall()]
    if p.suffix in (".tsv", ".csv"):
        sep = "\t" if p.suffix == ".tsv" else ","
        with p.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.startswith("#"):
                    import csv
                    return next(csv.reader([line.rstrip("\r\n")], delimiter=sep))
        return []
    return None


def _missing(d: dict, fields: list[str]) -> list[str]:
    out = []
    for k in fields:
        v = d.get(k)
        if v is None and d.get(f"{k}_reason"):
            continue
        if v is None or v == "" or v == [] or v == {}:
            out.append(k)
    return out


def meta_gaps(steps) -> dict[str, list[str]]:
    sch = yaml.safe_load(SCHEMA.read_text())
    gaps: dict[str, list[str]] = {}
    for u in topo(steps):
        s, g = steps[u], []
        mp = s.get("meta")
        if not mp or not (ROOT / mp).exists():
            g.append("no metadata file" + (f" ({mp})" if mp else " (no `meta:` in dag.yml)"))
            gaps[u] = g
            continue
        m = yaml.safe_load((ROOT / mp).read_text()) or {}
        kind = "snapshot" if u.startswith("snapshot://") else "dataset"
        g += [f"missing {k}" for k in _missing(m, sch[kind]["required"])]
        for k, allowed in sch[kind].get("enums", {}).items():
            if m.get(k) is not None and m.get(k) not in allowed:
                g.append(f"{k}={m.get(k)!r} not in {allowed}")
        if kind == "dataset":
            if m.get("status") == "witness":
                g += [f"missing {k} (witness)" for k in _missing(m, sch["dataset"]["witness_required"])]
                if m.get("proposal_only") is not True:
                    g.append("witness without proposal_only: true")
            if u.startswith("data://witness/") and m.get("status") != "witness":
                g.append("witness channel but status is not witness")
            tables = m.get("tables") or {}
            for f in files(s["outputs"]):
                rel = str(f.relative_to(ROOT))
                t = tables.get(rel)
                if t is None:
                    g.append(f"table {rel}: undocumented")
                    continue
                g += [f"table {rel}: missing {k}" for k in _missing(t, sch["table"]["required"])
                      if not (k == "columns" and columns_of(f) is None)]
                cols = columns_of(f) if f.exists() else None
                if cols is not None:
                    if not t.get("primary_key"):
                        g.append(f"table {rel}: missing primary_key")
                    doc = t.get("columns") or {}
                    g += [f"table {rel}: column {c!r} undocumented" for c in cols if c not in doc]
                    g += [f"table {rel}: documented column {c!r} not in file" for c in doc if c not in cols]
                    for c, cm in doc.items():
                        g += [f"table {rel}: column {c!r} missing {k}" for k in _missing(cm or {}, sch["column"]["required"])]
            for rel in tables:
                if not (ROOT / rel).exists():
                    g.append(f"table {rel}: documented but not an output")
        if g:
            gaps[u] = g
    return gaps


def cmd_meta(steps, strict: bool) -> int:
    gaps = meta_gaps(steps)
    n = sum(len(v) for v in gaps.values())
    for u in topo(steps):
        if u in gaps:
            print(f"{u}  ({len(gaps[u])})")
            for x in gaps[u][:12]:
                print(f"    {x}")
            if len(gaps[u]) > 12:
                print(f"    ... {len(gaps[u]) - 12} more")
    print(f"\n{len(steps) - len(gaps)}/{len(steps)} steps complete; {n} gaps")
    return 1 if strict and n else 0


def main() -> int:
    steps = load()
    cmd, args = (sys.argv[1] if len(sys.argv) > 1 else "status"), sys.argv[2:]
    if cmd == "mermaid":
        print(mermaid(steps), end="")
        return 0
    fn = {"check": cmd_check, "status": cmd_status, "lock": cmd_lock}.get(cmd)
    if cmd == "plan":
        return cmd_plan(steps, args)
    if cmd == "meta":
        return cmd_meta(steps, "--strict" in args)
    if not fn:
        sys.exit(__doc__)
    return fn(steps)


if __name__ == "__main__":
    sys.exit(main())
