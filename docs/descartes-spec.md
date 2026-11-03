# Descartes

Descartes is part of Praxis, an open-source release from Ethical Capital.
Its license today is `MIT OR Apache-2.0` (`Cargo.toml`). A Praxis license
has not been written yet.

**Objective.** Build a public epistemic commons: a set of claims, each of
which quotes its evidence byte for byte, stored in a content-addressed graph
that anyone can re-verify from the bytes alone.

**Method.** Assume nothing that has not been checked first. Every check
leaves a deterministic artifact behind. Everything that enters the repo is
ingested into the graph, and the graph is rebuilt and re-verified from
scratch on every run.

**Template.** Descartes is the template every Ethical Capital module starts
from. A module made from it keeps this README's section order (§0) and
replaces the content. A section with nothing in it yet still appears, with
the line `none yet`.

This file is the specification. It states what the code must do and the
constraints on it, in order, and every statement is meant to be falsifiable.
Each rule names the check that enforces it, or is marked **open**. If this
file and the code disagree, one of them has a bug. Fix whichever is wrong,
and update this file in the same commit. Files under `docs/` are design
notes and records. They bind nothing until a rule here names them.

Contents:
0. The template standard
1. Run it
2. Constraints
3. The machine, in pseudocode
4. The graph
5. The loop
6. Supply chain and isolation
7. Signing
8. From sources to claims
9. Contracts and their status
10. Work order
11. Not part of Descartes

## 0. The template standard

Every module's README has these sections, in this order:

| § | Section | What it must state |
|---|---|---|
| — | Header | name; "part of Praxis"; license; objective in one sentence; method in three |
| 0 | Template standard | this table, unchanged, so each module carries the standard it follows |
| 1 | Run it | the exact commands, and what a plain run versus an accepting run does |
| 2 | Constraints | numbered rules, each naming its check or marked **open** |
| 3 | The machine | pseudocode for every operation the code performs |
| 4 | Data | every stored format, with exact keys or columns |
| 5 | The loop | each step's guarantee and what it compares against, plus the assumption register |
| 6 | Supply chain and isolation | dependencies with their governance, build isolation, network steps |
| 7 | Signing | keys, what gets signed, and where signatures live |
| 8 | Inputs | how outside material becomes data the module trusts |
| 9 | Contracts | the table: contract, enforced by, proved by, status |
| 10 | Work order | open contracts, ordered by what blocks a passing loop |
| 11 | Not part of this module | design notes, records, and what is out of scope |

Rules for every module:
- Names people only where they act as witnesses or signers. A use case is
  named by its role (for example an **enclave**, a tenant running on the
  shared graph), never by a person's name.
- Has no standalone governing document outside its README. `docs/` holds
  design notes and records, and they bind nothing until the README names
  them.
- Has one source of truth per value. If two files pin the same thing, one is
  generated from the other or checked against it.

## 1. Run it

```sh
sh stage0/verify.sh          # assumptions about the shell environment only
sh stage1/loop.sh            # check: every result must equal what is committed
sh stage1/loop.sh --accept   # write: regenerate the expectations, then review `git diff artifacts/`
git config core.hooksPath .githooks   # once per clone
```

A plain run only compares results, and it fails on any difference from what
is committed. `--accept` is the only way expectations change, and the diff
under `artifacts/` is the change you are accepting.

## 2. Constraints

These come from [permacomputing](https://permacomputing.net/principles/) and
[FAIR data](https://en.wikipedia.org/wiki/FAIR_data). We adopt neither
wholesale. Each constraint is written so that a check can enforce it.

| # | Constraint | Enforced by |
|---|---|---|
| P1 | **Doubt first.** Nothing is trusted until it is checked, and the checker is checked first. Stage 0 tests its SHA-256 tool against known vectors before it hashes a file; the BLAKE3 crate is tested against the official vectors before the loop trusts it. | A002, A013 |
| P2 | **Smallest foundation.** Each stage depends on the least it can. Stage 0 needs only POSIX `sh`. We skip a dependency when the problem is small enough to solve without one. | three direct crates (§6) |
| P3 | **Determinism.** The same inputs give the same output bytes. No timestamps, hostnames, usernames, random ids or locale-dependent ordering in anything that gets hashed. Time is recorded beside an artifact, never inside it. | A007, A009, A015 |
| P4 | **Inspectable with base tools.** Someone 20 years from now, holding only POSIX tools, can read and verify every artifact: plain files, line-oriented or documented formats, BLAKE3 checkable with `b3sum`. | **open** for later stages |
| P5 | **Run on every chip.** No architecture is assumed. | **open**: only darwin/arm64 has run |
| P6 | **Dependencies are judged by their governance**: who controls each one, its bus factor, its license, and the open standard that could replace it. | **open**: no `docs/dependencies.md` register or check |
| P7 | **FAIR.** Findable by digest, accessible as plain files, interoperable through open formats, reusable because every artifact records the stage and script that produced it. | partly, through §4 and §5 |
| P8 | **Privacy is part of determinism.** No artifact records who ran it or where. | path and identity grep in the binary; boundary check |
| P9 | **Accessibility.** Every human-facing output passes accessibility review. Plain text comes first, and anything visual degrades to text. | **open** until a human-facing surface exists |
| P10 | **Governance outlives individuals.** Everything needed to rebuild trust from zero lives in this repo. | this file; the loop |
| P11 | **Conflicts resolve in the client's interest.** Strictness cannot rank rules that constrain different things. When the interest is unclear, choose the reversible action, and never resolve a conflict silently. | **open** until evaluations exist (`docs/primitives.md`) |
| P12 | **Decisions may be wrong, and are never overwritten.** A revisit is a new node that stands against the old one. | write-once store (S1) |
| P13 | **Everyone who speaks is a witness.** Analysts, agents, companies and the people named in a document all enter as claims. A dispute is recorded, never suppressed. | **open** until `against` exists |
| P14 | **The graph never depends on the tool that wrote it.** The formats and verifier rules in §3–§4 are enough to re-implement a verifier from this file alone. The binary only makes the checks faster. | **open**: no second implementation, and no check that one is possible |
| P15 | **Measure the cost of rebuilding.** Every run records wall time, store size and node counts next to the graph, never inside it. A cache or energy budget is a recorded decision based on those numbers. | **open** |
| P16 | **No heavier machinery than the problem.** No Nix or Bazel, no containers or microVMs for the loop's own tools, no daemon, server or database, and no plugin system before a second instrument exists. | by review |

## 3. The machine, in pseudocode

```
id(bytes)        = "blake3:" ++ lowerhex(BLAKE3(bytes))      -- one id space for blobs and nodes
encode(value)    = canonical JSON: no whitespace, keys sorted bytewise,
                   integers only (i128), minimal escapes, UTF-8
link(id)         = {"/": id}                                  -- IPLD DAG-JSON link shape

store:
  put_blob(b)   -> write_once(blobs/<ab>/<hex>, b)
  put_node(n)   -> write_once(objects/<ab>/<hex>, encode(n))
  write_once(p, b):
    if p exists: return ok if the bytes are equal, else "store corrupt"
    refuse a symlink in the area, shard or entry
    write a temp file (create_new, random name), fsync, re-check, rename

sign(subject, key) = Ed25519(key, "descartes-attestation-v2\n" ++ encode({kind, signer, subject}))
verify_sig         = verify_strict, lowercase hex only

verify_root(store, root):
  closure = everything reachable from root
  fail if any stored node or blob lies outside closure
  for n in closure:
    name == id(content); encode(parse(content)) == content
    exact keys for its kind; every link resolves to the right kind
    artifact:    the blob's size and sha256 match
    claim:       rests on something; each evidence slice lies inside its
                 artifact and re-hashes to slice_blake3; lists strictly sorted
    attestation: the signature verifies over the subject
  fail on any cycle

loop(tracked inputs) -> root:
  env -i, allowlisted variables only
  boundary(tree)                                 -- nothing secret or stray is in the tree
  stage0 --check   == artifacts/stage0/<os>-<arch>.tsv
  build twice, sandboxed, vendored, offline      -- the two binaries must be identical
  our sha256       == stage0's sha256, for every inventoried file
  re-run derivations, sandboxed                  -- output == committed derived/*
  ingest inventoried files + claims/*.tsv
  root  = snapshot(nodes this run produced)
  verify(store); rebuild into an empty store; root' == root; verify_root(root')
  results          == artifacts/stage1/<os>-<arch>.tsv, artifacts/loss/*   -- byte for byte
```

## 4. The graph

`.descartes/` is the store: plain files you can check with `cat` and `b3sum`.
It is a projection, not committed. The loop rebuilds it from tracked inputs:
code, `sources/`, `claims/` and `attestations/`. Git holds code, vendored
crates, manifests and the human-readable inputs, never the store. Any index
added later is a disposable cache, never a source of truth.

```
.descartes/blobs/<ab>/<blake3>     raw bytes, named by their BLAKE3 hash
.descartes/objects/<ab>/<blake3>   nodes, canonical JSON, named by the hash of that encoding
```

There are five node kinds. Each has an exact key set; a missing or extra key
is an error.

| Kind | Keys | The verifier checks |
|---|---|---|
| `artifact` | `blob`, `bytes`, `media_type`, `name`, `sha256` | the blob exists and its size and SHA-256 match |
| `claim` | `statement`, `witness`, `evidence` (each: `artifact`, `start`, `end`, `slice_blake3`), `supports` | it rests on something; each range is non-empty and inside its artifact; each slice re-hashes to its digest; `supports` links are claims |
| `derivation` | `input`, `output`, `tool`, `args` | both ends are artifacts and the tool is named. The loop, not the crate, re-runs the tool and requires identical output. |
| `attestation` | `subject`, `signer` (`did:key`), `signature` | the subject exists, and the signature verifies over `descartes-attestation-v2\n` plus the canonical `{kind, signer, subject}` |
| `snapshot` | `members` | every member is a node, sorted and unique |

For every node in the root's closure, the verifier also checks that:
- the file name equals the digest of the content;
- re-encoding gives the same bytes;
- no link dangles, and every link points to the right kind;
- the kind is known;
- the graph has no cycles.

Anything in the store that the root cannot reach is an error.

## 5. The loop

Each stage relies only on what an earlier stage checked and recorded.

| Step | Guarantee | Compared against |
|---|---|---|
| env | Re-runs under `env -i` and refuses any variable outside the allowlist, a forged `DESCARTES_ISOLATED`, or a visible global git or mise config | `stage1/env.sh` |
| 0 boundary | The tree holds no store, keys, `.env`, symlinks, hard links, oversized or compressed unmanifested files, home paths, or secret-shaped content | `stage1/boundary-allow.tsv` (each exception pinned by SHA-256) |
| 1 stage 0 | Every file's SHA-256 and size, and the base tool versions, match | `artifacts/stage0/<os>-<arch>.tsv` |
| 2 build | Two sandboxed, offline, vendored builds are byte-identical, mode 555, re-hashed before each later use, and free of home, temp, user or host paths | each other, then the `binary` row |
| 2b isolation | Seven probes fail inside the sandbox: TCP, home write, `~/.ssh` read, Unix socket, resolver, environment leak, `.git` read | `isolation_*` rows |
| 2c tests | BLAKE3 vectors pass; line and region coverage is 100% outside named exemptions, and there are no stale exemptions | `src/COVERAGE_EXEMPT.tsv` |
| 2d manifest | Every external source matches its recorded BLAKE3, and every file under `sources/` has a row | `sources/MANIFEST.tsv` |
| 3 cross-check | Our SHA-256 equals stage 0's for every inventoried file | stage-0 inventory |
| 3b derivations | Only allowlisted tools with a fixed argument shape run, sandboxed, and reproduce byte for byte | committed `derived/*` |
| 3c fidelity | Instrument digests and the colouring report reproduce | `artifacts/fidelity/*` |
| 4–6 graph | Ingest, snapshot, verify, rebuild into an empty store: same root, verified from the root | the `root` row |
| 8 compare | Every result matches byte for byte | `artifacts/stage1/<os>-<arch>.tsv`, `artifacts/loss/*` |

A check that cannot run records `skipped`, never `pass` (rule L5). A
`skipped` row differs from the committed expectation, so a plain run still
fails on it.

**Assumption register.** A new assumption gets an id, a check in the first
stage that relies on it, and a row here, all in the same change.

| ID | Assumption | Kind | Stage |
|---|---|---|---|
| A001 | Base utilities exist | asserted | 0 |
| A002 | The system SHA-256 tool reproduces known test vectors | asserted | 0 |
| A003 | `sort` under `LC_ALL=C` is bytewise | asserted | 0 |
| A004 | OS and architecture | observed | 0 |
| A005 | File names fit the artifact format; no symlinks or hard links; every file's digest and size | asserted and observed | 0 |
| A006 | Toolchain versions | observed | 0 |
| A007 | Artifact bytes are stable under re-sort | asserted | 0 |
| A008 | Our SHA-256 agrees with the stage-0 hasher on every file | asserted | 1 |
| A009 | Rebuilding the graph from empty gives the same root | asserted | 1 |
| A010 | Every node and blob in the root's closure verifies | asserted | 1 |
| A011 | Each derivation recipe reproduces its committed output | asserted (skipped if the tool is absent) | 1 |
| A012 | Fidelity instruments and the report reproduce from the source digest | asserted (skipped if the tools are absent) | 1 |
| A013 | The BLAKE3 crate reproduces all 35 official test vectors | asserted | 1 |
| A014 | The sandbox denies the seven probes | asserted (skipped with no sandbox tool) | 1 |
| A015 | Two builds into different directories are byte-identical | asserted | 1 |
| A016 | Every external file still matches the BLAKE3 recorded at fetch time | asserted | 1 |
| A017 | The binary carries its dependency list (`cargo auditable`) | asserted (skipped if the tool is absent) | 1 |
| A018 | The dependency policy (`deny.toml`) holds offline | asserted (skipped if the tool is absent) | 1 |

**Artifact rules.** Artifacts are line-oriented, tab-separated and sorted
bytewise. They contain no timestamps, hostnames, usernames or absolute
paths.

## 6. Supply chain and isolation

- **Three direct dependencies**, each pinned exactly, with `Cargo.lock`
  committed:
  - `serde`: typed structs to canonical bytes;
  - `blake3`: built `pure`, so no C or assembly, checked against the
    official vectors;
  - `ed25519-dalek`: attestations, checked against RFC 8032 vector 1.

  Our crate forbids `unsafe`. The dependencies do use it, so that lint is
  not a memory-safety proof for the binary. Canonical encoding, SHA-256, the
  store and the verifier are written here.
- **Vendored and offline.** All dependency source is committed in `vendor/`,
  and `.cargo/config.toml` replaces crates.io with it and sets
  `offline = true`. Adding a dependency is a deliberate online step: set the
  config aside, `cargo fetch`, `cargo vendor`, then restore the config.
- **Bare, pinned toolchain.** `rust-toolchain.toml` pins 1.99.0. The loop
  builds with `rustup run 1.99.0 cargo` from empty target directories.
- **Deny-default sandbox.** `stage1/sandbox.sh` runs every build, test,
  derivation and OCR step under `env -i` with a fresh `CARGO_HOME` and a
  scratch `HOME`. On darwin it applies `stage1/no-network.sb`:
  - reads are allowed only in the repo (not `.git` or `.descartes`), the
    toolchain, system paths and the Command Line Tools;
  - in the tools phase, reads are allowed in the instrument kegs as well;
  - writes go only to the run's scratch directory;
  - all sockets and mach lookups are denied.

  Each step runs in its own process group, which is killed when the step
  returns. The trusted binary is copied out of the sandbox's reach and
  re-hashed before every use. On Linux the equivalent is `bwrap`, which is
  untested.
- **Boundary.** `stage1/boundary.sh` refuses, reporting the rule and path but
  never the match:
  - the store, key files and `.env`, case-insensitively;
  - symlinks and hard links;
  - 64-hex key-shaped content;
  - files over 1 MiB, and compressed content, without a manifest row;
  - absolute home or temp paths;
  - credential patterns.

  Nothing overrides the boundary. `.githooks/` runs the staged copy before a
  commit. Hooks can be skipped, so the loop is the backstop.
- **Network steps are separate and deliberate:**
  - `stage1/audit.sh` checks RustSec advisories and records the database
    commit in `artifacts/audit/advisory-db.tsv`;
  - `stage1/fetch-sources.sh` fetches pinned upstream documents into
    `sources/` and records each one's BLAKE3 in `sources/MANIFEST.tsv`.

  The loop itself never touches the network.

## 7. Signing

Signatures are `attestation` nodes, kept apart from what they sign, so a
claim's id never depends on who signed it. Signers are `did:key`
identifiers.

```sh
descartes keygen                 # key at .descartes/identity.key (0600); prints only the did:key
descartes sign blake3:<id>       # appends subject, signer, signature to attestations/<did>.tsv
```

`attestations/*.tsv` is tracked, and the loop verifies every row before
recording it. Two kinds of key are planned:
- a **release key**, cold and off this machine, which signs release digests;
- a **node key**, which signs evaluations.

No key has been generated yet.

## 8. From sources to claims

1. **Derive.** A row in `derived/recipes.tsv` names the tool. The loop
   re-runs it and records a `derivation`.
2. **Witness.** An LLM, following `prompts/distill.md`, writes
   `proposals/<name>.tsv`. Leaves quote the text byte for byte; composites
   rest on other claims. The `witness` column names the model and the
   SHA-256 of the prompt.
3. **Check.** `descartes check FILE` reports every problem and writes
   nothing:
   - a quote that does not occur exactly once;
   - a claim with no evidence;
   - a dangling label;
   - a cycle.

   A failed claim fails every composite that rests on it.
4. **Accept.** A file with zero problems moves to `claims/`. Ingest is
   all-or-nothing per file.

The file format is six tab-separated columns:
`label rests_on witness statement path quote` (`src/claims.rs`). Evidence
paths must be relative, visible, free of symlinks and single-linked, and
inside the repo.

The verifier proves that a quote **exists**. It does not prove that the
statement **follows** from it. An LLM-witnessed claim is testimony until a
person concurs, and nothing records that concurrence yet.

Two more measures of what a step kept:
- **Fidelity** (`stage1/fidelity.sh`) colours each part of a derivation by
  the highest circle of assumption at which it is verified
  (`docs/circles.md`).
- **Coverage** (`descartes coverage`) reports how much of a source its claims
  anchor (`docs/epistemics.md`).

## 9. Contracts and their status

Status values:
- **held**: code blocks the break, and a test proves it;
- **code-only**: code blocks it, but nothing proves it;
- **partial**: some of the break is blocked;
- **open**: stated, not enforced;
- **decide**: the rule itself needs a decision.

These statuses were extracted from the working tree on 2026-11-02 and are
not yet confirmed by a passing loop and negative suite.

### Identity and encoding

| # | Contract | Enforced by | Proved by | Status |
|---|---|---|---|---|
| I1 | An id is `blake3:` plus 64 lowercase hex, and only that form parses | `src/lib.rs` `id_hex` | `lib::ids_are_blake3_prefix_plus_lowercase_hex` | held |
| I2 | One meaning, one encoding: re-encoding a stored node reproduces its bytes | `src/canon.rs` `is_canonical`; verify load | `canon::rejects_or_flags_non_canonical_input`; `graph::detects_non_canonical_node_even_with_correct_name` | held |
| I3 | No floats, raw bytes, duplicate keys, raw control characters or invalid UTF-8 reach a node | `src/ser.rs`, `canon::parse` | `ser::floats_and_bytes_are_refused`; `canon::every_parse_error_names_its_reason_and_offset` | held |
| I4 | Constructors sort and dedup their lists | `src/model.rs` | `model::constructors_sort_and_dedup_so_one_meaning_has_one_id` | held |
| I5 | Blobs and nodes share one id space with no domain separation. Kind safety rests on the store area and link-kind checks. | design | — | **decide** before any id is published |

### Store

| # | Contract | Enforced by | Proved by | Status |
|---|---|---|---|---|
| S1 | Write once: different bytes never overwrite an existing path | `store.rs` `write_once`, `check_existing` | `store::put_is_idempotent_and_get_round_trips` | held |
| S2 | Writes never follow a planted symlink | `create_new` with a random temp name; area and shard checks | `graph::write_once_does_not_follow_planted_symlinks` | held |
| S3 | Reads refuse a symlink anywhere on the path | `read_plain` (final component only) | `store::reads_refuse_a_symlink_in_place_of_a_file` | **partial**: symlinked shards and areas are followed, and the root is unchecked |
| S4 | Rebuilding into an empty store gives the same root | loop rebuild | `root` row | code-only |
| S5 | An interrupted or failed write never leaves the store unverifiable | nothing | — | **open**: an orphaned `.partial` (Ctrl-C, or a failed `rename` at `store.rs:79`) makes every later `verify` fail |
| S6 | A completed write survives a crash | `sync_all` on the file only | — | **open**: the directory is not fsynced after `rename` or after a shard is created. Each platform's durability level (crash-only, or power loss via darwin `F_FULLFSYNC`) belongs in the assumption register. |
| S7 | The store has one writer, the loop. Everything else writes to scratch or `proposals/`, and a run commits by writing its nodes, then the snapshot, then recording the root outside the store. | loop structure | — | code-only |
| S8 | An export is a plain closure (the root plus every store file it reaches), readable with no new code, and re-deriving its root reproduces the recorded root | nothing | — | **open**: no export exists |

### Signatures

| # | Contract | Enforced by | Proved by | Status |
|---|---|---|---|---|
| K1 | The signature covers the whole body except the signature, under a versioned domain | `sign.rs` `DOMAIN` (v2) | `sign::message_is_domain_plus_canonical_body`; `sign::v1_subject_only_signature_is_rejected` | held |
| K2 | One signature, one encoding | lowercase `hex_decode`, `verify_strict` | `graph::uppercase_hex_signature_fails` | held; small-order keys untested |
| K3 | A key file is 0600, never overwritten, never printed | `keygen`, `load_key` | `sign::load_key_refuses_group_or_other_bits` | **partial**: `load_key` follows symlinks; `keygen` zeroes the seed without `black_box` |
| K4 | Only verified rows for stored subjects get recorded | `attest` | `cli::attest_records_only_verified_rows_for_stored_subjects` | **partial**: `sign` doesn't check its subject and appends through symlinks |

### Verification

| # | Contract | Enforced by | Proved by | Status |
|---|---|---|---|---|
| V1 | The report covers the root's closure, and anything outside it is an error | `verify_root` | `graph::verify_root_reports_unreachable_nodes` | held |
| V2 | Exact key sets for every kind and for Evidence | `exact_keys` | `graph::every_kind_has_an_exact_key_set` | held |
| V3 | A claim rests on something, and every slice re-hashes | claim checks | `verify::claim_problems` | held |
| V4 | No cycles | depth-first search | `cycles_are_found_and_reported` | held |
| V5 | Attestations are verified only if a snapshot lists them | follows from V1 | — | **decide** |

### Claims ingestion

| # | Contract | Enforced by | Proved by | Status |
|---|---|---|---|---|
| E1 | Evidence paths are relative, visible, free of symlinks, single-linked and inside the repo | `claims.rs` `resolve_evidence_path` | `claims::evidence_paths_must_stay_inside_the_repo`; `claims::hidden_and_hard_linked_evidence_is_refused` | held |
| E2 | Evidence comes only from files in the stage-0 inventory | a comment only | — | **open**: a gitignored `target/` file qualifies |
| E3 | A quote occurs exactly once | `evidence_for_quote` | `graph::quote_must_be_unique` | held |
| E4 | Ingest is all-or-nothing per file | trial run into a scratch store | `cli::claims_ingest_all_or_nothing_per_file` | **partial**: a failure in the real run leaves partial writes |

### The loop

| # | Contract | Enforced by | Status |
|---|---|---|---|
| L1 | A plain run never writes its own expectations | `loop.sh` (only `--accept` writes) | held: on 2026-11-03 a plain run passed end to end on darwin-arm64; the root is in `artifacts/stage1/`, never here, because this file is itself ingested |
| L2 | The build is hermetic: `env -i`, vendored, offline, deny-default sandbox | `env.sh`, `sandbox.sh`, `no-network.sb`, probes | code-only; reads are too broad (§10 item 8) |
| L3 | Two builds are identical, and the binary carries no path or identity | build and grep | code-only |
| L4 | Derivations run only allowlisted tools with a fixed argument shape, sandboxed | `loop.sh` 3b | **partial**: standalone `fidelity.sh` checks recipes more weakly (a leading `-` passes; `output` is never checked) |
| L5 | A check that cannot run records `skipped`, never `pass` or `checked` | partly | **partial**: §10 item 6 |
| L6 | The negative suite proves each gate fires, at the gate it targets, and the unmodified control passes | `stage1/negative.sh` | **open**: the last run's control failed, and `run_case` accepts any failure |
| L7 | Commits pass the boundary check | `.githooks/` | **open** in this clone: `core.hooksPath` is unset, and history still holds `.descartes/` blobs |
| L8 | The toolchain that built is the one recorded | `rustc_binary` digest | **partial**: `librustc_driver`, std and cargo are not hashed; A006 reads rustc from PATH |
| L9 | A fresh clone can build, test and run the loop | git | **open**: files the scripts depend on are untracked (§10 item 2) |

### Enclaves (apply only once a tenant runs on a shared graph)

| # | Contract | Status |
|---|---|---|
| T1 | Private material never goes into a blob area shared across enclaves, because a bare BLAKE3 address reveals which digests exist. Use a blob area per enclave, or keyed addressing (HMAC or HKDF). | **open**, not designed in code |
| T2 | Shared nodes carry no fields private to an enclave. Enclave annotations are separate nodes that point at shared ids. | **open** |
| T3 | Canary nodes planted in one enclave can't be found from any other, or after a purge. | **open** |

## 10. Work order

Ordered by what stops the loop from working, then by what stops it meaning
anything:

1. ~~**Clear stage-0 drift.**~~ Done 2026-11-03: inventory re-accepted, and
   the loop passes in check mode.
2. **Commit the working tree as one unit (L9).** That includes:
   - `src/tests/*.rs`;
   - `stage1/{env,sandbox,coverage,boundary,negative}.sh` and
     `stage1/boundary-allow.tsv`;
   - `artifacts/audit/advisory-db.tsv`;
   - `sources/docs/law/*` and `sources/llm-witness-strictness.md`;
   - `claims/strictness.tsv` and `.githooks/`.
3. **Make interrupted writes recoverable (S5).** Keep temp files in a
   scratch area that `list` and `verify` ignore, and clean up on every error
   path.
4. **Make the negative suite prove something (L6).** Find out why the
   control fails, and make `run_case` require the targeted gate's message.
5. **Bind evidence to the stage-0 inventory (E2).**
6. **Close the paths where a failure or skip records as passed (L5):**
   - `fidelity.sh` records `checked` with no PDF recipe, or with
     `SB_KIND=none`;
   - an empty tool version is accepted silently;
   - `fidelity.sh:90` has no pipefail on `--write`;
   - `boundary.sh:195` ends with `find … || true`;
   - an unexpected llvm-cov format parses as no misses.
7. **One recipe validator for both scripts (L4).**
8. **Narrow the sandbox's reads (L2):**
   - all of the repo, including ignored files;
   - all of `/usr` and `/dev`;
   - every `sysctl-read`.

   cargo-deny runs unsandboxed and is not pinned by hash.
9. **Store and signing hardening:**
   - symlinks on the read path and the store root (S3);
   - `sign` checks its subject and refuses symlinks (K4);
   - `load_key` refuses symlinks (K3).
10. **Decide I5 and V5.** Settle the allowlist rule as well: this file says
    the allowlist can't change after the root commit, and also that a
    future change will need a signature.
11. **Durability (S6).** Fsync the directory after `rename` and after
    creating a shard.
12. **One pin per value.** Rust 1.99.0 is pinned in both
    `rust-toolchain.toml` and `mise.toml`. Check one against the other, or
    drop one.
13. **Fix stale code comments:**
    - `model.rs`, on the signed bytes;
    - `canon.rs`, "strict subset of JSON";
    - `claims.rs`, "case-insensitively" and "inventoried".
14. **Later:**
    - signed claims;
    - a human-concurrence node;
    - Linux and other architectures;
    - `cargo-vet`;
    - key generation and release signing;
    - the dependency register (P6).

## 11. Not part of Descartes

Design notes that bind nothing until a rule above names them:
- [`docs/primitives.md`](docs/primitives.md): evaluations, frameworks,
  `against`, custody, the roster;
- [`docs/circles.md`](docs/circles.md) and
  [`docs/epistemics.md`](docs/epistemics.md): fidelity and loss beyond what
  the code computes.

Records:
- [`docs/research-spike-permaculture-atomic.md`](docs/research-spike-permaculture-atomic.md), the source of P14–P16 and S6–S8;
- [`docs/enclave-capital-introduction.md`](docs/enclave-capital-introduction.md) and [`docs/research-spike-enclave-domain-landscape.md`](docs/research-spike-enclave-domain-landscape.md), the source of T1–T3;
- [`docs/adversarial-review-2026-11-02.md`](docs/adversarial-review-2026-11-02.md);
- [`docs/strictness.md`](docs/strictness.md);
- [`docs/history.md`](docs/history.md);
- [`docs/review-secure-alternatives-to-iroh.md`](docs/review-secure-alternatives-to-iroh.md).

Out of scope entirely:
- performance gates and allocator accounting;
- release channels;
- client-domain work;
- the commons strategy material.
