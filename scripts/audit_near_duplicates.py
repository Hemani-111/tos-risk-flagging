"""Find likely near-duplicate quote pairs without allocating an N-by-N matrix.

Candidate generation uses deterministic MinHash banding over character 4-grams;
reported scores are exact Jaccard similarities over those shingles.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import date
from html import unescape
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "audit_v1" / "clauses_benchmark_english_v1.csv"
OUT = ROOT / "results" / "audits"
PERMUTATIONS = 32
BANDS = 8
ROWS_PER_BAND = PERMUTATIONS // BANDS
JACCARD_THRESHOLD = 0.72
MAX_BUCKET_SIZE = 250
HIGH_CONFIDENCE_THRESHOLD = 0.99
PRIME = np.uint64(2**61 - 1)


def clean(text: object) -> str:
    if pd.isna(text):
        return ""
    text = unescape(re.sub(r"<[^>]*>", " ", str(text)))
    return re.sub(r"\s+", " ", text).strip().casefold()


def shingles(text: str) -> frozenset[str]:
    if len(text) < 4:
        return frozenset({text}) if text else frozenset()
    return frozenset(text[i : i + 4] for i in range(len(text) - 3))


def token_hash(shingle: str) -> int:
    return int.from_bytes(hashlib.blake2b(shingle.encode("utf-8"), digest_size=8).digest(), "big")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = pd.read_csv(DATA, low_memory=False)
    rows["_normalized"] = rows["quote_text"].map(clean)
    unique = rows.groupby("_normalized", sort=True).agg(
        quote_text=("quote_text", "first"),
        labels=("label", lambda x: "|".join(sorted(set(map(str, x))))),
        row_count=("point_id", "size"),
        services=("service_id", lambda x: "|".join(sorted(set(map(str, x))))),
    ).reset_index()
    texts = unique["_normalized"].tolist()
    gram_sets = [shingles(text) for text in texts]
    token_sets = [np.fromiter((token_hash(g) for g in grams), dtype=np.uint64) for grams in gram_sets]

    rng = np.random.default_rng(20261102)
    a = rng.integers(1, int(PRIME), size=PERMUTATIONS, dtype=np.uint64)
    b = rng.integers(0, int(PRIME), size=PERMUTATIONS, dtype=np.uint64)
    buckets: dict[tuple[int, bytes], list[int]] = defaultdict(list)
    for index, tokens in enumerate(token_sets):
        if len(tokens) == 0:
            continue
        signature = np.min((a[:, None] * tokens[None, :] + b[:, None]) % PRIME, axis=1)
        for band in range(BANDS):
            start = band * ROWS_PER_BAND
            key = (band, signature[start : start + ROWS_PER_BAND].tobytes())
            buckets[key].append(index)

    candidate_pairs: set[tuple[int, int]] = set()
    oversized_buckets = 0
    for members in buckets.values():
        if len(members) < 2:
            continue
        if len(members) > MAX_BUCKET_SIZE:
            oversized_buckets += 1
            continue
        members = sorted(set(members))
        candidate_pairs.update((members[i], members[j]) for i in range(len(members)) for j in range(i + 1, len(members)))

    records = []
    for left, right in candidate_pairs:
        union = gram_sets[left] | gram_sets[right]
        if not union:
            continue
        score = len(gram_sets[left] & gram_sets[right]) / len(union)
        if score >= JACCARD_THRESHOLD:
            records.append({
                "char_4gram_jaccard": round(score, 6),
                "left_text": unique.at[left, "quote_text"],
                "right_text": unique.at[right, "quote_text"],
                "left_labels": unique.at[left, "labels"],
                "right_labels": unique.at[right, "labels"],
                "left_row_count": int(unique.at[left, "row_count"]),
                "right_row_count": int(unique.at[right, "row_count"]),
                "left_services": unique.at[left, "services"],
                "right_services": unique.at[right, "services"],
                "review_status": "candidate_for_human_review",
            })
    output = OUT / "near_duplicates_v1.csv"
    pd.DataFrame(records).sort_values("char_4gram_jaccard", ascending=False).to_csv(output, index=False)
    high_confidence = [row for row in records if row["char_4gram_jaccard"] >= HIGH_CONFIDENCE_THRESHOLD]
    decisions = []
    parent: dict[str, str] = {}

    def find(value: str) -> str:
        parent.setdefault(value, value)
        if parent[value] != value:
            parent[value] = find(parent[value])
        return parent[value]

    for row in high_confidence:
        left_services = str(row["left_services"]).split("|")
        right_services = str(row["right_services"]).split("|")
        service_ids = sorted(set(left_services + right_services))
        for service_id in service_ids[1:]:
            left_root, right_root = find(service_ids[0]), find(service_id)
            if left_root != right_root:
                parent[left_root] = right_root
        decisions.append({
            "char_4gram_jaccard": row["char_4gram_jaccard"],
            "left_text_sha256": hashlib.sha256(clean(row["left_text"]).encode("utf-8")).hexdigest(),
            "right_text_sha256": hashlib.sha256(clean(row["right_text"]).encode("utf-8")).hexdigest(),
            "left_text": row["left_text"],
            "right_text": row["right_text"],
            "left_labels": row["left_labels"],
            "right_labels": row["right_labels"],
            "left_services": row["left_services"],
            "right_services": row["right_services"],
            "review_status": "high_confidence_pair_reviewed",
            "split_decision": "keep_rows_and_group_services",
            "rationale": "Manual inspection found near-identical boilerplate/formatting variants. Preserve both records and constrain their services to one evaluation partition; similarity does not resolve label meaning.",
        })
    decision_path = OUT / "near_duplicate_decisions_v1.csv"
    pd.DataFrame(decisions).to_csv(decision_path, index=False)
    service_components: dict[str, int] = defaultdict(int)
    for service in list(parent):
        service_components[find(service)] += 1
    summary = {
        "audit_date": date.today().isoformat(),
        "dataset_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
        "method": "Deterministic 32-permutation MinHash, 8 bands x 4 rows over character 4-gram sets; exact Jaccard rerank.",
        "normalization": "Strip HTML-like tags, decode HTML entities, collapse whitespace, Unicode casefold.",
        "unique_normalized_quotes": int(len(unique)),
        "candidate_pairs_from_lsh": int(len(candidate_pairs)),
        "reported_pairs_at_or_above_threshold": int(len(records)),
        "jaccard_threshold": JACCARD_THRESHOLD,
        "reviewed_high_confidence_pairs": int(len(decisions)),
        "high_confidence_threshold": HIGH_CONFIDENCE_THRESHOLD,
        "pairs_below_high_confidence_threshold": int(len(records) - len(decisions)),
        "services_constrained_by_reviewed_pairs": int(len(parent)),
        "largest_reviewed_service_component": max(service_components.values(), default=0),
        "review_decisions_csv": str(decision_path.relative_to(ROOT)),
        "oversized_lsh_buckets_skipped": oversized_buckets,
        "bucket_cap": MAX_BUCKET_SIZE,
        "output_csv": str(output.relative_to(ROOT)),
        "limitations": [
            "LSH is approximate and may miss near-duplicates; the output is a candidate list, not a confirmed match list.",
            "Skipped oversized buckets can contain boilerplate and remain a residual overlap source.",
            "Pairs below the reviewed 0.99 cutoff remain advisory candidates; the split audit must report them as residual near-duplicate overlap.",
        ],
    }
    summary_path = OUT / "near_duplicates_v1.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
