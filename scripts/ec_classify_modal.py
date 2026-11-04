"""Run scripts/ec_classify.py's scoring on Modal GPUs, in parallel.

Same functions, same pins, same codebook; only the device differs. Shards come
back to this machine and are merged locally by ec_classify.merge(), which writes
the committed parquet and run record. Shards are tagged with the backend
(`modal-<GPU>`), so they never mix with a local MPS run.

    uvx --with duckdb==2.0.0 --with blake3 modal run scripts/ec_classify_modal.py --model deberta --limit 2048
    uvx --with duckdb==2.0.0 --with blake3 modal run scripts/ec_classify_modal.py --model deberta
    uvx --with duckdb==2.0.0 --with blake3 modal run scripts/ec_classify_modal.py --model modernbert
    # another unit file / codebook (output: proposals/earnings-calls/<codebook stem>/):
    ... --model deberta --units .eccorpus/ai-questions.parquet \
        --codebook corpus/earnings-calls/codebook-questions-v0.1.tsv --id-col question_id
    # Hacker News focused sets (units are local-only text; --out keeps proposals apart):
    ... --model deberta --units .hncorpus/units-anthropic.parquet --out proposals/hacker-news/anthropic

GPU type: EC_GPU env var (default L40S). Containers: EC_MAX_CONTAINERS (default 8;
the Starter plan allows 10 concurrent GPUs). Cost is per second of GPU time;
--limit runs one shard on one GPU and prints throughput before any full run.
"""


import os
import sys
import time
from pathlib import Path

import modal

sys.path.insert(0, str(Path(__file__).resolve().parent))

GPU = os.environ.get("EC_GPU", "L40S")
MAX_CONTAINERS = int(os.environ.get("EC_MAX_CONTAINERS", "8"))

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("torch==2.9.1", "transformers==4.57.3", "sentencepiece==0.2.1",
                 "protobuf==6.33.1", "duckdb==2.0.0", "blake3==1.0.8")
    .add_local_python_source("ec_classify")
)
app = modal.App("ec-classify", image=image)


@app.cls(gpu=GPU, timeout=3600, max_containers=MAX_CONTAINERS)
class Scorer:
    model_key: str = modal.parameter()
    dtype: str = modal.parameter(default="bfloat16")
    batch: int = modal.parameter(default=128)

    @modal.enter()
    def load(self) -> None:
        import ec_classify as ec
        self.ec = ec
        self.tok, self.model, self.ent = ec.load_model(self.model_key, self.dtype, "cuda")

    @modal.method()
    def score(self, si: int, wins: list, hyps: list) -> tuple[int, list, float]:
        t0 = time.monotonic()
        try:
            rows = self.ec.score_windows(self.tok, self.model, self.ent, "cuda", wins, hyps, self.batch)
        except Exception as e:  # torch exception types cannot be unpickled locally (no torch there)
            raise RuntimeError(f"shard {si}: {type(e).__name__}: {e}") from None
        return si, rows, time.monotonic() - t0

    @modal.method()
    def runtime(self) -> dict:
        return self.ec.runtime_info("cuda", self.dtype, self.batch)


@app.local_entrypoint()
def main(model: str, limit: int = 0, dtype: str = "bfloat16", batch: int = 128,
         units: str = "", codebook: str = "", id_col: str = "", out: str = "") -> None:
    import ec_classify as ec

    ec.configure(units, codebook, id_col, out)
    hyps, wins = ec.load_inputs(limit)
    backend = f"modal-{GPU}"
    tag = ec.make_tag(model, dtype, backend)
    chunks = ec.shard_chunks(wins)
    todo = [(si, chunks[si], hyps) for si in range(len(chunks)) if limit or not ec.shard_path(tag, si).exists()]
    print(f"{model}: {len(wins)} windows x {len(hyps)} hypotheses, {len(todo)}/{len(chunks)} shards to score on {GPU}")
    scorer = Scorer(model_key=model, dtype=dtype, batch=batch)
    t0 = time.monotonic()
    done = 0
    for si, rows, secs in (scorer.score.starmap(todo, order_outputs=False) if todo else []):  # empty starmap hangs
        done += 1
        if limit:
            print(f"smoke: {len(rows)} pairs in {secs:.1f}s GPU time = {len(rows)/secs:.0f} pairs/s on {GPU}")
            return
        ec.write_shard(ec.shard_path(tag, si), rows)
        print(f"  shard {si:04d}: {len(rows)/secs:.0f} pairs/s  ({done}/{len(todo)}, {time.monotonic()-t0:.0f}s wall)", flush=True)
    missing = [si for si in range(len(chunks)) if not ec.shard_path(tag, si).exists()]
    if missing:
        sys.exit(f"{len(missing)} shard(s) missing; rerun to resume")
    rt = scorer.runtime.remote()
    ec.merge(model, tag, len(wins), hyps, {**rt, "backend": backend})
