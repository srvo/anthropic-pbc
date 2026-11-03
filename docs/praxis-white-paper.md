# Praxis — White Paper (Consolidation Draft)

**Status:** Draft for public review. Consolidation of the Descartes repository
as it stood at commit `1a2951d` (two commits: root + first outside witness).
**Companion:** [`praxis-standard.md`](praxis-standard.md) — normative skeleton
extracted from this narrative.
**Binding authority:** None. Per [`README.md`](../README.md:16),
the README is the specification. Files in `docs/` bind nothing until the README
names them. This paper is an editorial base, not a spec change.

## How to read this paper

Every material claim carries a tier. Do not promote a claim by quoting it
without its tier.

| Tier | Meaning |
|---|---|
| **BUILT** | Implemented in `src/` and/or recorded in `claims/`, `artifacts/` |
| **SPEC** | Normative in `README.md`; loop confirmation partial (see §8) |
| **DESIGNED** | In a `docs/` design note; not built, not binding |
| **ASPIRATIONAL** | Stated as planned/later; no design or no code |
| **EXTERNAL** | From a cited outside source; repo may not hold its bytes |
| **ABSENT** | Searched for; not in the repo. Named so editorial work does not invent it |
| **EDITORIAL** | Synthesis or framing added here. Sloane's layer to keep, cut, or evidence |

### Three corrections to the common one-line description

1. **Praxis is not a built system.** `README.md:3` — "Descartes is part of
   Praxis, an open-source release from Ethical Capital." The enclave brief
   states the repo has "no tenant concept, no Praxis code"
   ([`docs/enclave-capital-introduction.md`](../docs/enclave-capital-introduction.md:11)).
   License today is `MIT OR Apache-2.0`; "A Praxis license has not been
   written yet" (`README.md:4`). **[SPEC]**
2. **Descartes is not distributed or fault-tolerant, by design and by gap.**
   Constraint P16 forbids a "daemon, server or database" for the loop
   (`README.md:108`). Contract S7: the store has one writer, the loop.
   Fault tolerance is open negative evidence: S5 (an orphan `.partial` makes
   verify fail) and S6 (directory not fsynced after rename; crash/power-loss
   behaviour undecided) (`README.md:371`). No replication, consensus, or
   multi-writer protocol exists in the repo. **[SPEC/ABSENT]**
3. **There is no maker–taker pricing model and no anti-fascist argument in
   the repo.** See §3 and §4.4. Both are EDITORIAL hooks below, not findings.
   **[ABSENT]**

---

## 0. The argument in one chain

> **P1 [BUILT]** Every translation loses something, measurably. One held
> PDF→text derivation preserved 10,898/10,910 words (99.89%, circle 1),
> independently OCR-confirmed 10,619/10,910 (97.33%, circle 2), left 2.41%
> of ink in 17 regions outside any word box, and did not capture tables.
> ([`claims/fidelity-secure-alternatives-to-iroh.tsv`](../claims/fidelity-secure-alternatives-to-iroh.tsv:3),
> [`docs/circles.md`](../docs/circles.md:26))
>
> **P2 [BUILT]** Witnesses — including the LLM witnesses this repo itself
> used — assert false things fluently: wrong BLAKE3 dependency claims,
> nonexistent strictness gates, false "formally verified" / "100% pure
> Rust" transport claims. Each was falsified only against primary sources.
> ([`claims/blake3-decision.tsv`](../claims/blake3-decision.tsv:14),
> [`claims/strictness.tsv`](../claims/strictness.tsv:25),
> [`docs/review-secure-alternatives-to-iroh.md`](../docs/review-secure-alternatives-to-iroh.md:23))
>
> **P3 [BUILT]** Therefore split the check in two: a machine proves a quote
> *exists* byte-for-byte in held evidence; a human judges whether the
> statement *follows*. The verifier "proves quotes exist not follow"
> ([`src/model.rs`](../src/model.rs:51),
> [`prompts/distill.md`](../prompts/distill.md:3)).
>
> **P4 [BUILT/SPEC]** That split needs deterministic identity: `id =
> blake3:` + hex of canonical encoding, no timestamps/hosts/random inside
> hashed bytes, a write-once plain-file store rebuilt from committed
> inputs, and a loop requiring `root' == root` on rebuild from empty.
> (`README.md:93`, `README.md:110`)
>
> **P5 [DESIGNED]** Trust stratifies: circle 0 source bytes → 1 one
> instrument → 2 independent instrument → 3 LLM proposal → 4 human
> discernment. Only the source is assumed.
> ([`docs/circles.md`](../docs/circles.md:7))
>
> **P6 [DESIGNED]** Judgment must not hard-code one framework. Frameworks
> become ingested data; an `evaluation` pins framework version, rating,
> and justifying claims. The evaluation node does not exist yet.
> ([`docs/epistemics.md`](../docs/epistemics.md:30))
>
> **P7 [DESIGNED]** Conflict is data, not overwrite: a proposed `against`
> edge, revisits as new nodes, unresolved conflict never silent.
> ([`docs/primitives.md`](../docs/primitives.md:41))
>
> **P8 [DESIGNED]** "More strict" has no total order when rules constrain
> different things, so conflict needs a person and a record — resolved in
> the client's interest, then by proposed reversibility/visibility
> tie-breaks. ([`docs/strictness.md`](../docs/strictness.md:10),
> [`docs/primitives.md`](../docs/primitives.md:14))
>
> **P9 [DESIGNED]** The first tenant makes P6–P7 concrete: a correction
> held "in his head, where the next run cannot see it" is judgment that
> evaporates. Persisting corrections is the first reason to build them.
> ([`docs/enclave-capital-introduction.md`](../docs/enclave-capital-introduction.md:52))
>
> **P10 [DESIGNED]** Private judgment stays private — no training, no
> product analytics, no cross-tenant retrieval. A commons grows only by
> deliberate, attributable, per-item contribution.
> ([`docs/enclave-capital-introduction.md`](../docs/enclave-capital-introduction.md:205))
>
> **P11 [DESIGNED]** Dependence is the forbidden shape: exit in complete
> checkable form is a feature, operator reads are attested and visible to
> the tenant, and a multi-tenant SaaS control plane is explicitly rejected.
> ([`docs/research-spike-enclave-domain-landscape.md`](../docs/research-spike-enclave-domain-landscape.md:514))
>
> **P12 [EXTERNAL]** The claimed market opening is a vendor gap, not a
> sizing: no fetched vendor claims an end-to-end scan → transcript →
> fit-score → quoted-outreach loop; vendor figures are unverified and the
> cited survey contains no dollar data. (§7)
>
> **∴ [ASPIRATIONAL]** A *public epistemic commons* — claims quoting
> evidence byte-for-byte in a content-addressed graph anyone can re-verify
> from bytes alone (`README.md:7`). The conclusion is the objective. It is
> not yet a built fact: enclaves (T1–T3), keys, signed claims, and the
> human-concurrence record are all unbuilt (`README.md:418`).

**Strongest honest claim today [EDITORIAL]:** Descartes demonstrates, on one
machine for one corpus, that LLM distillation can be put under a deterministic
quote-existence check with measured per-stage loss — and that doing so catches
its own witnesses being wrong. Everything past that sentence is design.

---

## 1. The problem, empirically (and its limits)

### 1.1 Translation loss is measurable; a single "fidelity score" hides it [BUILT/DESIGNED]

[`docs/epistemics.md`](../docs/epistemics.md:5): every stage is a
translation — ingestion (bytes→artifact, identity), derivation (PDF→text,
formal), distillation (text→claims, semantic), evaluation (claims→ratings,
not built). The ledger reports loss per component per circle and "never
reports one fidelity score."

Measured instance (Gemini transcript PDF, 2026-11-02): 0.11% of words lost
at circle 1, 2.67% OCR-unconfirmed at circle 2, 2.41% of ink outside words
across 17 regions, tables/positions not captured, and only 8.85% of derived
bytes under any distillation quote. Coverage is a lower bound that "tells
you where to look, not whether loss was justified"; classifying gaps as
redundant/out-of-scope/missed is circle 3, human agreement circle 4.

*Limit:* one document, one toolchain. No general "documents lose X%" claim
is licensed.

### 1.2 Witness unreliability is demonstrated, not hypothesized [BUILT]

The repo's method is itself the evidence. Three witness corpora were checked
against primary sources and found wrong in material ways:

| Witness corpus | Checked against | Result |
|---|---|---|
| BLAKE3 paste (`sources/llm-witness-blake3.md`) | BLAKE3 spec, crate manifest | Authorship misattributed; "zero external dependencies" wrong |
| Strictness paste (`sources/llm-witness-strictness.md`) | Repo code, Utah/CFR law texts | `forbid(unsafe)` binds one crate, not the binary; bwrap never ran; claimed PR gates/resolver do not exist; ML-DSA sizes false (FIPS 204 itself "not anchored") |
| Iroh-alternatives transcript (141 claims) | Vendor docs, crate sources | s2n-quic "formally verified using Coq" false; webrtc-rs "100% pure Rust" false; all version pins stale; draft protocols presented as settled |

Total ingested: **234 claim rows across 7 TSV files** (141 + 35 + 21 + 15 +
8 + 7 + 7 in [`claims/`](../claims/secure-alternatives-to-iroh.tsv:1)).
No claim file proves external technical truth. Each proves quote
occurrence/attribution only. That boundary is the point.

### 1.3 Provenance ≠ truth; existence ≠ entailment [SPEC/DESIGNED]

A hash proves bytes are the bytes. It does not prove a statement follows
from them ([`docs/research-spike-permaculture-atomic.md`](../docs/research-spike-permaculture-atomic.md:46)).
An LLM claim "is testimony until a person concurs, [and] nothing records
that concurrence yet" (`README.md:330`). Any system that collapses these —
content addressing as credibility, a quote as an argument — overclaims.
Descartes' own pasted-draft corrections make the same point about
Admiralty/ACH machinery: inventing 3/2/1 weights and calling hypotheses
"mathematically eliminated" overstates ACH
([`docs/epistemics.md`](../docs/epistemics.md:78)).

### 1.4 Corrections evaporate [DESIGNED, single-subject]

The enclave operator "built steps 1–3 himself: daily scans, custom prompts,
fit scores. What is manual is the handoffs." His corrections live in his
head, invisible to the next run. Judgment — ICPs, rubric versions,
corrections — "is the asset" and is exactly what current tooling cannot
hold, version, or hand back.

*Limit:* n=1 design brief, explicitly "not [a] finding"
([`docs/enclave-capital-introduction.md`](../docs/enclave-capital-introduction.md:3)).
Do not generalize to "asset owners" as a class without more subjects.

### 1.5 The default platform shape extracts the asset [DESIGNED]

The brief's non-needs name the default: model training on tenant data,
vendor benchmarks, "anyone scoring his knowledge," product analytics,
aggregate-over-tenants learning, `"service improvement" reuse`. The
landscape spike rejects the shape that produces them: a multi-tenant SaaS
control plane "makes the operator a platform vendor — the dependence shape
… forbids." §3 formalizes this as the maker/taker structure the repo
implies but never states.

### 1.6 What the problem definition cannot yet claim [ABSENT]

- No prevalence data: how often corrections evaporate, vendors train on
  tenant data, or witnesses err, outside this repo's three corpora.
- No substantive distillation of the five held grounding papers
  (Bonvoisin 2020; Soiland-Reyes 2022; Leo 2024; Visser 2023; Konkol 2025):
  one matched fragment each (§6.2). Their conclusions are **not** repo claims.
- No audio/image/table path: testimony that cannot be quoted (speech,
  photos) suffers "evidentiary paralysis"; ingestion not built
  ([`docs/strictness.md`](../docs/strictness.md:100)).

---

## 2. Actors and their interrelationships

Names follow the template rule: people only as witnesses/signers; use cases
by role, never by personal name (`README.md:62`). "Asset owner" in this
repo means **owner of judgment as an asset** (the enclave tenant), not a
financial asset owner class. That distinction matters for §7.

| Actor | Gives | Gets | Power / constraint | Tier |
|---|---|---|---|---|
| **Ethical Capital (sponsor)** | Spec, template, Descartes code | Reusable module standard | Sets README spec; license MIT/Apache today | SPEC |
| **Verifier / loop** | Quote-existence, closure, rebuild checks | `sources/`, `claims/`, `attestations/` | Rejects dangling/cyclic/non-unique quotes; cannot judge entailment | BUILT |
| **Witness** (LLM or speaker, circle 3) | Byte-for-byte quote proposals | Attribution, not endorsement | None over truth; falsifiable vs primaries | BUILT |
| **Human signer / concurrer** (circle 4) | Discernment; Ed25519 attestation (`did:key`) | Legible, revisitable record | Only roster humans may sign interest/custody (designed); concurrence currently unrecorded | BUILT sig / DESIGNED roster |
| **Enclave tenant** (capital introducer) | ICPs, rubrics, corrections, watchlist — all private | Scan→fit→quoted outreach; corrections persist; complete checkable exit | Owns the judgment asset; operator reads attested + visible to him | DESIGNED |
| **Allocators** (RIAs, family offices, foundations, pensions, consultants) | Mandates via distinct speaking/deciding/filing units | Matched managers/funds | Deciding unit allocates; three units are three actors, not one "client" | DESIGNED |
| **Emerging managers / funds** | Fund materials for fit scoring | Allocator introductions | No system power; no fee/rent stated anywhere | DESIGNED |
| **Named operator** | Runs tenant workload; queue fairness as service term | Bounded, attested access | No training/analytics/aggregate learning; "dependence never permanent"; path to self-operation | DESIGNED |
| **Other tenants / commons contributors** | Items deliberately contributed upward, per item/class | A commons "both tenants drink from" | Opt-in only; private strata train nothing shared | DESIGNED |
| **Client (advisory)** | The interest in whose name conflicts resolve | Conflicts resolved in client interest, never silently | Tie-break authority via signed interest evaluation (designed) | DESIGNED |
| **Named subject** (person spoken about) | Testimony as witness | Contest via claim `against` — designed, not built | **Weakest actor in the system** (§2.1) | ASPIRATIONAL |
| **Upstream maintainers** (3 pinned direct deps) | `serde`, `blake3` (pure), `ed25519-dalek` | Proposed endowment payout | Weights are signed interest decisions; unclaimed → escrow, never reverts | BUILT deps / ASPIRATIONAL payout |
| **Dependency governors** | Crates judged by governance, bus factor, license, exit standard (P6) | Adoption only with recorded exit route | Most recommended Iroh-stack crates are bus-factor 1; `bao-tree` is n0 (the Iroh company) | SPEC (register open) |

### 2.1 Who bears the burden today (veil pass)

Ask who this design serves if you might occupy any position in it:

- **Named subjects** have no contest path. Strictness: "not designed."
  Primitives designs one (`against`), unbuilt. Until then, a person can be
  claimed about, with byte-perfect quotes, and have no in-graph reply.
  P13 ("a dispute is recorded, never suppressed") is **open until `against`
  exists** (`README.md:104`).
- **Speakers whose evidence is not text** — audio testimony, images — cannot
  be quoted byte-for-byte today. The system privileges already-textual,
  already-archived speech. Whose knowledge survives as text is not a neutral
  filter (§9).
- **Tenants without an operator's resources** — the design assumes a named
  operator, a machine, custody decisions; all open. Exit rights help only
  if export (S8: "no export exists") is built.
- **Non-darwin/arm64 users, screen-reader users**: P5 (every chip) and P9
  (accessibility) are open. One platform has run.
- **Future rebuilders**: P14 (second independent verifier) and P15 (rebuild
  cost) are open. "Governance outlives individuals" (P10) currently rests on
  one implementation read by its author.

None of these are reasons to stop. All are reasons not to call the commons
"public" yet without qualification.

---

## 3. Maker–taker relationships: absent as pricing, present as extraction

**ABSENT:** No rent, fee, take rate, subscription, revenue share, or
maker–taker spread appears in any file. The only economics are inference
cost shapes (batch ~50% cheaper; local = "electricity + operator time; no
per-token fee") and the proposed upstream endowment.

**EDITORIAL synthesis (evidence-anchored):** The repo does define an
epistemic maker–taker structure — who *makes* verifiable value and who
*takes* it by default — through its prohibitions. Read each prohibition as
a taker flow refused:

| Maker (creates the asset) | Default taker flow | Praxis refusal [DESIGNED unless noted] |
|---|---|---|
| Tenant judgment (ICPs, rubrics, corrections) | Training on tenant data; aggregate-over-tenants learning | "These train nothing shared and enter no other tenant's retrieval" |
| Tenant activity | Product analytics; "service improvement" reuse | "Activity is not surveillance"; no analytics, no reuse |
| Tenant dependence | SaaS control plane; exit friction | Exit complete + checkable; control-plane shape rejected; path to self-operation |
| Sources & witnesses | unattributed absorption into model output | Quote byte-for-byte or reject; attribute, never endorse [BUILT mechanism] |
| Operator access | Invisible reads of tenant stratum | Operator reads attested and visible to tenant |
| Upstream maintainers | Unpaid foundational dependence | Endowment: dependency list × `MAINTAINERS.tsv` = payout derivation; weights signed, unclaimed→escrow [ASPIRATIONAL; 1/depth formula contradicts its own rationale — §8] |
| Other tenants' compute | Bulk job starves daily run | Queue priority as an explicit service term |

The inversion is the point **[EDITORIAL]**: in the default shape, makers
supply judgment and takers capture it as training data, lock-in, and
benchmarks. In the designed shape, capture requires a deliberate,
attributable, per-item act by the maker. If a future Praxis business model
needs a taker side, it must be designed against this table — any take not
listed as a service term (queue priority is the one example) is currently
forbidden by the design notes.

---

## 4. Governance over truth

### 4.1 Who decides what is true? Nobody, mechanically [BUILT/SPEC]

The verifier decides three things only: quotes exist uniquely in held
bytes, links resolve to the right kinds, and the graph rebuilds to the same
root. Entailment, credibility, and conflict resolution are human acts that
must leave records. "Say what is true, say who decided, say whose interest"
([`docs/primitives.md`](../docs/primitives.md:3)) — the second and third clauses are
governance, and both are unbuilt.

### 4.2 The designed stack [DESIGNED]

1. **Circles 0–4** stratify trust; credibility grade 1 ("confirmed") under
   the drafted Admiralty framework requires the same content from an
   *independent* source, and independence is itself a challengeable claim.
2. **Frameworks are data.** Admiralty, ACH, interest, custody, gates,
   use-policy — each an ingested, versioned file; each evaluation pins its
   version. No framework is compiled into the verifier. Scores are computed
   deterministically, never stored.
3. **`against` + revisits.** Conflict is verifier-checkable (two claims
   either against the other). A correction is a new evaluation against the
   original; "nothing is overwritten" (P12).
4. **Strictness has no total order.** CFA I(A)'s "the more strict" fails
   when rules constrain different things (isolation vs freshness). The
   resolver is a signed human interest evaluation: client interest →
   reversibility → visibility (proposed order). Skipped gates still emit an
   evaluation; a check that cannot run records `skipped`, never `pass` (L5).
5. **Custody over erasure/immutability collisions.** Strictness justifies a
   `withheld` node; primitives re-expresses it as a custody evaluation
   rating. Unreconciled (§8). Utah-law analysis in-repo: no erasure right
   currently forced (source "not anchored" — treat as unverified).
6. **Keys and roster.** Release key (cold) and node key planned; "no key has
   been generated yet" (`README.md:300`). Key custody is "an open governance
   decision." Only roster keys may sign interest/custody — roster unbuilt.

### 4.3 Governance of the governors [SPEC, partial]

- Dependencies judged by governance/bus factor/exit standard (P6) — register
  `docs/dependencies.md` does not exist; the Iroh review applies the rule by
  hand and adopts only `blake3` (pure, vector-checked).
- Everything needed to rebuild trust from zero lives in the repo (P10);
  the graph must not depend on the tool that wrote it (P14, open).
- Time is an input, never a sample: facts carry no clock; time enters as a
  recorded claim/attestation. Determinism forbids sampling the clock, not
  recording it.

### 4.4 Authoritarian capture: ABSENT, with two legitimate hooks

**ABSENT:** No file argues about fascism, authoritarianism, or state capture
of truth. Do not cite this repo for that argument.

What the repo *does* contain, usable as mechanisms if Sloane evidences the
political claim separately **[EDITORIAL hooks]**:

- **Surveillance-by-record:** artifacts omit who/where ran them (P8) —
  in the landscape spike, "because such records enable surveillance."
- **Suppression-by-overwrite:** P12/P13 make disputes recordable and
  decisions un-overwritable — *when `against` is built*. Today P13 is open,
  so the anti-suppression property is designed, not held.
- **Capture-by-dependence:** single-vendor control planes and bus-factor-1
  dependencies are treated as governance risks with required exit routes.

An editorial that extends these to authoritarian truth-governance needs its
own external evidence (who captures, through which of these mechanisms,
with what observed cases). The mechanisms are real; the politics are not
in the graph.

---

## 5. The architecture as it stands

### 5.1 BUILT — Descartes core (Rust, single machine, single writer)

- **Identity:** `blake3:` + lowerhex of canonical JSON (sorted keys, i128
  integers only, minimal escapes); IPLD DAG-JSON links `{"/": id}`.
  One id space for blobs and nodes — flagged **decide before publish**
  (I5: no domain separation).
- **Five node kinds**, exact key sets, extra/missing key = error:
  `artifact{blob,bytes,media_type,name,sha256}`,
  `claim{statement,witness,evidence{artifact,start,end,slice_blake3},supports}`,
  `derivation{input,output,tool,args}`,
  `attestation{subject,signer,signature}` (Ed25519, `did:key`, domain
  `descartes-attestation-v2`), `snapshot{members}`.
- **Store:** `.descartes/{blobs,objects}/<ab>/<blake3>` plain files —
  a projection, never committed, rebuilt from `code + sources/ + claims/ +
  attestations/`. Write-once (temp + fsync + rename, symlinks refused).
  Anything unreachable from the root is an error; cycles fail.
- **CLI:** `hash, ingest, claims, check, derive, fidelity, coverage,
  probe-net, keygen, sign, attest, snapshot, verify[--root]`; TSV out,
  exits 0/1/64 ([`src/main.rs`](../src/main.rs:32)).
- **Supply chain:** exactly 3 pinned direct dependencies (`serde 1.0.229`,
  `blake3 1.8.7` pure, `ed25519-dalek 3.0.0`), vendored offline, Rust 1.99.0
  pinned, `forbid(unsafe)` in own crate only (dependencies do use `unsafe`;
  not a memory-safety proof). Canonical encoding, SHA-256, store, verifier
  hand-written here. **[BUILT config; SPEC guarantees]**
- **The loop:** `env -i` → boundary (no keys/.env/symlinks/secrets/>1MiB
  unmanifested) → stage-0 POSIX-`sh` checks (SHA-256 tool verified against
  vectors first, P1) → two sandboxed offline builds must be byte-identical
  → 7 isolation probes denied (net, home write, `~/.ssh`, Unix socket,
  resolver, env leak, `.git`) → 100% line/region coverage outside named
  exemptions → manifest, cross-check, derivations, fidelity → ingest →
  snapshot → verify → rebuild into empty store → byte-compare artifacts.
  Committed artifact records `binary … reproducible`, all `isolation_*`
  denied, `coverage 144 tests; 100%` on darwin-arm64
  ([`artifacts/stage1/darwin-arm64.tsv`](../artifacts/stage1/darwin-arm64.tsv:1)).
  See §8 for the "not yet confirmed" contradiction.
- **Method template:** Descartes is the template every Ethical Capital
  module starts from — fixed README §0–§11 order, one source of truth per
  value, no governing doc outside the README. This, not a network, is the
  current "Praxis architecture." **[SPEC]**

### 5.2 DESIGNED — judgment layer and enclaves

Evaluation/framework nodes, `against`, gates/custody/interest/roster
(build order in [`docs/primitives.md`](../docs/primitives.md:143));
per-tenant strata with commons joins by opt-in contribution; attested
operator reads; queue fairness; export bundle; custody/teardown. Blob-area
design contradicts between brief ("either is defensible") and landscape
(rejects shared probed area) — decision open before tenant ingestion.
Bao byte-range proofs, sync, and offline archive (R2) explicitly not built.

### 5.3 ASPIRATIONAL / transcript-only [do not present as Praxis]

From the distilled Iroh transcript, attributed never adopted: did:key +
UCAN delegation, BLAKE3/Bao, QUIC transport (s2n-quic/webrtc), MoQ +
fountain codes, Tor/HPKE/MLS, WARC/OpenTimestamps (adds Bitcoin dep —
flagged), Wasm agent sandboxes. The review endorses the *layering*
(identity / content addressing / transport / claims) and adopts **only**
`blake3`. Open review items: redb format stability, raptorq RFC 6330
interop, rs-ucan v1 status.

### 5.4 Explicit non-properties

Not distributed (single writer). Not fault-tolerant (S5/S6 open). Not
real-time (no daemon/server). Not multi-platform (darwin/arm64 only; Linux
`bwrap` untested). Not semantic (verifier cannot judge entailment). Not
private by cryptography (enclave encryption undecided; no keys exist).
Performance, release channels, client-domain behavior, and "commons
strategy" are out of scope in the spec itself (`README.md:484`).

---

## 6. Capacity for collective organization, and latent attempts

### 6.1 Latent attempt #1: the tenant already built the front half [DESIGNED]

Steps 1–3 (scan, prompt, fit-score) exist as one operator's manual system.
What's missing is not invention but *persistence of correction* and
*handoffs*. The commons design generalizes that: private strata first,
contribution upward only as a deliberate attributable act per item or per
class. Collective benefit is gated by maker consent, not aggregation.

### 6.2 Latent attempt #2: the open-science stack (Ai2 witness) [EXTERNAL, half-checked]

First outside witness: the Ai2 "grounding Praxis" report, checked against
its own sources — **5 of 9 citations fragment-matched** (matched fragment
only; full quotes need whitespace normalization), 4 unchecked and URL-only:

| Source | Topic | Bytes held? |
|---|---|---|
| Soiland-Reyes et al. 2022 | Packaging research artefacts with RO-Crate | Yes |
| Leo et al. 2024 (report says 2023) | Recording provenance of workflow runs with RO-Crate | Yes |
| Visser et al. 2023 | Ten quick tips for building FAIR workflows | Yes |
| Bonvoisin et al. 2020 (CC-BY-4.0) | Standardisation of practices in Open Source Hardware | Yes |
| Konkol 2025 | Data-to-Knowledge Packages (matched in v3 HTML only) | Yes |
| Chard et al. 2019 | Whole Tale reproducibility — publisher blocks scripted download | **No** |
| Link et al. 2016 | Open Community Data Exchange / SPDX — ACM-licensed | **No** |
| Roman et al. 2023 | Open Datasheets — CC-BY-NC-ND | **No** |
| Solarin 2026 | Artifact verifiability in decentralized build — unrefereed, future-dated arXiv id as cited | **No** |

Reading **[EDITORIAL]**: RO-Crate, FAIR workflow, OSH manifest, and
reproducibility-platform work are independent latent attempts at the same
shape — bundle claims with checkable provenance so strangers can rebuild
trust. Descartes differs in where it puts the check (byte-exact quote +
deterministic rebuild, witness explicitly demoted to circle 3). But since
no conclusion from these papers is distilled into `claims/`, treat them as
topic grounding, not evidence. Distilling them properly is identified
future work, and redistribution terms already block 4 of 9 — itself a
finding about commons-building under current rights defaults.

### 6.3 Latent attempt #3: vendor ecosystems [EXTERNAL, weak]

Five vendor ecosystems surveyed, "all vendor-owned marketing; no
independent practitioner source was found." Two patterns: outbound
database/CRM enrichment vs inbound two-sided platform + AI-matched-event
meetings. Scale claims ("150,000+ monitored sources", "4,700 fundraises",
"60% drop") unverified vendor marketing. Useful as a map of what money
currently buys; useless as demand evidence.

### 6.4 Why a commons could work here at all [EDITORIAL, from P4+P10]

Two properties do the work: (1) contribution is *checkable by strangers*
(rebuild from bytes), so trust need not be interpersonal; (2) contribution
is *revocable-by-omission* (private strata are the default; nothing shared
trains anything), so participation does not require surrendering the asset.
Most failed commons invert one of these. This is a hypothesis about the
design, not an observed outcome — no second tenant exists.

---

## 7. Opportunity — what is licensed, what is not

**Licensed [EXTERNAL]:** a workflow gap. No fetched vendor claims the full
scan → transcript → fit-score → quoted-outreach loop; "absence is the
market opening" ([`docs/research-spike-enclave-domain-landscape.md`](../docs/research-spike-enclave-domain-landscape.md:79)).
The installed base is legible: CRM penetration 91.08% in the cited T3
survey, CRM "binds together the rest of the tech stack" — an integration
surface, not a budget.

**Not licensed [ABSENT]:**

- **No dollar sizing.** T3 "contains no dollar spending or budget data
  anywhere — do not cite T3 for spend," which also voids the spike's own
  later sentence that "T3 shows the money … concentrated in the CRM."
  There is no TAM/SAM/SOM in the repo. Do not write one from penetration %.
- **The buyers were not sampled.** "Allocators, family offices, pensions,
  and capital-introduction operators are not sampled as such" in T3.
- **No willingness-to-pay, pricing, or second subject.** One tenant brief.
- **Unbenchmarked cores:** entity resolution, 100-name mention search,
  MLX determinism, and the assembled 48h SLA are unproven.

**EDITORIAL — the big-opportunity claim that *can* be argued:** the asset
(judgment: ICPs, rubrics, corrections) is currently unholdable — it lives
in heads and prompts, evaporates between runs, and can only be
platform-hosted by surrendering it to training/analytics defaults. Whoever
holds judgment *without taking it* — checkable, portable, exit-complete —
holds the layer every scan/fit/outreach tool must sit on. That is a
structural claim from §1.4 + §3, sized by nothing. Editorialize it as
structure; do not dress it as market research until spend/sample evidence
exists (new sources, ingested as claims, would be the repo-native way).

---

## 8. Contradictions, open contracts, and falsification register

Honest inventory. Each item blocks a specific stronger claim.

| # | Item | Blocks the claim… |
|---|---|---|
| C1 | `README.md:350` contracts "not yet confirmed by a passing loop" vs L1 "plain run passed 2026-11-03"; negative suite L6 open (control failed) | "The loop proves the spec" — say *plain run passed on darwin-arm64; adversarial suite open* |
| C2 | Adversarial review (2026-11-02) confirmed highs then: vendored-checksum rewrite passed build, sandbox leaked `~/.ssh`/sockets/DNS, `recipes.tsv` ran any tool unsandboxed, absolute paths = quote oracle. Loop artifacts since record deny-default fixes; review doc does not confirm each landed | "Sandbox/boundary is proven" — re-audit before claiming |
| C3 | `withheld`: new node kind (strictness) vs custody rating (primitives), unreconciled | Any erasure/custody conformance clause |
| C4 | Endowment 1/depth pays foundational crates least, contradicting rationale; $1500/$350/$150 unvalidated; MiFID II doesn't govern a Utah adviser; SSDF citation unchecked | Any payout figure or regulatory justification |
| C5 | Blob area: "either defensible" vs shared-area rejected | Any tenant-isolation claim (T1–T3 all open) |
| C6 | I5 one id space, no domain separation; V5 attestation-in-snapshot semantics; Rust pinned in two files vs one-source-of-truth | Publish as a standard others implement against |
| C7 | Unanchored externals flagged by the docs themselves: FIPS 204, Utah erasure (S9), STANAG number, 15–20% threshold found in neither cited source | Quoting those numbers/laws as settled |
| C8 | History rewrite (7 commits / 1,609 store files → one root) and records/ redaction derivations await explicit go-ahead; Ai2 PDF redistribution terms unconfirmed | "Sealed append-only history"; redistributing the Ai2 PDF |
| C9 | P4–P6, P9, P11, P13–P15 open (later-stage inspectability, every-chip, dependency register, accessibility, evaluations, contest, second implementation, rebuild cost) | "Public", "for everyone", "governance outlives individuals" without qualification |
| C10 | Transcript internals: 48h vs 72h domain age, bao-tree 0.5 vs 0.13, temperature-0 "zero hallucination" overstated | Citing transcript numbers without the review's flags |

**What would falsify the core thesis [EDITORIAL]:** (a) a checked witness
corpus where byte-exact quotes routinely survive while entailment fails
undetectably at circle 4 — i.e. the human layer doesn't scale; (b) a second
tenant whose corrections cannot be expressed as evaluations against claims
without loss the tenant rejects; (c) rebuild cost (P15, unmeasured) that
grows faster than the graph's value. None has been tested.

---

## 9. Editorial gate — standing, framing, open questions

Applied before this draft is editorialized further. Outputs are questions
and flagged limits, not a clean bill of health.

**Stakeholder pass (veil):** §2.1. Sharpest: named subjects (no contest
path), non-text witnesses (evidentiary paralysis), tenants without operator
resources, non-darwin users, future rebuilders. If you could wake up as the
person *claimed about* in this graph, the feature you would demand first is
`against` with roster-signed visibility — currently build-order step 2.

**Standing pass:** This paper speaks *about* the enclave tenant and
allocators from one design brief written by the sponsor side; no tenant,
allocator, manager, named subject, or maintainer is quoted with standing in
the repo. Vendor sources are marketing. The Ai2 report is an outside
*witness* (circle 3), half fragment-checked — not community standing.
Claims about what asset owners, allocators, or marginalized speakers need
require sources from those positions, ingested as claims, before
publication as anything stronger than a sponsor-side design hypothesis.
Byte-exact quoting privileges literate, archived, English-text evidence;
oral and non-text knowledge traditions enter only as unquotable testimony
today. That asymmetry is structural, stated here rather than solved.

**Correction mechanism:** Subjects and witnesses can be corrected only by
new claims from someone with repo access; there is no external contest,
appeal, or feedback channel. Until `against` + a public intake exist, this
paper must not claim the commons is contestable.

**Buzz-saw flags retained in text:** `[ABSENT]` maker–taker pricing,
authoritarian capture, dollar sizing, distributed/fault-tolerant
properties; `[NON SEQUITUR avoided]` P12 vendor gap does not entail P13
commons viability; `[VAGUE in sources]` "asset owner" (= judgment owner,
n=1), "commons" for podcast transcripts undefined, endowment weights;
`[FALSE if repeated]` "Praxis is a distributed Rust architecture" (§0).

---

## Appendix A. Evidence index (where to check every load-bearing claim)

| Claim family | Primary files |
|---|---|
| Objective, template, constraints P1–P16, loop, contracts, work order | [`README.md`](../README.md:1) (§0–§11, 505 lines) |
| Node kinds, identity, verifier semantics | [`src/model.rs`](../src/model.rs:22), [`src/lib.rs`](../src/lib.rs:1), [`src/main.rs`](../src/main.rs:1) |
| Loss/fidelity, circles 0–4 | [`docs/epistemics.md`](../docs/epistemics.md:1), [`docs/circles.md`](../docs/circles.md:1), [`claims/fidelity-secure-alternatives-to-iroh.tsv`](../claims/fidelity-secure-alternatives-to-iroh.tsv:1), `artifacts/fidelity/*`, `artifacts/loss/*` |
| Judgment layer design | [`docs/primitives.md`](../docs/primitives.md:1), [`docs/strictness.md`](../docs/strictness.md:1), [`claims/strictness.tsv`](../claims/strictness.tsv:1) |
| Enclave tenant, actors, market | [`docs/enclave-capital-introduction.md`](../docs/enclave-capital-introduction.md:1), [`docs/research-spike-enclave-domain-landscape.md`](../docs/research-spike-enclave-domain-landscape.md:1) |
| Permaculture/FAIR framing, endowment | [`docs/research-spike-permaculture-atomic.md`](../docs/research-spike-permaculture-atomic.md:1), [`docs/endowment.md`](../docs/endowment.md:1) |
| Witness falsifications | [`claims/blake3-decision.tsv`](../claims/blake3-decision.tsv:1), [`claims/secure-alternatives-to-iroh.tsv`](../claims/secure-alternatives-to-iroh.tsv:1), [`docs/review-secure-alternatives-to-iroh.md`](../docs/review-secure-alternatives-to-iroh.md:1) |
| Outside grounding (Ai2 + 9 papers) | [`claims/ai2-grounding-praxis.tsv`](../claims/ai2-grounding-praxis.tsv:1), [`works-cited/ai2-grounding-praxis.tsv`](../works-cited/ai2-grounding-praxis.tsv:1), [`sources/MANIFEST.tsv`](../sources/MANIFEST.tsv:60) (66 sources) |
| Security posture | [`docs/adversarial-review-2026-11-02.md`](../docs/adversarial-review-2026-11-02.md:1), [`docs/history.md`](../docs/history.md:1), [`docs/tooling.md`](../docs/tooling.md:1) |
| Distillation method | [`prompts/distill.md`](../prompts/distill.md:1) ("witness, not a judge"; unique 6–20-word quotes; attribute, never endorse) |
| Self-description | [`CITATION.cff`](../CITATION.cff:5) ("Part of Praxis. A draft for public review"), [`Cargo.toml`](../Cargo.toml:6) |
| Verification state | `artifacts/stage1/darwin-arm64.tsv` (root `blake3:e0fdd6…`), `artifacts/stage0/`, `stage1/loop.sh`, `.githooks/` — re-run `sh stage1/loop.sh`; plain run must byte-match, `--accept` is the only way expectations change |

## Appendix B. Glossary (repo senses only)

- **Praxis** — parent open-source program of Ethical Capital; one module
  (Descartes) exists; license unwritten.
- **Descartes** — first/template module: deterministic claim/evidence graph.
- **Epistemic commons** — objective, not system: public claims quoting
  evidence byte-for-byte, re-verifiable from bytes alone.
- **Enclave** — a tenant (role name) running private judgment on shared
  machinery without surrendering it; first instance is a capital introducer.
- **Asset** — the tenant's judgment (ICPs, rubrics, corrections).
- **Witness / circles** — anyone who speaks enters as testimony; circles
  0–4 grade how checked that testimony is.
- **Loop** — the rebuild-and-compare pipeline that is the real conformance
  test (§5.1). A check that cannot run is `skipped`, never `pass`.
