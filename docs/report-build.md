# The report as a build product

Status, 2026-11-04: the edition is one Praxis research report,
`edition/REPORT.md`, built by `scripts/build_edition.py` from
`edition/report.template.md` and rendered to PDF by the Praxis report writer.
The Marp deck (`DECK.md`, `deck/`) is retired: Marp needed Node and a headless
browser, and its styling was generic rather than the Praxis brand. The paper
template (edition v1 of the argument itself) is not built yet.

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
   deck (now retired), which showed v0.1 charts beside a v0.2-draft chart (executives'
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

The `edition/` folder: `REPORT.md` (the report, in the Praxis research
format), the SVG charts it uses, and a stamp file, `edition/STAMP.json`:

- source commit;
- codebook version;
- BLAKE3 of `dag.lock.tsv` (and of the Praxis catalog pin, once the data moves
  there);
- tool versions (Python packages) and the render command;
- the BLAKE3 of every output file.

A human signs the stamp (the dataset attestation mechanism, applied to the
edition). Agents never sign.

## Checks the build enforces

- every `dag.yml` step `ok`;
- one codebook version across all charts and bindings;
- every binding resolves; no unbound number in bound prose;
- a rebuild at the source commit is byte-identical.

## One source, the Praxis research format

`edition/report.template.md` follows the Praxis research presentation standard
(`praxis/design/research-presentation.md`, template
`praxis/design/research-template.md`): Bottom line, Decision-relevant facts,
What could change the conclusion, Analysis, Methods and limitations, Claims
index, Sources index, Revision and review record. The build requires exactly
these level-two sections, in this order (Praxis's `report check` requires the
same). Author: Sloane Ortell. Publisher: `praxis` (this is a personal working
paper; the Ethical Capital publisher is locked pending verified owner identity
and is never selected here). Classification: Working paper. It is marked DRAFT
in the revision line and the bottom line.

Every number is a claim. Claim ids live in `edition/claims.tsv` (`id, key,
kind, statement_ref, status, aliases, upstream, review, address,
content_id`), assigned once in file order and never reused: the build checks
the file against every committed version of it, so a reused, dropped or
renumbered id fails. `address` (`praxis:claim/anthropic-pbc/C0001`) is the
claim's address across all Praxis-governed repositories; `content_id` is the
BLAKE3 of its canonical statement (for a data claim, its claims-index heading
in the template with bindings unfilled), so the same claim in two
repositories can be matched. `build_edition.CLAIMS` lists the bindings each
data claim rests on; its order sets no id. For each binding the
build writes an Evidence line from the registry: the value, the binding it was
taken from, its numerator and denominator, how it was computed, and its source
ids. The Sources index (S001, ...) is built from the registry's source paths;
each entry names the `dag.yml` step that writes the file, its metadata file and
its BLAKE3 (directories of witness scores point to `dag.lock.tsv`). The claims
index adds no assertion the registry does not hold; its prose repeats the
retired deck's sentences or describes method.

### Render the report PDF

    uv run scripts/build_edition.py --codebook v0.2-draft
    uv run scripts/render_report.py -o /absolute/path/outside/the/repo/anthropic-pbc-report.pdf

`render_report.py` is `./praxis report from-md edition/REPORT.md --template
research --publisher praxis -o OUT` run from the Praxis checkout beside this
repository (`../praxis`), with one addition. `from-md` compiles with Typst's
root at `praxis/report_writer`, and Typst cannot read a file outside its root,
so the plain command fails on the charts ("file not found"). The wrapper hands
Typst each chart's SVG bytes instead of its path and sets the image's `alt` to
the alt text binding; everything else (the eight-section check, the publisher
lock, fonts, design tokens) is Praxis's own code, unchanged. The fix belongs in
Praxis: resolve local images against the report's directory. Python 3.14 or
later and Typst are needed (Praxis's requirements); the build itself is not.

`./praxis report bundle` is not better here: its PDF is the same `from-md`
call (same image failure), its HTML shows only the caption for a local image,
and it refuses an output directory inside a Git repository.

**Determinism.** Two renders of the same `REPORT.md` with Typst 0.15.1 and the
same Praxis checkout gave byte-identical PDFs (SHA-256 equal, 2026-11-04):
Typst writes no clock, and the PDF date is the report's `date:` (the data's
as-of). So the PDF can be hashed and signed, provided the Typst version and the
Praxis commit are recorded with it. The build does not render or hash the PDF
(it runs on Python 3.12 and needs no Praxis report writer); the stamp records
the render command.

### Slides

There is no Praxis slide template for the `praxis` publisher yet
(`report_writer/templates/presentation.typ` imports the Ethical Capital
styling). The slides are to come from the same `REPORT.md` through Typst, on
the Praxis brand: a proposed `report_writer/md_slides.py` and
`report_writer/templates/praxis-slides.typ` (title slide, then one slide per
section and per finding through Analysis, same claim tags, a closing slide
pointing to the claims and sources indices) awaits review in Praxis. No slide
styling is kept in this repository. Until it lands there, the edition has no
slides.

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
3. **One source per number.** The build draws every chart in the report itself,
   from the same registered values as the captions.
4. **Provenance.** Each value is registered with its source file, computation,
   numerator and denominator. `edition/STAMP.json` lists them all.
5. **No unbound numerals, by identity.** The template may contain no digit
   outside a `{{binding}}`. A numeral in a built report line must be supplied by
   a binding used on that same template line; a numeral in chart text must be
   supplied by the bindings that string was built from (`Build.say`, which
   records the keys). A composite binding (`Build.compose`, e.g. `ec_top3`)
   supplies only its parts' numerals. Matching any registered value is not
   enough. Minus signs are part of a numeral, and "500" passes only inside the
   name "S&P 500". The check covers every channel that ships: body text, HTML
   comments, image alt text, the front-matter `title`, `subtitle`, `author`,
   `date`, `revision`, `classification`, `note` and `watermark`, SVG
   element and `<tspan>` text, tail text, comments and `aria-label`, and
   matplotlib tick labels set from data. Only tick labels that a formatter
   computes from the axis scale are exempt.
6. **Quotes.** Quoted text in the template must be a single quote binding:
   straight and curly double quotes, single quotes (an apostrophe inside a
   word is not a quote), markdown blockquotes and HTML `<blockquote>`/`<q>`.
   Each quote must occur verbatim in edition v0. A quote taken from the
   paper's claims table also binds the status that table gives it (`q_33k`
   is bound with `UNVERIFIED/MED`), so the report cannot quote a claim without
   the paper's own verdict on it. A binding that copies another
   (`Registry.copy`) carries the original's source, numerator and denominator.
7. **Nothing clipped or malformed.** Chart text must lie inside the figure;
   every SVG must parse.
8. **One codebook** per edition.
9. **Alt text.** Every image in the template carries exactly one `{{alt_*}}`
   binding. Each alt text is composed from the same registered values as its
   chart and caption, so the numbers a screen reader hears are the numbers on
   the page (Praxis Q23). The Praxis writer prints it as the figure caption;
   `render_report.py` also sets it as the image's PDF alt text.
10. **Reading order.** The template's level-two headings are the eight Praxis
   research sections, in order.

`uv run scripts/test_edition_controls.py` feeds each control a bad input and
confirms it fails (52 cases at the 2026-11-04 review fixes; 63 after the move
to the Praxis research format, which dropped the two Marp alt-text cases and
added front-matter, section-order and claims/sources cases).

Moving the cross-source chart onto this path changed none of its 125 cell
values. The corpus report scripts moved onto `display.py` at `23a4bb6`: no
value changed; 113 cells changed format only (fixed decimal places).
