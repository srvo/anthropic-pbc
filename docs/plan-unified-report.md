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

## 2. Outline

**Decided (Sloane, 2026-11-04):** the open question organises the report, not
the Praxis research template. Sections run in the order they answer *is
Anthropic a public benefit corporation?*

**The paper is the linear version of a platform.** On the web, a reader
branches: what we think about governance, how the method works, a single
corpus. On paper there is one line, so it makes the strongest single case and
marks each branch with a short callout at the top of its section ("On the
web: …") linking to the page that would carry it. The callouts are pointers,
not summaries; the case reads complete without them.

### Draft order (Claude's second pass, 2026-11-04, for Sloane to edit)

Two rules from Sloane, 2026-11-04:

- **The reader has no context.** Every term is defined at first use, in plain
  words: Anthropic (the company that makes the Claude AI models), public
  benefit corporation, Delaware, the S-1 (the filing to sell shares to the
  public), the Long-Term Benefit Trust, Claude's Constitution, CVE, the share
  classes. No acronym appears before its words do. Nothing assumes the reader
  has seen the paper, the repository or Praxis.
- **Anthropic's best case comes first, in its strongest form.** We state
  Anthropic's argument better than a hostile reader would, say what in it
  holds, and only then turn it. A rebuttal of a weak version proves nothing.

Each step follows from the one before (`therefore`) or turns it (`but`).
Paper sections in brackets are what each step draws on.

0. **The argument, at the top.** The whole chain in one paragraph, below.
   The answer comes first; the report then earns it.
1. **Why we are asking.** (Sloane, 2026-11-04; introduced on the web by a
   short video of Sloane's.)
   - **Who we are.** Ethical Capital identifies companies that create
     unambiguous positive impact and aligns capital with them. A public
     benefit corporation is the legal form of that promise, so the category
     is ours to care about.
   - **What the form should look like: Wood Cache.** Its front page tells
     you in a minute what it does. It buries dead trees that would otherwise
     burn and verifies the stored carbon end to end, and Colorado regulates
     its burial sites as landfills. It is low-key: it does not advertise how
     hard its verification was. Its CEO's view of its risk, in conversation
     with Sloane: the only thing that can go wrong is that the good things do
     not happen. The scrutiny on it is immense, like regulating a lemonade
     stand like crazy. [Opening, Wood Cache] *Needs Sloane:* whether to
     quote the CEO, and a source for any "first to complete" claim about its
     audit (not in the paper; Descartes will need one).
   - **The missed risk.** Scrutiny runs backwards: the small, observable
     benefit whose worst case is "nothing good happens" is checked hard; the
     company whose worst case is the serious risks it discloses is checked by
     its own report. That gap is the risk the market misses, and Anthropic's
     listing will make the category much larger.
   - **Governance, slimmest version.** Governance is effective control over
     your surroundings: whether the people affected by a system can steer
     it, and whether it survives the loss of any one person ("Governance
     exists so that systems can survive individuals"). One paragraph only;
     the full premise is a separate Praxis paper.
   - *Therefore* the promise is worth checking. Callout: what we think about
     governance (the premise paper).
2. **What Anthropic says it is.** The charter's purpose and five pillars, the
   Long-Term Benefit Trust, the Public Benefit Fund, the 2026 Public Benefit
   Report, each explained for a newcomer. [§1 cantus firmus, §2, §2a]
3. **Anthropic's best case.** In its own strongest terms: the purpose is in
   the charter, and directors must balance it; a Delaware court has held
   that a public benefit corporation's directors need not maximise
   shareholder value (*Drakes Landing*); an independent trust elects four of
   seven directors, which is more than a plain public benefit corporation
   has; it discloses more than its peers (system cards, threat reports, the
   Economic Index, incident disclosures, its own models' failures in
   testing); it has set aside equity for a Public Benefit Fund; it published
   its model's Constitution openly; and outcomes take time, so a first report
   describes inputs. What holds: the pillar conditions are well chosen, the
   disclosures are ahead of peers, the trust exists. [§1a, §2, §3 "What
   survives the buzz saw", §6 cantus firmus of each pillar, closing]
4. **What the law and the share structure make of it.** *But* §365(b) gives
   directors no duty to any person on account of the purpose, and §367 lets
   only 2% or $2M holders sue. The trust that elects the board can be amended
   away by the share classes it checks, and seven founders hold 50.1% of the
   vote. The promise is legally real and practically unenforceable by anyone
   it names. [Verdict 1, §2, §2a]
   - **"Only we can save us."** Anthropic's case rests on being the safety-
     focused lab at the frontier. If it is true that only a few people can
     steer this technology safely, the governance has to be far stronger,
     not weaker, because it must survive those people. Here it depends on
     them. (Sloane's argument; *needs* Anthropic's own words for the "only
     we" stance, quoted and verified, or it stays marked as opinion.)
   *Therefore* the promise rests on Anthropic's word.
5. **How we check its word.** Against the deepest word Anthropic has given:
   Claude's Constitution, which Anthropic wrote to set its model's values and
   which names Anthropic as a possible violator. This is the paper's novel
   move. Every quote is verified byte-exact (Descartes), and we hold
   ourselves to the same rubric. [§0, §1, Verification status] Callout: the
   method; Praxis and Descartes.
6. **What the record shows.** *But* by that standard the record diverges
   from the word, and "outcomes take time" does not cover it: the Report
   grades its own homework, and its own trust says so; documented harm is
   priced while documented benefit is mostly anecdote; what is documented at
   scale is exposure, not victims; Anthropic acts at leverage points 12 and 6
   and declines 5, 4 and 3; the people most affected have no standing. Our
   outside data (C0001–C0008) attaches here, each finding to the step it
   bears on. [Verdicts 2–4, §1a, §3, §4, §4b, §5, §6] Callouts: each corpus.
7. **The answer.** *Therefore* Anthropic is a public benefit corporation in
   law and not in the sense the category promises: nobody it names can make
   it act like one. The best case fails not on its aims but on one inference,
   *inputs + intentions + revocable trustees → discharged public duty*. The
   remedy is governance that someone Anthropic does not appoint, pay or
   outvote can invoke: ten mechanisms, and what Praxis builds instead.
   [Verdict 5, §3, §7, §7a, Appendix A]
8. **What would change our mind.** The falsifiers and the open questions,
   led by the one that governs them: what lever can an affected community
   pull? [§8, §9]
9. **Back matter.** Methods and limitations, claims index, sources index,
   revision and review record (the Praxis research sections that do not
   answer the question).

In the causal chain (§2a), each claim of the best case is a node, and the
turn against it is a `but` link with its evidence attached, so a reader can
see exactly which of Anthropic's points we accept and which we contest.

### Draft opening argument (step 0)

> Anthropic, the company that makes the Claude AI models, has filed to sell
> its shares to the public, and it does so as a public benefit corporation.
> That label is a promise: the company is built, at its core, to do what it
> says. Anthropic's best case that it keeps the promise is strong. Its
> purpose is written into its charter. A Delaware court has held that a
> public benefit corporation's directors need not maximise shareholder
> value. An independent trust elects four of its seven directors. And it
> discloses more about its models' risks than its peers do, including its
> own failures. But the law gives directors no duty to any person on account
> of that purpose, and lets only holders of 2% (or, once listed, the lesser
> of 2% and $2 million) sue to enforce it. The public the charter names
> cannot. The trust can be amended away by the shareholders it is meant to
> check, and seven founders hold 50.1% of the vote. If only a few people can
> steer this technology safely, the governance must survive them; this one
> depends on them. So the promise rests on
> Anthropic's word, and we take Anthropic at the deepest word it has given:
> the Constitution it wrote to set Claude's values. That document counts
> selective emphasis as deception and names Anthropic itself as a possible
> violator. Anthropic's Public Benefit Report does what it forbids: it
> reports inputs as outcomes and grades itself, and its own trust says so.
> On a like-for-like standard of proof, its harms are documented and priced;
> its benefits are mostly anecdote. Therefore Anthropic is a public benefit
> corporation in law, and not in the sense the category promises: no one it
> names can make it act like one. The remedy is not a better report. It is
> governance that someone Anthropic does not appoint, pay or outvote can
> invoke.

**Separate paper (Praxis):** the premise that governance is effective control
over your surroundings. This report carries one paragraph of it and links out.

The template-order list below is the earlier draft, kept until this order is
approved.

1. **Bottom line.** Paper Verdict 1 excerpt (charter real, toothless) +
   H synthesis: what the outward data adds and does not.
2. **Decision-relevant facts** (≤10 rows, selected from claims): Verdicts
   1–4, the 5–7% violator revenue, $895.4B commitments, and the strongest data
   rows (C0004 analyst intent, C0007 CVE credits).
3. **What could change the conclusion.** Built from `falsifier-for` edges: each
   paper falsifier, the data that tests it, and the result (e.g. §8 (1)
   CVE-level counts → C0007: not met, not refuted). Then data caveats (no gold
   set, draft codebook, survivorship).
4. **Analysis**, in chain order (§2a): from the root, each link in turn,
   with the paper's claim (excerpt with status), the mechanism ("because"),
   and the evidence attached to that link. Charts sit with the link they
   support.
5. **Methods and limitations.** Descartes quote audit; witnesses; one line
   per corpus limit, linking its method doc.
6. **Claims index.** Every claim, paper and data, in one id space.
7. **Sources index.** Paper at pin, filings as the paper cites them, dag steps.
8. **Revision and review record.** Review state counts, signatures, review doc.

## 2a. The argument is a causal chain

The report's argument is written the way South Park's writers break a story:
never "this happened, and then this happened", always "this happened, *therefore*
this happened, *but* then this happened". It is the buzz-saw logical chain made
structural.

- **Root.** The chain starts from an open question, not a fact: **is
  Anthropic a public benefit corporation?** (decided by Sloane, 2026-11-04).
  It keeps the kind *open question* until the chain answers it. Every link
  after it is a step toward the answer, and the Bottom line states the answer
  the chain reaches, with its status.
- **Links.** Every step from one claim to the next is a `therefore` (it follows
  because of the one before) or a `but` (it complicates or reverses the one
  before). There is no third kind: a step that is only "and then" is not an
  argument, and the build rejects it. Each link carries its *because*: one
  sentence naming the mechanism, a reviewed prose block.
- **Evidence attaches to links, not to the report.** A data finding, filing or
  excerpt is attached to the claim or link it bears on, as `supports`,
  `contradicts`, `qualifies` or `falsifier-for`. A link with no evidence
  renders as *asserted*.
- **The causality matrix.** The build renders the chain as a table, one row
  per link in order (from, therefore/but, to, because, evidence for, evidence
  against, status), plus a small chain diagram (SVG). The Bottom line reads the
  chain from root to conclusion in one paragraph.
- **Pulling things in.** Reworking the argument or adding evidence is one row
  in `edition/relations.tsv` (or `edition/chain.tsv`); the build places it in the
  matrix, the Analysis and the claims index. Nothing is moved by hand.
- **Checks.** Every argument claim is reachable from the root; every link is
  `therefore` or `but` and has a *because*; no cycles; every data claim attaches
  to some link or claim, or is listed as unattached.

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

**Claim → claim, the chain** (`edition/chain.tsv`): `from, link, to, because,
review`, with `link` either `therefore` or `but` (§2a).

**Evidence → claim or link** (`edition/relations.tsv`): `subject, predicate,
object, review`, predicates `supports | contradicts | qualifies | falsifier-for`;
the object may be a claim id or a chain link id. Example
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
4. **Chain and evidence.** `chain.tsv` (root, `therefore`/`but` links with
   their *because*), `relations.tsv` (evidence onto claims and links), the
   causality matrix and chain diagram, the falsifier section. Done when every
   argument claim is reachable from the root, every link is `therefore` or
   `but` with a *because*, no data claim is unattached, and every link and edge
   shows its review state.
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

9. **The root.** Answered by Sloane, 2026-11-04: the chain starts from the
   open question "Is Anthropic a public benefit corporation?" (§2a).

### Answers, Sloane, 2026-11-04

1. **Pin:** the latest committed (recompiled) paper, not frozen v0. Today that
   is still `1afb042`; the pin moves forward each time the paper is recompiled
   and committed, and every edition records the paper commit it quoted.
2. **Claim wording:** verbatim excerpts, with the most relevant part of each
   quote highlighted (a highlighted sub-span inside the excerpt, both checked
   by hash).
3. **Ids:** C-ids with aliases (recommendation stands; not contested).
4. **Descartes:** every number in the report becomes a Descartes claim
   (answers Praxis Q21).
5. **Disclosure:** (c). The adviser disclaimer goes only on outputs published
   under the Ethical Capital brand. Under Praxis, a different statement: this
   is not a publication; it is set up to facilitate dialogue between
   communities, toward the goal of asserting collective stewardship (Praxis
   `PRINCIPLES.md` P2). The paper's intro can be improved separately.
6–8. Recommendations stand (CiTO plus one local term; indexes inline unless
   the PDF passes 25 pages; risk-governance rows included, marked unsealed).
9. **Root:** "Is Anthropic a public benefit corporation?"
10. **Aggregate.** Every claim in every index must be addressable together,
    across all Praxis-governed repositories (Sloane, 2026-11-04). Each row of
    `claims.tsv` carries a global `address` (`praxis:claim/anthropic-pbc/C0001`,
    never reused) and a `content_id` (BLAKE3 of the canonical statement), so a
    claim made in two repositories can be matched. The aggregate itself belongs
    to the Praxis catalog: Praxis `OPENQUESTIONS.md` Q27.
