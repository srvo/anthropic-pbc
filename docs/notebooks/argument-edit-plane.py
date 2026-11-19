import marimo

__generated_with = "0.23.2"
app = marimo.App(
    width="medium",
    app_title="The argument's gaps — Anthropic PBC edit plane",
)


@app.cell
def _():
    """The argument's edit plane: read each premise, then mark it up.

    The paper's argument is a chain of claims. The notebook lists them, and lets
    you open any one to its full detail and write a change against it — at the
    level of the whole argument, a single premise, or a single quotation under a
    premise.

    Nothing is written to the repository. What you write collects as pending
    changes, shown as tracked changes (the old words struck, the new words added),
    and becomes a GitHub issue when you file it. The paper changes when someone
    acts on the issue and it is reviewed.

    Design follows the Praxis primitive (`design/praxis.css`). The tokens in
    `praxis-tokens.css` are generated from it by `scripts/praxis_tokens.py`.
    """
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    """Load the Praxis tokens and the stylesheet that binds them to the notebook."""
    from pathlib import Path as _Path

    _here = _Path(__file__).resolve().parent

    def _read(name):
        path = _here / name
        return path.read_text(encoding="utf-8") if path.exists() else None

    # The tokens are generated from Praxis design/praxis.css. Missing them is a
    # finding, not something to paper over with an invented palette.
    praxis_tokens = _read("praxis-tokens.css")
    tokens_status = (
        "Praxis tokens loaded"
        if praxis_tokens
        else "Praxis tokens missing — run `uv run scripts/praxis_tokens.py emit`"
    )

    # Every value below is a Praxis custom property: no literal colour, font or
    # size appears, so the notebook inherits the primitive rather than copying it.
    praxis_css = """
    .praxis-plane {
      margin: 0; padding: 0;
      background: var(--paper); color: var(--ink);
      font: var(--type-body)/var(--leading-reading) var(--font-reading);
      max-width: var(--page-width);
    }
    .praxis-plane ::selection { background: var(--ink); color: var(--paper); }
    .praxis-plane a { color: inherit; text-underline-offset: 4px; }
    .praxis-plane a:hover { color: var(--accent); }
    .praxis-plane h1, .praxis-plane h2, .praxis-plane h3 { text-wrap: balance; font-weight: 400; }
    .praxis-plane:first-of-type { padding-top: var(--space-section); }
    .praxis-plane :is(h1, h2, h3, p, ol, ul, table, dl, pre, section, article, div.list)
      { padding-inline: var(--page-gutter); }
    .praxis-plane h1 { font-size: var(--type-title); margin: 0 0 var(--space-small); line-height: 1.2; }
    .praxis-plane h2 { font-size: var(--type-section); letter-spacing: -.025em; line-height: 1.2;
      margin: var(--space-section) 0 var(--space-small); }
    .praxis-plane h3 { font-size: var(--type-body); margin: var(--space-group) 0 var(--space-small); }
    .praxis-plane p { max-width: var(--measure); margin: var(--space-small) 0; }
    .praxis-plane .meta { font: var(--type-small)/1.6 var(--font-label); color: var(--muted); }
    .praxis-plane .intro { max-width: 58ch; font-size: clamp(20px, 2vw, 24px); line-height: 1.5; }
    .praxis-plane :focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; }
    .praxis-plane table { border-collapse: collapse; width: 100%; margin: var(--space-small) 0;
      font: var(--type-small)/1.6 var(--font-label); }
    .praxis-plane caption { text-align: left; padding-bottom: 10px; color: var(--muted); }
    .praxis-plane th, .praxis-plane td { text-align: left; vertical-align: top;
      padding: 8px 12px 8px 0; border-bottom: 1px solid var(--rule);
      overflow-wrap: anywhere; }
    .praxis-plane th { font-weight: 600; }
    .praxis-plane code, .praxis-plane .formula { font-family: var(--font-data); }

    .praxis-plane .tally { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: var(--space-small) var(--space-group); margin: var(--space-group) 0; max-width: var(--measure); }
    .praxis-plane .tally div { border-top: 1px solid var(--rule); padding-top: 8px; }
    .praxis-plane .tally dt { font: var(--type-small)/1.5 var(--font-label); color: var(--muted); }
    .praxis-plane .tally dd { margin: 2px 0 0; font-size: var(--type-section); line-height: 1.1; }

    /* The premise list: a row per claim, one open at a time. */
    .praxis-plane .premise-row { display: grid; grid-template-columns: 5.5ch 9ch 12ch 1fr;
      gap: var(--space-small); align-items: baseline; width: 100%;
      padding: 9px 0; border-bottom: 1px solid var(--rule);
      background: none; border-left: 0; border-right: 0; border-top: 0;
      font: var(--type-small)/1.5 var(--font-label); color: inherit; text-align: left; cursor: pointer; }
    .praxis-plane .premise-row:hover { background: var(--wash); }
    .praxis-plane .premise-row[aria-expanded='true'] { background: var(--wash);
      border-bottom-color: var(--accent); }
    .praxis-plane .premise-row .pid { font-family: var(--font-data); }
    .praxis-plane .premise-row .st { color: var(--muted); }
    .praxis-plane .premise-row .st[data-bad='yes'] { color: var(--accent); font-weight: 600; }
    .praxis-plane .premise-row .stmt { color: var(--muted); overflow: hidden;
      text-overflow: ellipsis; white-space: nowrap; }

    /* Detail: the open premise, its evidence, and the feedback attached to it. */
    .praxis-plane .detail { border-left: 2px solid var(--accent); padding-inline-start: var(--space-group);
      margin-top: var(--space-small); }
    .praxis-plane .detail .statement { font-size: var(--type-body); margin: var(--space-small) 0; }
    .praxis-plane .evidence { list-style: none; padding: 0; margin: var(--space-small) 0; }
    .praxis-plane .evidence li { border-top: 1px solid var(--rule); padding: var(--space-small) 0; }
    .praxis-plane .evidence blockquote { margin: 4px 0; font-size: var(--type-body);
      color: var(--ink); }
    .praxis-plane .evidence .src { font: var(--type-small)/1.5 var(--font-data); color: var(--muted); }
    .praxis-plane .flag { font: var(--type-small)/1.5 var(--font-label); color: var(--accent); }

    /* A proposed change reads as a tracked change: struck, then added. */
    .praxis-plane .change { margin: var(--space-small) 0; padding: var(--space-small);
      background: var(--wash); border-top: 1px solid var(--rule); }
    .praxis-plane .change .old { color: var(--muted); text-decoration: line-through;
      text-decoration-thickness: 1px; }
    .praxis-plane .change .new { border-left: 2px solid var(--accent); padding-left: 10px;
      display: block; }
    .praxis-plane .change .why { font: var(--type-small)/1.6 var(--font-label); color: var(--muted);
      margin-top: 6px; }
    .praxis-plane .chip { font: var(--type-small)/1.5 var(--font-label); border: 1px solid var(--rule);
      padding: 1px 8px; }
    .praxis-plane .empty { color: var(--muted); font: var(--type-small)/1.6 var(--font-label); }

    @media (max-width: 640px) {
      .praxis-plane .premise-row { grid-template-columns: 5.5ch 1fr; }
      .praxis-plane .premise-row .st, .praxis-plane .premise-row .stmt { grid-column: 2; }
    }
    @media (prefers-reduced-motion: reduce) {
      .praxis-plane * { scroll-behavior: auto !important; transition: none !important; }
    }
    """

    # marimo wraps every cell separately, so the tokens are scoped to .praxis-plane
    # rather than the primitive's global body rules.
    mo.Html(f"<style>{praxis_tokens or ''}{praxis_css}</style>")
    return praxis_tokens, tokens_status


@app.cell
def _(mo):
    REPO = "srvo/anthropic-pbc"
    BRANCH = "main"
    ARTIFACT_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/argument.json"
    PAPER_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/docs/anthropic-contrapunctus.md"
    return ARTIFACT_URL, BRANCH, PAPER_URL, REPO


@app.cell
def _(ARTIFACT_URL, BRANCH, PAPER_URL):
    """Read the artifact and the paper. Local checkout first, then the branch."""
    import json
    import pathlib
    import urllib.request

    def _get(url):
        req = urllib.request.Request(url, headers={"User-Agent": "anthropic-pbc-edit-plane"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")

    def _why(exc):
        """Turn an exception into something a reader can act on.

        A raw `HTTPError: HTTP Error 429` tells the reader nothing they can use and
        leaks internals. Each case here says what happened and what to do.
        """
        import urllib.error

        if isinstance(exc, urllib.error.HTTPError):
            if exc.code == 429:
                return "the host is rate-limiting requests; wait a minute and reload"
            if exc.code == 404:
                return "the file is not on that branch yet; run the emit command and commit it"
            if 500 <= exc.code < 600:
                return f"the host returned a server error ({exc.code}); try again shortly"
            return f"the host refused the request ({exc.code})"
        if isinstance(exc, TimeoutError):
            return "the request timed out; check the connection and reload"
        if isinstance(exc, (urllib.error.URLError, ConnectionError)):
            return "no network reachable; open this from a checkout, or reconnect and reload"
        if isinstance(exc, OSError):
            # A bare OSError from the socket layer, e.g. "Network is unreachable",
            # arrives without a URL attached.
            return "no network reachable; open this from a checkout, or reconnect and reload"
        if isinstance(exc, json.JSONDecodeError):
            return f"the file is not valid JSON ({exc.msg} at line {exc.lineno})"
        return f"unexpected {type(exc).__name__}; see the notebook log for detail"

    root = pathlib.Path(__file__).resolve().parent.parent.parent

    def _local(name):
        path = root / name
        return path.read_text(encoding="utf-8") if path.exists() else None

    argument = {}
    artifact_error = ""
    artifact_source = ""
    local_artifact = _local("argument.json")
    if local_artifact is not None:
        try:
            argument = json.loads(local_artifact)
            artifact_source = "the working tree"
        except Exception as exc:
            artifact_error = f"the local argument.json would not parse — {_why(exc)}"
    if not argument and not artifact_error:
        try:
            argument = json.loads(_get(ARTIFACT_URL))
            artifact_source = BRANCH
        except Exception as exc:
            artifact_error = _why(exc)

    # A file can parse as JSON and still not be the artifact this notebook reads.
    # Without this guard a missing key raises KeyError out of a later cell and takes
    # the whole page down, which is the failure the interface must not have: one bad
    # field should degrade the view, not blank it.
    REQUIRED = {
        "premises": list,
        "counts": dict,
        "provenance": dict,
        "source": dict,
        "prompt_kinds": list,
        "unsupported_premises": list,
    }
    # `argument` may legitimately be {} (nothing loaded), so test the loaded flag,
    # not truthiness: an empty JSON object is a real parse, and a bad one.
    if artifact_source:
        missing = [k for k, t in REQUIRED.items() if not isinstance(argument.get(k), t)]
        if missing:
            artifact_error = (
                "argument.json is not the shape this page reads; missing or wrong type: "
                + ", ".join(f"`{k}`" for k in missing)
                + ". Run `uv run scripts/argument_json.py emit`."
            )
            argument = {}
    # `counts` is a dict of counters the header reads by name. Fill the ones the
    # header needs so a partial counts object renders as zero rather than raising.
    if argument:
        argument["counts"] = {
            "premises": 0, "arguments": 0, "unsupported_premises": 0,
            "failing": 0, "quotations": 0, "open_reviews": 0,
            **argument["counts"],
        }
    # Normalise each premise so one partial row degrades to "unknown" instead of
    # raising out of whichever cell touches the missing field first.
    if argument:
        _defaults = {
            "label": "?", "role": "premise", "statement": "", "section": "",
            "rests_on": [], "rests_on_evidence": [], "rests_on_premises": [],
            "rests_on_missing": [], "supported_by": [], "because_ness": 0,
            "unsupported": False, "fails": False, "failure_reasons": [],
            "open_reviews": [], "evidence": [], "evidence_count": 0,
            "kind": "observation",
        }
        argument["premises"] = [
            {**_defaults, **p} if isinstance(p, dict) else {**_defaults, "label": "?"}
            for p in argument["premises"]
        ]
    if argument:
        artifact_status = f"loaded from {artifact_source}"
    else:
        artifact_status = f"could not load `argument.json` — {artifact_error or 'unknown error'}"

    paper_text = ""
    try:
        paper_text = _local("docs/anthropic-contrapunctus.md") or _get(PAPER_URL)
        paper_status = f"the paper loaded ({len(paper_text):,} characters)"
    except Exception as exc:
        paper_status = f"the paper did not load — {_why(exc)}"

    claims_digest = (
        argument.get("source", {})
        .get("inputs_blake3", {})
        .get("claims/anthropic-contrapunctus.tsv", "unknown")
        if argument
        else "unknown"
    )
    return argument, artifact_error, artifact_status, claims_digest, paper_status


@app.cell
def _(argument, artifact_error, artifact_status, claims_digest, mo, paper_status, tokens_status):
    """The header, and the counts that say how much of the chain stands."""
    if artifact_error:
        header = mo.Html(
            f"""<div class="praxis-plane"><h1>The argument's gaps</h1>
            <div class="change"><strong>The argument graph did not load.</strong>
            <p>{artifact_error}</p>
            <p>This page reads <code>argument.json</code>, which
            <code>scripts/argument_json.py</code> emits from the claims file. Run
            <code>uv run scripts/argument_json.py emit</code> and commit it.</p></div></div>"""
        )
    else:
        c = argument["counts"]
        header = mo.Html(
            f"""<div class="praxis-plane">
            <h1>Where the argument is incomplete</h1>
            <p class="intro">A chain of claims: premises, a thesis, a remedy. A premise
            stands only if everything it rests on stands. Open any premise to read it
            and write a change.</p>
            <dl class="tally">
              <div><dt>Premises</dt><dd>{c["premises"]}</dd></div>
              <div><dt>Standing on nothing</dt><dd>{c["unsupported_premises"]}</dd></div>
              <div><dt>Not standing</dt><dd>{c["failing"]}</dd></div>
              <div><dt>Quotations</dt><dd>{c["quotations"]}</dd></div>
            </dl>
            <p class="meta">{artifact_status} · {paper_status} · {tokens_status}
            · claims <code>{claims_digest[:20]}</code></p>
            <p class="meta">Every row is a proposal: {argument["provenance"]["status_note"]}</p>
            </div>"""
        )
    header
    return


@app.cell
def _(argument, artifact_error, mo):
    """The premise list: one row per claim, one open at a time.

    This is a radio group, not a table. marimo's table selection does not carry a
    click through to `.value` in `marimo run` (reproduced in a ten-line notebook),
    so a table would look right and do nothing. A radio is the primitive that
    actually reports what was picked.
    """
    if artifact_error:
        listing = mo.md("")
        premise_list = None
    elif not argument["premises"]:
        # A valid artifact can hold zero premises (a fresh claims file, or one whose
        # argument rows were removed). Say so; do not build an empty radio, whose
        # `next(iter(...))` default raises StopIteration and blanks the page.
        premise_list = None
        listing = mo.Html(
            """<div class="praxis-plane"><h2>The premises</h2>
            <p class="empty">This artifact contains no premises. The claims file has
            argument rows (labels A01, T0, R0 and so on) that
            <code>scripts/argument_json.py</code> turns into this list; with none
            present there is nothing here to open or annotate.</p>
            <p class="meta">If that is unexpected, re-run
            <code>uv run scripts/argument_json.py emit</code> and check that
            <code>claims/anthropic-contrapunctus.tsv</code> still has its argument
            rows.</p></div>"""
        )
    else:
        options = {}
        for p in argument["premises"]:
            state = (
                "unsupported"
                if p["unsupported"]
                else ("fails" if p["fails"] else "stands")
            )
            # The label carries what the table's columns would have shown, so the
            # list reads as a list of premises rather than a list of ids.
            options[f"{p['label']} · {p['role']} · {state} · because-ness {p['because_ness']}"] = p[
                "label"
            ]
        premise_list = mo.ui.radio(
            options=options,
            value=next(iter(options)),
            label="Premises",
        )
        listing = mo.vstack(
            [
                mo.Html(
                    """<div class="praxis-plane"><h2>The premises</h2>
                    <p>Pick a premise to open it. Because-ness is how many claims rest
                    on it, counting through to the remedy, so a high score on an
                    unsupported premise is the biggest exposure. <em>Unsupported</em>
                    means the premise stands on nothing.</p></div>"""
                ),
                premise_list,
            ]
        )
    listing
    return (premise_list,)


@app.cell
def _(premise_list):
    """Which premise is open, read outside the cell that built the control."""
    open_claim = premise_list.value if premise_list is not None else None
    return (open_claim,)


@app.cell
def _(argument, artifact_error, mo, open_claim):
    """The whole argument, when nothing is open: what the list is a list of."""
    if artifact_error or open_claim is not None:
        overview = mo.md("")
    else:
        overview = mo.Html(
            """<div class="praxis-plane"><p class="empty">No premise is open.
            Choose one above to read it and write a change.</p>
            <p class="meta">Or use the toggle below to read the whole chain, the
            argument cards, or the formal logic.</p></div>"""
        )
    overview
    return


@app.cell
def _(argument, artifact_error, mo, open_claim):
    """The open premise in full: its statement, what it needs, and its evidence."""
    if artifact_error or open_claim is None:
        detail = mo.md("")
        open_premise = None
        evidence_items = []
    else:
        open_premise = next(
            (p for p in argument["premises"] if p["label"] == open_claim), None
        )
        evidence_items = open_premise["evidence"] if open_premise else []

        fits = (
            "".join(f"<li>{r}</li>" for r in open_premise["failure_reasons"])
            if open_premise and open_premise["failure_reasons"]
            else ""
        )
        fail_block = (
            f'<div class="change"><strong>Why it does not stand</strong><ul>{fits}</ul></div>'
            if fits
            else ""
        )

        needs = (
            ", ".join(f"<code>{d}</code>" for d in open_premise["rests_on"])
            if open_premise and open_premise["rests_on"]
            else "<em>nothing — this premise stands on no evidence</em>"
        )

        if evidence_items:
            ev_rows = "".join(
                f"""<li><code>{e["label"]}</code>
                    <blockquote>{e["quote"]}</blockquote>
                    <span class="src">{e["path"]}</span>
                    {f'<br><span class="flag">review: {e["review"]}</span>' if e["review"] else ""}
                </li>"""
                for e in evidence_items
            )
            evidence_html = f'<ol class="evidence">{ev_rows}</ol>'
        else:
            evidence_html = '<p class="empty">No quotation is attached to this premise.</p>'

        detail = mo.Html(
            f"""<div class="praxis-plane"><div class="detail">
            <h2>{open_premise["label"]}</h2>
            <p class="meta">{open_premise["role"]} · because-ness
              {open_premise["because_ness"]} · section {open_premise["section"] or "—"}</p>
            <p class="statement">{open_premise["statement"]}</p>
            <p class="meta">Rests on: {needs}</p>
            {fail_block}
            <h3>Evidence under it ({len(evidence_items)})</h3>
            {evidence_html}
            </div></div>"""
        )
    detail
    return evidence_items, open_premise


@app.cell
def _(argument, artifact_error, mo):
    """Choose the level a change attaches to."""
    # Options are plain strings, not a dict: marimo serialises only the keys of a
    # dict, so `value` would come back as the display label and no equality test
    # against an internal key would ever hold. The level is the label itself.
    level_ui = mo.ui.radio(
        options=["Whole argument", "This premise", "One quotation"],
        value="This premise",
        label="Attach the change to",
    )
    level_ui
    return (level_ui,)


@app.cell
def _(artifact_error, level_ui, mo, open_claim):
    level = None if artifact_error else level_ui.value
    if level == "This premise" and open_claim is None:
        warning = mo.Html(
            '<div class="praxis-plane"><p class="empty">Open a premise above first, '
            "or attach the change to the whole argument.</p></div>"
        )
    else:
        warning = mo.md("")
    warning
    return (level,)


@app.cell
def _(argument, artifact_error, evidence_items, level, mo, open_claim, open_premise):
    """The change form: what it now says, what it should say, and why."""
    if artifact_error or level is None:
        change_form = mo.md("")
        change_fields = None
    else:
        target_options = ["— (no premise selected)"] + [p["label"] for p in argument["premises"]]
        default_target = open_claim if open_claim in target_options else target_options[0]

        fields = {
            "target": mo.ui.dropdown(
                options=target_options,
                value=default_target,
                label="Claim",
            ),
            "current": mo.ui.text_area(
                label="What it says now",
                full_width=True,
            ),
            "proposed": mo.ui.text_area(
                label="What it should say",
                placeholder="The replacement wording, as you would have the paper print it.",
                full_width=True,
            ),
            "reason": mo.ui.text_area(
                label="Why",
                placeholder="The evidence, or the step the argument does not defend.",
                full_width=True,
            ),
        }
        if level == "One quotation" and evidence_items:
            fields["quotation"] = mo.ui.dropdown(
                options=[e["label"] for e in evidence_items],
                value=evidence_items[0]["label"],
                label="Quotation",
            )
        change_fields = mo.ui.dictionary(fields, label="Write the change")
        change_form = change_fields
    change_form
    return (change_fields,)


@app.cell
def _(change_fields):
    """Read the form's values outside the cell that built it."""
    change_values = change_fields.value if change_fields is not None else None
    return (change_values,)


@app.cell
def _(change_values, level, mo, open_premise):
    """The pending change, rendered as a tracked change."""
    if change_values is None or level is None:
        tracked = mo.md("")
        pending = None
    else:
        proposed = (change_values.get("proposed") or "").strip()
        if not proposed:
            tracked = mo.Html(
                '<div class="praxis-plane"><p class="empty">Nothing proposed yet — '
                "write the replacement wording and the tracked change appears here.</p></div>"
            )
            pending = None
        else:
            current = (change_values.get("current") or "").strip() or (
                open_premise["statement"] if open_premise else ""
            )
            reason = (change_values.get("reason") or "").strip() or "(no reason given)"
            target_label = change_values.get("target", "—")
            where = change_values.get("quotation")
            change_scope = target_label + (f" · quotation {where}" if where else "")

            pending = {
                "level": level,
                "target": target_label,
                "quotation": where,
                "current": current,
                "proposed": proposed,
                "reason": reason,
            }
            tracked = mo.Html(
                f"""<div class="praxis-plane"><h3>This change</h3>
                <p class="meta">{change_scope} · at the {level} level</p>
                <div class="change">
                  <span class="old">{current or "(nothing to strike)"}</span>
                  <span class="new">{proposed}</span>
                  <p class="why">Why: {reason}</p>
                </div></div>"""
            )
    tracked
    return (pending,)


@app.cell
def _(mo):
    """A token, only needed to file. It never enters the notebook file."""
    token = mo.ui.text(
        kind="password",
        label="GitHub token (issues: write) — optional",
        placeholder="github_pat_…",
        full_width=True,
    )
    token
    return (token,)


@app.cell
def _(REPO, claims_digest, level, mo, pending):
    """The issue body, ready to read before anything is filed."""
    if pending is None:
        title = body = ""
        preview = mo.Html(
            f'<div class="praxis-plane"><p class="empty">Write a change above to '
            f'preview the issue. Or open one by hand at '
            f'<a href="https://github.com/{REPO}/issues/new">github.com/{REPO}/issues/new</a>.</p></div>'
        )
    else:
        issue_scope = pending["target"] + (
            f" · quotation {pending['quotation']}" if pending["quotation"] else ""
        )
        title = f"[change] {pending['target']}: propose a revision at the {level} level"
        body = f"""\
## Proposed change

**Level:** {level}
**Target:** {issue_scope}

### Now

{pending["current"] or "(nothing recorded)"}

### Proposed

{pending["proposed"]}

### Why

{pending["reason"]}

---

Filed from the edit plane (`docs/notebooks/argument-edit-plane.py`) against
`argument.json`, emitted from `claims/anthropic-contrapunctus.tsv` at `{claims_digest}`.

This is a reader's proposal, not a finding. The paper changes by appending to the
spec's §10 log and by human review, never by editing an earlier entry; see AGENTS.md,
"Checks are not beaten" and "Disagree in the open".
"""
        preview = mo.Html(
            f"""<div class="praxis-plane"><h3>Preview</h3>
            <p class="meta">Title: {title}</p>
            <pre style="white-space:pre-wrap;border:1px solid var(--rule);
              padding:var(--space-small);background:var(--wash)">{body}</pre></div>"""
        )
    preview
    return body, title


@app.cell
def _(mo):
    button = mo.ui.button(
        value=0,
        on_click=lambda n: n + 1,
        label="File this issue on GitHub",
        kind="warn",
    )
    button
    return (button,)


@app.cell
def _(REPO, body, button, mo, title, token):
    """File it, when pressed. Nothing leaves the notebook until then."""
    def _file():
        import json as _json
        import urllib.error
        import urllib.request as _req

        if not token.value:
            return (
                "No token entered — copy the preview above and file it at "
                f"https://github.com/{REPO}/issues/new"
            )
        payload = _json.dumps({"title": title, "body": body}).encode()
        req = _req.Request(
            f"https://api.github.com/repos/{REPO}/issues",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {token.value}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "User-Agent": "anthropic-pbc-edit-plane",
            },
        )
        try:
            with _req.urlopen(req, timeout=30) as resp:
                return f"Filed: {_json.loads(resp.read().decode())['html_url']}"
        except urllib.error.HTTPError as exc:
            return f"GitHub refused it ({exc.code}): {exc.read().decode()[:400]}"
        except Exception as exc:
            return f"Could not file — {type(exc).__name__}: {exc}"

    result = (
        mo.Html(f'<div class="praxis-plane"><p>{_file()}</p></div>')
        if button.value
        else mo.md("")
    )
    result
    return


if __name__ == "__main__":
    app.run()
