"""Check candidate document services against the full conflict-free dataset."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ALIASES = {
    "Anthropic": ["Anthropic"],
    "Mistral AI": ["Mistral AI", "Mistral"],
    "Perplexity AI": ["Perplexity AI", "Perplexity"],
    "You.com": ["You.com"],
}


def main() -> None:
    services = pd.read_csv(ROOT / "data" / "raw" / "services.csv", usecols=["id", "name"])
    benchmark = pd.read_csv(ROOT / "data" / "processed" / "audit_v1" / "clauses_benchmark_v1.csv", usecols=["service_id"])
    present_ids = set(benchmark["service_id"].dropna().astype(int))
    results = []
    for canonical, aliases in ALIASES.items():
        matches = services.loc[services["name"].fillna("").map(lambda name: any(alias.casefold() in name.casefold() for alias in aliases))]
        benchmark_matches = matches.loc[matches["id"].isin(present_ids)]
        results.append({"service": canonical, "matched_raw_names": matches["name"].astype(str).tolist(),
                        "matched_dataset_names": benchmark_matches["name"].astype(str).tolist(),
                        "matched_dataset_service_ids": benchmark_matches["id"].astype(int).tolist(),
                        "absent_from_full_conflict_free_benchmark": benchmark_matches.empty})
    if not all(row["absent_from_full_conflict_free_benchmark"] for row in results):
        raise SystemExit("At least one candidate document service occurs in the benchmark; replace it before annotation")
    output = ROOT / "results" / "error_analysis" / "v1" / "document_source_overlap_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"benchmark": "clauses_benchmark_v1.csv", "results": results}, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
