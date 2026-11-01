"""Validate and summarize both committed evaluation split settings."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.splitting import load_split_bundle  # noqa: E402


def main() -> None:
    report = {}
    for protocol in ("primary", "clause"):
        frame, metadata = load_split_bundle(protocol, ROOT)
        partition_col = f"{protocol}_partition"
        include_col = f"{protocol}_include"
        report[protocol] = {
            "source_rows": int(len(frame)),
            "included_rows": int(frame[include_col].sum()),
            "excluded_rows": int((~frame[include_col]).sum()),
            "partitions": {
                partition: int((frame[partition_col].eq(partition) & frame[include_col]).sum())
                for partition in ("train", "validation", "test")
            },
            "dataset_sha256": metadata["dataset_sha256"],
        }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
