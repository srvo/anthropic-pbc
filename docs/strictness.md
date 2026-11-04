# Is this the strictest standard?

> **Copy.** This document comes from the Praxis/Descartes project and describes that project, not this repository. Relative links and code paths (`src/`, `claims/`, `sources/`, `Cargo.toml`, ...) point into that project and do not resolve here, except links to the other copied docs in this folder.

Source: `sources/llm-witness-strictness.md`, an LLM text Sloane pasted on
2026-11-02 (model unknown). Its claims and the checks against them are in
`claims/strictness.tsv` (W = witness, K = check, S = verdict), and the loop
ingests them like any other claims.

## The point that holds

CFA Standard I(A) settles a conflict between rules by picking "the more
strict" one (K12). That works only when the rules can be ranked by strictness.
When two rules constrain different things, such as isolation and freshness, or
determinism and time, no ranking exists, and "the more strict" has no meaning.
Choosing between such rules is a judgment, and a judgment needs a person and a
record (S7). The witness's three gates find these cases:

1. **Null set.** The two rules cannot both be satisfied.
2. **Second-order cost.** Tightening one rule quietly loosens another.
3. **Worst-off party.** Someone the author doesn't think about pays for the
   rule.

## What the witness got wrong

| Claim | Finding | Row |
|---|---|---|
| `forbid(unsafe_code)` proves the binary has no undefined behaviour | **False.** The lint covers one crate. blake3, curve25519-dalek, sha2 and zeroize all contain `unsafe`. | S1 |
| Descartes already forbids `unsafe` | **False when pasted.** Our source had none, so the lint is now on and costs nothing. | S2 |
| Zero C toolchains | **Partly.** No C is compiled, but the `cc` driver crate is built as a blake3 build dependency. | S3 |
| bwrap sandbox | **Not verified.** bwrap is Linux-only and has never run here; the darwin path uses sandbox-exec. | S4 |
| A resolver rejects PRs that add unaudited crates | **False.** No such gate exists, and cargo-vet is not built. | S5 |
| ML-DSA signatures are about 40 KB | **False.** FIPS 204 gives 2,420 / 3,309 / 4,627 bytes; the ~50 KB figure is SLH-DSA-256f. **Not anchored:** FIPS 204 is 3.3 MB and waits on the payloads-in-git decision (C5). | W6 |
| Erasing on request violates 204-2, and retention violates privacy law | **False for Utah law.** The Utah privacy act exempts financial institutions under Gramm-Leach-Bliley (K15). Regulation S-P requires secure disposal, not deletion on request. That was checked by a research agent and is **not anchored** here. What remains is a conflict with whatever the firm promises voluntarily. | S9 |
| 204-2 and R164-5-1 set a five-year floor | **True.** R164-5-1 adopts 204-2 by reference. | S8 |
| Offline builds need an out-of-band advisory check | **True.** The witness's own check 2 contradicts it: that check fires even after `audit.sh` exists. | S6 |

The witness's Rust code does not compile, because `StrictnessResolver` is
never defined (K10). It also hard-codes its findings instead of testing for
them (K11). We don't adopt it.

Firm references, checked in monocloud and **not ingested here**:

- **Matches:** §6.16 (technology duties) and §6.14 (seven-year recording
  retention) match. AI Governance Principle 1 is real.
- **Mismatches:** §4.4 is vendor oversight and has no 15% threshold. §3.1 and
  §3.3 are numbered differently from what the witness cites.
- **Draft only:** the Data Retention Policy's sealed-original and
  derived-surface split exists only in draft.

## The gates, run on Descartes's own standards

### Collisions

**C1. Doubt first vs. run on every chip (principles 1 and 5).**
Failing closed on every missing gate would shut out any machine without
sandbox-exec, bwrap, cargo-deny or tesseract. The loop therefore runs and
records what it skipped (K5). **Gap found and fixed today:** a skipped
fidelity check left no trace in the artifact. The artifact now carries a
`fidelity checked|skipped` row.

**C2. Offline build vs. advisories (second-order).**
Resolved in structure, since `stage1/audit.sh` is separate from the loop (S6).
**Gap:** nothing records which advisory database the last audit checked
against, so "audited" has no date or version.
**Proposal:** `audit.sh` writes the advisory-db commit hash to a tracked
artifact. That records which version was checked without putting wall-clock
time in content.

**C3. Immutable store vs. erasure (null set).**
The verifier treats a missing object as corruption (K7). For client records
no law forces erasure (S9). Erasure still matters in two cases:
- the firm promises deletion voluntarily;
- an ingested document carries third-party personal data the firm decides
  not to keep.

Neither case has been checked against a specific obligation.

The store is already a rebuildable projection, so erasure means removing the
source and rebuilding. Every claim quoting that source then fails
verification.
**Needs a decision:** a `withheld` node that keeps the digest, drops the
bytes, and records who authorised the drop. The verifier would accept
"withheld by attestation" and still reject "missing".

**C4. Determinism vs. retention clocks.**
204-2 counts from fiscal year end (K13), but Descartes forbids time in hashed
content. **Resolution:** time belongs to an attestation or an external record
about a node, never inside the node. Not built.

**C5. No raw payloads in git vs. circle 0.**
Circle 0 needs the original bytes. The Iroh PDF cannot be fetched again, and
FIPS 204 was left out because of its size. **Open since the four decisions.**

**C6. `-D warnings` placement (second-order).**
In `Cargo.toml` it would make old source fail on any newer rustc that adds a
lint, which breaks principle 4. It is in the loop instead, against the pinned
toolchain.

### Worst-off parties

**R1. Testimony.**
Evidence must be a unique, byte-exact quote (K9). Actors who produce text,
such as companies, courts and regulators, can be cited directly. People whose
account exists only as speech or photographs cannot be cited until someone
transcribes them. This is the witness's "evidentiary paralysis" point, and it
applies to this design.

The circles mitigate it: a transcript enters at circle 2 or 3, with its
lossiness stated, and is not excluded. **Not built:** an audio or image
ingestion path.

**R2. The operator on old hardware.**
The loop asks for rustup, mise, poppler and tesseract. C1's record-and-run
behaviour keeps that operator in, at a recorded lower assurance.

**R3. People named in ingested documents.**
Anyone can attest to a claim, but a subject has no way to contest one. **Not
designed.**

## No resolver yet

A collision does not need a new engine. It can be stored with the node kinds
we already have:

1. Two claims that conflict.
2. A claim resting on both that states the collision.
3. A human's attestation of the resolution (circle 4).

C3's `withheld` node is the only new kind this review justifies.
