# Anthropic PBC

A public, versioned, cryptographically verifiable working paper:
**Anthropic PBC** — a counterpoint to Anthropic's
2026 Public Benefit Report, read against its S-1 and judged by Anthropic's own
(CC0) Constitution.

- **Read it:** [`docs/anthropic-contrapunctus.md`](docs/anthropic-contrapunctus.md)
- **Sign on or dispute it:** [`docs/contrapunctus-attest.md`](docs/contrapunctus-attest.md)
- **How the claims were checked:** every load-bearing quote is verified
  byte-exact against the primary filings with the Descartes verifier.

## Canonical version

    paper:   docs/anthropic-contrapunctus.md
    version: v0 (2026-11-03)
    blake3:  698b6c6785961b566e27dbf6306707ec530b4ba6e9f3823b6a99b3b42504dcea
             (provisional — refreshes when the title is finalized)

Recompute it yourself: `b3sum docs/anthropic-contrapunctus.md`.

## DOI

    (minted by Zenodo on the first GitHub release — the concept DOI goes here)

## What's in here

- `docs/anthropic-contrapunctus.md` — the paper (§0 rubric … §9 open questions, appendices).
- `docs/contrapunctus-attest.md` + `docs/contrapunctus-attestations/` — the
  sign-on / dispute protocol, the dispute-equal ledger, `allowed_signers`, and `verify.sh`.
- `docs/praxis-white-paper.md`, `docs/praxis-standard.md`, `docs/descartes-spec.md`,
  and the primitives (`circles`, `epistemics`, `primitives`, `strictness`) — the
  method the paper argues from.
- `docs/contrapunctus-compliance-review.md` — the RIA compliance assessment.
  *(Decide whether this belongs in the public version — see the note the author left.)*

## License

Text licensed **CC BY 4.0** (see `LICENSE`) — reuse with attribution. Quoted
excerpts from Anthropic's filings and Constitution, from SEC/court records, and
from cited third-party works remain under their own terms.

## Author

Sloane Ortel · ORCID [0009-0000-8491-1589](https://orcid.org/0009-0000-8491-1589) · affiliation: Ethical Capital.
Personal research. It is not published on, or by, Ethical Capital's platform, and
the author derives no economic benefit from it.
