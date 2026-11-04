# Loss ledger and analytical frameworks

> **Copy.** This document comes from the Praxis/Descartes project and describes that project, not this repository. Relative links and code paths (`src/`, `claims/`, `sources/`, `Cargo.toml`, ...) point into that project and do not resolve here, except links to the other copied docs in this folder.

## Every stage is a translation

Each stage carries the source into a new form, and
[translation studies](https://en.wikipedia.org/wiki/Translation_studies)
says every translation loses something. Which thing it loses depends on what
the translator chose to keep. So the ledger never reports one fidelity
score. It reports what each stage lost, component by component, with the
circle of assumption at which that loss is measured
([`circles.md`](circles.md)).

| Stage | From → to | Kind of translation | Measured loss (Gemini transcript, 2026-11-02) | Not yet measured |
|---|---|---|---|---|
| Ingestion | bytes → artifact | identity | none: the bytes are stored whole under their digest | — |
| Derivation | PDF → text | formal (keeps the words, drops the form) | words: 0.11% lost (circle 1), 2.67% not confirmed by OCR (circle 2). Ink: 2.41% outside every word, in 17 regions. Tables and positions are not carried. | the 12 lost words by name |
| Distillation | text → claims | semantic (keeps the assertions, drops everything else) | 8.85% of bytes and 8.65% of non-blank lines lie under any quote. The largest gaps are whole code blocks, the macro-claim diagram and the Rawlsian section. | hedging, tone, speaker intent; whether a gap was dropped on purpose or missed |
| Evaluation | claims → ratings | interpretive | not built | |

`descartes coverage ROOT FILE` produces the distillation numbers. The loop
writes them to `artifacts/loss/`.

Coverage is a lower bound. A claim can carry more meaning than its quote,
and a good distillation should drop repetition. Coverage tells you where to
look, not whether the loss was justified. That judgment needs one more
proposal type: each large gap classified as *redundant* (say what it
repeats), *out of scope*, or *missed*. That classification is circle 3, and
a person agreeing with it is circle 4.

## Frameworks are data, applied as separate nodes

Claims record what a source says. A framework rates claims. If a rating were
a field inside a claim, the claim would be committed to one framework and
frameworks could never be compared. So a rating goes in its own node:

```
evaluation { framework: link to the framework's definition file,
             subject:   link to the claim being rated,
             rating:    values the framework allows,
             rests_on:  links to the claims that justify the rating,
             witness }
```

- A framework definition is a file under `frameworks/`, for example
  `admiralty.tsv` listing A–F and 1–6 with their meanings. It is ingested as
  an artifact, so each evaluation pins the exact version of the framework it
  used.
- The verifier checks that every rating is a value its framework allows, and
  that the justifying claims exist.
- Any number of frameworks can rate the same claims over the same circle 0.
  Comparing them later, for instance against outcomes, means running a query
  over evaluation nodes. No schema change is needed. Any search over
  frameworks (autoresearch) runs only when explicitly requested.

### How the three techniques fit

- **Admiralty (source reliability A–F × information credibility 1–6).** Two
  separate evaluations of one claim: one rates the source artifact's origin,
  the other the information. The verifier already proves a quote's
  *provenance*: the source really said it. That is not *credibility*.
  Credibility 1 ("confirmed") requires a claim with the same content from an
  *independent* source artifact. Independence is itself an assumption, since
  two articles can repeat one wire report. So it has to be stated as a claim
  that can be challenged.
- **ACH (Analysis of Competing Hypotheses).** Hypotheses are claims. Each
  matrix cell is an evaluation (evidence claim × hypothesis → consistent /
  inconsistent / not diagnostic). Scores are computed deterministically from
  those nodes and never stored, so they can always be recomputed.
- **Key Assumptions Check.** The DAG already makes these explicit: a
  composite claim's `rests_on` list *is* its stated assumptions. A
  red-teaming agent is just another witness that proposes counter-evidence
  claims, and the same checker verifies them.

## Errors in the pasted SAT draft

The structure is useful. The details below should not be copied into code:

- **The ACH example's arithmetic is wrong.** H3 shows two inconsistencies
  (E1, E3), not the −3 printed. Under the draft's own credibility weighting,
  B1 and A1 inconsistencies weigh 3 each, giving −6. The printed scores
  follow from neither rule.
- **Its diagnosticity test is wrong.** The code treats a row as diagnostic if
  *any* cell is inconsistent. In Heuer's method, evidence is diagnostic when
  its ratings *differ across hypotheses*. A row inconsistent with every
  hypothesis tells you nothing about which one to prefer (and may mean a
  hypothesis is missing), yet the code counts it against all of them.
- **The credibility weighting (3/2/1) is the draft's own invention**, not
  part of ACH. It may be a reasonable variant, but it should be recorded as a
  separate framework version so the two can be compared.
- **"Mathematically eliminated" overstates ACH.** ACH ranks hypotheses
  tentatively by inconsistency and pairs that with a sensitivity check on the
  few pieces of evidence that drive the result. Rejecting a hypothesis
  remains an analyst's judgment.
- **It treats a Bao proof as "confirmed" (credibility 1)**, which conflates
  provenance with truth, as explained above.
- **The STANAG number it cites has not been checked here.** Verify it before
  quoting it.
