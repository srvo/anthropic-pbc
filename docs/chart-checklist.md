# Chart checklist

Every chart in this repository passes these before it ships. A chart that only
looks right is the failure this list exists to catch: a curve drawn from fixed
numbers beside a slider that does not move it tells the reader something false.

## Truth

- [ ] **Built from committed data.** The chart names its input file(s); no number is
      typed into the drawing code.
- [ ] **Every control is wired.** Each slider, toggle or input visibly changes the
      drawing, and a test proves it (change the input, assert the output changed).
      A control that changes nothing is removed.
- [ ] **No shape without a source.** Every curve, slope and band comes from an
      observed, applied or implied quantity (`argument/quantities.tsv`). A shape chosen
      for illustration is labelled "illustrative" on the chart itself.
- [ ] **Assumptions on the face.** Applied (reader-set, unsourced) values are labelled
      as such next to the mark they move, not only in a footnote.
- [ ] **Status shown.** Pinned, proposal (model output) or draft, on the chart.

## Reading

- [ ] One y-axis. Units on every axis. Zero baseline for bars.
- [ ] Legend for two or more series; identity never by colour alone.
- [ ] A table or text view of the same numbers.
- [ ] Works in light and dark, and at phone width.
- [ ] Hover gives the exact value and its source.

## Record

- [ ] A `viz://` step in `dag.yml`, rebuilt by the build, emitted files not committed
      (`docs/figures/*.svg` is gitignored).
- [ ] Listed on the trace page with what it shows, its data and its stage.
- [ ] Checked against `docs/chart-checklist.md` in review, with any failing box named.
