"""Load and validate the project-wide frozen train/validation/test manifests."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
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


def load_development_bundle(protocol: str, root: Path | str = ROOT) -> tuple[pd.DataFrame, dict[str, object]]:
    """Load train/validation rows without parsing locked-test CSV fields.

    The frozen source CSV is row-aligned with the manifest. We checksum the
    source bytes, scan CSV record boundaries while retaining only the first
    point_id field, and ask pandas to skip every locked-test record before
    parsing any of its fields.
    """
    if protocol not in {"primary", "clause"}:
        raise ValueError("protocol must be 'primary' or 'clause'")
    root = Path(root).resolve()
    metadata_path = root / "data" / "splits" / "split_manifest_v1.json"
    manifest_path = root / "data" / "splits" / "split_manifest_v1.csv"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    dataset_path = root / metadata["dataset"]
    if _sha256(dataset_path) != metadata["dataset_sha256"]:
        raise ValueError("Dataset checksum differs from the frozen split metadata")
    manifest = pd.read_csv(manifest_path, low_memory=False)
    partition_col = f"{protocol}_partition"
    dev_manifest = manifest.loc[manifest[partition_col].isin(["train", "validation"])].copy()
    dev_ids = set(dev_manifest["point_id"].astype(int))
    development_records: list[tuple[int, int]] = []
    seen_ids: set[int] = set()
    with dataset_path.open("rb") as source:
        header_line = source.readline()
        header = header_line.rstrip(b"\r\n").split(b",", 1)[0]
        if header != b"point_id":
            raise ValueError("Expected point_id as the first dataset column")
        record_start_offset = source.tell()
        offset = record_start_offset
        row_number = 0
        first_field = bytearray()
        at_first_field = True
        in_quotes = False
        quote_pending = False
        while chunk := source.read(64 * 1024):
            for index, value in enumerate(chunk):
                absolute_offset = offset + index
                if at_first_field:
                    if value == ord(","):
                        at_first_field = False
                    else:
                        first_field.append(value)
                    continue
                if quote_pending:
                    if value == ord('"'):
                        quote_pending = False  # escaped quote inside a field
                        continue
                    in_quotes = False
                    quote_pending = False
                if value == ord('"'):
                    if in_quotes:
                        quote_pending = True
                    else:
                        in_quotes = True
                elif value == ord("\n"):
                    if not in_quotes:
                        try:
                            point_id = int(first_field.rstrip(b"\r"))
                        except ValueError as exc:
                            raise ValueError("Could not read a dataset record point_id") from exc
                        row_number += 1
                        if point_id in dev_ids:
                            if point_id in seen_ids:
                                raise ValueError("Dataset point_id values are not unique")
                            development_records.append((record_start_offset, absolute_offset + 1))
                        else:
                            if point_id in seen_ids:
                                raise ValueError("Dataset point_id values are not unique")
                        seen_ids.add(point_id)
                        first_field.clear()
                        at_first_field = True
                        in_quotes = False
                        quote_pending = False
                        record_start_offset = absolute_offset + 1
            offset += len(chunk)
        if first_field or not at_first_field:
            try:
                point_id = int(first_field.rstrip(b"\r"))
            except ValueError as exc:
                raise ValueError("Could not read final dataset record point_id") from exc
            row_number += 1
            if point_id in seen_ids:
                raise ValueError("Dataset point_id values are not unique")
            if point_id in dev_ids:
                development_records.append((record_start_offset, offset))
            seen_ids.add(point_id)
    if row_number != metadata["row_count"] or seen_ids != set(manifest["point_id"].astype(int)):
        raise ValueError("Dataset physical row order does not match the frozen manifest contract")

    with tempfile.TemporaryDirectory(prefix="tos-development-split-") as temp_dir:
        development_path = Path(temp_dir) / "development.csv"
        with development_path.open("wb") as target, dataset_path.open("rb") as source:
            target.write(header_line)
            for start, end in development_records:
                source.seek(start)
                remaining = end - start
                while remaining:
                    block = source.read(min(64 * 1024, remaining))
                    if not block:
                        raise ValueError("Unexpected end of dataset while creating development-only split")
                    target.write(block)
                    remaining -= len(block)
        data = pd.read_csv(development_path, low_memory=False)
    if set(data["point_id"].astype(int)) != dev_ids:
        loaded_ids = set(data["point_id"].astype(int))
        raise ValueError(f"Development-only CSV load mismatch: {len(loaded_ids)} loaded vs {len(dev_ids)} expected; missing={len(dev_ids - loaded_ids)}; extra={len(loaded_ids - dev_ids)}; sample_extra={sorted(loaded_ids - dev_ids)[:10]}")
    merged = data.merge(dev_manifest, on="point_id", how="outer", validate="one_to_one", indicator=True)
    if not merged["_merge"].eq("both").all():
        raise ValueError("Development dataset rows do not match the split manifest")
    merged = merged.drop(columns="_merge")
    group_col = "service_component" if protocol == "primary" else "text_component"
    if not merged.groupby(group_col)[partition_col].nunique().le(1).all():
        raise ValueError(f"{group_col} crosses {protocol} development partitions")
    included = merged.loc[merged[f"{protocol}_include"]]
    normalize = _normalize_exact if protocol == "primary" else _normalize_visible
    normalized = included["quote_text"].map(normalize)
    if included.assign(_key=normalized).groupby("_key")[partition_col].nunique().gt(1).any():
        raise ValueError(f"Exact text crosses included {protocol} development partitions")
    train = merged.loc[merged[partition_col].eq("train")]
    fold_col = f"{protocol}_cv_fold"
    if not train.groupby(group_col)[fold_col].nunique().le(1).all() or train[fold_col].lt(0).any():
        raise ValueError("Training development groups cross or lack fixed CV folds")
    if merged.loc[merged[partition_col].eq("validation"), fold_col].ne(-1).any():
        raise ValueError("Validation rows must not receive training CV folds")
    return merged, metadata
