# Recurring standards review

The standards inventory is `standards.json` beside this document. It distinguishes
binding standards, shared contracts, a draft skeleton and a decision/plan history.
A plan sentence is not proof that its implementation exists.

Run `uv run scripts/standards_review.py --brain --output ~/tray/standards-run.json`
from this repository. It records source hashes, check scope, failed/unavailable
checks and proposed reconciliation opportunities. It does not repair sources,
authorize changes, or approve a claim. The weekly CI workflow runs the same
portable checks and retains its machine receipt even on failure. A missing shared
Praxis checkout is reported as unknown and keeps the audit from passing; public
CI never receives private DarkDB credentials. Local/private orchestration admits
these receipts into the existing planning graph under its actual access boundary.

The argument-unit contract belongs to Praxis `design/argument-units.json` and
`design/argument-units.md`. One paragraph has one argumentative or explanatory
purpose, potentially several sentences. Appropriate prose, tables, charts,
diagrams and equations are representations; HTML/PDF are formats, not two kinds.
Representations bind to one canonical unit and preserve its kind, qualifications,
evidence references and digest. Changed units invalidate old representations and
review records. Semantic unity/equivalence and reviewer identity are not established
by structural tests. Existing reports without a unit register remain unassessed;
no units or reviews are invented merely to pass a check.

`uv run scripts/test_standards_review.py` exercises version drift, changed
qualifications, question/observation confusion, missing review bindings, duplicate
identity, paragraph boundaries and missing shared runtime. These synthetic tests
are separate from current-document conformance. An audit may finish with findings.
