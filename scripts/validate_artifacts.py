#!/usr/bin/env python3
"""Validate the structural invariants of the released CCD artifacts."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    paired_path = ROOT / "artifacts" / "paired_items.csv"
    mbpp_path = ROOT / "artifacts" / "mbpp_functional_paired_items.csv"

    paired = pd.read_csv(paired_path, low_memory=False)
    key = ["model", "dataset", "config", "pair_index"]

    require(len(paired) == 49_140, f"Expected 49,140 pairs, found {len(paired):,}")
    require(paired["model"].nunique() == 14, "Expected 14 checkpoints")
    require(paired["dataset"].nunique() == 4, "Expected four datasets")
    require(paired["config"].nunique() == 9, "Expected nine configurations")
    require(len(paired[key].drop_duplicates()) == len(paired), "Duplicate paired-item key")
    require(
        len(paired[["model", "dataset", "config"]].drop_duplicates()) == 495,
        "Expected 495 evaluation cells",
    )
    require(
        len(paired[["model", "dataset"]].drop_duplicates()) == 55,
        "Expected 55 model--dataset blocks",
    )
    require(
        paired["pre_task_id"].fillna("").astype(str).equals(
            paired["post_task_id"].fillna("").astype(str)
        ),
        "Pre/post task IDs are not matched",
    )

    for stage in ("pre", "post"):
        strict = paired[f"{stage}_strict"].astype(int)
        expected = (
            paired[f"{stage}_format"].astype(int)
            * paired[f"{stage}_relaxed"].astype(int)
        )
        require(strict.equals(expected), f"Strict identity failed at {stage} stage")

    mbpp = pd.read_csv(mbpp_path)
    mbpp_key = ["model", "config", "pair_index"]
    require(len(mbpp) == 11_700, f"Expected 11,700 MBPP pairs, found {len(mbpp):,}")
    require(mbpp["model"].nunique() == 13, "Expected 13 MBPP checkpoints")
    require(len(mbpp[mbpp_key].drop_duplicates()) == len(mbpp), "Duplicate MBPP key")
    require(int(mbpp["pre_pass"].sum()) == 2_222, "Unexpected pre-SFT MBPP pass count")
    require(int(mbpp["post_pass"].sum()) == 1_794, "Unexpected post-SFT MBPP pass count")

    print("CCD artifact validation passed.")
    print("  paired records: 49,140")
    print("  cells: 495")
    print("  model--dataset blocks: 55")
    print("  MBPP functional pairs: 11,700")


if __name__ == "__main__":
    main()
