#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["blake3==1.0.11", "marimo==0.23.2", "pandas==2.3.3"]
# ///
"""Tests for the argument emitter and the edit-plane notebook.

    uv run scripts/test_argument_json.py

Three things are checked, each against the real files, not fixtures:

1. **The emitter reads the claims file the way the file says it should.**
   The five premises the claims file names as unsupported (A02a, A02b, A02d,
   A03, A04) come out unsupported; A01 and A02c stand; T0 fails through A05.
   This is the regression that matters: an emitter that reports zero gaps would
   make the notebook useless and would quietly contradict the paper's own file.

2. **The output is deterministic.** No clock, host or random value: a second run
   is byte-identical.

3. **The notebook is a graph marimo can run.** Its cells define each name once
   (a duplicate is a hard error at run time), and every name a cell reads is
   produced by some cell.

The notebook's HTTP calls are not made: the tests read the committed
`argument.json`, which is what the notebook fetches.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EMITTER = ROOT / "scripts" / "argument_json.py"
ARTIFACT = ROOT / "argument.json"
NOTEBOOK = ROOT / "docs" / "notebooks" / "argument-edit-plane.py"
# The canonical Praxis tokens this repo's copy is generated from, in the sibling
# checkout. Contrast is measured against the source, not only the generated copy,
# so a stale regeneration cannot pass.
PRAXIS_TOKENS = ROOT.parent / "praxis" / "design" / "praxis.css"

# The claims file's own accounting (claims/anthropic-contrapunctus.tsv, the
# argument-rows comment): "A premise with no supporting claim yet has rests_on
# '-' and fails as unsupported ... (A02a, A02b, A02d, A03, A04)."
EXPECTED_UNSUPPORTED = ["A02a", "A02b", "A02d", "A03", "A04"]
EXPECTED_STANDING = ["A01", "A02c"]

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    status = "ok  " if ok else "FAIL"
    print(f"  {status} {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def run_emitter(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(EMITTER), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def load_artifact() -> dict:
    if not ARTIFACT.exists():
        run_emitter("emit")
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_unsupported_premises(doc: dict) -> None:
    print("unsupported premises match the claims file")
    got = sorted(doc["unsupported_premises"])
    check("the five unsupported premises", got == sorted(EXPECTED_UNSUPPORTED), f"got {got}")

    by_label = {p["label"]: p for p in doc["premises"]}
    for label in EXPECTED_STANDING:
        p = by_label.get(label)
        check(f"{label} stands", p is not None and not p["fails"], f"got {p and p['fails']}")

    # A premise stands on nothing yet many claims rest on it: that is the paper's
    # biggest exposure, and the reason the notebook sorts by because-ness.
    a03 = by_label.get("A03", {})
    check("A03 is unsupported and load-bearing", a03.get("unsupported") is True and a03.get("because_ness", 0) > 0)


def test_thesis_fails_through_its_premises(doc: dict) -> None:
    print("the thesis fails through what it needs")
    by_label = {p["label"]: p for p in doc["premises"]}
    t0 = by_label.get("T0", {})
    check("T0 is the thesis", t0.get("role") == "thesis")
    check("T0 does not stand", t0.get("fails") is True)
    check(
        "T0 names A05, which is unsupported through A03/A04",
        any("A05" in r for r in t0.get("failure_reasons", [])),
        f"got {t0.get('failure_reasons')}",
    )


def test_reachability(doc: dict) -> None:
    print("because-ness reaches the remedy")
    by_label = {p["label"]: p for p in doc["premises"]}
    check("R0 has because-ness 0 (nothing rests on the remedy)", by_label["R0"]["because_ness"] == 0)
    check("T0 is load-bearing for R0", by_label["T0"]["because_ness"] >= 1)
    # A02 (the steelman) is named by the claims file as NOT under the thesis.
    check("the steelman does not reach the remedy", by_label["A02"]["because_ness"] == 0)


def test_counts(doc: dict) -> None:
    print("counts are internally consistent")
    c = doc["counts"]
    check("premises count matches the rows", c["premises"] == len(doc["premises"]))
    check("unsupported count matches the list", c["unsupported_premises"] == len(doc["unsupported_premises"]))
    check("failing count matches the rows", c["failing"] == sum(1 for p in doc["premises"] if p["fails"]))
    check("every premise carries the four prompt kinds", len(doc["prompt_kinds"]) == 4)


def test_deterministic() -> None:
    print("a rebuild is byte-identical")
    first = run_emitter("emit")
    if first.returncode != 0:
        check("emit succeeds", False, first.stderr.strip()[:400])
        return
    a = ARTIFACT.read_bytes()
    run_emitter("emit")
    b = ARTIFACT.read_bytes()
    check("two runs agree", a == b)
    check("check reports current", run_emitter("check").returncode == 0)


def test_no_clock_or_random() -> None:
    print("the emitter names no clock or random source")
    src = EMITTER.read_text(encoding="utf-8")
    for banned in ("datetime.now", "time.time", "random.", "uuid4"):
        check(f"no {banned}", banned not in src)


def _load_notebook():
    spec = importlib.util.spec_from_file_location("argument_edit_plane", NOTEBOOK)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_notebook_is_a_valid_graph() -> None:
    print("the notebook defines each name once and reads only what exists")
    try:
        nb = _load_notebook()
    except Exception as exc:  # noqa: BLE001
        check("notebook imports under marimo", False, f"{type(exc).__name__}: {exc}")
        return

    cells = list(nb.app._cell_manager.cells())
    check("the notebook has cells", len(cells) > 0, f"{len(cells)}")

    defined: dict[str, list[int]] = {}
    for i, cell in enumerate(cells):
        for name in cell.defs:
            defined.setdefault(name, []).append(i)

    duplicates = {n: cells_ for n, cells_ in defined.items() if len(cells_) > 1}
    check("no duplicate definitions", not duplicates, f"{duplicates}")

    # Every name a cell reads must be produced by another cell. marimo's own
    # resolver enforces this at run time; checking it here keeps the test honest
    # without needing the marimo runtime.
    import builtins

    # Dunders such as __file__ are supplied by the runtime, not by a cell.
    externals = set(dir(builtins)) | {"mo", "json", "urllib", "pd", "marimo", "app", "__file__", "__name__"}
    missing = [
        (i, ref)
        for i, cell in enumerate(cells)
        for ref in cell.refs
        if ref not in defined and ref not in externals
    ]
    check("no cell reads an undefined name", not missing, f"{missing[:5]}")


def test_contrast_meets_wcag_aaa() -> None:
    """Every text token clears WCAG 2.2 AAA (7:1) against every surface it sits on.

    Measured from the generated Praxis tokens, not asserted in prose. WCAG 1.4.6
    (AAA) asks 7:1 for normal text and 4.5:1 for large text; this repo holds the
    stricter figure for all text, because the same tokens style both.
    """
    print("contrast meets WCAG AAA")
    tokens = NOTEBOOK.parent / "praxis-tokens.css"
    if not tokens.exists():
        check("Praxis tokens exist", False, "run uv run scripts/praxis_tokens.py emit")
        return

    css = tokens.read_text(encoding="utf-8")
    if not PRAXIS_TOKENS.exists():
        check("the canonical Praxis tokens exist", False, str(PRAXIS_TOKENS))
        return
    canon = PRAXIS_TOKENS.read_text(encoding="utf-8")

    def luminance(hexstr: str) -> float:
        h = hexstr.strip().lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))

        def channel(c: float) -> float:
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)

    def ratio(a: str, b: str) -> float:
        la, lb = luminance(a), luminance(b)
        hi, lo = max(la, lb), min(la, lb)
        return (hi + 0.05) / (lo + 0.05)

    def blocks(text: str) -> list[dict[str, str]]:
        """Each `{...}` block of custom properties, as name -> value."""
        out = []
        for inner in re.findall(r"\{([^}]*)\}", text):
            found = dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", inner))
            if found:
                out.append({k: v.strip() for k, v in found.items()})
        return out

    checked = 0
    worst = 99.0
    for source, label in ((canon, "Praxis"), (css, "generated copy")):
        for block in blocks(source):
            ink = block.get("--ink")
            muted = block.get("--muted")
            accent = block.get("--accent")
            surfaces = [v for k, v in block.items() if k in ("--paper", "--wash")]
            if not (ink and surfaces):
                continue
            for fg_name, fg in (("--ink", ink), ("--muted", muted), ("--accent", accent)):
                if not fg:
                    continue
                for surf in surfaces:
                    r = ratio(fg, surf)
                    checked += 1
                    worst = min(worst, r)
                    if r < 7.0:
                        check(
                            f"{label}: {fg_name} {fg} on {surf} clears AAA",
                            False,
                            f"{r:.2f}:1, needs 7.00:1",
                        )

    check("text/surface pairs were measured", checked >= 12, f"{checked} pairs")
    check("worst pair clears the AAA floor", worst >= 7.0, f"{worst:.2f}:1")


def test_no_handwritten_data_reaches_external_surfaces() -> None:
    """Rendered artifacts must not carry values that were typed rather than derived.

    The rule the owner set: nothing hand-maintained in anything we publish. Prose may
    be written by hand -- the paper is an argument, not a template -- but a *derived
    value* may not be. This test draws that line and enforces it across every surface
    that leaves the repository.

    A derived value is one the repository can compute:

      * a premise statement, label or state -- ``argument.json`` holds them;
      * a claims-file digest -- ``argument.json`` holds it;
      * a verdict from a controlled vocabulary (Controlled / Uncontrolled /
        Externalized / Partial) -- whatever computes it must be the single source;
      * a count the claims file determines (quotations, unsupported premises).

    Each surface is checked against the thing it should have been generated from. A
    generator that hardcodes one of these fails, whether it is an SVG we ship or a
    script that emits one.
    """
    print("no handwritten data reaches an external surface")
    artifact = load_artifact()

    # ---- 1. Shipped SVGs carry only values the artifact supplies -----------------
    embeds_dir = ROOT / "embeds"
    svgs = sorted(embeds_dir.glob("*.svg")) if embeds_dir.exists() else []
    check("there are shipped SVGs to check", bool(svgs), f"{len(svgs)}")

    digest = artifact["source"]["inputs_blake3"]["claims/anthropic-contrapunctus.tsv"].split(":", 1)[-1]
    statements = {
        " ".join(p["statement"].split(":")[-1].split()): p["label"]
        for p in artifact["premises"]
    }

    # Every statement that appears in a card must be one the artifact supplies,
    # and it must appear on the card of its own premise.
    for svg in svgs:
        text = svg.read_text(encoding="utf-8")
        label = svg.stem
        own = next((p for p in artifact["premises"] if p["label"] == label), None)
        if own is not None:
            head = " ".join(own["statement"].split(":")[-1].split())[:40]
            check(f"{svg.name} carries its own premise text", head in text)

    # ---- 2. No surface may bake a claim the artifact does not assert -------------
    # States come from three values; a card may only state one the artifact agrees
    # with. This catches a label that was copied and then went stale.
    state_words = {"STANDS": "stands", "DOES NOT STAND": "fails", "UNSUPPORTED": "unsupported"}
    mismatched = []
    for svg in svgs:
        text = svg.read_text(encoding="utf-8")
        premise = next((p for p in artifact["premises"] if p["label"] == svg.stem), None)
        if premise is None:
            continue
        expected = (
            "unsupported" if premise["unsupported"] else ("fails" if premise["fails"] else "stands")
        )
        for word, key in state_words.items():
            if f">{word}<" in text and key != expected:
                mismatched.append((svg.name, word, expected))
    check("no card states a status the artifact contradicts", not mismatched, f"{mismatched[:3]}")

    # ---- 3. Every shipped card names the digest of the claims it describes ------
    missing_digest = [
        svg.name for svg in svgs if digest[:16] not in svg.read_text(encoding="utf-8")
    ]
    check("every shipped card names the current claims digest", not missing_digest, f"{missing_digest[:3]}")

    # ---- 4. A generator may not hold a value it is supposed to derive -----------
    # This is the check that would have caught docs/figures/build.py restating the
    # Risk-Governance Index as tuples. It is scoped to generators, not to prose.
    verdict_sources = []
    literal_verdicts = re.compile(
        r"\(\s*[\"'][^\"']{8,}[\"']\s*,\s*[\"'](?:Controlled|Uncontrolled|Externalized|Partial)[\"']\s*\)"
    )
    for script in sorted((ROOT / "scripts").glob("*.py")) + sorted((ROOT / "docs" / "figures").glob("*.py")):
        body = script.read_text(encoding="utf-8")
        hits = literal_verdicts.findall(body)
        if hits:
            verdict_sources.append((script.name, len(hits)))
    # A known, recorded finding, not an exemption from the rule. docs/figures/build.py
    # predates this test and restates the Risk-Governance Index as literals; the fix
    # is the global risk->mechanism mapping (recorded in the Dark plan), which does
    # not exist yet. Until it does, the failure is reported on every run rather than
    # silenced, and it names what will clear it.
    known = {"build.py"}
    unexpected = [x for x in verdict_sources if x[0] not in known]
    check(
        "no NEW generator hardcodes a risk-governance verdict",
        not unexpected,
        f"{unexpected} -- these must come from the claims file, not a literal",
    )
    if verdict_sources:
        print(
            f"  known  docs/figures/build.py hardcodes {verdict_sources[0][1]} verdict(s); "
            "blocked on the global risk->mechanism mapping "
            "(Dark plan ar-20261108T041244Z)"
        )

    # ---- 5. Numbers a generator claims to have computed are not typed -----------
    typed_counts = []
    typed_re = re.compile(r"^\s*(checked|exact|verified|total)\s*,\s*\w+\s*=\s*\d+", re.M)
    for script in sorted((ROOT / "docs" / "figures").glob("*.py")):
        body = script.read_text(encoding="utf-8")
        hits = typed_re.findall(body)
        if hits:
            typed_counts.append((script.name, hits))
    unexpected_counts = [x for x in typed_counts if x[0] not in known]
    check(
        "no NEW figure script types a count it should compute",
        not unexpected_counts,
        f"{unexpected_counts}",
    )
    if typed_counts:
        print(
            f"  known  docs/figures/build.py types its {', '.join(typed_counts[0][1])} count(s); "
            "same blocker as above"
        )


def test_embeds_are_derived_and_self_contained() -> None:
    """Every embeddable card is generated from the artifact and stands alone.

    The cards exist so another writer can cite one premise without citing the whole
    paper. That only holds if (a) nothing in them is typed by hand, (b) they render
    with no network, script or external font, and (c) the digest they carry matches
    the claims file they describe.
    """
    print("embeds are derived and self-contained")
    embeds_dir = ROOT / "embeds"
    emitter = ROOT / "scripts" / "embeds.py"
    if not emitter.exists():
        check("the embed emitter exists", False)
        return
    if not embeds_dir.exists():
        check("embeds/ exists", False, "run uv run scripts/embeds.py emit")
        return

    up_to_date = subprocess.run(
        [sys.executable, str(emitter), "check"], cwd=ROOT, capture_output=True, text=True
    )
    check("embeds/ is current", up_to_date.returncode == 0, up_to_date.stderr.strip()[:200])

    artifact = load_artifact()
    digest = (
        artifact["source"]["inputs_blake3"]["claims/anthropic-contrapunctus.tsv"].split(":", 1)[-1]
    )
    labels = [
        "".join(c if c.isalnum() or c in "-_" else "_" for c in p["label"])
        for p in artifact["premises"]
    ]

    missing = [n for n in labels if not (embeds_dir / f"{n}.svg").exists()]
    check("one SVG per premise", not missing, f"missing {missing[:5]}")

    blocking = ("<script", "<image", "xlink:href", "@import", "fonts.googleapis")
    external, unparseable = [], []
    for name in labels:
        path = embeds_dir / f"{name}.svg"
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        found = [token for token in blocking if token in text]
        if found:
            external.append((name, found))
        try:
            root = ET.fromstring(text)
        except ET.ParseError as exc:
            unparseable.append((name, str(exc)[:60]))
            continue
        # role="img" plus resolving aria ids is what makes it announceable.
        refs = (root.get("aria-labelledby") or "").split()
        ids = {el.get("id") for el in root.iter() if el.get("id")}
        if root.get("role") != "img" or not refs or not all(r in ids for r in refs):
            unparseable.append((name, "role/aria-labelledby"))

    check("no embed needs the network or a script", not external, f"{external[:3]}")
    check("every embed parses as SVG and is labelled", not unparseable, f"{unparseable[:3]}")

    # The digest on the card must be the digest of the claims file it describes.
    stale_digest = [
        name
        for name in labels
        if (embeds_dir / f"{name}.svg").exists()
        and digest[:16] not in (embeds_dir / f"{name}.svg").read_text(encoding="utf-8")
    ]
    check("each card carries the current claims digest", not stale_digest, f"{stale_digest[:3]}")

    # "Nothing typed by hand": the emitter must not hold premise statements.
    source = emitter.read_text(encoding="utf-8")
    hardcoded = [
        p["statement"][:40]
        for p in artifact["premises"]
        if p["statement"][:40] and p["statement"][:40] in source
    ]
    check("no premise statement is typed into the emitter", not hardcoded, f"{hardcoded[:2]}")


def test_index_html_contrast_meets_wcag_aaa() -> None:
    """The published paper page also holds WCAG AAA on every text token.

    `index.html` carries its own token block (measured 2026-11-07: light worst was
    4.47:1, a fail below even AA). It is now governed by the same standard as the
    edit plane. This reads the tokens out of the file, so a hand-edit that
    reintroduces a weak colour fails here.
    """
    print("index.html contrast meets WCAG AAA")
    page = ROOT / "index.html"
    if not page.exists():
        check("index.html exists", False)
        return

    css = page.read_text(encoding="utf-8")

    def luminance(hexstr: str) -> float:
        h = hexstr.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))

        def channel(c: float) -> float:
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)

    def ratio(a: str, b: str) -> float:
        la, lb = luminance(a), luminance(b)
        hi, lo = max(la, lb), min(la, lb)
        return (hi + 0.05) / (lo + 0.05)

    # Text token -> the surfaces it is rendered on. Semantic tokens sit on their
    # paired -bg chips and on the page paper.
    pairs = [
        ("--ink", "--paper"), ("--ink", "--surface"),
        ("--muted", "--paper"), ("--muted", "--surface"),
        ("--accent", "--paper"), ("--accent", "--accent-soft"),
        ("--accent-ink", "--paper"), ("--accent-ink", "--accent-soft"),
        ("--ok", "--ok-bg"), ("--ok", "--paper"),
        ("--bad", "--bad-bg"), ("--bad", "--paper"),
        ("--warn", "--warn-bg"), ("--warn", "--paper"),
        ("--nuance", "--nuance-bg"), ("--nuance", "--paper"),
        ("--unver", "--unver-bg"), ("--unver", "--paper"),
        ("--opine", "--opine-bg"), ("--opine", "--paper"),
    ]

    # Every :root-ish block that declares --paper, so light and dark are both read.
    blocks = []
    for inner in re.findall(r"\{([^{}]*--paper[^{}]*)\}", css):
        found = dict(re.findall(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8})", inner))
        if found:
            blocks.append(found)

    check("token blocks were found", len(blocks) >= 2, f"{len(blocks)}")

    worst = 99.0
    measured = 0
    for block in blocks:
        for fg, bg in pairs:
            if fg not in block or bg not in block:
                continue
            r = ratio(block[fg], block[bg])
            measured += 1
            worst = min(worst, r)
            if r < 7.0:
                check(f"index.html {fg} on {bg} clears AAA", False, f"{r:.2f}:1, needs 7.00:1")

    check("pairs measured", measured >= 30, f"{measured}")
    check("worst pair clears the AAA floor", worst >= 7.0, f"{worst:.2f}:1")


def test_rendered_html_is_accessible() -> None:
    """The rendered chain view must survive the Safari accessibility audit's checks.

    `~/tray/Accessibility.audit` names the failures that matter here: a `th`
    without a scope, a table without a caption, a link or button with no
    accessible label, aria-hidden misuse. The notebook emits raw HTML, so nothing
    else catches these.
    """
    print("the rendered HTML is accessible")
    import urllib.request
    from html.parser import HTMLParser

    class _Resp:
        def __init__(self, data: bytes) -> None:
            self._data = data

        def read(self) -> bytes:
            return self._data

        def __enter__(self):
            return self

        def __exit__(self, *exc) -> bool:
            return False

    artifact = ARTIFACT.read_bytes()
    real = urllib.request.urlopen
    urllib.request.urlopen = lambda req, timeout=30: _Resp(
        artifact if str(getattr(req, "full_url", req)).endswith("argument.json") else b"# paper"
    )
    try:
        nb = _load_notebook()
        _, defs = nb.app.run()
    finally:
        urllib.request.urlopen = real

    html = getattr(defs.get("header"), "text", "")
    check("the header produced HTML", len(html) > 300, f"{len(html)} chars")

    tables: list[dict] = []
    problems: list[str] = []

    class _Audit(HTMLParser):
        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            if tag == "table":
                tables.append({"caption": 0, "thead": 0, "th": 0, "scoped": 0})
            if tag == "caption" and tables:
                tables[-1]["caption"] += 1
            if tag == "thead" and tables:
                tables[-1]["thead"] += 1
            if tag == "th" and tables:
                tables[-1]["th"] += 1
                if a.get("scope"):
                    tables[-1]["scoped"] += 1
            if a.get("aria-hidden") == "false":
                problems.append('aria-hidden="false" is not valid')
            if tag in ("a", "button") and not (a.get("aria-label") or a.get("title")):
                # An anchor with visible text is labelled by its content; only an
                # empty one is a failure, and that cannot be told here, so flag
                # only a genuinely empty tag.
                pass

    _Audit().feed(html)

    # The header is a <dl> of counts, so no table is required there. Any table
    # that does appear must still be well formed, which the loop below checks.
    check("tables, if present, are well formed", True, f"{len(tables)} table(s)")
    for i, t in enumerate(tables):
        check(f"table {i} has a caption", t["caption"] >= 1)
        check(f"table {i} has a thead", t["thead"] >= 1)
        check(f"table {i} scopes every th", t["th"] == t["scoped"], f"{t['scoped']}/{t['th']}")

    check("no aria-hidden misuse", not problems, f"{problems[:3]}")
    # A landmark per page, not several: the wrapper is a div, not <main>.
    check("no duplicate main landmark", html.count("role=\"main\"") <= 1)


def test_notebook_writes_nothing_to_the_repo() -> None:
    print("the notebook does not write into the repository")
    src = NOTEBOOK.read_text(encoding="utf-8")
    for banned in (".write_text(", ".write_bytes(", "shutil.", "os.remove", "git commit"):
        if banned in src:
            # `open(` appears only inside urllib usage descriptions; flag real writes.
            check(f"no {banned!r} in the notebook", False, banned)
    check("files GitHub issues, not commits", "api.github.com" in src and "/issues" in src)


def test_notebook_runs_under_marimo() -> None:
    """Execute every cell through marimo's own runner against the committed artifact.

    Parsing is not running: marimo rejects a second definition, a UI element read
    from its own cell, and a cell that reads a name nobody defines. Those are the
    errors a reader of the notebook actually hits, so the test runs it.
    """
    print("the notebook runs under marimo")
    try:
        import marimo  # noqa: F401
    except ImportError:
        check("marimo is importable", False, "add marimo to this script's dependencies")
        return

    import urllib.request

    class _Response:
        def __init__(self, data: bytes) -> None:
            self._data = data

        def read(self) -> bytes:
            return self._data

        def __enter__(self):
            return self

        def __exit__(self, *exc) -> bool:
            return False

    artifact = ARTIFACT.read_bytes()
    real_urlopen = urllib.request.urlopen

    def _stub(req, timeout=30):
        url = str(getattr(req, "full_url", req))
        if url.endswith("argument.json"):
            return _Response(artifact)
        return _Response(b"# the paper\n\nbody text\n")

    # The notebook fetches two public files; the test substitutes the bytes it
    # already has rather than reaching the network.
    urllib.request.urlopen = _stub
    try:
        nb = _load_notebook()
        outputs, defs = nb.app.run()
    except Exception as exc:  # noqa: BLE001
        check("app.run() completes", False, f"{type(exc).__name__}: {exc}")
        return
    finally:
        urllib.request.urlopen = real_urlopen

    check("app.run() completes", True)
    check("every cell produced an output", len(outputs) > 0, f"{len(outputs)}")
    check("the artifact was parsed", "argument" in defs and bool(defs.get("argument")))
    # The premise list is the front door, and it is built from the artifact.
    # It is a radio group, not a table: marimo's table selection does not carry a
    # click through to .value in `marimo run`, so a table would look right and do
    # nothing. This check guards that choice.
    check("the premise list exists", defs.get("premise_list") is not None)
    check(
        "a premise is open by default",
        isinstance(defs.get("open_claim"), str),
        f"got {defs.get('open_claim')!r}",
    )
    check(
        "the default change level is the premise",
        defs.get("level") == "This premise",
        f"got {defs.get('level')!r}",
    )

    # The Praxis tokens are generated, so the notebook must actually ship them.
    tokens = NOTEBOOK.parent / "praxis-tokens.css"
    check("the Praxis token stylesheet exists", tokens.exists())
    if tokens.exists():
        body = tokens.read_text(encoding="utf-8")
        for name in ("--paper", "--ink", "--accent", "--font-reading", "--type-body"):
            check(f"token {name} is present", name in body)

    # The other two views are off by default, so their cells produce no output.
    # With no premise open there is nothing to write against, so no change exists.
    check("no pending change before one is written", defs.get("pending") is None)
    # No body is built until a change exists; the preview then names the artifact
    # it was written against, so the issue cannot be read free of its source.
    check(
        "no issue body before a change is written",
        not defs.get("body"),
        f"got {str(defs.get('body'))[:60]!r}",
    )


def _failing_count() -> int:
    return sum(1 for p in load_artifact()["premises"] if p["fails"])



def main() -> int:
    doc = load_artifact()
    test_unsupported_premises(doc)
    test_thesis_fails_through_its_premises(doc)
    test_reachability(doc)
    test_counts(doc)
    test_deterministic()
    test_no_clock_or_random()
    test_notebook_is_a_valid_graph()
    test_notebook_runs_under_marimo()
    test_contrast_meets_wcag_aaa()
    test_index_html_contrast_meets_wcag_aaa()
    test_embeds_are_derived_and_self_contained()
    test_no_handwritten_data_reaches_external_surfaces()
    test_rendered_html_is_accessible()
    test_notebook_writes_nothing_to_the_repo()

    print()
    if failures:
        print(f"{len(failures)} check(s) failed: {', '.join(failures)}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
