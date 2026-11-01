"""Load and validate the project-wide frozen train/validation/test manifests."""

from __future__ import annotations

import hashlib
import json
import re
from html import unescape
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_exact(text: object) -> str:
    if pd.isna(text):
        return ""
    return re.sub(r"\s+", " ", str(text)).strip().casefold()


def _normalize_visible(text: object) -> str:
    if pd.isna(text):
        return ""
    text = unescape(re.sub(r"<[^>]*>", " ", str(text)))
    return re.sub(r"\s+", " ", text).strip().casefold()


def load_split_bundle(protocol: str, root: Path | str = ROOT) -> tuple[pd.DataFrame, dict[str, object]]:
    """Return source rows joined to the frozen manifest after checking its contract.

    `protocol` is `primary` for unseen-service or `clause` for duplicate-aware
    clause-level evaluation. Excluded holdout rows remain in the returned frame;
    callers must filter by the corresponding `<protocol>_include` column.
    """
    if protocol not in {"primary", "clause"}:
        raise ValueError("protocol must be 'primary' or 'clause'")
    root = Path(root).resolve()
    metadata_path = root / "data" / "splits" / "split_manifest_v1.json"
    manifest_path = root / "data" / "splits" / "split_manifest_v1.csv"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    dataset_path = root / metadata["dataset"]
    if _sha256(dataset_path) != metadata["dataset_sha256"]:
        raise ValueError("Dataset checksum differs from the frozen split metadata; regenerate splits deliberately")

    data = pd.read_csv(dataset_path, low_memory=False)
    manifest = pd.read_csv(manifest_path, low_memory=False)
    if len(data) != metadata["row_count"] or len(manifest) != len(data):
        raise ValueError("Dataset and split manifest row counts do not match metadata")
    if data["point_id"].duplicated().any() or manifest["point_id"].duplicated().any():
        raise ValueError("point_id must be unique in both dataset and manifest")
    merged = data.merge(manifest, on="point_id", how="outer", validate="one_to_one", indicator=True)
    if not merged["_merge"].eq("both").all():
        raise ValueError("Split manifest does not cover the dataset row IDs exactly")
    merged = merged.drop(columns="_merge")

    partition_col = f"{protocol}_partition"
    include_col = f"{protocol}_include"
    group_col = "service_component" if protocol == "primary" else "text_component"
    cv_col = f"{protocol}_cv_fold"
    if not merged.groupby(group_col)[partition_col].nunique().le(1).all():
        raise ValueError(f"{group_col} crosses {protocol} partitions")
    train = merged.loc[merged[partition_col].eq("train")]
    if not train.groupby(group_col)[cv_col].nunique().le(1).all() or train[cv_col].lt(0).any():
        raise ValueError(f"Training {group_col} values cross or lack development CV folds")
    if merged.loc[~merged[partition_col].eq("train"), cv_col].ne(-1).any():
        raise ValueError("Validation and test rows must not receive training CV folds")

    included = merged.loc[merged[include_col]].copy()
    normalize = _normalize_exact if protocol == "primary" else _normalize_visible
    text_col = included["quote_text"].map(normalize)
    if included.assign(_key=text_col).groupby("_key")[partition_col].nunique().gt(1).any():
        raise ValueError(f"Exact text crosses included {protocol} partitions")
    if protocol == "primary":
        if included.groupby("service_component")[partition_col].nunique().gt(1).any():
            raise ValueError("Services cross primary partitions")
        docs = included.loc[included["document_id"].notna()]
        if docs.groupby("document_id")[partition_col].nunique().gt(1).any():
            raise ValueError("Documents cross primary partitions")

    all_labels = set(merged["label"])
    for partition in ("train", "validation", "test"):
        found = set(included.loc[included[partition_col].eq(partition), "label"])
        if found != all_labels:
            raise ValueError(f"Included {partition} rows do not contain every dataset label")
    if metadata["overlap_audit"][f"residual_near_duplicate_candidate_pairs_crossing_{protocol}_partitions"] != 0:
        raise ValueError("Detected near-duplicate candidates still cross included partitions")
    return merged, metadata
