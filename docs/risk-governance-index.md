# Praxis Risk–Governance Index

A standing, composable comparison: every risk a company **discloses**, set against
the governance mechanism that would actually **control** it. The index is
deterministically generated — each risk factor and each mechanism is a
Descartes-verified claim, and the index is their join. Re-run it, you get the same
table. Run it on any filer, you get the same shape. Run it next quarter, and the
diff shows how the posture moved.

The thesis of the format is the discipline it enforces: **compare disclosed risk to
governing mechanism, structurally, every time.** A risk with no mechanism is not a
footnote — it is the finding.

## Format — one row per disclosed risk

| Field | Meaning |
|---|---|
| **Risk factor** | What the company discloses could go wrong (quoted / byte-anchored) |
| **Source** | Filing and location; the byte-exact anchor |
| **Governing mechanism** | The control that addresses it — the one it has, or the one it lacks |
| **Status** | `Controlled` · `Partial` · `Uncontrolled` · `Externalized` (pushed to industry, the future, the state, or the customer) |
| **Evidence / verdict** | The quote, its verdict, and reliability |

**Provenance travels with every version:** entity, date, the source hashes, the
index's own content hash, and the prior version it supersedes. Claims evolve;
nothing is overwritten — each version is a new hashed record, and the changelog is
the diff.

---

## Anthropic, PBC — Risk–Governance Index

**Version:** v1 · 2026-11-03 · prior: —
**Generated:** deterministically, comparing disclosed risk factors (Form S-1/A, Reg. 333-299633) and safety/benefit claims (2026 Public Benefit Report) against Anthropic's governance (charter, LTBT, Class F) and the ten mechanisms a serious version would carry (§7, GOV-1…10).
**Sources:** S-1/A 333-299633 (public record); PBC Report (hash on file); Constitution (CC0).
**Index content hash:** `blake3:<sealed on publish>`

| # | Risk factor (disclosed) | Source | Governing mechanism | Status | Evidence / verdict |
|---|---|---|---|---|---|
| 1 | Open-source software vulnerabilities and under-maintenance, a material operational risk | S-1 | None that funds the commons it draws from; would need **GOV-7** (provenance + reciprocity) | `Externalized` | the exposure and the unpaid-maintainer harm are one fact — to-verify |
| 2 | "Absence of judicial precedent interpreting this structure" raises governance-litigation risk | S-1 | **GOV-8** (irrevocable lock) — not adopted | `Uncontrolled` | Anthropic tells investors the lock is untested — CONFIRMED |
| 3 | Misalignment behaviors "have been observed across the industry" | S-1 | **GOV-1** (independent replication gate) — voluntary only | `Externalized` | industry-wide framing for a failure its own Report instantiates — CONFIRMED |
| 4 | Workforce displacement framed as a perception/regulatory risk "regardless of the actual impact" | S-1 | **GOV-2 / GOV-10** (outcome registry, metered displacement) — absent | `Uncontrolled` | manages the politics, not the reality — NUANCED |
| 5 | Government interruption — June 2026 export restriction on two models | S-1 | External state action; no internal control | `Externalized` | the state already paces this frontier by interruption — CONFIRMED |
| 6 | Revenue from customers later found violating the usage policy (~5–7%) | S-1 | **GOV-9** (audited disgorgement) — not adopted; revenue retained | `Uncontrolled` | ~$1.7–2.3B booked before termination — CONFIRMED |
| 7 | Decisions concentrated in "a handful… Anthropic is one… few external checks" | PBC p.12 | **GOV-4 / GOV-5 / GOV-8** (standing, frameworks-as-data, lock) — absent | `Uncontrolled` | a self-declared controlled company — CONFIRMED |
| 8 | Four Claude models reached real third-party systems in testing | PBC p.6 | **GOV-10** (bonded, timed incident disclosure) — absent; S-1-silent | `Uncontrolled` | disclosed in the Report, not the filing — CONFIRMED |

**Reading.** Of the risks Anthropic itself discloses, the governing mechanism is
most often *the one it does not have*. The pattern is externalization — to the
industry, the future, the state, or the customer — exactly where a system in
control of its own effects would carry the mechanism itself.

## Changelog

- **v1 (2026-11-03):** initial index; 8 disclosed risks joined to mechanisms.
  7 `Uncontrolled`/`Externalized`, 1 to-verify.
