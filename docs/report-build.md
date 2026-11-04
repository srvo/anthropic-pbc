# The report as a build product

Status: plan, 2026-11-04. Nothing below is built yet except the first deck
(`DECK.md`, hand-assembled).

## Principle

The paper is not edited; it is **built**. An edition is a deterministic function
of one source commit and a few recorded parameters:

    edition = build(source commit, codebook version)

Rerunning the build at the same commit with the same parameters gives the same
bytes. Building produces a **new commit** whose parent is the source commit, so
every edition names exactly the code, data, codebook and prose it came from.

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

1. **Codebook for the first built edition**: v0.1 (reviewed; analysts'
   questions were never scored against it, so the cross-source chart loses
   them) or v0.2 (all five sources; every chart says DRAFT until its wording is
   approved, OPENQUESTIONS Q2).
2. **Where editions live**: a folder per edition in this repository, git tags
   with release assets, or both.
3. ~~Whether the build commits by itself~~ Decided 2026-11-04: the build is the
   review step. It writes the working tree; a person reviews the diff and commits.
4. **How bindings and Descartes claims meet**: whether every binding becomes a
   Descartes claim, or only quotes from outside documents do.
5. **Where the data lives** when this runs: here, or the Praxis catalog
   (paused, pending the other session's registry work).

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
5. **No unbound numerals.** The template may contain no digit outside a
   `{{binding}}`. Every numeral in the built deck, and in chart text (axis tick
   labels aside), must be a registered value.
6. **Quotes.** Quoted text in the template must be a single quote binding, and
   each quote must occur verbatim in edition v0.
7. **Nothing clipped or malformed.** Chart text must lie inside the figure;
   every SVG must parse.
8. **One codebook** per edition.

`uv run scripts/test_edition_controls.py` feeds each control a bad input and
confirms it fails (14 cases).

Moving the cross-source chart onto this path changed none of its 125 cell
values. The corpus report scripts outside the deck (`ec_risk_series.py`,
`ec_question_report.py`, `hn_report.py`, `v02_map.py`) still format numbers
themselves. `ec_question_report.py` rounds a column that was already rounded
to two places before printing it to one. Those outputs are not shown in any
edition until they move onto `display.py`.
