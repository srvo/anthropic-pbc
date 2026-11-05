# Primitives

> **Copy.** This document comes from the Praxis/Descartes project and describes that project, not this repository. Relative links and code paths (`src/`, `claims/`, `sources/`, `Cargo.toml`, ...) point into that project and do not resolve here, except links to the other copied docs in this folder.

Every open problem so far reduces to three needs: say what is true, say who
decided, and say whose interest the decision served. This document proposes
how to express all three with the node kinds we already have, plus two
changes:

- one edge (`against`);
- building the evaluation node, which `docs/epistemics.md` designs but which
  doesn't exist yet.

## The rule

**When rules conflict, resolve in the client's interest.** This is the rule
Sloane was taught at CFA Institute. It also fixes the defect in Standard
I(A)'s "more strict" test (`docs/strictness.md`): strictness can't rank rules
that constrain different things, but the client's interest can.

The rule needs two tie-breaks, and both are proposals:

1. **Reversibility.** When the client's interest is unclear, prefer the action
   that can be undone. Retaining sealed bytes can be undone; destroying them
   cannot.
2. **Visibility.** Never resolve a conflict silently. A hidden resolution
   takes the client's ability to object.

## The primitives

### What exists

| Kind | Holds | Meaning |
|---|---|---|
| artifact | bytes, by digest | What was received. Circle 0. |
| claim | statement, witness, quoted evidence, `supports` | What someone says is true, and why. |
| derivation | input, tool, args, output | What a tool turned into what. |
| attestation | signer, subject | Who stands behind a node. |
| snapshot | members | What one run saw. |

### The two changes

**A. `against` on claims and evaluations.**
Today a claim can only list what supports it, so the graph can only build up
agreement. Neither a contested claim nor its contest can be written down, and
ACH needs both. With `against`, any claim can name the claims it opposes.

**Conflict** then has a definition the verifier can check: two claims, either
of which is against the other.

This change applies to the claim node, so it changes the ids of every claim
that uses `against`. Claims that don't use it keep their ids if the field is
omitted when empty.

**B. Evaluations, as designed in `docs/epistemics.md`.**
An evaluation has this shape:

```
evaluation { framework, subject, rating, rests_on, witness }
```

A framework is an ingested file under `frameworks/` that lists the ratings it
allows. Every judgment the system makes then has the same shape: a rating,
under a named version of a framework, resting on claims, signed by whoever
stands behind it.

### Everything else is a framework

What other designs would add as new machinery, these primitives express as a
framework file plus evaluations:

| Need | Framework | Subject | Ratings | Signer must be |
|---|---|---|---|---|
| Resolve a conflict | `interest` | the conflicting claims | which side, and which party it serves | a human (circle 4) |
| Hold or drop bytes | `custody` | an artifact | `held`, `sealed`, `withheld` | an authorised human |
| Record a gate outcome | `gates` | a run's snapshot | `pass`, `fail`, `skipped`, `not-applicable` | the loop (witness), checkable |
| Source reliability | `admiralty` | a claim | A–F × 1–6 | an analyst |
| Fitness to use | `use-policy` | a snapshot, as of a reference | `fit`, `unfit` | a human or a stated rule |

Four verifier rules follow from these:

1. **A missing blob is corruption** unless an attested `custody` evaluation
   rates it `withheld` or `sealed`. The digest stays, so circle 0 survives:
   anyone holding the bytes can still prove they are the original.
2. **A conflict with no attested `interest` evaluation is reported as
   unresolved.** It is not an error, but it is never silent.
3. **Every gate the loop runs produces a `gates` evaluation, including
   `skipped`.** The stage 1 artifact becomes a projection of these.
4. **Only keys on the roster may sign** `interest` and `custody` evaluations.
   The roster is an ingested artifact, so changing it leaves a record.

### Time is an input, never a sample

Facts carry no clock. Anything that depends on time (fiscal year end, which
advisory database was current, when a signature was made) enters as a
recorded input: a claim or attestation written once and tracked, then
reproduced byte for byte. Determinism forbids *sampling* the clock during a
derivation. It does not forbid *recording* a time a witness asserts.

"Is this fit to touch client data today?" is a `use-policy` evaluation made at
the time of use, against an as-of reference such as an advisory-db commit.
The facts underneath it stay timeless.

## Checking the primitives against the cases

Each case from `docs/strictness.md`, resolved without new kinds:

| Case | Expressed as | Resolution in the client's interest |
|---|---|---|
| Missing sandbox or tool (C1) | `gates`: `skipped` | Run and say so. The client keeps the work and learns its assurance level. |
| Advisory freshness (C2) | derivation over an advisory-db commit, then `use-policy` | Builds stay offline. Use on client data requires a recent audit. |
| Erasure (C3) | `custody`: `sealed` or `withheld` | Seal the original, drop the derived copies. Reversible, and it keeps the client's record. |
| Retention clocks (C4) | the fiscal-year claim as a recorded input | No clock inside any node. |
| Payloads in git (C5) | `custody`: `held` by a named custodian | Git is one custodian among others. The digest is the identity. |
| Testimony (R1) | audio artifact, then a transcription derivation, then quotes | The transcript enters at circle 2 or 3 with its loss stated. It is not excluded. |
| Named people contest (R3) | a claim `against` the claim | Anyone can contest, and the contest stays visible. |

## The paste on key custody, SSDF and seams, read through these primitives

These items are not yet ingested as a witness, and the facts in them are not
checked.

- **OpenBao key custody.**
  - This fits the primitives without changes: the signer is still a
    `did:key`, and a `custody` claim states where its secret lives
    (non-exportable transit key, unseal shares) without ever containing the
    secret.
  - Descartes needs only `sign` to accept an external signer.
  - Who holds each unseal share is a governance decision for you. It goes on
    the roster with your attestation, not in code.
- **SSDF.** It becomes `frameworks/ssdf.tsv` with `gates` evaluations against
  it, so a pass is computed from those evaluations rather than stored as a
  `bool`. The paste's practice-to-principle mapping needs checking against SP
  800-218 before it is ingested. For example, I believe PO.5 covers secure
  development environments, not continuity, but I haven't verified it.
- **Seams telemetry.** The `SeamEvent` struct breaks two rules:
  - `timestamp_unix` samples the clock inside a record;
  - `f64` and `f32` fields are values canonical encoding refuses.

  Measurements are observations: integer units, recorded as derivation
  outputs. Joule and carbon figures are estimates, so they are circle 3 claims
  with their method stated. Network egress needs no telemetry, because the
  sandbox probe already proves it.

## Build order, if accepted

1. `frameworks/` and the evaluation node, plus verifier checks: ratings come
   from the framework, and `rests_on` must exist.
2. `against` on claims, plus the unresolved-conflict report.
3. The `gates` framework. The loop emits evaluations, and the stage 1 artifact
   becomes their projection.
4. The `custody` framework and verifier rule 1.
5. The roster and verifier rule 4.
6. `interest`. At first it holds only what you sign, with no automation.

## Bad decisions, revisited

Principle 12 means the graph must be able to hold a mistake and its
correction side by side. No new primitive is needed for that:

- A decision is an `interest` (or `admiralty`, `use-policy`) evaluation
  signed by a person.
- When the outcome is known, it enters as claims, such as returns or later
  findings.
- A revisit is a new evaluation that rests on the outcome claims and carries
  `against` the original. The original stays. Nothing is overwritten.
- Learning from decisions means querying for evaluations that carry
  `against`, alongside the outcomes that prompted them. This becomes a
  framework comparison (`docs/epistemics.md`) once there are enough of
  them. Running that search automatically requires explicit opt-in.

## Received attestations

A company's statement about itself, such as a supplier code or a response to
a screening finding, enters like any other witness:

1. Its document is an artifact.
2. A claim quotes it, with witness `org:<name>`. If the company signed it with
   a key, an attestation records that too.
3. When it disputes our claim, the two claims carry `against` each other.
   The verifier reports the pair as an unresolved conflict until an
   `interest` evaluation resolves it.
4. The company's interest in the outcome is rated by `admiralty`, not
   handled by excluding its statement.

A person named in a claim contests it the same way.

## Answers to the pasted decision memo (2026-11-02)

How each answer maps onto these primitives:

- **Withheld: yes.**
  - It becomes a `custody` evaluation with rating `withheld` or `sealed`, not
    a separate node kind:
    - the memo's `tombstone_type` becomes the rating;
    - `authority_ref` becomes `rests_on` claims that quote the authority;
    - `authorizer_did` becomes the attestation signer.
  - Two departures from the memo:
    - The signature does not cover a timestamp. If the time matters, it goes
      in as a recorded claim (time is an input).
    - The `ClientForgetAuthorized` reason stays, but `docs/strictness.md` S9
      found no statutory right to be forgotten for a Utah adviser. It is a
      voluntary commitment and should be described as one.
- **Payloads out of git.**
  - Every source is listed in `sources/MANIFEST.tsv` by digest and size,
    plus one of: a URL to fetch it from, or a named custodian (`held`) for
    sources that have no upstream URL.
  - The bytes live in `.descartes/sources/`, which git ignores.
  - The loop checks hashes only for bytes that are present, and records
    `skipped` for the rest as `gates` evaluations.
  - Moving the PDFs already committed out of git changes the stage 0
    inventory, but not the graph root.
  - **Not built:**
    - R2 sync, through the `bws run` and rclone guardrails;
    - the offline archive.
- **Advisory freshness.** `audit.sh` writes the advisory-db commit to a
  tracked file. The loop checks only that the file is well formed, which
  needs no network and no clock.
- **Retention clocks.**
  - Fiscal-year-end and the retention authority enter as claims.
  - "Retain until" is a derivation from them (FYE + 5 years, or 7 years for
    §6.14 recordings), so it is computed and never typed in.
  - The memo's separate `retention_events.tsv` is not needed.
- **Contest (R3).**
  - The memo's `rebuttals.tsv` and its `DissentRecorded` state are claims
    carrying `against`, plus the unresolved-conflict report. Both already
    fit the primitives.
  - One correction: Bao byte-range proofs are not built. Evidence today is a
    quote plus its BLAKE3 slice digest, checked against the whole artifact.
- **Deadlocks.** The memo's `decisions/deadlocks.tsv` is also the
  unresolved-conflict report. Its "FiduciaryResolutionReceipt" is an
  attested `interest` evaluation.
- **One fact to check.** The memo puts the 15–20% revenue threshold at
  screening-policy §4.4. The earlier check of monocloud found no such
  threshold in `screening-policy.md` or in Written Procedures §4.4. This
  needs a source before anything cites it.
