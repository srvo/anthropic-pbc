# Attestation ledger — Contrapunctus

Signed endorsements, disputes, and amendments of the Contrapunctus working paper.
Protocol and instructions: [`../contrapunctus-attest.md`](../contrapunctus-attest.md).

Each entry is three files with the same basename, plus one line in `allowed_signers`:

    <stance>-<signer-slug>.txt       the record (stance / version hash / statement)
    <stance>-<signer-slug>.txt.sig   the SSH signature (namespace: contrapunctus)
    <stance>-<signer-slug>.pub       the signer's public key (also published at their domain)

`stance` is one of `endorse`, `dispute`, `amend`. Disputes sit in the same ledger
as endorsements and are never removed.

## Current paper version

    v0 (2026-11-03)  blake3:698b6c6785961b566e27dbf6306707ec530b4ba6e9f3823b6a99b3b42504dcea

## Ledger

*(empty — be the first to sign on, or the first to dispute.)*

| stance | signer | version | date | key bound at |
|---|---|---|---|---|
| — | — | — | — | — |

## Verify

    ./verify.sh

Checks every record in this directory against its signature and `allowed_signers`,
and reports `ok` / `FAIL` per record. A green run proves the signatures are valid;
confirming each key belongs to the organization it names is the separate,
published-at-their-domain step described in the protocol.
