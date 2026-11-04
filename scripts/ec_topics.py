#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "bertopic==0.17.4",
#   "sentence-transformers==5.1.2",
#   "umap-learn==0.5.12",
#   "hdbscan==0.8.44",
#   "scikit-learn==1.7.2",
#   "numpy==2.3.5",
#   "pandas==2.3.3",
#   "torch==2.9.1",
#   "transformers==4.57.3",
#   "duckdb==2.0.0",
#   "blake3>=1.0",
# ]
# ///
"""BERTopic map of the earnings-call AI windows. EXPLORATORY.

docs/bert-enrichment-spec.md §9 bars "BERTopic/UMAP clusters as signed output"
and "embeddings or cosine scores as evidence". This script respects that:
clusters are a reading aid for choosing what to hand-code next. They are
never cited as a finding, never a column in the Risk-Governance Index, and
never a verdict. Every topic lists window ids so any reading of it can be
checked against verbatim text.

    uv run scripts/ec_topics.py

Pins: embedding model revision, UMAP random_state, every library version.
UMAP with a fixed seed is reproducible on one machine and library set; it is
not claimed to be reproducible across hardware.
Outputs (proposals/earnings-calls/topics-v0.1/):
    topics.tsv        topic, size, top c-TF-IDF terms, three representative window ids
    assignments.parquet  window_id -> topic (-1 = unclustered)
    by-year.tsv       topic x fiscal_year window counts
    run.json          pins and parameters
"""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import blake3
import duckdb
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus" / "earnings-calls"
WINDOWS = CORPUS / "ai-windows.parquet"
OUT = ROOT / "proposals" / "earnings-calls" / "topics-v0.1"
CACHE = ROOT / ".eccorpus"

EMBED = ("sentence-transformers/all-mpnet-base-v2", "e8c3b32edf5434bc2275fc9bab85f82640a19130", "Apache-2.0")
SEED = 42


def _device() -> str:
    import torch
    return "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")


DEVICE = _device()
UMAP_KW = dict(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=SEED)
HDB_KW = dict(min_cluster_size=60, min_samples=10, metric="euclidean", cluster_selection_method="eom",
              prediction_data=True)
VEC_KW = dict(stop_words="english", ngram_range=(1, 2), min_df=5)


def fhash(p: Path) -> str:
    return blake3.blake3(p.read_bytes()).hexdigest()


def main() -> int:
    from bertopic import BERTopic
    from hdbscan import HDBSCAN
    from sentence_transformers import SentenceTransformer
    from sklearn.feature_extraction.text import CountVectorizer
    from umap import UMAP

    con = duckdb.connect()
    rows = con.execute(f"SELECT window_id, fiscal_year, text FROM '{WINDOWS}' ORDER BY window_id").fetchall()
    ids = [r[0] for r in rows]
    years = [r[1] for r in rows]
    docs = [r[2] for r in rows]

    wh = fhash(WINDOWS)
    emb_path = CACHE / f"emb.mpnet.{wh[:12]}.npy"   # not committed: embeddings are not evidence
    if emb_path.exists():
        emb = np.load(emb_path)
    else:
        st = SentenceTransformer(EMBED[0], revision=EMBED[1], device=DEVICE)
        emb = st.encode(docs, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
        np.save(emb_path, emb)

    model = BERTopic(
        umap_model=UMAP(**UMAP_KW),
        hdbscan_model=HDBSCAN(**HDB_KW),
        vectorizer_model=CountVectorizer(**VEC_KW),
        top_n_words=10,
        calculate_probabilities=False,
        verbose=True,
    )
    topics, _ = model.fit_transform(docs, embeddings=emb)

    OUT.mkdir(parents=True, exist_ok=True)
    con.execute("CREATE TABLE a (window_id VARCHAR, fiscal_year INT, topic INT)")
    con.executemany("INSERT INTO a VALUES (?,?,?)", list(zip(ids, years, [int(t) for t in topics])))
    con.execute(f"COPY (SELECT window_id, topic FROM a ORDER BY window_id) TO '{OUT / 'assignments.parquet'}' "
                f"(FORMAT parquet, COMPRESSION zstd)")
    con.execute(f"COPY (PIVOT (SELECT topic, fiscal_year FROM a) ON fiscal_year USING count(*) ORDER BY topic) "
                f"TO '{OUT / 'by-year.tsv'}' (HEADER, DELIMITER '\t')")

    # Representative windows: the 3 closest to each topic's embedding centroid (deterministic).
    t_arr = np.array(topics)
    lines = ["topic\tsize\tterms\trepresentative_window_ids"]
    for t in sorted(set(int(x) for x in topics)):
        idx = np.where(t_arr == t)[0]
        terms = ", ".join(w for w, _ in (model.get_topic(t) or []))
        c = emb[idx].mean(axis=0)
        order = idx[np.argsort(-(emb[idx] @ c), kind="stable")[:3]]
        lines.append(f"{t}\t{len(idx)}\t{terms}\t{','.join(ids[i] for i in order)}")
    (OUT / "topics.tsv").write_text("\n".join(lines) + "\n")

    import bertopic, hdbscan, sentence_transformers, sklearn, umap
    run = {
        "status": "EXPLORATORY reading aid; not evidence, not signed (docs/bert-enrichment-spec.md §9)",
        "embedding_model": EMBED[0], "embedding_revision": EMBED[1], "embedding_license": EMBED[2],
        "embedding_device": DEVICE, "normalize_embeddings": True,
        "umap": UMAP_KW, "hdbscan": HDB_KW, "vectorizer": {**VEC_KW, "ngram_range": list(VEC_KW["ngram_range"])},
        "windows": str(WINDOWS.relative_to(ROOT)), "windows_blake3": wh, "n_windows": len(ids),
        "n_topics": len(set(topics)) - (1 if -1 in topics else 0),
        "n_unclustered": int((t_arr == -1).sum()),
        "versions": {"bertopic": bertopic.__version__, "umap": umap.__version__, "hdbscan": getattr(hdbscan, "__version__", "0.8.44"),
                     "sentence_transformers": sentence_transformers.__version__, "sklearn": sklearn.__version__,
                     "numpy": np.__version__, "python": platform.python_version()},
        "machine": platform.machine(),
        "outputs": {p.name: fhash(p) for p in sorted(OUT.glob("*")) if p.name != "run.json"},
    }
    (OUT / "run.json").write_text(json.dumps(run, indent=2, sort_keys=True) + "\n")
    print(f"ok: {run['n_topics']} topics, {run['n_unclustered']} unclustered of {len(ids)} windows -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
