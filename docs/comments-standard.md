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

## Dissent beats comments

A free-text comment can't be checked, so it adds noise as easily as signal
(Sloane, 2026-11-04). The verification chain at the end of every rendering
(its colophon) gives each claim a version, a source and a result. The
strongest response therefore names what it disputes: a claim, at a commit,
with a reason and, where possible, a pinned counter-source. It enters as a
fork of the argument graph, beside ours, not as an overwrite. The ledger below
still records every comment, because a comment is often where dissent starts.

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
| `status` | `open`, `applied`, `declined`, `open-question` or `discussion` |
| `resolution` | the commit that acts on the comment, the reason it was declined, or where its open question lives |

A comment is closed only by a commit or a stated reason. A comment is never
interpreted silently. Anchors are approximate (text near
a note), so whoever resolves a comment confirms where it applies.

## Open questions graduate into discussions

A comment that raises something we can't settle by an edit becomes an
**open question**, and that is a good outcome. An open question is published
as an invitation; once someone takes it up, it graduates into a
**discussion**. It isn't expected to close: the hope is that the best ones
stay open, because the conversation is the point (Sloane, 2026-11-04).

- Every open question first names the primitives it concerns
  (`docs/editorial-standard.md`, "Questions point at primitives").
- An open question about the subject goes into the paper's §8.1, with the
  comment's ledger id. One about the form (design, wording) stays in the
  ledger as `open-question`.
- When a question draws a reply, its status becomes `discussion` and the
  resolution column points to where the discussion is (a trail, an issue, the
  workspace).
- These differ from the decisions in Praxis `OPENQUESTIONS.md`, which wait on
  an owner and are answered. An open question here has no owner and no
  answer due.

## Comments on the method versus comments on the claims

A comment about design, layout or legibility follows
`docs/editorial-standard.md`. A comment disputing a finding follows the paper's
rules: a factual correction goes in §9 Errata, and the claim is rechecked.
