# How we check an argument

A fact check asks whether a statement is true. We ask: **what does the
conclusion stand on, and does that hold?** This is an instrument for
understanding an argument: which claims it stands on, which of those hold,
and what falls if one goes. Checking the facts is its first layer, not its
point.

## Fact check versus argument check

| | A fact check | This |
|---|---|---|
| Unit | one statement | the whole argument, as a graph of claims |
| Question | is this true? | what does the conclusion stand on, and does that hold? |
| Output | a verdict per statement | which claims stand, which fail, and why, all the way up to the thesis |
| A failure | marks one statement false | shows every conclusion that rests on it |
| What it says about the rest | nothing | how much of the argument depends on each claim (*because-ness*) |

Every sentence of an argument can pass a fact check while its conclusion
rests on a premise nobody sourced. An argument check catches that: the
conclusion is a node of its own, and it stands only if everything it rests on
stands. Whether those supports entail it is still a judgement (below).

## The layers

Each layer stands on the one below it, and each is deterministic unless Sloane
overrides it editorially (AGENTS.md).

1. **Sources.** Every source is pinned by its bytes and digest
   (`sources/MANIFEST.tsv`). A reader can re-fetch and compare.
2. **Text.** Each source becomes text through one recorded, general recipe
   (`derived/recipes.tsv`), and the text is rebuilt byte-identical on demand.
3. **Quotations.** Each quotation is a claim row. Descartes checks that the
   quoted words occur in the text exactly once, as whole words. This layer
   is the fact check: it proves the source says the words. It doesn't prove
   our summary of them is fair; that is model testimony (circle 3).
4. **The argument.** Each inference is a claim row with no quote of its own,
   naming in `rests_on` the claims it needs. Descartes resolves the graph: a
   claim stands only if everything it rests on stands. A premise with nothing
   under it fails, and the failure climbs to every claim above it.
5. **Order and weight.** From the graph we compute each claim's because-ness
   (how much of the argument rests on it), the order to present the argument
   in, and how much each link matters to the reader. These are computed,
   never assigned (`docs/editorial-standard.md`).
6. **The rendering.** Every document built from the paper ends with the
   verifier's result for that build (`scripts/render_report.py`).

## What it does not do

- **It doesn't judge whether an inference is valid.** It checks that a
  conclusion's supports stand, not that they entail it. Which claims a
  conclusion rests on is an editorial decision, and a proposal until it is
  computed from the paper's text or made by Sloane.
- **It doesn't check paraphrase.** A quote can exist and still be
  summarised unfairly. Atomic review (`docs/atomic-review.md`) asks that
  question claim by claim.
- **It doesn't weigh corroboration.** `rests_on` means "needs". Descartes has
  no link yet for "also supports".
- **A failure is not a refutation.** A claim fails when its support is
  missing or its instrument can't read the source (a PDF line break, a
  duplicated page). The failure says what to fix or find, not that the
  claim is false.

## Reading a result

- **ok:** the claim, and everything under it, stands.
- **has no surviving evidence:** nothing supports it yet. Find a source, or
  it becomes an open question.
- **rests on X, which is missing or failed:** look at X; this claim falls
  with it.
- **quote not found / occurs more than once:** the instrument layer. See the
  cause before touching the quote; never reshape a source to pass
  (AGENTS.md, "Checks are not beaten").

## Where this paper stands

The live result is in each rendering's verification appendix and in
`descartes check claims/anthropic-contrapunctus.tsv`. As of 2026-11-04 the
thesis (T0) fails. Five premises have no support yet, and two fail through
quotations the instrument can't yet read (`docs/editorial-standard.md`, "The
argument lives in the DAG"). The encoding of §0 is a proposal awaiting
Sloane's override or a computed form.
