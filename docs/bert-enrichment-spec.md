# BERT enrichment spec

### Corroborating the promise↔action pattern without breaking Descartes

**Status: DESIGN. Binds nothing.** Under [`descartes-spec.md`](descartes-spec.md)
("Files under `docs/` are design notes and records. They bind nothing until a
rule here names them"), nothing below is held, measured, or sealed. No model
has been run. Every performance statement below is methods knowledge from
general NLP practice, not a result on this corpus.

Version: v0.1 · 2026-11-03 · Companion to
[`anthropic-contrapunctus.md`](anthropic-contrapunctus.md) v0 and
[`risk-governance-index.md`](risk-governance-index.md) v1. This file does not
edit the paper, its BLAKE3, its DOI, or any attestation target. Corrections to
this file are new versions, never silent overwrites. Verify this file the
same way as the paper: `b3sum docs/bert-enrichment-spec.md`.

Author's note on provenance: this design was drafted after a full read of the
paper (§0–§9, Appendices A–D), `descartes-spec.md`, `praxis-white-paper.md`,
`praxis-standard.md`, `primitives.md`, `epistemics.md`, `strictness.md`,
`circles.md`, `risk-governance-index.md`, and `contrapunctus-attest.md`, then
attacked by an adversarial review pass against those same files. Two tempting
shortcuts from the first draft were cut as invented: integerised
"milli-probabilities" and pinned CPU inference. Neither appears in any Praxis
document, and neither is proposed below as compliance.

---

## 1. Verdict

Do not start with BERT. Start with the corpus, the codebook, and the controls.

Run today — one company, two self-authored documents of different genre
(a 20-page benefit report against a ~245,000-word S-1 sampled by keyword
windows; absence claims MED by the paper's own tagging) — a BERT layer would
measure how benefit reports and S-1s differ. It would not corroborate that
words and acts diverge. [`epistemics.md`](epistemics.md) already states why:
the verifier proves a quote's *provenance*; that is not *credibility*, which
requires the same content from an independent source. Report↔S-1 alignment
compares Anthropic to Anthropic. High alignment shows internal consistency.
Low alignment shows genre difference. Neither shows an outcome happened.

A BERT layer earns its place only in one role: exhaustive, denominator-known
extraction that replaces keyword sampling and hand-picked pairs with rates
that could come out against the paper. Everything upstream of that role —
unit definition, gold labels, section matching, peer controls, external
outcome evidence — is the work. The model is the last 10% of it.

## 2. The logical chain

1. The paper's thesis is a rate-shaped claim currently evidenced by examples:
   published values diverge from filed acts ("the measurable gap between a
   published value and a filed act," §0). Sixty hand-checked fragments
   (51 byte-exact) prove the method catches errors. They do not establish
   prevalence.
2. Prevalence requires a denominator: every commitment in the Report and
   Constitution, every candidate discharging act in the S-1, extracted the
   same way.
3. A denominator requires a unit and a codebook. The paper defines neither:
   no sentence/clause/claim unit, no promise-vs-aspiration-vs-condition
   boundary, no time window in which a forward promise could be discharged.
   The six moves in §3 (future-benefit discounting through voluntary-restraint
   fallacy) are categories illustrated by examples, not a labelling manual.
4. Rates require controls. Without the identical frozen pipeline run on a
   peer non-PBC filing, a comparator benefit report, and shuffled
   promise↔act pairs, an "Anthropic signature" is indistinguishable from
   "how S-1s hedge and benefit reports aspire" — including hedging that
   securities law mandates.
5. Corroboration requires independence. Text-internal alignment populates
   only the *(quote/source exists)* column of GOV-2. The *(outcome entailed,
   measured)* column needs Anthropic-external artifacts — the paper's own
   falsifier class in §8 (externally attested counts, partner outcome
   evaluations, audited provenance, metered footprints) — or enforcement and
   incident records joined after the fact.
6. Admissibility requires a legal home for model output. Today only one
   exists: the model as a named *witness* proposing byte-exact excerpts for
   checking (§8 of the spec). The label it attaches — commitment, entailed,
   contradicted — is never quote-checked, because a label is not a quote.
   Every other home (derivation, evaluation) is unproven or unbuilt. (§5.)
7. ∴ Build in this order: corpus + codebook + gold pilot → deterministic
   counters → one encoder extractor on the witness route → alignment with
   controls. Stop at any gate that fails. (§7.)

## 3. Hypotheses: the pattern as rates

Each hypothesis maps one paper move to one countable comparison. Thresholds,
effect floors, and α are **author decisions** (§8, D2) — none is stated in the
paper, whose falsifiers are document-level. Any number used must be
pre-registered in the versioned codebook (§6) before test data is seen, or
the headline rate is threshold-shoppable.

| # | Paper move | Rate that must differ | Fails if |
|---|---|---|---|
| H1 | "Aspirational conditions, not metrics" (§2 table) | Commitment-strength + dated/metric slot completeness: Report pillar commitments vs section-matched S-1 binding covenants | Equal or reversed under section-matched permutation test |
| H2 | Input-for-outcome substitution (§3.2) | Share of extracted benefit commitments with a slot-verified filed *outcome* (not input) | Share ≥ pre-registered floor |
| H3 | Paradigm rhetoric, parameter acts (§1a) | Specificity density (numerals, dates, entities, citations per 100 tokens): benefit sentences vs risk/financial sentences | Benefit ≥ risk/financial |
| H4 | Attribution asymmetry (§3.5) | `actor = Anthropic` rate for benefits vs for harms (industry / perception / passive) | Rates equal |
| H5 | Future-benefit discounting (§3.1) | Undated-future vs dated-future commitments | Dated ≥ undated |

Scope limit, stated once and binding on every result slide thereafter:
H1–H5 measure **register divergence inside filed text**. They corroborate
the paper's textual pattern. They do not corroborate world outcomes, and no
wording in any output may upgrade them to that claim. Outcome corroboration
is §6.4 or it does not happen.

What already exists is **not gold** for any of these. The 60 fragments are a
quote audit, not span annotations. The 234 Descartes claim rows prove quote
occurrence only. Appendix C verdicts are the paper's conclusions; training
or validating on them grades the paper with its own answer key — the
self-grading move §3.4 names. Gold must be created (§6.1).

## 4. Pipeline, in build order

Deterministic before neural, at every stage. P16: "No heavier machinery than
the problem." Each stage lists its role against the paper:
**corroborate** (independent check on the same claim), **substantiate**
(turn an adjective into a distribution), **extend** (supply a denominator
or coverage the paper lacks).

### Stage 0 — Corpus and gold pilot. No model. *Extends.*

Hash-pinned ingestion of: PBC Report, S-1/A, Constitution, Trust Agreement
exhibit when available; one peer non-PBC S-1; one comparator benefit report.
None of the primary texts is in this repo today (external URLs only;
ingestion is already the paper's tracked follow-on, Appendix D). Sentence
segmentation and section inventory for every document. Double annotation of
a stratified (document × section) sample under codebook v0.1, with per-label
agreement reported. This stage alone retires the keyword-window caveat.

### Stage 1 — Commitment extraction. *Extends.*

Fine-tuned encoder (DeBERTa-v3 / ModernBERT class): multi-label sentence or
clause classification {binding, conditional, intention, aspiration,
capability, past-act, non-commitment} plus span extraction {trigger,
content, condition, deadline, beneficiary, metric}. Output is byte ranges —
(artifact, start, end, slice_blake3) — in the claim-evidence shape the spec
already defines. Plain `bert-base-uncased` is the wrong tool: uncased
(destroys defined-term casing), stale legal vocabulary, no intermediate
entailment training. A generative LLM is admissible only as witness
testimony, never as the extractor of record, and never the subject's own
model labelling the subject.

### Stage 2 — Deterministic counters. Build before any neural head. *Substantiates H1, H3, H4, H5.*

- **Modality:** closed-class lexicon + dependency parse (shall/will/must >
  intends/plans > aims/hopes > may/could; conditionality flag). Ordinal
  strength per commitment span, integer tables.
- **Specificity:** numerals, dates, money, percentages, share counts,
  statute citations, named entities per 100 tokens. Regex and grammar, not
  a network.
- **Temporal / actor:** tense, aspect, and temporal expressions; dependency
  extraction of actor-of-benefit vs actor-of-harm into integer contingency
  tables.
- **Boilerplate:** shingle + MinHash near-duplicate rates across documents,
  amendments, and peer filings. Solved deterministically; a neural
  duplicate detector would only add variance.
- **Slot extraction:** {entity, attribute, value, amount, date, condition}
  by deterministic patterns plus the Stage-1 span head. Slots are compared
  by exact and integer arithmetic ("separate entity" vs "wholly-owned
  subsidiary"; 5% vs 846,840,960 shares) — the comparisons neural
  entailment is known to botch.

A fine-tuned neural head may later act as a *second witness* on modality
ambiguity (negation scope, commissive vs predictive "will"). Rule and
network are both reported. Disagreement is a recorded conflict, never an
average, and never resolved by confidence ([`strictness.md`](strictness.md):
a judgment between rules constraining different things "needs a person and
a record").

### Stage 3 — Topic and leverage distribution. *Extends §1a.*

Fixed human taxonomy (five pillars + harm/risk + governance + financials)
applied by a fine-tuned multi-label paragraph classifier. Report share-per-
pillar against S-1 share-per-pillar; divergence by Jensen–Shannon with a
document-level permutation test. BERTopic is excluded from any signed tier:
UMAP/HDBSCAN topics are stochastic and cannot survive a re-run-identical
requirement. Exploratory clustering may propose taxonomy revisions for a
human to adopt into the versioned taxonomy file. Nothing more.

### Stage 4 — Promise↔act alignment. *Corroborates or refutes H2, at text level only.*

Bi-encoder embeddings retrieve candidate act sentences per commitment —
recall only. Cosine similarity is symmetric and negation-blind ("will
publish" ≈ "will not publish") and is never evidence of alignment. A
cross-encoder NLI model then *proposes* entail / neutral / contradict per
candidate pair; Stage-2 slot comparison *disposes* on every load-bearing
pair. Where NLI says "entail" and a numeric or control slot differs, the
pair is recorded as a contradiction claim, not smoothed. NLI entailment is
textual entailment between two sentences. It is not outcome entailment,
and the output schema must say so in the column name, not a footnote.

## 5. Admissibility: where model output may legally sit

Held rules only. Designed machinery is labelled designed and cited as
nothing stronger.

**Route A — witness. Admissible today, and the only route this spec uses.**
The model writes proposals; the witness column names model and prompt hash;
leaves quote byte-exactly and occur exactly once; a zero-problem file moves
to claims. The verifier "proves that a quote exists. It does not prove that
the statement follows from it. An LLM-witnessed claim is testimony until a
person concurs, and nothing records that concurrence yet"
([`descartes-spec.md`](descartes-spec.md), closing note to §8). So Route A
covers excerpt existence, never the attached label. The label is testimony:
circle 3 ([`circles.md`](circles.md)). A second model is a second circle-3
witness, not a circle-2 instrument — circles 1–2 are PDF conservation laws
(poppler, tesseract) and have no commitment-labelling analogue. Two further
ceilings: nodes admit no floats (contract I3, held), so raw probabilities
have no node representation; and the graph admits exactly five node kinds
(artifact, claim, derivation, attestation, snapshot) — there is no
evaluation kind to put a rating in.

**Route B — derivation. Unproven; a spike question, not an assumption.**
A derivation tool is re-run by the loop and must reproduce byte-for-byte,
allowlisted, offline, deny-default sandboxed; a check that cannot run
records skipped, and a plain run still fails on it. Nothing yet shows a
transformer checkpoint, tokenizer, and ML runtime can meet that bar across
machines inside the three-vendored-dependency, >1 MiB-manifest-boundary,
run-on-every-chip (P5, open: darwin/arm64 only) posture — or that P16
permits machinery that heavy for this problem. The v0.1 spike (§7) tests
exactly this, twice from empty on two architectures, and publishes the
result either way. Until it passes, no model output enters as a derivation.

**Route C — evaluation under a pinned framework. Designed, not held.**
[`epistemics.md`](epistemics.md) and [`primitives.md`](primitives.md) design
a separate evaluation node pinning a versioned framework file, scores
computed and never stored. [`praxis-standard.md`](praxis-standard.md) is
explicit that no §3 clause is held. Route C may be the right long-term home
for ratings. Citing it as current law would be false. Promoting it is an
owner decision (§8, D4) that amends the spec with a named check, in the
same commit.

Signing follows the same split. Attestations bind a human stance to a
`version_blake3` ([`contrapunctus-attest.md`](contrapunctus-attest.md)). A
model never signs interest or custody — those are human (circle 4) roles,
and the roster and concurrence machinery that would record them is unbuilt.
Model and human disagreements therefore persist as recorded conflicts.
That is a feature of the method, and the enrichment inherits it.

## 6. Validation

### 6.1 Gold

Stratified random sample (document × section), never model-selected. Two
independent annotators under the versioned codebook; per-label κ/α
published; third-human adjudication; unadjudicable items kept as recorded
conflicts, never force-labelled. Train/dev/test split **by section**, never
by random sentence — adjacent sentences share boilerplate and defined
terms, so sentence-level splits leak. The codebook, taxonomy, modality
lexicon, and every threshold live in versioned files ingested as artifacts,
so each result pins the exact definitions it ran under
([`epistemics.md`](epistemics.md) on frameworks).

### 6.2 Calibration and error analysis

Temperature or isotonic calibration on dev only. Report ECE, Brier score,
and full PR curves on held-out test — never a single F1 at a tuned
threshold. Every headline rate reported across a pre-registered threshold
range. Error analysis stratified by section type, sentence length, and
numeric density; every false "entail" on a load-bearing claim gets a named
error record. Below the pre-registered confidence band the system abstains
and records the abstention. (Note: an abstained derivation is not a pass —
the spec's skipped rule makes a plain run fail. Route A proposals may
abstain freely; Route B may not exist until it can stop abstaining
deterministically.)

### 6.3 Controls. Mandatory, not polish.

- **Shuffled placebo:** permuted promise↔act pairs must collapse to neutral
  at a pre-registered rate.
- **Peer control:** identical frozen pipeline on a non-PBC S-1.
- **Comparator control:** identical pipeline on another benefit report +
  filing pair.
- **Mandated hedging:** forward-looking safe-harbour language labelled
  `mandated` and excluded from evasion counts. A modality counter without
  this stratum rediscovers securities law and calls it deceit.
- **Section and length matching:** every cross-document rate computed
  within matched sections, length-stratified. Raw Report-vs-S-1 hedging
  rates are uninterpretable and must not be published.

### 6.4 Independence: the outcome join

Text rates need an external spine or they stay genre measurement. Two joins
provide it. First, the paper's own §8 falsifier documents, checked for a
sample of extracted promises. Second, the enforcement/incident join
designed in Appendix E of the working paper (data corpus: the Index run on
the S&P 500 — in the working tree at the time of writing, uncommitted):
disclosed risk (Item 1A) joined to governing mechanism (Item 106, Rule
10D-1 exhibits, DEF 14A) and to realized incidents (8-K Items 1.05/8.01,
litigation releases, AAERs). Appendix E's stated falsifier is the right
one and this spec adopts it verbatim in spirit: if low mechanism coverage
does not predict later enforcement, incidents, or restatements, the index
is decoration, and we will say so. Its cyber-first pilot — risk, mechanism,
and incident all inside SEC filings — is also the right first control
corpus for Stage 4, because it supplies realized outcomes at filing scale.
EDGAR full text and EDGAR-CORPUS give the negative-control universe the
single-company design lacks. Rater design follows Appendix E: every
model-assigned rating enters at circle 3 with a byte-exact quote, three
independent labellers, disagreement published (GOV-5 applied to ourselves).

## 7. Phased plan

### v0.1 spike — go/no-go. Adds this repo's first enrichment artifacts; paper v0 untouched.

At committed HEAD this repo holds documents only (the working tree also
holds an uncommitted `scripts/seal.py`, figures pipeline, and seal-check
CI from parallel work; the spike must compose with `seal.py`, not fork it).
Spike artifacts:

```
sources/MANIFEST.tsv            Report, S-1/A, Constitution, peer S-1,
                                comparator report — BLAKE3 per file
sources/                        fetched bytes, untouched (fetch is a
                                separate recorded step; the loop is offline)
frameworks/promise-act-v0.1.md  codebook: unit, labels, modality lexicon,
                                taxonomy, thresholds, control definitions
gold/pilot-v0.1.tsv             double-annotated stratified pilot +
gold/pilot-v0.1.agreement.md    per-label κ/α, adjudication log, conflicts kept
scripts/enrich_stage2.py        deterministic counters (uv script, pinned
                                inline deps, no clock/network/randomness)
proposals/enrich-extraction-v0.1.tsv   one encoder extractor, witness route only
docs/bert-enrichment-spec.md    this file, versioned; results appended in
                                the §10 log, never edited into §§1–9
```

Plus one derivation-determinism spike report (§5, Route B): the extractor
run twice from empty on two architectures, byte comparison published.

**Go criteria — all three, or stop:** (a) annotators agree on the "promise"
unit at the pre-registered κ floor; (b) the shuffled placebo collapses to
neutral; (c) the peer filer's H1–H5 signature differs from Anthropic's. If
(a) fails, the construct is undefined and no model fixes it. If (b) or (c)
fails, the pipeline measures genre and §3 must be rewritten before any
further spend.

### v1 — only if the spike passes and the author promotes the needed law

Exhaustive extraction and alignment over the full corpus; H1–H5 with
confidence intervals; calibrated second-witness heads; external-outcome
sample check (§6.4); Risk–Governance Index v2 with the full S-1
risk-factor enumeration its v1 lacks — new **rows** in the existing
Status/verdict vocabulary, no new score column without a format bump; a
standalone companion results document with its own version and hash,
linked from the README document list, disputed under an attestation
protocol amended to name it as a target; new Zenodo version DOI. An
evaluation node kind or human-concurrence record ships only as a spec
amendment (§5), never as an implementation fait accompli.

## 8. Author decisions

- **D1 — Unit and codebook.** Sentence, clause, or claim? Promise vs
  aspiration vs condition vs risk-disclosure boundary; act time window;
  denominator. Nothing proceeds past the pilot without this.
- **D2 — Numeric falsifiers.** H2 outcome-share floor, threshold range, α,
  effect floors. Pre-register in `frameworks/promise-act-v0.1.md` before
  test data is seen.
- **D3 — Control corpus.** Which peer S-1(s), which comparator PBC, section
  matching, safe-harbour strata, placebo failure rate. EDGAR universe vs
  hand-picked peers is part of this decision.
- **D4 — Admissibility route.** Witness-only (held today) vs amending
  `descartes-spec.md` for derivation-route models and/or a sixth,
  evaluation, node kind — breaking the exact-five-kinds rule deliberately,
  with a named check. Human-concurrence and roster design ride with this.
- **D5 — Attach surface.** Standalone versioned companion (recommended;
  preserves paper v0, its hash, and future attestations) vs Index v2 rows
  vs paper appendix (new paper hash; attestations do not carry forward;
  re-signing required). The attestation protocol currently names one
  target; a multi-target registry is a protocol amendment.
- **D6 — S&P 500 sequencing.** Appendix E's corpus subsumes D3 at universe
  scale and adds the 0–5 mechanism test plus `Undisclosed` status. Decide
  whether the Anthropic spike is the pilot for that corpus (recommended:
  cyber-first, per Appendix E) or a separate single-company study. Running
  both with different codebooks would fork the construct.

## 9. What not to build

- A neural quote matcher. Byte-exact checking already solves it; fuzziness
  would weaken the one held guarantee.
- Embeddings or cosine scores as evidence, in any column, at any tier.
- BERTopic/UMAP clusters as signed output.
- Model-issued CONFIRMED/REFUTED verdicts. Verdicts are human attestations.
- Training labels generated by any LLM, above all the subject's.
- A single aggregate fidelity/alignment score
  ([`epistemics.md`](epistemics.md): loss per component per circle, never
  one number).
- An appendix bolted onto paper v0, or a silent `index.html` embed edit.
  Either moves the hash every attestation will name.
- Anything trained across tenant or subject boundaries. Designed
  prohibitions aside, it is also bad method here: the control must stay
  uncontaminated by the case.

### Silence the method must state

A filing-text pipeline hears only actors who produce citable text
([`strictness.md`](strictness.md), R1 testimony). Affected people —
authors, data-center neighbours, labelling workers, users — appear in this
corpus in Anthropic's voice or not at all; the paper's §8 says the same of
itself. The enrichment scores that silence as *unmeasured*, never as
absence of harm, and every results document carries this paragraph or its
successor.

---

*Results, when they exist, are appended below as dated records. §§1–9 above
are the pre-registration and do not change to fit them.*

## 10. Results log

*v0.1 (2026-11-03): empty. No corpus ingested, no annotation run, no model run.*

### 2026-11-04 · Earnings-call AI windows, codebook v0.1, two NLI witnesses

**Status: witness proposals only.** No human gold set exists for this
codebook, so precision and recall are unknown and go criterion (a) in §7 is
not met. No count below is citable as a rate of anything except witness
agreement. Method: [`earnings-call-ai-corpus.md`](earnings-call-ai-corpus.md).

- **Input.** 38,600 windows from 33,622 unique, non-stub S&P 500 calls
  (fiscal 2005–2027), scored against 16 hypotheses: 617,600 pairs per witness.
- **Witnesses.** DeBERTa-v3-large and ModernBERT-large zero-shot NLI at pinned
  revisions, bfloat16 on Modal L40S. Outputs:
  `proposals/earnings-calls/codebook-v0.1/deberta.parquet` (BLAKE3 `e3f0601b…`)
  and `modernbert.parquet` (`740db8fd…`). The full pins are in `run-*.json`.
- **Agreement** (`report/agreement.tsv`). Cohen's κ is 0.70 for `about_ai`,
  0.61 for `ai_risk`, 0.53 for `ai_opportunity`, and 0.41 for `governance`.
  Across the 12 risk types κ ranges from 0.26 (`disruption`) to 0.69
  (`energy`). The witnesses differ most on `capex` (231 vs 639 positives),
  `disruption` (357 vs 87) and `safety_ethics` (429 vs 875). Those are the
  first hypotheses to put in front of a human coder.
- **Proposed positives** (both witnesses ≥ 0.5). 6,427 calls have at least
  one window about AI, 251 have a proposed `ai_risk` window, and 68 have a
  proposed `governance` window. 125 of the 251 `ai_risk` calls fall in fiscal 2026.
  Analyst-heuristic windows are proposed as risk at 3.1% of their AI windows,
  against 1.2% for issuer-heuristic windows (`report/by-role.tsv`).
- **Next gate.** Draw a stratified hand-coded sample, oversampling the
  disagreement cells above, and report precision and recall per hypothesis
  before any rate leaves `proposals/`.



### 2026-11-04 · Analyst questions about AI, codebook-questions v0.1

**Status: witness proposals only.** There is no gold set yet; the sample is
in `gold/earnings-calls/`. Method:
[`earnings-call-ai-corpus.md`](earnings-call-ai-corpus.md) §10.

- **Input.** 4,288 AI questions asked by outside questioners on S&P 500 calls,
  scored against 10 intent hypotheses by the same two witnesses on Modal L40S.
- **Agreement** (`codebook-questions-v0.1/report/agreement.tsv`). κ runs from
  0.32 (`q_harm`, only 4 joint positives) to 0.74 (`q_security`), with
  `q_revenue` at 0.62 and `q_controls` at 0.48.
- **12 months to 2026-11-04.** There were 1,645 AI questions from 654
  questioners on 293 firms (`report/ttm.tsv`).
  - **Selling or spending on AI:** 21.2% revenue, demand or pricing; 8.7% AI
    spending and its return; 4.7% cost savings.
  - **Governing its risks:** 3.0% security or privacy; 2.9% risks or
    downsides; 0.8% (13 questions) how the company controls or governs AI
    risk; 0.3% regulation or liability; 0.2% harm to customers or society.
- **Word cross-check, calendar 2026.** 50.4% of AI questions use a commercial
  word and 2.2% use an oversight word. The direction matches the witnesses.
- **Read of the verbatim oversight questions.** Most frame risk as exposure of
  the firm's own earnings, such as an insurer's AI liability book or deposits
  drained by AI agents. Few ask about harm to anyone else. This is a reading,
  not a count, until the gold set is coded.

### 2026-11-04 · Hacker News: Anthropic and AI-security comments, codebook v0.1

**Status: witness proposals only; no gold set.** Method:
[`hacker-news-corpus.md`](hacker-news-corpus.md). The repository holds ids,
offsets and hashes, never comment text.

- **Input.** `open-index/hacker-news` @ `c54ced59`, 2021-01 to 2026-08:
  118,321 windows on 111,662 comments. The anthropic set has 105,559
  windows and the ai_security set 12,762. Both witnesses ran on Modal L40S
  against the unchanged `codebook-v0.1.tsv`.
- **Agreement** (`proposals/hacker-news/report/agreement.tsv`). κ on
  `ai_risk` is 0.54 in both sets, against 0.61 on calls.
  `safety_ethics` drops to 0.52 (anthropic) and 0.24 (ai_security), and
  `governance` to about 0.3.
- **Precision read.** On HN, `safety_ethics` and `regulation` take in
  general grievances: outages, terms of service, spending. A spot check
  of 6 windows each found roughly half off-topic for `regulation`. The HN
  type shares are therefore not comparable to calls in level, only in
  rough order.
- **Volume** (`report/by-month.tsv`). Anthropic comments rose from about
  1,000 a month in early 2025 to 8,500–9,800 a month from February to July
  2026. The share proposed as `ai_risk` rose from about 3.6% to 7–12%.
- **Twelve months to 2026-08, share of AI-risk units naming each type**
  (`report/risk-ranking-ttm.tsv`).

  | Type | Calls | HN anthropic | HN ai_security |
  |---|---|---|---|
  | Cybersecurity | 36% | 23% | 85% |
  | Safety, ethics, misuse | 12% | 40% | 24% |
  | Regulation | 2% | 12% | 4% |
  | Overspending / capex | 8% | 10% | 1% |

  Accuracy and hallucination is 0 on calls and 3% on HN. IP is 1% on
  calls and 6% on HN.

### 2026-11-04 · Codebook v0.2 DRAFT across five sources; batch-dependence of bf16 scores

**Status: witness proposals on a draft codebook; no gold set; wording awaits
review (OPENQUESTIONS Q2).**

- **Codebook.** `corpus/codebooks/codebook-v0.2-draft.tsv` keeps the 16 v0.1
  hypotheses word for word and adds 14. Each new one cites the Wikipedia
  heading and revision it came from.
- **Sources scored.** Earnings-call windows, analyst questions, both HN sets,
  and the Wikipedia windows. Both witnesses ran on Modal L40S in bf16.
- **Reproducibility finding.** Re-scoring the unchanged v0.1 hypotheses
  inside the larger codebook did *not* reproduce the v0.1 scores, though the
  model, GPU type, text and hypothesis were all the same.

  | Run | Max \|Δp\| | Calls flipped at 0.5 |
  |---|---|---|
  | Calls, DeBERTa | 0.13 | 244 of 617,600 (0.04%) |
  | Calls, ModernBERT | 0.05 | 1 |
  | HN, DeBERTa | 0.19 | 936 of 1,688,944 (0.06%) |
  | HN, ModernBERT | 0.26 | 292 |

  The likely cause is bf16 arithmetic varying with batch composition: a
  30-hypothesis codebook groups pairs differently than a 16-hypothesis one.
  So bf16 scores are reproducible only for the same codebook, batch and
  hardware. They are not invariant to batch composition. That is a narrower
  claim than the spec's §5 Route B, which already declines to claim
  reproducibility across hardware. Rates built on these scores move by about
  0.05% of decisions. A float32 rerun would show whether precision is the
  whole cause.
- **Dialogue space**
  (`proposals/cross-source/codebook-v0.2-draft/report/dialogue-space.tsv`).
  This is the share of each source's AI-risk units naming each type. The
  AI-risk units number 179 for executives, 64 for analysts, 6,281 for HN
  Anthropic, 3,096 for HN security and 833 for Wikipedia.
  - Executives and analysts: cyber dominates (40% and 20%), then capex and
    disruption. Every new v0.2 dimension is at or near 0, except
    loss_of_control at 5%.
  - Wikipedia spreads widely: safety/ethics 61%, regulation and
    loss_of_control 17%, bias 10%, misinformation 7%, weapons 5%, existential
    4%.
  - HN Anthropic sits between: transparency 20%, loss_of_control 12%,
    regulation 12%, capex 10%.
  - The executive and analyst bases are small; their single-digit cells rest
    on a handful of passages.
- **Wording failure: `bio_chem`.** It is near zero everywhere, including
  Wikipedia's own "Challenges > Biosecurity" section, where most passages
  score about 0.001. Its wording ("helping to create biological or chemical
  weapons or dangerous pathogens") is narrower than the discourse
  ("repurposed or misused in the biological sciences"). It must be reworded
  before any bio claim.

### 2026-11-04 · What the metadata backfill found

Writing column-level metadata for every step (`dag.py meta`: 33 of 33
complete, 471 fields declared unknown) meant reading the code that writes each
column. That reading found these problems:

- **Fixed: HN dates depended on the build host.** `hn_extract.py` formatted
  the source's zoned timestamps in the host's zone (America/Denver).
  `hn_report.py`'s monthly counts disagreed with `months.tsv` in 45 of 68
  months. It is now pinned to UTC, and a rebuild under another zone is
  byte-identical. Scored text was unchanged, so the witness scores stand
  (commit 29c344d).
- **Two definitions of "AI as a risk".** `ec_risk_series.py` (the AI-risk
  time series, the 12-month ranking and the quotes) uses the `ai_risk` flag
  alone. `ec_report.py` (by-year, by-firm, risk types by year) requires
  `about_ai` and `ai_risk` together. Results from the two scripts are not
  interchangeable; each table's metadata says which rule it uses.
- **One column name, two definitions.** `calls_mentioning_ai` in
  `report/by-year.tsv` counts calls with any regex window. In
  `report/by-firm.tsv` it requires both witnesses to agree on `about_ai`.
- **Window doc corrected.** Clipped windows can still exceed 1,500
  characters (856 do), and windows that only touch are merged as well as
  overlapping ones. `earnings-call-ai-corpus.md` §2 now says so.
- **"Verbatim" outputs normalise whitespace.** `risk-quotes-ttm.tsv` and
  `oversight-questions.tsv` replace newlines and tabs with spaces. No unit in
  this build contains either, so today's files are verbatim; a future build
  might not be.
- **Some tables have no primary key.** Three Epoch tables have no unique key:
  data-center chillers, GPU clusters, and benchmark model metadata, which
  holds blank and duplicate rows against Epoch's own "one row per model
  version". Each is declared, not invented.
- **Democracy metadata: seven doc-versus-data fixes.** The Rooney series
  are stated attitudes, not conditions (the script docstring and README
  said conditions). The user agent no longer calls `corpus/democracy/` CC0.
  R01 has one page and two reports have an image-free page. Of 30
  questionnaire items, one is from May 2026 and two have no report percent.
  R09's AI disclosure reads "identification/ summarization". `build` does
  not check the hand-entered wave, group, item or `response` columns, and
  `response` is not a word of the quote in 56 of 129 rows. All outputs
  rebuilt byte-identical.
