#!/usr/bin/env python3
"""Sampling provenance analysis.

Inspects the actual selection code and saved sample IDs to:
1. Establish whether sampling was independently stratified by document or globally random
2. Derive inclusion probabilities from the actual two-phase design
3. Correct metadata and scoring guidance accordingly

Usage:
    .venv-training-stack/bin/python scripts/sampling_provenance_analysis.py
"""
from __future__ import annotations

import csv
import json
import random
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "data" / "review" / "real_document_eval_v2"
SHEET_DIR = EVAL_DIR / "review_sheets"
API_DIR = EVAL_DIR / "api_outputs"
OUT_DIR = EVAL_DIR / "aggregate" / "sampling_provenance"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_SEED = 20261106
SAMPLE_TARGET_MIN = 150
SAMPLE_TARGET_MAX = 250


def load_population_clauses() -> dict[str, list[dict]]:
    """Load all clauses from API outputs (the population frame).
    Only includes documents with usable clauses (7 successful docs)."""
    by_doc = {}
    for p in sorted(API_DIR.glob('*.json')):
        obj = json.loads(p.read_text(encoding='utf-8'))
        did = obj['document_id']
        d = obj.get('api_first') or {}
        clauses = d.get('clauses') or []
        if clauses:  # only include documents with usable clauses
            by_doc[did] = clauses
    return by_doc


def load_actual_sample() -> list[dict]:
    """Load the actual sampled clauses from reviewer A sheet."""
    path = SHEET_DIR / "reviewer_A_blind_representative_v2.csv"
    sample = []
    with path.open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            sample.append(row)
    return sample


def compute_design_inclusion_probs(by_doc: dict[str, list[dict]]) -> dict[str, dict]:
    """Compute design-based inclusion probabilities for the two-phase design.

    Phase 1: stratified allocation of per = SAMPLE_TARGET_MIN // n_docs clauses per document.
    Phase 2: global random fill from pooled remaining to reach SAMPLE_TARGET_MAX.
    """
    n_docs = len(by_doc)
    per = max(1, SAMPLE_TARGET_MIN // max(1, n_docs))  # = 21
    phase1_total = sum(min(per, len(items)) for items in by_doc.values())  # = 147
    phase2_slots = SAMPLE_TARGET_MAX - phase1_total  # = 103
    total_remaining = sum(len(items) for items in by_doc.values()) - phase1_total  # = 2308

    phase2_prob = phase2_slots / total_remaining  # = 103/2308

    results = {}
    for did, items in by_doc.items():
        N_h = len(items)
        k_h = min(per, N_h)  # = 21 for all docs (all N_h >= 243)
        p_phase1 = k_h / N_h
        p_phase2_given_not_phase1 = phase2_prob
        pi_h = p_phase1 + (1 - p_phase1) * p_phase2_given_not_phase1

        results[did] = {
            "N_h": N_h,
            "k_h_phase1": k_h,
            "p_phase1": p_phase1,
            "p_phase2_given_not_phase1": p_phase2_given_not_phase1,
            "design_inclusion_probability": pi_h,
            "design_weight": 1 / pi_h,
            "empirical_n_h": None,  # filled below
            "empirical_inclusion_probability": None,  # filled below
        }
    return results, per, phase1_total, phase2_slots, total_remaining


def main():
    by_doc = load_population_clauses()
    actual_sample = load_actual_sample()

    # Count actual sample per document
    actual_n_h = {}
    for row in actual_sample:
        did = row['document_id']
        actual_n_h[did] = actual_n_h.get(did, 0) + 1

    print("=== SAMPLING PROVENANCE ANALYSIS ===")
    print(f"Population documents: {len(by_doc)}")
    print(f"Total population clauses (N): {sum(len(v) for v in by_doc.values())}")
    print(f"Sample seed: {SAMPLE_SEED}")
    print(f"Sample target range: [{SAMPLE_TARGET_MIN}, {SAMPLE_TARGET_MAX}]")
    print(f"Actual sample size: {len(actual_sample)}")
    print()

    # Reproduce the design
    design, per, phase1_total, phase2_slots, total_remaining = compute_design_inclusion_probs(by_doc)

    print("=== TWO-PHASE DESIGN ===")
    print(f"Phase 1: stratified allocation of {per} clauses per document")
    print(f"Phase 1 total: {phase1_total} ({len(by_doc)} docs × {per})")
    print(f"Phase 2: global random fill of {phase2_slots} clauses from {total_remaining} remaining")
    print(f"Phase 2 inclusion probability (given not in phase 1): {phase2_slots}/{total_remaining} = {phase2_slots/total_remaining:.6f}")
    print()

    print("=== PER-DOCUMENT DESIGN PROPERTIES ===")
    print(f"{'Document':<30} {'N_h':>6} {'n_h (actual)':>12} {'k_h (phase1)':>12} {'pi_h (design)':>14} {'1/pi_h (weight)':>16} {'n_h/N_h (empirical)':>18}")
    print("-" * 110)

    total_N = 0
    total_n = 0
    for did in sorted(by_doc.keys()):
        N_h = len(by_doc[did])
        n_h_actual = actual_n_h.get(did, 0)
        d = design[did]
        d["empirical_n_h"] = n_h_actual
        d["empirical_inclusion_probability"] = n_h_actual / N_h if N_h > 0 else 0

        total_N += N_h
        total_n += n_h_actual

        print(f"{did:<30} {N_h:>6} {n_h_actual:>12} {d['k_h_phase1']:>12} {d['design_inclusion_probability']:>14.6f} {d['design_weight']:>16.2f} {d['empirical_inclusion_probability']:>18.6f}")

    print("-" * 110)
    print(f"{'TOTAL':<30} {total_N:>6} {total_n:>12} {'':>12} {'':>14} {'':>16} {'':>18}")
    print()

    # Verify: does the design match the actual sample?
    print("=== DESIGN vs ACTUAL VERIFICATION ===")
    for did in sorted(by_doc.keys()):
        d = design[did]
        print(f"  {did}: design k_h={d['k_h_phase1']}, actual n_h={d['empirical_n_h']}, "
              f"fill_from_phase2={d['empirical_n_h'] - d['k_h_phase1']}")

    print(f"\nPhase 2 fill total: {sum(d['empirical_n_h'] - d['k_h_phase1'] for d in design.values())} (expected {phase2_slots})")
    print()

    # Stratum weights (population composition)
    print("=== STRATUM WEIGHTS (population composition) ===")
    for did in sorted(by_doc.keys()):
        N_h = len(by_doc[did])
        stratum_weight = N_h / total_N
        print(f"  {did}: N_h/N = {N_h}/{total_N} = {stratum_weight:.6f}")

    print()

    # Save corrected metadata
    corrected_meta = {
        "analysis_id": f"sampling_provenance_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "evaluation_id": "real_document_eval_v2",
        "design": "two-phase: (1) stratified allocation of per-document clauses, (2) global random fill to target",
        "seed": SAMPLE_SEED,
        "target_range": [SAMPLE_TARGET_MIN, SAMPLE_TARGET_MAX],
        "phase1": {
            "per_document_allocation": per,
            "phase1_total": phase1_total,
            "description": f"{per} clauses sampled without replacement from each document stratum",
        },
        "phase2": {
            "slots": phase2_slots,
            "pool_size": total_remaining,
            "inclusion_probability_given_not_phase1": phase2_slots / total_remaining,
            "description": f"{phase2_slots} additional clauses sampled without replacement from pooled remaining across all documents",
        },
        "population": {
            "total_clauses_N": total_N,
            "documents": len(by_doc),
        },
        "sample": {
            "total_clauses_n": total_n,
        },
        "strata": [
            {
                "document_id": did,
                "N_h": design[did]["N_h"],
                "n_h": design[did]["empirical_n_h"],
                "k_h_phase1": design[did]["k_h_phase1"],
                "phase2_fill": design[did]["empirical_n_h"] - design[did]["k_h_phase1"],
                "design_inclusion_probability_pi_h": design[did]["design_inclusion_probability"],
                "design_weight_1_over_pi_h": design[did]["design_weight"],
                "empirical_inclusion_probability_n_h_over_N_h": design[did]["empirical_inclusion_probability"],
                "stratum_weight_N_h_over_N": design[did]["N_h"] / total_N,
                "note": "Use design_inclusion_probability_pi_h (not empirical n_h/N_h) for inverse-probability weighting in population estimation.",
            }
            for did in sorted(by_doc.keys())
        ],
        "estimation_guidance": {
            "unweighted_sample_metrics": "Compute accuracy/F1/confusion matrix on the 250 sampled clauses using human labels. Estimates performance for this sampling design only.",
            "population_estimates": "Once human labels exist, derive population estimates from a weighted confusion matrix. Weight each sampled clause by 1 / design_inclusion_probability_pi_h (inverse probability weighting). Do NOT use empirical n_h/N_h as the inclusion probability because the two-phase design (stratified + global fill) makes the actual inclusion probability different from the realized sampling fraction.",
            "stratum_weight": "N_h / N = document_clause_count / 2,455 describes population composition, not inclusion probability.",
            "precision_recall_f1": "Calculate population estimates from the weighted confusion matrix BEFORE deriving precision, recall, and F1. Per-class metrics should be computed on the weighted population estimates, not on the unweighted sample.",
            "challenge_set_metrics": "Report targeted challenge-set metrics separately. Do not mix with representative sample metrics.",
        },
        "reviewer_instructions": {
            "sheets_are_blind": "Reviewer sheets contain NO prediction, confidence, or explanation columns. Do not add model outputs to reviewer sheets.",
            "what_reviewers_need_to_complete": [
                "For each sampled clause: assign human_label (Safe | Neutral | Risky)",
                "Mark uncertain_or_context_insufficient = true if the clause text is too short, fragmented, or lacks sufficient context to classify",
                "Add notes explaining any classification difficulty",
                "Do NOT look at model predictions before labeling",
                "Do NOT share labels between reviewers before independent completion"
            ],
            "after_sheets_exist": [
                "Validate IDs/labels against the sample frame",
                "Measure inter-reviewer agreement before adjudication",
                "Produce disagreement queue for clauses where reviewers disagree",
                "Keep original annotations (do not overwrite)",
                "Adjudicate disagreements",
                "Compute accuracy, macro+weighted F1, per-class metrics, balanced accuracy, confusion matrix, Risky FP/FN on adjudicated labels"
            ]
        },
        "analyzed_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    meta_path = OUT_DIR / "sampling_provenance_corrected.json"
    meta_path.write_text(json.dumps(corrected_meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Corrected sampling metadata saved: {meta_path}")

    # Also update the existing sampling_metadata_final.json
    final_meta_path = SHEET_DIR / "sampling_metadata_final.json"
    if final_meta_path.exists():
        existing = json.loads(final_meta_path.read_text(encoding="utf-8"))
        # Update strata with correct design-based inclusion probabilities
        for stratum in existing.get("strata", []):
            did = stratum["document_id"]
            if did in design:
                d = design[did]
                stratum["design_inclusion_probability_pi_h"] = d["design_inclusion_probability"]
                stratum["design_weight_1_over_pi_h"] = d["design_weight"]
                stratum["empirical_inclusion_probability_n_h_over_N_h"] = d["empirical_inclusion_probability"]
                stratum["k_h_phase1"] = d["k_h_phase1"]
                stratum["phase2_fill"] = d["empirical_n_h"] - d["k_h_phase1"]
                stratum["note"] = "Use design_inclusion_probability_pi_h (not empirical n_h/N_h) for inverse-probability weighting in population estimation."
        existing["design"] = "two-phase: (1) stratified allocation of per-document clauses, (2) global random fill to target"
        existing["phase1"] = {"per_document_allocation": per, "phase1_total": phase1_total}
        existing["phase2"] = {"slots": phase2_slots, "pool_size": total_remaining, "inclusion_probability_given_not_phase1": phase2_slots / total_remaining}
        final_meta_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Updated existing sampling_metadata_final.json with design-based inclusion probabilities")


if __name__ == "__main__":
    main()
