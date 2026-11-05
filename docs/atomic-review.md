# Atomic review: one claim at a time, traceable by anyone

Status: standard, Sloane, 2026-11-04. Applies to every quotation and every
claim in the working paper (`docs/anthropic-contrapunctus.md`).

Review happens at the level of the single claim, so that each one rests on a
checked foundation and the paper can be built up from them. A reader who is
not an expert must be able to follow any claim back to the exact words in a
pinned source, with the surrounding passage, and see why it says what the
paper says it says.

**Why (Sloane, 2026-11-04).** Two goals. First, reduce the need for future
inference: a fact verified once, with its trail, is reused by anyone without
being re-derived, re-read or re-argued. Second, be extremely rigorous about the
fact pattern, so others can verify it easily and build on it.

## The four questions, asked of every claim

1. **Pinned?** The source is in `sources/MANIFEST.tsv` (URL, bytes, BLAKE3) and
   matches its hash. If not, go to *No source* below. Pin each text once: where
   a publisher offers several forms, pin the document form in which the text
   occurs once (a PDF or plain text over a web page that embeds its content
   twice, as the Constitution's page does), and replace the pin rather than
   keeping both. Repetition inside the document itself (an S-1's summary
   restating its Business section) is the source's own, and is handled by
   choosing a passage that occurs once.
2. **Present?** The quotation occurs exactly once, byte for byte, in the pinned
   source (or its recorded Descartes derivation): `descartes check` passes. A
   failure is a finding, never something to fit (AGENTS.md, "Checks are not
   beaten").
3. **Faithful?** Read the source passage around the quotation, enough to know
   what it is about. The paper's use must keep its meaning:
   - not a paraphrase in quotation marks;
   - not fragments joined into a sentence the source never wrote;
   - not a qualifier, condition, subject or negation cut away;
   - not a hedge turned into a fact, or a plan turned into a result;
   - not one example presented as the general case.
   Existence does not prove fidelity: Descartes proves the words are there; this
   question is whether the paper's statement follows from them in context.
4. **Breadcrumbed?** The claims file row names the source, and the review row
   records the context passage, so the trail from paper to source is complete.

A claim passes only on all four. There is no partial pass: a quotation is
verified, or it loses its quotation marks (AGENTS.md, "Always pin, always
verify, always breadcrumb").

## Verdicts (one per claim)

| Verdict | Meaning | Action |
|---|---|---|
| `verified` | All four questions pass. | None. |
| `requote` | The point stands, but the quotation is not the source's words or splits on layout. | Replace with the source's exact words, chosen to carry the point, with enough context to stand alone. |
| `unquote` | The paper's words are a fair summary but not a quotation. | Drop the quotation marks; keep the citation. |
| `context` | The quotation exists but the paper's use loses or changes its meaning. | Rewrite the paper's claim to match the source, or cut it. |
| `not-in-source` | The words are not in the cited source, and no better pinned source has them. | Research (below); until then, unquote or cut. |
| `unpinned` | The source is not pinned. | Research (below). |

## No source: research, then an open question

When a claim has no pinned source, or its words are not in the one cited:

1. **Search what we already hold**, in this order: the pinned sources
   (`sources/`), this repository's corpora (`DATASETS.md`), the Entire brain
   (`entire brain query`), and the Praxis lake and catalog.
2. **Search for a primary source**: the publisher's own document or filing, not
   a summary of it. Pin it if found.
3. **If nothing is found**, the claim becomes an open question: state the
   question precisely, what was searched, and what evidence would settle it.
   File it as an issue (Forgejo) and link it from the review row. The paper
   carries the claim without quotation marks, marked as unsourced, or not at
   all.

## Where the work lives

- `claims/anthropic-contrapunctus.tsv`: the quotations, in Descartes's format.
- `claims/anthropic-contrapunctus.review.tsv`: one row per claim:
  `label  verdict  source  context  proposed  reason  reviewer  status`.
  `context` is the source passage around the quotation, verbatim; `proposed` is
  the replacement quotation or wording; `reviewer` names who reviewed it (an
  LLM's review is a proposal; `status` stays `proposed` until a person accepts
  it).
- `docs/quote-check-<date>.md`: the unedited result of each check run.
