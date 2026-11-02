"""Cache frozen, local ONNX sentence embeddings for development rows only.

Locked test rows are excluded before tokenization or inference. Model assets and
the resulting vectors are stored in Git-ignored data/cache directories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import onnxruntime as ort
from huggingface_hub import snapshot_download
from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.splitting import load_development_bundle  # noqa: E402

REPOSITORY = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "b9db1e8a0d3a51769172ba8546f282a73f066e47"
MAX_LENGTH = 256
LABELS = ["Risky", "Neutral", "Safe"]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_revision() -> str:
    import subprocess

    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-rows", type=int, default=None, help="Optional explicit development-only cap; capped runs are not full experiment results.")
    args = parser.parse_args()
    if args.batch_size < 1 or (args.max_rows is not None and args.max_rows < 1):
        raise ValueError("batch-size and max-rows must be positive")

    protocol_rows = []
    for protocol in ("primary", "clause"):
        data, split_meta = load_development_bundle(protocol, ROOT)
        part, included = f"{protocol}_partition", f"{protocol}_include"
        dev = data.loc[data[included] & data[part].isin(["train", "validation"]), ["point_id", "quote_text"]].copy()
        dev["point_id"] = dev["point_id"].astype(int)
        protocol_rows.append((protocol, dev, split_meta))

    dev_ids = sorted(set().union(*(set(rows.point_id.tolist()) for _, rows, _ in protocol_rows)))
    if args.max_rows is not None:
        dev_ids = dev_ids[: args.max_rows]
    source_by_id: dict[int, str] = {}
    for _, rows, _ in protocol_rows:
        for row in rows.itertuples(index=False):
            source_by_id.setdefault(int(row.point_id), str(row.quote_text or ""))
    texts = [source_by_id[point_id] for point_id in dev_ids]
    input_ids_sha = sha256_bytes("\n".join(map(str, dev_ids)).encode("utf-8"))
    text_sha = sha256_bytes("\n".join(f"{pid}\t{source_by_id[pid]}" for pid in dev_ids).encode("utf-8"))
    cache_id = f"{REPOSITORY.rsplit('/', 1)[-1]}_{REVISION[:8]}_{input_ids_sha[:12]}"
    cache_root = ROOT / "data" / "cache" / "encoders" / f"{REPOSITORY.rsplit('/', 1)[-1]}_{REVISION[:8]}"
    vector_root = ROOT / "data" / "cache" / "embeddings"
    cache_root.mkdir(parents=True, exist_ok=True)
    vector_root.mkdir(parents=True, exist_ok=True)

    snapshot_download(
        repo_id=REPOSITORY,
        revision=REVISION,
        local_dir=cache_root,
        allow_patterns=["onnx/model.onnx", "tokenizer.json", "config.json"],
    )
    model_path = cache_root / "onnx" / "model.onnx"
    tokenizer_path = cache_root / "tokenizer.json"
    if not model_path.is_file() or not tokenizer_path.is_file():
        raise FileNotFoundError("Pinned encoder snapshot did not contain the requested ONNX graph and tokenizer")

    vector_path = vector_root / f"{cache_id}.npz"
    meta_path = vector_root / f"{cache_id}.json"
    if vector_path.is_file() and meta_path.is_file():
        prior = json.loads(meta_path.read_text(encoding="utf-8"))
        if prior.get("text_sha256") != text_sha or prior.get("revision") != REVISION:
            raise RuntimeError("Embedding cache metadata does not match the exact texts/model revision")
        print(json.dumps({"cache_hit": True, "vectors": str(vector_path), "metadata": str(meta_path)}, indent=2))
        return

    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    raw_lengths = [len(tokenizer.encode(text, add_special_tokens=True).ids) for text in texts]
    truncated_count = sum(length > MAX_LENGTH for length in raw_lengths)
    tokenizer.enable_truncation(max_length=MAX_LENGTH)
    tokenizer.enable_padding(pad_id=tokenizer.token_to_id("[PAD]") or 0, pad_token="[PAD]", direction="right")
    encoded = tokenizer.encode_batch(texts, add_special_tokens=True)

    session_options = ort.SessionOptions()
    session_options.intra_op_num_threads = min(4, max(1, (os_cpu_count() or 4) // 2))
    session_options.inter_op_num_threads = 1
    session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session = ort.InferenceSession(str(model_path), sess_options=session_options, providers=["CPUExecutionProvider"])
    input_names = {item.name for item in session.get_inputs()}
    output_names = [item.name for item in session.get_outputs()]
    embeddings = np.empty((len(texts), 384), dtype=np.float32)
    started = time.perf_counter()
    for start in range(0, len(texts), args.batch_size):
        stop = min(len(texts), start + args.batch_size)
        batch = encoded[start:stop]
        feed = {
            "input_ids": np.asarray([row.ids for row in batch], dtype=np.int64),
            "attention_mask": np.asarray([row.attention_mask for row in batch], dtype=np.int64),
        }
        if "token_type_ids" in input_names:
            feed["token_type_ids"] = np.asarray([row.type_ids for row in batch], dtype=np.int64)
        output = session.run(output_names, feed)
        hidden = np.asarray(output[0], dtype=np.float32)
        mask = feed["attention_mask"].astype(np.float32)[:, :, None]
        pooled = (hidden * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1e-9)
        norms = np.linalg.norm(pooled, axis=1, keepdims=True)
        embeddings[start:stop] = pooled / np.maximum(norms, 1e-12)
        if stop % (args.batch_size * 100) == 0 or stop == len(texts):
            print(f"Embedded {stop:,}/{len(texts):,} development clauses", flush=True)
    elapsed = time.perf_counter() - started

    np.savez(vector_path, point_ids=np.asarray(dev_ids, dtype=np.int64), embeddings=embeddings)
    model_info = {
        "repository": REPOSITORY,
        "revision": REVISION,
        "license": "Apache-2.0 (model repository card)",
        "language_scope": "English",
        "dimension": 384,
        "maximum_wordpieces": MAX_LENGTH,
        "long_input_policy": "truncate to 256 wordpieces; no chunking",
        "truncated_rows": truncated_count,
        "truncated_fraction": truncated_count / max(1, len(texts)),
        "model_file": str(model_path.relative_to(ROOT)),
        "model_sha256": sha256_file(model_path),
        "tokenizer_file": str(tokenizer_path.relative_to(ROOT)),
        "tokenizer_sha256": sha256_file(tokenizer_path),
        "onnxruntime_version": ort.__version__,
        "provider": session.get_providers(),
        "batch_size": args.batch_size,
        "inference_seconds": elapsed,
        "rows_per_second": len(texts) / max(elapsed, 1e-9),
        "dataset_sha256": protocol_rows[0][2]["dataset_sha256"],
        "development_point_ids_sha256": input_ids_sha,
        "development_text_sha256": text_sha,
        "protocols_included": ["primary", "clause"],
        "locked_test_used": False,
        "capped_run": args.max_rows is not None,
        "git_revision": git_revision(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "cache_file": str(vector_path.relative_to(ROOT)),
        "cache_sha256": sha256_file(vector_path),
    }
    meta_path.write_text(json.dumps(model_info, indent=2), encoding="utf-8")
    print(json.dumps(model_info, indent=2))


def os_cpu_count() -> int | None:
    import os

    return os.cpu_count()


if __name__ == "__main__":
    main()
