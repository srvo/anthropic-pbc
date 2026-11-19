# /// script
# [tool.marimo.runtime]
# auto_instantiate = false
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", auto_download=["html"])


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo, open_url, page_text, pd):
    def _():
        def _():
            import itertools

            # ------------------------------------------------------------------
            # Formal-logic representation of the Anthropic PBC argument
            # ------------------------------------------------------------------
            # Source content is fetched directly from the underlying GitHub
            # repository. We define atomic propositions, encode the argument's
            # premises and conclusion in propositional logic, and check validity
            # via a truth table and a derivation chain.

            # ---- Fetch source directly from the underlying repository ----
            repo_urls = [
                'https://raw.githubusercontent.com/srvo/anthropic-pbc/main/README.md',
                'https://raw.githubusercontent.com/srvo/anthropic-pbc/main/index.html',
            ]
            repo_text = ''
            repo_fetch_url = ''
            repo_status = 'not attempted'
            for _url in repo_urls:
                try:
                    repo_text = open_url(_url).read()
                    repo_fetch_url = _url
                    repo_status = f'loaded {len(repo_text)} characters from {_url}'
                    break
                except Exception:
                    continue
            if not repo_text:
                try:
                    repo_text = page_text
                    repo_status = f'fell back to page text ({len(repo_text)} characters)' if repo_text else 'no source available'
                except NameError:
                    repo_status = 'no source available'
                    repo_text = ''

            # ---- Atomic propositions (dictionary: symbol -> natural language) ----
            atoms = {
                'A': 'AI systems could pose catastrophic risks to humanity',
                'B': 'AI developers are primarily motivated by profit / shareholder returns',
                'C': 'Profit maximisation can conflict with safety precautions',
                'D': 'A PBC charter legally requires directors to weigh public benefit',
                'E': 'Anthropic is incorporated as a Public Benefit Corporation',
                'F': 'Directors face legal accountability for neglecting public benefit',
                'G': 'The firm will reliably prioritise safety over profit when they conflict',
                'H': 'Catastrophic AI risk is meaningfully reduced',
            }

            # ---- Premises and conclusion as (symbolic, plain-English) pairs ----
            premises = [
                ('A',                         'P1  AI could pose catastrophic risk'),
                ('B',                         'P2  AI firms are profit-motivated'),
                ('C',                         'P3  Profit can conflict with safety'),
                ('D',                         'P4  A PBC charter requires public-benefit weighing'),
                ('E',                         'P5  Anthropic is a PBC'),
                ('D ∧ E → F',                 'P6  If a PBC charter applies and Anthropic is a PBC, directors face accountability'),
                ('F → (G ∨ C)',               'P7  Accountability means safety is prioritised OR profit still conflicts'),
                ('G → H',                     'P8  Prioritising safety reduces catastrophic risk'),
                ('¬G ∧ C ∧ A → ¬H',            'P9  Without prioritisation, conflict persists, and risk is not reduced'),
            ]
            conclusion = ('H', 'C  Catastrophic AI risk is meaningfully reduced')

            # ---- Build a small evaluator for our formula language ----
            # Supports atoms, ¬, ∧, ∨, →

            def _parse_and_eval(expr, assignment):
                """Evaluate a propositional-logic expression given a dict of atom -> bool."""
                tokens = expr.replace('(', ' ( ').replace(')', ' ) ').replace('¬', '¬ ').replace('∧', '∧ ').replace('∨', '∨ ').replace('→', '→ ').split()
                pos = 0
                def peek():
                    return tokens[pos] if pos < len(tokens) else None
                def consume():
                    nonlocal pos
                    tok = tokens[pos]
                    pos += 1
                    return tok
                def parse_implies():
                    left = parse_or()
                    while peek() == '→':
                        consume()
                        right = parse_or()
                        left = (not left) or right
                    return left
                def parse_or():
                    left = parse_and()
                    while peek() == '∨':
                        consume()
                        right = parse_and()
                        left = left or right
                    return left
                def parse_and():
                    left = parse_unary()
                    while peek() == '∧':
                        consume()
                        right = parse_unary()
                        left = left and right
                    return left
                def parse_unary():
                    if peek() == '¬':
                        consume()
                        return not parse_unary()
                    return parse_atom()
                def parse_atom():
                    tok = consume()
                    if tok == '(':
                        val = parse_implies()
                        assert consume() == ')'
                        return val
                    return assignment[tok]
                return parse_implies()

            # ---- Generate the truth table for all atoms ----
            atom_syms = list(atoms.keys())
            rows = []
            for combo in itertools.product([False, True], repeat=len(atom_syms)):
                assignment = dict(zip(atom_syms, combo))
                row = {s: 'T' if assignment[s] else 'F' for s in atom_syms}
                all_premises_true = all(_parse_and_eval(sym, assignment) for sym, _ in premises)
                conclusion_true = _parse_and_eval(conclusion[0], assignment)
                row['All premises'] = 'T' if all_premises_true else 'F'
                row['Conclusion (H)'] = 'T' if conclusion_true else 'F'
                rows.append(row)

            tt_df = pd.DataFrame(rows)
            counterexamples = tt_df[(tt_df['All premises'] == 'T') & (tt_df['Conclusion (H)'] == 'F')]
            is_valid = len(counterexamples) == 0

            # ---- Human-readable reference table for atoms ----
            atom_table = pd.DataFrame({
                'Symbol': list(atoms.keys()),
                'Proposition': list(atoms.values()),
            })

            # ---- Premise table ----
            premise_table = pd.DataFrame({
                'Formal': [p[0] for p in premises],
                'Plain English': [p[1] for p in premises],
            })

            # ---- Derivation chain (separate Step / Formula / Justification / Type) ----
            derivation = [
                (1,  'A',                'Premise P1',                                          'Premise'),
                (2,  'B',                'Premise P2',                                          'Premise'),
                (3,  'C',                'Premise P3',                                          'Premise'),
                (4,  'D',                'Premise P4',                                          'Premise'),
                (5,  'E',                'Premise P5',                                          'Premise'),
                (6,  'D ∧ E',            'Conjunction of 4, 5',                                 'Inference'),
                (7,  'D ∧ E → F',        'Premise P6',                                          'Premise'),
                (8,  'F',                'Modus ponens on 6, 7',                                'Inference'),
                (9,  'F → (G ∨ C)',      'Premise P7',                                          'Premise'),
                (10, 'G ∨ C',            'Modus ponens on 8, 9',                                'Inference'),
                (11, 'G → H',            'Premise P8',                                          'Premise'),
                (12, 'C ∧ A',            'Conjunction of 1, 3 (both premises)',                'Inference'),
                (13, '¬G ∧ C ∧ A → ¬H',  'Premise P9',                                          'Premise'),
                (14, '¬G → ¬H',          'From 12, 13: ¬G gives ¬G ∧ C ∧ A, so ¬H',             'Inference'),
                (15, 'H ↔ G',            'Biconditional from 11 (G → H) and 14 (¬G → ¬H)',      'Inference'),
                (16, 'H',                'Cannot derive — G ∨ C satisfied by C alone (step 3); G undetermined', 'Gap ⚠'),
            ]
            deriv_df = pd.DataFrame(derivation, columns=['Step', 'Formula', 'Justification', 'Type'])

            # ---- Truth-table display ----
            display_cols = atom_syms + ['All premises', 'Conclusion (H)']
            if len(counterexamples) > 0:
                truth_display = counterexamples[display_cols].copy()
                truth_label = 'Counterexample rows — all premises true, conclusion false'
            else:
                truth_display = tt_df[tt_df['All premises'] == 'T'][display_cols].head(8)
                truth_label = 'Rows where all premises are true'

            # ---- Source preview ----
            source_preview = repo_text[:800] if repo_text else '(source unavailable)'

            # ---- Assemble the UI ----
            return mo.vstack([
                mo.md("""
                ## Formal-logic representation of the Anthropic PBC argument

                The argument is reconstructed as a **propositional-logic** chain.
                Each atomic proposition gets a letter, the premises are encoded as formulas,
                and we check whether the conclusion is *entailed* by the premises using an
                exhaustive truth table.  Source content is fetched directly from the
                underlying repository at `https://github.com/srvo/anthropic-pbc`.
                """),

                mo.md(f"**Repository fetch status:** {repo_status}"),
                mo.md(f"""
            ```
            {source_preview}
            ```"""),

                mo.md("### 1 · Atomic propositions"),
                mo.ui.table(atom_table),

                mo.md("### 2 · Premises & conclusion"),
                mo.ui.table(premise_table),
                mo.md(f"**Conclusion:**  `{conclusion[0]}`  —  {conclusion[1]}"),

                mo.md("### 3 · Derivation chain"),
                mo.ui.table(deriv_df),

                mo.md("### 4 · Truth-table validity check"),
                mo.md(
                    f"Rows evaluated: **{len(tt_df)}**  |  "
                    f"Counterexamples found: **{len(counterexamples)}**  |  "
                    f"Argument is **{'VALID ✅' if is_valid else 'INVALID ❌'}**"
                ),
                mo.md(f"_{truth_label}_"),
                mo.ui.table(truth_display),

                mo.md("""
                ### 5 · Reading the result

                * If the table shows **VALID**, the conclusion follows *given the premises are true*.
                * If **INVALID**, counterexample rows show truth-value assignments where every
                  premise holds but the conclusion is still false — pinpointing the weakest link.
                * The logical gap is in **P7**: `F → (G ∨ C)`. Since `C` is already a premise
                  (profit *can* conflict with safety), the disjunction `G ∨ C` is trivially
                  true regardless of `G`. Accountability (F) does not force safety
                  prioritisation (G) — the profit-conflict branch (C) satisfies the
                  disjunction on its own. Without `G`, **P9** yields `¬H`, blocking the
                  conclusion.
                * The critical premises to challenge are **P6** (does a PBC charter *actually*
                  create enforceable accountability?) and **P7** (does accountability *guarantee*
                  safety prioritisation, or merely create a disjunction where the profit-conflict
                  branch still exists?).
                """),
            ])
        return _()


    _()
    return


@app.cell
def _(mo):
    mo.md("""
    # Extending an argument: Anthropic PBC

    This notebook pulls the page at `https://srvo.github.io/anthropic-pbc/` (when the browser allows it), shows the extracted text, and gives you a scaffold for pushing the argument further.

    **How to use it**

    1. Read the extracted text below. If the fetch is blocked, open the page in another tab and keep it beside this notebook.
    2. Write the argument's core claim in one sentence.
    3. Pick an extension lens and answer its prompts in your own notes.
    4. Switch lenses and repeat — the goal is to find the step the argument does not defend.
    """)
    return


@app.cell
def _():
    import re

    url = 'https://srvo.github.io/anthropic-pbc/'
    page_text = ''
    fetch_status = 'not attempted'
    try:
        from pyodide.http import open_url
        raw_html = open_url(url).read()
        stripped = re.sub(r'(?is)<(script|style).*?</\1>', ' ', raw_html)
        page_text = re.sub(r'\s+', ' ', re.sub(r'(?s)<[^>]+>', ' ', stripped)).strip()
        fetch_status = 'loaded ' + str(len(page_text)) + ' characters'
    except Exception as exc:
        fetch_status = 'could not load the page (' + type(exc).__name__ + ')'
    return fetch_status, open_url, page_text


@app.cell
def _(fetch_status, mo, page_text):
    preview = page_text[:1200] if page_text else '_No page text was retrieved. Open the source in another tab and keep it beside this notebook._'
    mo.md('**Source status:** ' + fetch_status + '\n\n---\n\n' + preview)
    return


@app.cell
def _(mo):
    core_claim = mo.ui.text_area(value='', label='Core claim of the argument (one sentence)', full_width=True)
    lens = mo.ui.dropdown(options=['Scope', 'Mechanism', 'Evidence', 'Counterexample', 'Institutional design', 'Stakeholders'], value='Scope', label='Extension lens')
    mo.vstack([core_claim, lens])
    return core_claim, lens


@app.cell
def _(core_claim, lens, mo):
    import pandas as pd

    lens_prompts = {
        'Scope': ['Which actors, places, and time horizons does the claim assume?', 'What changes at the edges of that scope?'],
        'Mechanism': ['Which causal step is asserted but not shown?', 'What would have to be true for that step to hold?'],
        'Evidence': ['What observation would confirm or falsify the claim?', 'What data is the argument missing?'],
        'Counterexample': ['Name the strongest case where the claim fails.', 'What does that case share with the original?'],
        'Institutional design': ['Which rule, incentive, or body carries the claim?', 'Who can veto or capture it?'],
        'Stakeholders': ['Who bears the cost if the claim is wrong?', 'Whose voice is missing from the argument?'],
    }
    claim_text = core_claim.value.strip() or '(write your core claim above)'
    prompt_md = '\n'.join('- ' + p for p in lens_prompts[lens.value])
    lens_table = pd.DataFrame({'Lens': list(lens_prompts), 'Opening prompt': [v[0] for v in lens_prompts.values()]})
    mo.vstack([
        mo.md('### Extending through: ' + lens.value + '\n\n**Claim under test:** ' + claim_text + '\n\n' + prompt_md),
        mo.ui.table(lens_table),
    ])
    return (pd,)


@app.cell
def _(page_text):
    full_source_text = page_text if page_text else '_No page text was retrieved. Open the source in another tab and keep it beside this notebook._'
    return


if __name__ == "__main__":
    app.run()
