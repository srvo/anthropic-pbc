# Dataset attestations

One signing record per dataset in `datasets/<id>.txt`, written by
`uv run scripts/attest_datasets.py record`. A record lists the BLAKE3 of every
committed file in the dataset's corpus folder and of every script that builds
it, plus what a signature attests. It holds no clock and no commit id, so it
changes exactly when the files do.

Signatures are OpenSSH Ed25519 (`ssh-keygen -Y`), in the namespace
`anthropic-pbc-dataset`, which is separate from the paper's `contrapunctus`
namespace (`docs/contrapunctus-attest.md`). A dataset signature cannot be
replayed as an endorsement of the paper.

## Sign

    uv run scripts/attest_datasets.py record        # then commit the records
    uv run scripts/attest_datasets.py sign --key ~/.ssh/YOUR_KEY --signer "Your Name" [dataset ...]

`sign` refuses a record that is not current. It runs each dataset's own
`verify` first and stops if that fails. `ssh-keygen` reads the key itself, from
the file or from the agent. The signer's public key is added once to
`allowed_signers`. Commit the `.sig`, the `.signer` file and `allowed_signers`.

## Check

    uv run scripts/attest_datasets.py status    # signed / unsigned / stale per dataset
    uv run scripts/attest_datasets.py verify    # exit 1 on a stale or bad signature

A signature goes **stale** when any listed file changes. The dataset is then
unsigned in effect until someone re-signs the new record. `DATASETS.md` shows
each dataset's status.

To bind a key to a person or organization, publish the same public key
somewhere they control, as the paper's protocol asks.
