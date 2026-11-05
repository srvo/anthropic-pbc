# Argument cards and workbench

The paper's argument as small cards. Each card holds one claim and names what it rests on: checked quotes in `claims/`, other cards, or pending sources. The prose paper and every view are generated from these files and never edited by hand.

| File | Holds |
|---|---|
| `cards.tsv` | One claim per card, in Descartes claims format |
| `sequence.tsv` | Order, theme, role, slot and circle for each card (the circle is computed) |
| `themes.tsv` | Theme questions and their lenses |
| `parties.tsv`, `coverage.tsv` | Who has standing or is affected, and how each theme covers them |
| `quantities.tsv` | Numbers, each marked observed (quoted), applied (a reader's assumption) or implied (a formula) |
| `sides.tsv` | Which cards carry Anthropic's case |
| `pending-sources.tsv` | Sources not yet pinned, and why |

## Views

- **Workbench:** the complaint sphere, chains, barriers, carry-forward and survivorship, on one page.
  - Live, rebuilt on every push by `.github/workflows/workbench-pages.yml`: https://srvo.github.io/anthropic-pbc/ (chain view at `chain/`, card deck at `cards/`).
  - Shareable snapshot: https://claude.ai/artifact/PfL9HsyEvaHm3UpWUdeCgj.
  - Build: `python3 scripts/render_workbench.py OUT_DIR` writes `index.html`, `artifact.html`, `MANIFEST.tsv` (SHA-256 of every input) and `inputs/`.
- **Chain shape:** `python3 scripts/render_chain.py OUT.html`.
- **Card deck:** `uv run scripts/render_cards.py OUT.html`.
- **Paper from cards:** `python3 scripts/render_paper_from_cards.py`.

## Checks

```
python3 scripts/check_cards.py
python3 scripts/check_workbench.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_check_cards.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_chain_shape.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_workbench.py
```

Renders depend only on the inputs and the commit, so building twice gives byte-identical files.
