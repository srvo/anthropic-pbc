# Plan: one report, paper and data linked

Status: PLAN, 2026-11-04. Nothing here is built. Today `edition/REPORT.md`
holds the data findings only (C0001–C0008, S001–S008, positional ids in
`build_edition.CLAIMS`). This plan folds the paper's argument into the same
report as its spine, with every corpus finding linked to the paper claim it
bears on. Paper text is read only from a pinned commit
(`git show 1afb042:docs/anthropic-contrapunctus.md`; HEAD is identical).

## 1. Inventory

M = mechanical (parsed from a table or registry at a pinned commit);
H = human prose (Sloane writes or reviews).

| Component (path) | Contributes | Mode |
|---|---|---|
| Paper, Verdict first 1–5 | argument spine; status tags (CONFIRMED/HIGH ...) | M statement + status; H framing |
| Paper, Appendix C (12 rows) | flagship claims with verdicts | M |
| Paper, §7 GOV-1…GOV-10 | recommendations | M |
| Paper, §6 pillar falsifiers (5); §8 falsifiers (1)–(6) | what would change the conclusion | M |
| Paper, §8 standing pass; §9 open questions 1–7 | caveats, conflict disclosure; open questions | M excerpt |
| Paper, Verification status (60 checked, 51 byte-exact) | method evidence | M excerpt |
| `docs/risk-governance-index.md` (8 rows) | disclosed risk → mechanism inferences | M |
| `edition/report.template.md` C0001–C0008 | data findings | M (built) |
| Corpus method docs, "does not answer" sections | limitations | H one line each + link |
| `docs/bert-enrichment-spec.md` §3 H1–H5, §10 log | hypotheses; witness results | M ids; H summary |
| `gold/`, `data://garden/earnings_calls/2026-11-04/gold_samples` | gold status (none coded) | M |
| `attestations/datasets/*.txt`, `docs/contrapunctus-attestations/` | signature status of sources and paper | M |
| `docs/review-2026-11-04.md` | review record | H summary + link |
| `dag.yml`, `dag.lock.tsv`, `corpus/*/MANIFEST.tsv`, `*.meta.yml` | source identity | M |

Not rebuildable, so excluded: the risk-factor corpus (no `dag.yml` step), and
any `sources/` filing copies (uncommitted).

## 2. Outline (Praxis research order)

1. **Bottom line.** Paper Verdict 1 excerpt (charter real, toothless) +
   H synthesis: what the outward data adds and does not.
2. **Decision-relevant facts** (≤10 rows, selected from claims): Verdicts
   1–4, the 5–7% violator revenue, $895.4B commitments, and the strongest data
   rows (C0004 analyst intent, C0007 CVE credits).
3. **What could change the conclusion.** Built from `falsifier-for` edges: each
   paper falsifier, the data that tests it, and the result (e.g. §8 (1)
   CVE-level counts → C0007: not met, not refuted). Then data caveats (no gold
   set, draft codebook, survivorship).
4. **Analysis**, one subsection per verdict: paper claims (excerpts with
   status), then the data findings linked to them, then H connecting prose.
   Charts stay where today's are.
5. **Methods and limitations.** Descartes quote audit; witnesses; one line
   per corpus limit, linking its method doc.
6. **Claims index.** Every claim, paper and data, in one id space.
7. **Sources index.** Paper at pin, filings as the paper cites them, dag steps.
8. **Revision and review record.** Review state counts, signatures, review doc.

## 3. Linking model

**Ids.** Existing ids: paper `GOV-1…10`; spec `H1–H5`; risk-governance rows
1–8; Descartes ids are `blake3:` content ids of claim nodes, and the 234
Descartes rows live outside this repo. Appendix C, verdicts and falsifiers
have no ids. The report keeps one Praxis id space, `C0001…`, held in a committed
`edition/claims.tsv`: `id, key, kind, statement_ref, status, aliases,
upstream, review`. Ids are assigned once, append-only, never reused; today's
C0001–C0008 keep their numbers. `aliases` carries `GOV-8`, `H2`, `RGI-6`,
`v0:Verdict-1`; `upstream` carries the Descartes id once Q21 is settled. Kinds:
observation, inference, recommendation, falsifier, open question (Praxis keeps
kinds intact).

**Claim → source** (`edition/sources.tsv`), three shapes: a dag step URI plus
file and BLAKE3 (from `dag.lock.tsv`); `git:<commit>:<path>#char=<a>,<b>` plus
the slice's BLAKE3 for paper and repo text (RFC 5147 fragment); an external URL
as the paper cites it, with "no captured digest" until a copy is pinned.

**Claim → claim** (`edition/relations.tsv`): `subject, predicate, object,
review`, predicates `supports | contradicts | qualifies | falsifier-for`. Example
rows: C0007 `qualifies` Appendix C ">33,000 flaws"; Verdict 2 is the object of
§8 (1) via `falsifier-for`. Every edge is an inference: it ships with a review
state, and an unreviewed edge renders as such. The build fails on a cycle, a
dangling id, or a data claim with no edge (or lists it as unlinked).

**Prose.** Two kinds only. *Excerpts*: `edition/excerpts.tsv` (`key, commit,
path, start, end, blake3`); the build re-slices from `git show` and fails on a
hash mismatch, generalising today's `QUOTES`. An excerpt carries its own
numerals as the paper's figures with the paper's status, never as computed
values. *Bound templates*: new prose under the existing controls (no unbound
numeral, quotes bound).

**Machine-readable.** From the same registry, the build writes
`edition/claims.csv` in the Praxis register format (`id, claim, value,
status, source_type, source_ref, as_of, last_checked, section_first, notes`,
`report_writer/register.py`), so the Praxis writer's attention appendix works;
and `edition/claims.jsonld` using Praxis's `render/semantics.py` context
(schema, dcterms, prov, dcat) plus `schema:Claim` nodes, CiTO predicates
(`cito:supports`, `cito:disagreesWith`, `cito:qualifies`) and one local term
for `falsifierFor`; `prov:wasDerivedFrom` to dag URIs and `urn:blake3:` ids.
Praxis's emitter has no claim nodes today; the extension is proposed upstream
as a note, not by editing Praxis.

## 4. What stays human

Bottom line synthesis; each Analysis connecting paragraph; every relation edge;
the choice of excerpts and facts rows; the one-line corpus limits. Each prose
block has an id; `edition/review.tsv` records `block, blake3, reviewer, date`,
written only by Sloane (agents never write accepted rows, as with signing). A
block whose current BLAKE3 differs from its reviewed hash renders under a
visible "Unreviewed draft" label, and the revision record counts them. Builds
always run (DRAFT); a `--release` flag refuses any unreviewed block or edge.

## 5. Size

Estimate: about 7,000 words (Bottom line 300, Facts 10 rows, Analysis 2,000,
claims ~55 × 50 words, sources ~25), about 45 KB of Markdown, 5 existing SVGs,
about 20 PDF pages; `claims.jsonld` about 40 KB. Not pulled in: Appendix B
question bank, §7a Praxis alternative, §1a, §2a, §4b and §4c detail, harm-ledger
tables (claims only), method-doc bodies, spec §§1–9, Descartes and Praxis
doctrine docs, raw tables, score shards, Epoch and democracy series (no claim
yet; democracy enters only as the limit "no series isolates Anthropic"). All are
linked by locator.

## 6. Phases

1. **Stable ids.** Move ids from `CLAIMS` order to `edition/claims.tsv`.
   Done when `build_edition.py --check` passes, `REPORT.md` is byte-identical,
   and new negative tests catch id reuse and reorder drift.
2. **Excerpts.** `excerpts.tsv` replaces `QUOTES`; the three quotes migrate.
   Done when output is byte-identical and tests catch a moved or edited slice.
3. **Paper claims.** Parse Appendix C, GOV table and falsifiers at the pin into
   about 50 rows with statuses. Done when every row's excerpt verifies and its
   status equals the paper's.
4. **Relations.** `relations.tsv`, edge rendering, the falsifier section. Done
   when no data claim is unlinked and every edge shows review state.
5. **Template.** Restructure to §2's outline; Sloane writes prose blocks.
   Done when the section check passes and the unreviewed count is shown.
6. **Exports.** `claims.csv`, `claims.jsonld`, both hashed in `STAMP.json`.
   Done when output is deterministic, the JSON-LD parses to the same graph as
   its N-Triples (as Praxis `check_rdf.py` does), and REPORT.md and JSON-LD
   carry the same id set.

## 7. Open decisions for Sloane

1. **Paper pin.** (a) v0 `1afb042`; (b) a later committed revision.
   Recommendation: (a); moving the pin is one commit and every excerpt
   re-verifies.
2. **Claim statements.** (a) verbatim one-sentence excerpts; (b) rewritten
   distillations. Recommendation: (a); new words only in the H blocks.
3. **Id scheme.** (a) C-ids with paper ids as aliases; (b) paper ids as
   primary; (c) Descartes ids as primary. Recommendation: (a).
4. **Praxis Q21.** (a) every binding becomes a Descartes claim; (b) only
   quotes from outside documents do; (c) separate, the stamp links them.
   Recommendation: (b): excerpts map directly onto Descartes rows.
5. **Publisher and disclosure.** v0 reads "From: The Praxis project (Ethical
   Capital)" with an adviser publication note; the report publishes as `praxis`.
   (a) carry the note verbatim; (b) omit it, keep the §8 standing pass;
   (c) wait for the Ethical Capital publisher. Recommendation: (a), after a
   compliance review, since GOV recommendations and investor-directed text
   would now ship under the report.
6. **Relation vocabulary.** (a) CiTO plus one local term; (b) local terms
   only. Recommendation: (a).
7. **Claims and sources.** (a) inline in REPORT.md; (b) companion pages.
   Recommendation: (a) unless the PDF passes 25 pages.
8. **Risk-governance index.** (a) its 8 rows as inference claims; (b) leave
   it out (its content hash is unsealed). Recommendation: (a), status as
   written there, marked unsealed.
