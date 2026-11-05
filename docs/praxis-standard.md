# Praxis Standard — Skeleton v0 (Draft)

> **Copy.** This document comes from the Praxis/Descartes project and describes that project, not this repository. Relative links and code paths (`src/`, `claims/`, `sources/`, `Cargo.toml`, ...) point into that project and do not resolve here, except links to the other copied docs in this folder.

**Status:** Skeleton extracted from [`praxis-white-paper.md`](praxis-white-paper.md)
for editorial development. **Binds nothing.** Where a clause restates
[`README.md`](../README.md:1), the README wins. Promote a clause to binding
only by naming it in a module README with its enforcing check, per the
template standard (`README.md:42`).

Normative key words **MUST / MUST NOT / SHOULD / MAY** are used as in
RFC 2119. Every clause carries: source (repo file) and status —
`held` (checked by loop), `code-only`, `partial`, `open`, `decide` —
reusing the README contract vocabulary (`README.md:341`). A clause whose
status is not `held` MUST NOT be cited as a held property of any system.

## 0. Scope and conformance levels

- **PS-0.1** This standard applies to Praxis modules: programs that build,
  verify, tenant-host, or publish claim/evidence graphs. `[skeleton]`
- **PS-0.2** Conformance is per level. Claiming a higher level without its
  clauses held is a conformance violation, not a roadmap statement.

| Level | Name | Essence | Status today |
|---|---|---|---|
| L0 | Module | Template README (§0–§11), doubt-first loop, deterministic artifacts | Descartes: partial→held on darwin-arm64, adversarial suite open |
| L1 | Graph | Content-addressed claim/evidence graph, rebuild-from-bytes verify | Descartes core `held` in part; see §2 |
| L2 | Judgment | Frameworks-as-data evaluations, conflict, custody, interest | **Designed only** |
| L3 | Tenant (enclave) | Private strata, operator bounds, exit | **Designed only** (T1–T3 open) |
| L4 | Commons | Opt-in contribution, cross-tenant/public reading | **Aspirational** |

## 1. Module conformance (from template standard, P1–P16)

- **PS-1.1 Template.** A module README MUST carry Header + §0–§11 in order;
  empty sections MUST appear with `none yet`. `[README §0; held by review]`
- **PS-1.2 One truth per value.** If two files pin a value, one MUST
  generate or check the other. `[README §0; violated today by dual Rust pin — C6]`
- **PS-1.3 Doubt first (P1).** A checker MUST be checked before use
  (vectors before hashing). `[A002/A013; held]`
- **PS-1.4 Smallest foundation (P2).** Each stage SHOULD depend on the least
  it can; stage 0 MUST need only POSIX `sh`. Dependencies MUST be exactly
  pinned, vendored, offline in the loop. `[held for Descartes deps]`
- **PS-1.5 Determinism (P3).** Hashed bytes MUST NOT contain timestamps,
  hostnames, usernames, random ids, or locale order. Time MUST be recorded
  beside artifacts or as claims, never sampled into facts. `[A007/A009/A015]`
- **PS-1.6 Inspectability (P4), every chip (P5), accessibility (P9).**
  Artifacts SHOULD be readable with POSIX tools + `b3sum` in 20 years;
  human outputs MUST pass accessibility review. `[open beyond darwin/arm64]`
- **PS-1.7 Dependency governance (P6).** Each dependency MUST be judged by
  controller, bus factor, license, and the open standard that could replace
  it, recorded with an exit route **before** adoption. `[open: no register]`
- **PS-1.8 FAIR (P7).** Findable by digest; accessible as plain files;
  interoperable via open formats; reusable with producer recorded. `[partial]`
- **PS-1.9 Privacy (P8).** Artifacts MUST NOT record who ran them or where.
  `[boundary + binary grep]`
- **PS-1.10 Longevity (P10/P14/P15).** Everything to rebuild trust from zero
  MUST live in the repo; formats MUST suffice to re-implement a verifier
  without the original binary; rebuild cost MUST be measured beside (never
  inside) artifacts before caches/budgets are decided. `[open: no 2nd impl]`
- **PS-1.11 Proportionality (P16).** No heavier machinery than the problem:
  no daemon/server/database/plugin system for the loop without a named,
  checked requirement. `[by review]`
- **PS-1.12 Loop semantics.** A plain run MUST only compare and fail on any
  difference; `--accept` (or equivalent) MUST be the only way expectations
  change; an unrunnable check MUST record `skipped`, never `pass`;
  the loop itself MUST NOT touch the network (fetch/audit are separate,
  deliberate, recorded steps). `[L1 held darwin-arm64; L2–L9 mixed]`

## 2. Graph conformance (Descartes core)

- **PS-2.1 Identity.** Node/blob id MUST be `blake3:` + lowerhex of canonical
  encoding (keys sorted bytewise, integers only, minimal escapes, UTF-8);
  links MUST use `{"/": id}`. Domain separation between blobs and nodes:
  **[decide — I5, before publish]**.
- **PS-2.2 Node kinds.** Implementations MUST reject unknown kinds and any
  missing/extra key. Core kinds and keys: `artifact`, `claim`,
  `derivation`, `attestation`, `snapshot` (exact sets in
  [`src/model.rs`](../src/model.rs:22)). `[held: V1–V4 in part]`
- **PS-2.3 Evidence slices.** Every claim MUST rest on something; every
  evidence range MUST be non-empty, inside its artifact, and re-hash to
  `slice_blake3`; lists MUST be strictly sorted. A claim resting on nothing
  MUST fail verification. `[held]`
- **PS-2.4 Existence ≠ entailment.** A verifier MUST NOT represent quote
  existence as truth, credibility, or endorsement. Distillation MUST
  attribute ("X says…"), never assert witness content as fact. `[held by
  construction + prompts/distill.md]`
- **PS-2.5 Closure & rebuild.** Verification MUST be from a root: every
  reachable node re-encodes identically, no dangling/mistyped links, no
  cycles, nothing stored outside closure; rebuild into an empty store MUST
  yield the same root. `[A009/A010; held]`
- **PS-2.6 Write-once store.** Stores MUST refuse symlink/hardlink attacks,
  write via temp+fsync+rename, and treat byte-divergent re-put as
  corruption. Interrupted-write recovery (S5) and directory fsync (S6)
  MUST be decided and tested before any durability claim. `[partial]`
- **PS-2.7 Derivations.** Only allowlisted tools with fixed argument shapes
  MAY produce committed derivations, sandboxed, byte-reproducible; the loop
  MUST re-run them. `[held in part; recipes re-audit per C2]`
- **PS-2.8 Attestation.** Signatures MUST be separations from their subject
  (subject id independent of signer), `did:key` signers, strict Ed25519
  verify, lowercase hex. Whether attestations verify only when listed in a
  snapshot: **[decide — V5]**. Export of a roots bundle (S8): `[open]`.
- **PS-2.9 Loss accounting.** Every translation stage MUST report loss per
  component per circle; implementations MUST NOT report a single aggregate
  fidelity score. Tables/non-text content not yet captured MUST be stated,
  with dependent claims demoted to circle 0. `[held for measured corpus]`

## 3. Judgment conformance (L2 — designed, not built)

Source: [`docs/primitives.md`](primitives.md),
[`docs/epistemics.md`](epistemics.md),
[`docs/circles.md`](circles.md),
[`docs/strictness.md`](strictness.md). **No clause in §3 is held.**

- **PS-3.1 Circles.** Claims MUST be classifiable 0 source bytes / 1 one
  instrument / 2 independent instrument / 3 LLM-or-witness proposal / 4
  human discernment. Only circle 0 is assumed; instruments are re-run, kept
  as digests.
- **PS-3.2 Frameworks as data.** Evaluations MUST be separate nodes
  `evaluation{framework, subject, rating, rests_on, witness}` pinning an
  ingested, versioned framework file; the verifier MUST check the rating is
  allowed and justifying claims exist. Scores MUST be computed, never stored.
- **PS-3.3 Conflict.** Claims/evaluations MUST support `against`; conflict
  (mutual `against`) MUST be verifier-checkable; unresolved conflict MUST
  NEVER be resolved silently; a revisit MUST be a new node against the old.
  Nothing is overwritten (P12/P13).
- **PS-3.4 Contest.** A named subject MUST have an in-graph contest path
  with visibility equal to the claim contested. *(Closes the weakest-actor
  gap, white paper §2.1. Currently not designed end-to-end.)*
- **PS-3.5 Conflict of rules.** Where rules constrain different things,
  resolvers MUST record a signed human interest evaluation: client's
  interest first, then reversibility, then visibility (proposed order).
  Automated "strictest wins" MUST NOT be used. Every gate, including
  skipped, MUST emit an evaluation.
- **PS-3.6 Custody.** Missing bytes MUST be corruption unless a custody
  evaluation records withheld/sealed with signer and reason class.
  **[decide: withheld node kind vs custody rating — C3]** Erasure-law
  inputs MUST be anchored to primary texts before use.
- **PS-3.7 Roster & keys.** Only roster keys MAY sign interest/custody;
  interest signers MUST be human (circle 4). Key generation, custody,
  release signing: `[open — no key exists]`.
- **PS-3.8 Concurrence.** An LLM/witness claim remains testimony until a
  recorded human concurrence exists; systems MUST NOT display it as more.

## 4. Tenant / enclave conformance (L3 — designed, not built)

Source: [`docs/enclave-capital-introduction.md`](../docs/enclave-capital-introduction.md:1) (tenant contracts T1–T3 open,
`README.md:418`).

- **PS-4.1 Judgment ownership.** Tenant ICPs, rubrics, corrections, history
  are tenant property. They MUST train nothing shared and MUST NOT enter
  another tenant's retrieval.
- **PS-4.2 No surveillance.** Tenant activity MUST NOT feed product
  analytics, aggregate learning, benchmarks, or "service improvement" reuse.
- **PS-4.3 Operator bounds.** Operator reads of tenant strata MUST be
  attested and visible to the tenant. Outsourced operation MUST carry a
  path to self-operation; dependence MUST NOT be permanent.
- **PS-4.4 Exit.** Everything a tenant puts in MUST come back out complete,
  usable, and checkable. Exit is a conformance feature, tested like one.
- **PS-4.5 Isolation.** Per-tenant addressing/encryption and canary
  isolation tests MUST be decided and held before tenant ingestion.
  **[decide blob area — C5]** No private fields in shared nodes.
- **PS-4.6 Fairness as service term.** Queue/priority effects across tenants
  MUST be explicit service terms, never emergent starvation. Any operator
  "take" (fee, data, priority) MUST be a named service term; unnamed takes
  are non-conforming. *(Maker–taker clause; economics otherwise ABSENT.)*
- **PS-4.7 Granular actors.** Speaking, deciding, and filing units MUST be
  modeled as distinct actors where a tenant's counterparties have them.

## 5. Commons conformance (L4 — aspirational)

- **PS-5.1 Opt-in contribution.** Material enters a commons only by a
  deliberate, attributable act of its maker, per item or per class.
  Cross-tenant learning without that act is non-conforming.
- **PS-5.2 Rights discipline.** Sources whose terms bar redistribution MUST
  be held as digest + URL only, with terms recorded at fetch time
  (`sources/MANIFEST.tsv` practice; cf. 4 of 9 Ai2 citations).
- **PS-5.3 Public means rebuildable.** A commons claim set is "public" only
  if a stranger can rebuild and verify it from published bytes + this
  standard, on more than one platform, with an accessible text-first
  surface (P4/P5/P9/P14 held). Until then use "published draft."
- **PS-5.4 Upstream reciprocity.** If an endowment/payout exists, its
  derivation (dependency list × maintainers × weights) MUST be
  reproducible and weights MUST be signed interest decisions; unclaimed
  funds escrow, never revert to the operator. Formula and amounts:
  **[open — C4]**.

## 6. Non-claims (anti-conformance traps)

An implementation or publication MUST NOT claim, on the basis of this
skeleton's sources: distributed consensus/replication; fault tolerance or
durability (S5/S6); real-time service; semantic truth of claims;
cryptographic tenant privacy; any market size, price, or take rate;
authoritarian-resistance properties beyond PS-3.3/PS-4.2 mechanisms once
held. Each requires new evidence ingested as claims and a held check.

## 7. Promotion path (skeleton → binding standard)

1. Reconcile C1–C6 (white paper §8); re-run adversarial review.
2. For each clause to promote: name it in the module README, add the
   enforcing check + assumption-register row in the same commit.
3. Second implementation verifies same roots (PS-1.10) on a second platform.
4. Write the Praxis license or state MIT OR Apache-2.0 as final.
5. Version as `PS 1.0` only when L0–L1 are `held` end-to-end, including the
   negative suite (L6) and a fresh-clone run (L9).
