# Receiving comments

A reader's comment on anything we emit is a record, kept like a source: pinned
by digest, verbatim, anchored, and answered in the open. This standard exists
because the first round of comments on the paper (Apple Preview notes on the
154d864 PDF, 2026-11-04) was saved into the file and then went unread, since
nothing compared the file with what had been sent.

## The primitive: compare bytes

Every output handed to a reader is recorded in `docs/emissions.tsv` with its
SHA-256, size and source commit (`scripts/pdf_comments.py record`). When a
reader says "I gave you feedback", or a file comes back, the first step is to
compare its bytes with that record (`pdf_comments.py pull`):

- **Same digest:** nothing was added. Say so; don't guess at what the reader
  meant to send.
- **Different digest:** extract every annotation from the returned file and
  append it, verbatim, to the document's ledger. Then read the whole ledger.

Emitted files themselves are never committed; the record of them is.

## Channels

Any channel works as long as its comments land in the ledger:

1. **PDF annotations** (Preview, Acrobat, any reader that saves notes,
   highlights or strike-outs into the file). `pull` reads them.
2. **Plannotator** annotations on the Markdown or HTML.
3. **Spoken or chat comments.** Enter them in the ledger with `kind` = `chat`
   and the reader's words quoted exactly.
4. **The shared workspace**, once it exists. Its comments export to the same
   ledger.

## The ledger

`comments/<document>.tsv`, one row per comment, append-only:

| column | meaning |
|---|---|
| `id` | `C1`, `C2`, … in order received |
| `received` | date, given as an argument (no clock) |
| `pdf_sha256` | digest of the file the comment came in |
| `emitted_sha256` | digest of the file we sent (`unrecorded` if it was never logged) |
| `built_from` | source commit of the rendering commented on |
| `page`, `anchor` | page number, plus the text the comment sits on or near, so it can be found in the source |
| `kind`, `author`, `comment` | annotation type, who wrote it, and the words exactly as written |
| `status` | `open`, `applied`, `declined` or `question` |
| `resolution` | the commit that answers the comment, or the reason it was declined, or the question sent back |

A comment is closed only by a commit or a stated reason. If a comment is
unclear, its status is `question` and the question goes back to the reader;
the comment is never interpreted silently. Anchors are approximate (text near
a note), so whoever resolves a comment confirms where it applies.

## Comments on the method versus comments on the claims

A comment about design, layout or legibility follows
`docs/editorial-standard.md`. A comment disputing a finding follows the paper's
rules: a factual correction goes in §9 Errata, and the claim is rechecked.
