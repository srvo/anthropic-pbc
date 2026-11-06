# Framework: promise↔act v0.1

### Codebook for the BERT enrichment pilot — definitions, thresholds, controls

**Status: FRAMEWORK (design). Binds nothing until a rule in
[`../docs/descartes-spec.md`](../docs/descartes-spec.md) names it.**
Version v0.1 · 2026-11-04 · Companion to
[`../docs/bert-enrichment-spec.md`](../docs/bert-enrichment-spec.md) §§3–7.

This file is the pre-registration. Thresholds below were chosen before any
test split was labelled or scored. Changing one after seeing results
requires v0.2, a new hash, and a changelog entry stating what was seen
first. The author ratifies or amends these numbers by editing this file in
a signed commit; until then every output that depends on them is labelled
`thresholds-provisional`.

## Resolved author decisions (2026-11-04)

| ID | Decision | Choice |
|---|---|---|
| D1 | Unit | **Clause**, annotated in sentence + paragraph context |
| D6 | Scope | Anthropic case + **cyber pilot** controls (Item 1A/106 universe) |
| D3 | Controls | **EDGAR peers + comparator PBC**, shuffled placebo, `mandated` stratum |
| D4 | Admissibility | **Route A witness-only**; no spec amendment in this spike |
| D5 | Attach | **Standalone**: results in `bert-enrichment-spec.md` §10 only |
| D2 | Thresholds | This file, §5 (provisional until author-signed) |

Corpus roles are pinned in [`../sources/MANIFEST.tsv`](../sources/MANIFEST.tsv):
case = Anthropic Report + S-1/A + Constitution; peer-nonpbc = CoreWeave
S-1/A (2025-03-20); comparator-pbc = Lemonade 10-K (2026-02-25; Lemonade is
a Delaware PBC; its benefit disclosure rides in SEC filings, not a standalone
public report — that asymmetry is recorded, not hidden). The `.rfcorpus`
Item 1A universe is the cyber-pilot negative-control pool.

## 1. Unit

A **clause**: a subject–predicate span carrying at most one modal/commitment
operator. Annotators see the full sentence and paragraph; the labelled span
is the clause byte range in the derived text artifact, recorded as
(artifact, start, end, slice_blake3). A sentence with two modals governing
different contents yields two clauses. Headings, captions, TOC rows, table
cells without a finite verb, and defined-term lists are `non-clause` and
excluded from every denominator.

## 2. Label 1 — commitment type (exactly one)

| Label | Definition | Anchors |
|---|---|---|
| `binding` | Present obligation with an external enforcer or stated penalty/consequence | "shall", "must", covenant, charter duty with a remedy |
| `conditional` | Obligation/intention expressly gated on a condition | "subject to stockholder approval", "if the board determines" |
| `intention` | Stated plan without external enforcement | "we intend", "we plan", "we will publish annually" |
| `aspiration` | Desired end-state, no actor-action commitment | "where AI has gone well", "we aim", "we hope" |
| `capability` | Claim about what a system can do (not what anyone will do) | "Claude can design…" |
| `past-act` | Assertion that something already happened/was done | past tense + agent |
| `risk-disclosure` | Forward harm stated as possibility (Item 1A grammar) | "could adversely affect" |
| `mandated` | Legally required forward-looking / safe-harbour language | PSLRA boilerplate, Item 106 mandated structure |
| `non-commitment` | Everything else with a finite verb | description, history, definition |

Boundary rules: reported speech is labelled by the *reported* clause's type
with `reported=1`. A benefit pillar statement is `aspiration` unless it
names an actor, action, and object, in which case it is the applicable
commitment type. "Will" is `intention` only when the subject is the filer
and the verb is volitional; predictive "will" about markets/technology is
`non-commitment` (or `capability` if system-subject). When two labels fit,
annotators record both and flag `boundary=1`; adjudication picks one and
the kept alternate is preserved in the row.

## 3. Label 2 — slots (per clause, span-or-absent)

`actor` (filer / named-third-party / industry / passive-unnamed / system),
`action` span, `object` span, `condition` span, `deadline` (dated /
relative / absent), `metric` (numeric target span or absent),
`beneficiary` span, `enforcer` (named / none). A clause is
**slot-complete** iff actor=filer-or-named, action present, and at least one
of {deadline dated/relative, metric} present.

## 4. Label 3 — act alignment (commitment clauses only)

For each `binding/conditional/intention` clause, annotators search the
paired filing's `past-act` clauses (retrieval candidates may assist; the
judgement is human):

| Label | Meaning |
|---|---|
| `outcome-filed` | A filed past-act whose slots satisfy the commitment's action+object (amount/date/condition compatible) |
| `input-only` | Filed acts exist on the same topic but report inputs/process, not the committed outcome |
| `contradicted` | A filed act/fact slot conflicts (different control fact, amount, date, negation) |
| `no-act-found` | Exhaustive search of the paired document finds no candidate |
| `not-yet-due` | Deadline, if any, is after the paired filing date — recorded, never counted as discharge or failure |

Textual alignment only. `outcome-filed` asserts the *filing says it
happened*, never that it happened (GOV-2 existence column).

## 5. Pre-registered thresholds (provisional, D2)

| Gate | Value | Where used |
|---|---|---|
| Annotation go/no-go | Cohen κ ≥ 0.65 on commitment type; Krippendorff α ≥ 0.65 on modality strength | §7 spike gate (a) |
| Placebo collapse | ≥ 90% of shuffled pairs judged `neutral/no-act` by the alignment instrument | §7 spike gate (b) |
| Peer separation | H1 and H3 effects differ case-vs-peer at permutation p < 0.05 (10,000 draws, seed 20261104) | §7 spike gate (c) |
| H2 outcome floor | Pattern weakened if ≥ 50% of benefit commitments reach `outcome-filed` | bert spec §3 |
| NLI witness band | `entail` ≥ 0.70, `contradict` ≥ 0.70, else `abstain`; headline rates also reported at 0.50 and 0.90 | Stage 4 witness only |
| Retrieval depth | top-k = 8 candidates per commitment | Stage 4 recall only |

## 6. Sampling, splits, and strata

Strata = document × section-kind {pillar/benefit, risk, governance,
capital/mechanism, financial, cyber-1A, cyber-106, other}. Pilot pack:
stratified random clauses, seed 20261104, sampled **before** any model
scores exist for them. Train/dev/test split is by section block, never by
random clause. `mandated` clauses are counted and reported, excluded from
H1/H5 evasion rates, and included in a sensitivity table. Every rate is
reported within-stratum before it is pooled; pooled Report-vs-S-1 raw rates
are not publishable numbers under this framework.

## 7. Roles and tiers

Human annotators A1/A2 label independently; A3 adjudicates. Models
(Stage 1/2/4 instruments) write `proposals/*.tsv` as named witnesses
(circle 3 testimony): witness column = model id + revision + prompt or
config hash. No model label enters gold. No label generated by the case
company's own models is admissible even as a witness for scoring the case.
Disagreements persist as recorded conflicts; confidence never adjudicates.

## 8. Changelog

- v0.1 · 2026-11-04 — initial codebook; D1–D6 recorded as resolved
  2026-11-04; thresholds provisional pending author signature.
