"""Create the shared Phase 2 split manifest; no model fitting is performed."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import date
from html import unescape
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "audit_v1" / "clauses_benchmark_english_v1.csv"
NEAR_PAIRS = ROOT / "results" / "audits" / "near_duplicates_v1.csv"
NEAR_DECISIONS = ROOT / "results" / "audits" / "near_duplicate_decisions_v1.csv"
OUT = ROOT / "data" / "splits"
SEED = 20261102
N_OUTER_FOLDS = 20


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(text: object) -> str:
    if pd.isna(text):
        return ""
    return re.sub(r"\s+", " ", str(text)).strip().casefold()


def clean_for_near(text: object) -> str:
    if pd.isna(text):
        return ""
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]*>", " ", str(text)))).strip().casefold()


def canonical_id(value: object) -> str:
    if pd.isna(value):
        return ""
    try:
        numeric = float(value)
        if numeric.is_integer():
            return str(int(numeric))
    except (TypeError, ValueError):
        pass
    return str(value).strip()


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, key: str) -> str:
        self.parent.setdefault(key, key)
        if self.parent[key] != key:
            self.parent[key] = self.find(self.parent[key])
        return self.parent[key]

    def union(self, keys: list[str]) -> None:
        keys = sorted(set(key for key in keys if key))
        if len(keys) < 2:
            for key in keys:
                self.find(key)
            return
        root = self.find(keys[0])
        for key in keys[1:]:
            other = self.find(key)
            if root != other:
                self.parent[other] = root

    def component_ids(self, prefix: str) -> dict[str, str]:
        members: dict[str, list[str]] = defaultdict(list)
        for key in list(self.parent):
            members[self.find(key)].append(key)
        output = {}
        for values in members.values():
            component = prefix + hashlib.sha256("|".join(sorted(values)).encode("utf-8")).hexdigest()[:12]
            output.update({value: component for value in values})
        return output


def split_labels(y: np.ndarray, groups: np.ndarray, seed: int, fold_counts: tuple[int, int, int]) -> tuple[np.ndarray, np.ndarray]:
    splitter = StratifiedGroupKFold(n_splits=N_OUTER_FOLDS, shuffle=True, random_state=seed)
    folds = np.full(len(y), -1, dtype=np.int16)
    for fold, (_, test_index) in enumerate(splitter.split(np.zeros(len(y)), y, groups)):
        folds[test_index] = fold
    if (folds < 0).any():
        raise AssertionError("Some rows were not assigned to an outer fold")
    train_count, validation_count, test_count = fold_counts
    if train_count + validation_count + test_count != N_OUTER_FOLDS:
        raise ValueError("Outer fold counts must sum to N_OUTER_FOLDS")
    validation_folds = set(range(train_count, train_count + validation_count))
    partition = np.select(
        [folds < train_count, np.isin(folds, list(validation_folds))],
        ["train", "validation"], default="test",
    )
    return partition.astype(str), folds


def training_cv(y: np.ndarray, groups: np.ndarray, partition: np.ndarray, seed: int) -> np.ndarray:
    cv_fold = np.full(len(y), -1, dtype=np.int8)
    train_idx = np.flatnonzero(partition == "train")
    splitter = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=seed)
    for fold, (_, heldout) in enumerate(splitter.split(np.zeros(len(train_idx)), y[train_idx], groups[train_idx])):
        cv_fold[train_idx[heldout]] = fold
    return cv_fold


def apply_near_duplicate_exclusions(
    frame: pd.DataFrame, partition_col: str, include_col: str, reason_col: str, near_pairs: pd.DataFrame
) -> tuple[int, dict[str, int], int]:
    priority = {"train": 0, "validation": 1, "test": 2}
    priority = {"train": 0, "validation": 1, "test": 2}
    partition_for_text = frame.groupby("near_text_key")[partition_col].agg(
        lambda values: min(set(values), key=priority.get)
    ).to_dict()
    excluded: dict[tuple[str, str], set[str]] = defaultdict(set)
    exact_crossing_groups = 0
    for text_key, group in frame.groupby("near_text_key", sort=False):
        partitions = set(group[partition_col])
        if len(partitions) > 1:
            exact_crossing_groups += 1
            keep_partition = min(partitions, key=priority.get)
            for partition in partitions - {keep_partition}:
                excluded[(text_key, partition)].add("exact_visible_text_cross_partition")
    crossing_pairs = 0
    for row in near_pairs.itertuples(index=False):
        left, right = clean_for_near(row.left_text), clean_for_near(row.right_text)
        if left not in partition_for_text or right not in partition_for_text:
            continue
        left_partition, right_partition = partition_for_text[left], partition_for_text[right]
        if left_partition == right_partition:
            continue
        crossing_pairs += 1
        drop_text, drop_partition = (left, left_partition) if priority[left_partition] > priority[right_partition] else (right, right_partition)
        excluded[(drop_text, drop_partition)].add("near_duplicate_cross_partition")
    row_keys = zip(frame["near_text_key"], frame[partition_col])
    frame[include_col] = [key not in excluded for key in row_keys]
    frame[reason_col] = ["|".join(sorted(excluded.get(key, set()))) for key in zip(frame["near_text_key"], frame[partition_col])]
    excluded_by_partition = {
        partition: int((frame[partition_col].eq(partition) & ~frame[include_col]).sum())
        for partition in ("train", "validation", "test")
    }
    return crossing_pairs, excluded_by_partition, exact_crossing_groups


def partition_summary(frame: pd.DataFrame, column: str, include_col: str) -> dict[str, object]:
    included_rows = int(frame[include_col].sum())
    counts = {}
    for partition in ("train", "validation", "test"):
        assigned = frame.loc[frame[column].eq(partition)]
        subset = assigned.loc[assigned[include_col]]
        counts[partition] = {
            "rows": int(len(subset)),
            "fraction_of_included": round(len(subset) / included_rows, 6),
            "fraction_of_source": round(len(subset) / len(frame), 6),
            "excluded_rows": int(len(assigned) - len(subset)),
            "labels": {str(k): int(v) for k, v in subset["label"].value_counts().sort_index().items()},
            "distinct_services": int(subset["service_key"].nunique()),
            "distinct_documents": int(subset["document_key"].replace("", np.nan).nunique()),
        }
    return counts


def check_group_isolation(frame: pd.DataFrame, group_col: str, partition_col: str) -> bool:
    return bool(frame.groupby(group_col)[partition_col].nunique().le(1).all())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(DATA, low_memory=False)
    if frame["point_id"].duplicated().any():
        raise ValueError("point_id must be unique in the benchmark candidate")
    frame["service_key"] = frame["service_id"].map(canonical_id)
    frame["document_key"] = frame["document_id"].map(canonical_id)
    frame["exact_text_key"] = frame["quote_text"].map(normalize)
    frame["near_text_key"] = frame["quote_text"].map(clean_for_near)
    frame["near_text_hash"] = frame["near_text_key"].map(lambda x: hashlib.sha256(x.encode("utf-8")).hexdigest())
    y = frame["label"].to_numpy()
    near_pairs = pd.read_csv(NEAR_PAIRS, low_memory=False)

    documents = pd.read_csv(ROOT / "data" / "raw" / "documents.csv", usecols=["id", "service_id"], low_memory=False)
    document_service = {
        canonical_id(doc_id): canonical_id(service_id)
        for doc_id, service_id in zip(documents["id"], documents["service_id"])
    }
    service_groups = UnionFind()
    for service in frame["service_key"]:
        service_groups.find(service)
    for _, group in frame.groupby("exact_text_key", sort=False):
        service_groups.union(group["service_key"].tolist())
    for _, group in frame.loc[frame["document_key"].ne("")].groupby("document_key", sort=False):
        service_groups.union(group["service_key"].tolist())

    document_service_mismatches = []
    for row in frame.loc[frame["document_key"].ne(""), ["point_id", "document_key", "service_key"]].itertuples(index=False):
        source_service = document_service.get(row.document_key, "")
        if source_service and row.service_key and source_service != row.service_key:
            document_service_mismatches.append({
                "point_id": int(row.point_id),
                "document_id": row.document_key,
                "point_service_id": row.service_key,
                "document_service_id": source_service,
            })
            service_groups.union([source_service, row.service_key])

    near_decisions = pd.read_csv(NEAR_DECISIONS, low_memory=False)
    for row in near_decisions.itertuples(index=False):
        linked_services = str(row.left_services).split("|") + str(row.right_services).split("|")
        service_groups.union(linked_services)
    service_component_map = service_groups.component_ids("svc-")
    frame["service_component"] = frame["service_key"].map(service_component_map)
    if frame["service_component"].isna().any():
        raise AssertionError("Missing service component assignment")

    frame["primary_partition"], primary_outer_fold = split_labels(y, frame["service_component"].to_numpy(), SEED, (14, 3, 3))
    frame["primary_outer_fold"] = primary_outer_fold
    frame["primary_cv_fold"] = training_cv(y, frame["service_component"].to_numpy(), frame["primary_partition"].to_numpy(), SEED + 1)
    primary_cross_pairs_before_exclusion, primary_excluded, primary_visible_cross_groups = apply_near_duplicate_exclusions(
        frame, "primary_partition", "primary_include", "primary_exclusion_reason", near_pairs
    )

    text_groups = UnionFind()
    for key in frame["near_text_hash"]:
        text_groups.find(key)
    for row in near_decisions.itertuples(index=False):
        text_groups.union([str(row.left_text_sha256), str(row.right_text_sha256)])
    text_component_map = text_groups.component_ids("txt-")
    frame["text_component"] = frame["near_text_hash"].map(text_component_map)
    frame["clause_partition"], clause_outer_fold = split_labels(y, frame["text_component"].to_numpy(), SEED, (14, 3, 3))
    frame["clause_outer_fold"] = clause_outer_fold
    frame["clause_cv_fold"] = training_cv(y, frame["text_component"].to_numpy(), frame["clause_partition"].to_numpy(), SEED + 1)
    clause_cross_pairs_before_exclusion, clause_excluded, clause_visible_cross_groups = apply_near_duplicate_exclusions(
        frame, "clause_partition", "clause_include", "clause_exclusion_reason", near_pairs
    )

    for partition_column, include_column in (("primary_partition", "primary_include"), ("clause_partition", "clause_include")):
        for partition in ("train", "validation", "test"):
            found = set(frame.loc[frame[partition_column].eq(partition) & frame[include_column], "label"])
            if found != set(frame["label"]):
                raise AssertionError(f"{partition_column}/{partition} is missing one or more labels")
    if not check_group_isolation(frame.loc[frame["primary_partition"].eq("train")], "service_component", "primary_cv_fold"):
        raise AssertionError("Primary training groups cross CV folds")
    if not check_group_isolation(frame.loc[frame["clause_partition"].eq("train")], "text_component", "clause_cv_fold"):
        raise AssertionError("Clause training groups cross CV folds")

    manifest = frame[[
        "point_id", "service_component", "text_component", "primary_partition", "primary_outer_fold",
        "primary_cv_fold", "primary_include", "primary_exclusion_reason", "clause_partition",
        "clause_outer_fold", "clause_cv_fold", "clause_include", "clause_exclusion_reason",
    ]].copy()
    manifest_path = OUT / "split_manifest_v1.csv"
    manifest.to_csv(manifest_path, index=False)

    primary_exact_text_overlap = any(
        group.loc[group["primary_include"], "primary_partition"].nunique() > 1
        for _, group in frame.groupby("exact_text_key", sort=False)
    )
    primary_document_overlap = any(
        group["primary_partition"].nunique() > 1
        for _, group in frame.loc[frame["document_key"].ne("")].groupby("document_key", sort=False)
    )
    clause_exact_text_overlap = any(
        group.loc[group["clause_include"], "clause_partition"].nunique() > 1
        for _, group in frame.groupby("near_text_key", sort=False)
    )
    primary_visible_text_overlap = any(
        group.loc[group["primary_include"], "primary_partition"].nunique() > 1
        for _, group in frame.groupby("near_text_key", sort=False)
    )
    primary_group_overlap = not check_group_isolation(frame, "service_component", "primary_partition")
    clause_group_overlap = not check_group_isolation(frame, "text_component", "clause_partition")
    if any((primary_exact_text_overlap, primary_visible_text_overlap, primary_document_overlap, clause_exact_text_overlap, primary_group_overlap, clause_group_overlap)):
        raise AssertionError("A split isolation assertion failed")

    primary_partition_by_text = frame.loc[frame["primary_include"]].groupby("near_text_key")["primary_partition"].first().to_dict()
    clause_partition_by_text = frame.loc[frame["clause_include"]].groupby("near_text_key")["clause_partition"].first().to_dict()
    primary_residual_near_crossings = 0
    clause_residual_near_crossings = 0
    for row in near_pairs.itertuples(index=False):
        left, right = clean_for_near(row.left_text), clean_for_near(row.right_text)
        if left in primary_partition_by_text and right in primary_partition_by_text:
            primary_residual_near_crossings += int(primary_partition_by_text[left] != primary_partition_by_text[right])
        if left in clause_partition_by_text and right in clause_partition_by_text:
            clause_residual_near_crossings += int(clause_partition_by_text[left] != clause_partition_by_text[right])

    service_component_sizes = frame.drop_duplicates("service_component")["service_component"].value_counts()
    text_component_sizes = frame.drop_duplicates("text_component")["text_component"].value_counts()
    try:
        git_revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        git_revision = "unknown"

    metadata = {
        "split_id": "split_manifest_v1",
        "created_date": date.today().isoformat(),
        "git_revision": git_revision,
        "dataset": str(DATA.relative_to(ROOT)),
        "dataset_sha256": sha256(DATA),
        "near_duplicate_candidate_sha256": sha256(NEAR_PAIRS),
        "near_duplicate_decisions_sha256": sha256(NEAR_DECISIONS),
        "row_count": int(len(frame)),
        "seed": SEED,
        "allocation": {"outer_folds": N_OUTER_FOLDS, "primary_fold_counts_train_validation_test": [14, 3, 3], "clause_fold_counts_train_validation_test": [14, 3, 3], "target_fractions": {"train": 0.70, "validation": 0.15, "test": 0.15}},
        "assignment_method": "One fixed StratifiedGroupKFold(20, shuffle=True, random_state=20261102) assignment per protocol. Folds 0-13 train, 14-16 validation, 17-19 locked test. No seed search.",
        "primary_grouping": "Connected service components from normalized exact quote text, repeated document IDs, point/document service mismatches, and reviewed near-duplicate pairs with character 4-gram Jaccard >=0.99. Cross-partition exact visible-text matches and lower-similarity candidates are excluded from the lower-priority holdout.",
        "secondary_grouping": "Connected normalized visible-text components from exact text matches and reviewed near-duplicate pairs with character 4-gram Jaccard >=0.99; services may overlap.",
        "development_cv": "Three-fold StratifiedGroupKFold within training rows only; validation is available for candidate selection; test remains locked.",
        "primary_partition_counts": partition_summary(frame, "primary_partition", "primary_include"),
        "clause_partition_counts": partition_summary(frame, "clause_partition", "clause_include"),
        "group_sizes": {
            "primary_component_count": int(service_component_sizes.size),
            "primary_largest_component_rows": int(frame["service_component"].value_counts().max()),
            "primary_largest_component_services": int(frame.drop_duplicates(["service_component", "service_key"]).groupby("service_component").size().max()),
            "clause_component_count": int(text_component_sizes.size),
            "clause_largest_component_rows": int(frame["text_component"].value_counts().max()),
        },
        "overlap_audit": {
            "primary_service_component_cross_partition": primary_group_overlap,
            "primary_exact_normalized_text_cross_partition": primary_exact_text_overlap,
            "primary_exact_visible_text_cross_partition_after_exclusion": primary_visible_text_overlap,
            "primary_exact_visible_text_groups_crossing_before_exclusion": primary_visible_cross_groups,
            "clause_exact_visible_text_groups_crossing_before_exclusion": clause_visible_cross_groups,
            "primary_document_id_cross_partition": primary_document_overlap,
            "primary_point_document_service_mismatch_rows": len(document_service_mismatches),
            "primary_point_document_service_mismatches": document_service_mismatches,
            "clause_text_component_cross_partition": clause_group_overlap,
            "clause_exact_visible_text_cross_partition": clause_exact_text_overlap,
            "residual_near_duplicate_candidate_pairs_crossing_primary_partitions": primary_residual_near_crossings,
            "residual_near_duplicate_candidate_pairs_crossing_clause_partitions": clause_residual_near_crossings,
            "near_duplicate_candidate_pairs_crossing_primary_before_exclusion": primary_cross_pairs_before_exclusion,
            "near_duplicate_candidate_pairs_crossing_clause_before_exclusion": clause_cross_pairs_before_exclusion,
            "rows_excluded_from_primary_by_partition": primary_excluded,
            "rows_excluded_from_clause_by_partition": clause_excluded,
            "note": "For every detected near-duplicate candidate pair crossing partitions, exclude the text group from the lower-priority holdout partition (train > validation > test). The MinHash audit is approximate and can miss matches.",
        },
        "selection_criteria_registered": {
            "primary_metric": "macro F1",
            "operating_tradeoffs": ["Risky recall", "Risky precision"],
            "operational_costs": ["inference latency", "artifact size", "peak memory when measurable"],
        },
        "near_duplicate_exclusion_policy": "Keep all training rows; if a detected near-duplicate text pair crosses partitions, remove its text rows from the lower-priority holdout (validation before test). Both endpoints are excluded from evaluation only if separate pairs require it. Rows remain in the source dataset and manifest with explicit exclusion reasons.",
        "limitations": [
            "The group constraints can move the achieved split proportions away from 70/15/15; report the actual counts above.",
            "Near-duplicate LSH has residual false negatives; detected pairs are excluded across partitions, while missed pairs remain possible.",
            "Rows excluded for conflicting labels remain outside both single-label split settings.",
        ],
    }
    metadata_path = OUT / "split_manifest_v1.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
