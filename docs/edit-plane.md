# The edit plane: reading the argument in a notebook

A marimo notebook that shows the paper's argument as a graph and lets you file a
GitHub issue for every place the argument does not get there.

    https://molab.marimo.io/notebooks/nb_uYDB2pEStjeXayzq8a4a1s

The source is `docs/notebooks/argument-edit-plane.py`. The molab copy is a
convenience; the versioned copy here is the one that matters, and a change to
the argument's shape should reach both.

## The premise list, and what you can write

The notebook opens on the premise list: one row per claim, with its state and
because-ness. Choose a row to open that premise in full — its statement, what it
rests on, why it does not stand, and every quotation under it with its text, source
path and review verdict.

Feedback attaches at one of three levels:

| Level | You are editing | The issue records |
| --- | --- | --- |
| Whole argument | the thesis's own wording | the target, now, proposed, why |
| This premise | one claim | the claim, now, proposed, why |
| One quotation | a single source quotation | the claim, the quotation id, now, proposed, why |

Each change renders as a tracked change: the current words struck through in the
Praxis muted tone, the proposed words below them behind an accent rule, and the
reason beneath that. The preview below it is the exact issue body.

Nothing is written to the repository. Filing is a button, or a copy of the body to
post by hand.

### Why a radio, not a table

The premise list is `mo.ui.radio`, not `mo.ui.table`. marimo's table
`selection="single"` renders and takes clicks but never updates `.value` under
`marimo run` — reproduced in a ten-line notebook with no project code. A table
would have looked correct and done nothing, which is worse than an uglier control
that works.

`mo.ui.radio` options are plain strings, not a dict. marimo serialises only a
dict's *keys*, so `value` returns the display label and any comparison against an
internal key silently fails.

## Design tokens

The notebook uses the Praxis primitive, not a copy of its look. `design/praxis.css` in
the Praxis checkout is the source; `scripts/praxis_tokens.py` extracts the custom
properties from it into `docs/notebooks/praxis-tokens.css`, which the notebook injects
as a style block.

    uv run scripts/praxis_tokens.py emit    # regenerate from Praxis
    uv run scripts/praxis_tokens.py check   # fail if Praxis moved and this did not

No literal colour, font or size appears in the notebook's CSS: every value is a
`var(--…)` from the generated tokens, so the palette, type scale and spacing are
Praxis's own, including the Ethical Capital variant and the dark-mode block.

The original molab notebook is kept at `docs/notebooks/formal-logic-original.py` for
provenance. It is not maintained; the merged notebook replaces it.

## What it is for

The paper's argument is a chain of claims in `claims/anthropic-contrapunctus.tsv`
(docs/descartes-spec.md §8): premises A01–A09, the thesis T0, the remedy R0. Each
claim names in `rests_on` what it needs, and `rests_on` is a conjunction — a claim
stands only if everything under it stands.

The notebook asks four questions of that chain, in Sloane's framing:

1. **The argument does not get there.** Which step does it need that it lacks?
2. **A premise carries more than it can.** Which premise does work that nothing
   under it supports?
3. **A premise needs more examination.** Which premise is stated more confidently
   than what is known?
4. **There is a case the argument does not answer.** What is the strongest case in
   which it fails?

Each answer becomes a GitHub issue on this repository. The issue is the edit: the
paper changes when someone acts on it and the change is reviewed, never because a
notebook wrote to a file.

## The connection, both ways

    claims/anthropic-contrapunctus.tsv
            │  scripts/argument_json.py emit   (deterministic; no clock, no random)
            ▼
        argument.json                       ← committed, fetched by the notebook
            │  docs/notebooks/argument-edit-plane.py
            ▼
    github.com/srvo/anthropic-pbc/issues    ← one issue per gap you file

`argument.json` is the contract between the repository and the notebook. It is
generated, never hand-edited, and `uv run scripts/argument_json.py check` fails if
it is stale against the claims file.

### What the emitter computes, and its limit

`rests_on` is read from the file, never inferred. Two values are derived:

- **unsupported** — a premise that names nothing under it. `docs/editorial-standard.md`
  is explicit: *"A premise with nothing under it stays in the file and fails."* The
  claims file names five: A02a, A02b, A02d, A03, A04.
- **because-ness** — how many claims transitively rest on a claim, through to R0.
  A premise standing on nothing that much of the argument leans on is the paper's
  biggest exposure.

Because-ness is a **proposal**, and the artifact says so in its `provenance`. The
editorial standard puts that computation in Descartes, in Rust, as a command beside
`check`; that command does not exist yet. When it does, this emitter should read its
output instead of computing a stand-in.

The atomic review's verdicts (`claims/anthropic-contrapunctus.review.tsv`) are
reported apart, as `open_reviews`. They are the reviewer's proposals; a row whose
decision column records Sloane's acceptance is dropped, because the fix was made on
her word and this script does not re-read the paper to confirm it. A verdict is
never counted as a structural failure.

## Running it

The friendly HTML view is the default. `marimo run` serves the app read-only with
no code panes; `marimo edit` is for changing the notebook, and shows the source
beside the output.

    uv run --with marimo==0.23.2 --with pandas marimo run docs/notebooks/argument-edit-plane.py --port 2718

## Accessibility

The output is raw HTML, so it is written to survive an accessibility audit
(`~/tray/Accessibility.audit` names the checks):

- every table has a `<caption>` and a `<thead>`;
- every `<th>` carries `scope="col"`, so a screen reader can announce the column a
  cell belongs to;
- the header tally is a `<dl>`, not a table, because it is a key/value list;
- focus is always visible, and no `aria-hidden="false"` is emitted;
- the page keeps one heading chain, h1 → h2 → h3.

`scripts/test_argument_json.py` checks each of these against the rendered output,
so a regression fails the suite rather than reaching you.

## Layout

marimo renders every cell as its own block, so a wrapper with vertical padding
became six separate padded boxes with ~100px gaps. `.praxis-plane` carries no
vertical padding: cells sit flush, the horizontal gutter is applied once per
element, and section spacing comes from the heading margin.

## Rebuilding

```sh
uv run scripts/argument_json.py emit    # write argument.json
uv run scripts/argument_json.py check   # fail if it is stale (CI does this)
uv run scripts/argument_json.py show    # print the chain to stdout

uv run scripts/praxis_tokens.py check   # fail if Praxis moved and the tokens did not
uv run scripts/test_argument_json.py    # emitter, determinism, accessibility, a real run
```

Filing an issue from the notebook needs a GitHub token with issue scope, entered in
the notebook's own field. It stays in that session and is never written into the
notebook file. Without a token the notebook still previews the exact issue body, to
be pasted at <https://github.com/srvo/anthropic-pbc/issues/new>.

## Why an issue and not a commit

- **Checks are not beaten.** A gap found in the argument is a finding. It is not
  fixed by editing the paper until a check passes.
- **Disagree in the open.** A finding is changed by appending to a spec's §10 log,
  never by rewriting an earlier entry. An issue is the attributable record of what
  you think is missing.
- **Privileged stays dark.** An issue filed here carries only what is already
  published in this repository. Anything touching pricing, margins, compensation,
  licensing, enforcement or named counterparties belongs in the dark repository,
  not in a public issue.

## Keeping it current

The notebook reads `main`. After changing the claims file:

```sh
uv run scripts/argument_json.py emit
uv run scripts/test_argument_json.py
git add argument.json && git commit
```

A stale `argument.json` is caught by `scripts/test_argument_json.py` in CI and by
`argument_json.py check`.
