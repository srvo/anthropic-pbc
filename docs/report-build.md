# The report as a build product

Status, 2026-11-04: the deck is built (`scripts/build_edition.py`); the paper
template is not.

## Principle

The paper is not edited; it is **built**. An edition is a deterministic function
of one source commit and a few recorded parameters:

    edition = build(source commit, codebook version)

Rerunning the build at the same commit with the same parameters gives the same
bytes. The edition is then committed on top, so every edition names exactly the
code, data, codebook and prose it came from.

The **source commit** is the last commit that touched any build input (the
template, the build scripts, the codebook, `dag.lock.tsv` and every table the
build reads; `Build.inputs()` lists them), not HEAD. Committing the edition's
own outputs moves HEAD but changes no input, so the stamp and the generated
notice stay the same and `build_edition.py --check` passes on the edition
commit, in CI or anywhere else. The build already refuses to run when an input
is uncommitted or modified, so the source commit always describes the bytes the
build read. Any commit that changes an input (including a relock of unrelated
data, since `dag.lock.tsv` is an input) makes a new source commit, and
`--check` then fails until the edition is rebuilt.

`docs/anthropic-contrapunctus.md` at `1afb042` ("v0, finalized") is **edition
v0**. It was written by hand and stays frozen as it is. Editions from v1 on are
built.

## What goes in

1. **Data**: the steps in `dag.yml`. The build refuses to run unless
   `dag.py status` is all `ok`, so every table it reads is locked by hash.
2. **One codebook version** for every model-labelled chart and number in the
   edition. Mixing versions is a build error. This is the fix for the first
   deck, which shows v0.1 charts beside a v0.2-draft chart (executives'
   cybersecurity share reads 36% on one slide and 40% on another).
3. **Charts**: scripts that turn tables into SVG, with the codebook version
   as an argument and printed on the chart.
4. **Bindings**: every number in the prose is a reference to a table cell, a
   computed value, or a Descartes claim id (`docs/descartes-spec.md`). There
   are no hand-typed numbers; a lint fails the build on a bare figure in
   bound prose.
5. **Prose templates**: the argument, written and reviewed by people
   (buzz-saw and brand-voice passes apply to the templates).

## What comes out

An edition folder holding the rendered paper, the deck, the charts it used,
and a stamp file:

- source commit;
- codebook version;
- BLAKE3 of `dag.lock.tsv` (and of the Praxis catalog pin, once the data moves
  there);
- tool versions (Python packages, Marp CLI);
- the BLAKE3 of every output file.

A human signs the stamp (the dataset attestation mechanism, applied to the
edition). Agents never sign.

## Checks the build enforces

- every `dag.yml` step `ok`;
- one codebook version across all charts and bindings;
- every binding resolves; no unbound number in bound prose;
- a rebuild at the source commit is byte-identical.

## First target

`DECK.md` becomes edition output: `deck_charts.py` and the corpus report
charts take `--codebook`, slide captions take their numbers from bindings, and
the build writes the deck with its stamp. The paper template comes later.

## Open decisions

Decided 2026-11-04: the build is the review step. It writes the working tree;
a person reviews the diff and commits.

Everything still open about the report and its PDF is in Praxis
`OPENQUESTIONS.md`, Q15–Q23, so it can be discussed in one place: the codebook
(Q15), witness rates before a gold set (Q16), where editions live (Q17), what
is signed when the PDF does not render reproducibly (Q18), the chart inclusion
rule (Q19), outside review (Q20), bindings and Descartes claims (Q21), the data
source (Q22) and accessibility (Q23).

## Display controls (built, 2026-11-04)

Every number that reaches a reader passes through `scripts/display.py`, and the
build (`scripts/build_edition.py`) fails on any breach:

1. **Exact inputs.** Values are computed from integer counts or exact
   fractions. A float raises an error, so a rounded table column can never be
   shown, or rounded a second time.
2. **One rounding rule.** Half up, from the exact fraction. (Python's own
   formatting rounds binary floats half-even, so 12.5 can print as 12.)
3. **One source per number.** The build draws every chart in the deck itself,
   from the same registered values as the captions.
4. **Provenance.** Each value is registered with its source file, computation,
   numerator and denominator. `deck/STAMP.json` lists them all.
5. **No unbound numerals, by identity.** The template may contain no digit
   outside a `{{binding}}`. A numeral in a built deck line must be supplied by
   a binding used on that same template line; a numeral in chart text must be
   supplied by the bindings that string was built from (`Build.say`, which
   records the keys). A composite binding (`Build.compose`, e.g. `ec_top3`)
   supplies only its parts' numerals. Matching any registered value is not
   enough. Minus signs are part of a numeral, and "500" passes only inside the
   name "S&P 500". The check covers every channel that ships: body text, HTML
   comments (Marp presenter notes), image alt text (Marp size keywords
   aside), the front-matter `title`/`description`/`header`/`footer`, SVG
   element and `<tspan>` text, tail text, comments and `aria-label`, and
   matplotlib tick labels set from data. Only tick labels that a formatter
   computes from the axis scale are exempt.
6. **Quotes.** Quoted text in the template must be a single quote binding:
   straight and curly double quotes, single quotes (an apostrophe inside a
   word is not a quote), markdown blockquotes and HTML `<blockquote>`/`<q>`.
   Each quote must occur verbatim in edition v0. A quote taken from the
   paper's claims table also binds the status that table gives it (`q_33k`
   is bound with `UNVERIFIED/MED`), so the deck cannot quote a claim without
   the paper's own verdict on it. A binding that copies another
   (`Registry.copy`) carries the original's source, numerator and denominator.
7. **Nothing clipped or malformed.** Chart text must lie inside the figure;
   every SVG must parse.
8. **One codebook** per edition.
9. **Alt text.** Every image in the template carries exactly one `{{alt_*}}`
   binding (Marp size keywords aside). Each alt text is composed from the
   same registered values as its chart and caption, so the numbers a screen
   reader hears are the numbers on the slide (Praxis Q23).

`uv run scripts/test_edition_controls.py` feeds each control a bad input and
confirms it fails (52 cases at the 2026-11-04 review fixes).

Moving the cross-source chart onto this path changed none of its 125 cell
values. The corpus report scripts moved onto `display.py` at `23a4bb6`: no
value changed; 113 cells changed format only (fixed decimal places).
