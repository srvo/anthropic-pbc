# Sign on, or dispute — the attestation protocol

This working paper is meant to gain value through disagreement. Any organization
or individual can publicly **endorse**, **dispute**, or **amend** it with a
cryptographic signature bound to the exact version. Endorsements and disputes are
recorded side by side, carry equal weight, and are never deleted — the `against`
relation the PBC statute denies the public (DGCL §365(b)), built here rather than
promised (GOV-4).

A signature proves two things: that the holder of a specific key took a specific
stance on a specific version. It does **not**, by itself, prove the key belongs
to the organization named. Binding a key to a real-world identity is a separate,
public step (below). We state that limit plainly rather than let a signature
imply more than it carries.

**Scope.** An attestation here endorses, disputes, or amends *the claims in this
document* — a public governance argument. It is **not** a testimonial or
endorsement of Ethical Capital as an investment adviser, and signing implies no
advisory relationship or view on Ethical Capital's services. If you are a current
client of Ethical Capital and choose to sign, please say so in your record: a
client statement is treated as a testimonial under SEC Rule 206(4)-1(b) and is
handled accordingly.

## What you are signing

The target is this version of the paper, identified by its BLAKE3 content hash:

    paper:    docs/anthropic-contrapunctus.md
    version:  v0 (2026-11-03)
    blake3:   698b6c6785961b566e27dbf6306707ec530b4ba6e9f3823b6a99b3b42504dcea

Recompute it yourself before signing — never trust a hash you did not check:

    b3sum docs/anthropic-contrapunctus.md
    # or, with the Descartes verifier in this repo:
    target/release/descartes hash docs/anthropic-contrapunctus.md

Later versions get new hashes; an attestation is valid only for the hash it
names. Re-sign to carry your stance forward.

## How to sign on or dispute (SSH key — recommended)

Most institutions already have an SSH key and the tools to use it. No new
software required.

1. Write a record (plain text), e.g. `endorse-example-foundation.txt`:

       stance: endorse        # endorse | dispute | amend
       document: Contrapunctus — Taking Anthropic at Its Word
       version_blake3: blake3:698b6c6785961b566e27dbf6306707ec530b4ba6e9f3823b6a99b3b42504dcea
       signer: Example Foundation
       signer_key_published_at: https://example.org/.well-known/contrapunctus.pub
       date: 2026-11-03
       statement: >
         One or more sentences. For a dispute, name the section and the claim you
         contest, and the evidence. For an amend, state the change you propose.

2. Sign it in the `contrapunctus` namespace, so the signature cannot be replayed
   in another context:

       ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n contrapunctus endorse-example-foundation.txt
       # produces endorse-example-foundation.txt.sig

3. Publish your public key where it binds to you — your official domain is best:

       https://example.org/.well-known/contrapunctus.pub   (the line from id_ed25519.pub)

4. Submit all three — the record, the `.sig`, and your public key — as a pull
   request adding them under `docs/contrapunctus-attestations/`, or open an issue
   with them attached, and add your line to `allowed_signers`. A **dispute** is
   submitted exactly the same way as an endorsement; it is not second class.

## How anyone verifies it

    ssh-keygen -Y verify -f docs/contrapunctus-attestations/allowed_signers \
      -I "Example Foundation" -n contrapunctus \
      -s endorse-example-foundation.txt.sig < endorse-example-foundation.txt

A pass means: the named key signed this exact record, in this namespace, and the
record names the version hash above. Then confirm the key really is the
organization's by fetching it from the domain in `signer_key_published_at`.
`docs/contrapunctus-attestations/verify.sh` runs this over every record at once.

## Other signing methods (accepted)

- **Descartes ed25519 attestation** — the native graph form. If you run the
  Descartes verifier, sign the paper's node id with an attestation (domain
  `descartes-attestation-v2`); it becomes a first-class edge in the graph.
- **minisign** or **GPG** — fine. Include the signature, the public key, and the
  same record fields, and say which tool you used.

## What happens to disputes

Nothing is overwritten. A dispute is merged into the ledger next to the claim it
contests and answered in the open; if it shows the paper is wrong, the paper is
corrected in a new version (new hash), with the dispute preserved as the record
of why. A claim that survives disputes is worth more than one no one tested.
