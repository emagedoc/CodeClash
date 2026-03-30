# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "pyarrow", "numpy"]
# ///
"""
Sample trajectories from the GPT-5 judge parquet for human annotation.

Produces:
  1. annotation_sample.csv — the subset for annotators (no GPT-5 labels, to avoid bias)
  2. annotation_sample_with_gpt5.csv — same subset with GPT-5 labels (for computing agreement after)

Usage:
    uv run sample_for_annotation.py [--n 100] [--seed 42]
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", default="llm_as_judge/aggregated_results.parquet")
    parser.add_argument("--n", type=int, default=80, help="Total samples to draw")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outdir", default=".")
    args = parser.parse_args()

    df = pd.read_parquet(args.parquet)
    df["arena"] = df["tournament_name"].str.extract(r"PvpTournament\.(\w+)\.")

    # Merge the two Qwen name variants
    df["model_name"] = df["model_name"].replace(
        "dashscope/qwen3-coder-plus-2025-09-23", "qwen3-coder-plus-2025-09-23"
    )

    # Derive the 3 binary labels from GPT-5
    h_cols = [c for c in df.columns if c.startswith("h_")]
    df["gpt5_grounded"] = df["edits_motivated_by_insights"]
    df["gpt5_hallucinated"] = df[h_cols].sum(axis=1) > 0
    df["gpt5_validated"] = df["edits_tested_with_simulations"]

    # Stratified sample: balanced across (model, arena)
    # We want roughly equal representation, but some cells are small
    models = sorted(df["model_name"].unique())
    arenas = sorted(df["arena"].unique())

    rng = np.random.RandomState(args.seed)

    # Target: n / (models * arenas) per cell, with remainder distributed randomly
    n_models = len(models)
    n_arenas = len(arenas)
    n_cells = n_models * n_arenas
    per_cell = max(1, args.n // n_cells)

    sampled = []
    for model in models:
        for arena in arenas:
            cell = df[(df["model_name"] == model) & (df["arena"] == arena)]
            k = min(per_cell, len(cell))
            if k > 0:
                sampled.append(cell.sample(n=k, random_state=rng))

    sample_df = pd.concat(sampled, ignore_index=True)

    # If we're short, fill from remaining pool
    if len(sample_df) < args.n:
        remaining = df[~df["instance_id"].isin(sample_df["instance_id"])]
        extra = remaining.sample(
            n=min(args.n - len(sample_df), len(remaining)), random_state=rng
        )
        sample_df = pd.concat([sample_df, extra], ignore_index=True)

    # If we're over, trim
    if len(sample_df) > args.n:
        sample_df = sample_df.sample(n=args.n, random_state=rng).reset_index(drop=True)

    # Shuffle
    sample_df = sample_df.sample(frac=1, random_state=rng).reset_index(drop=True)

    outdir = Path(args.outdir)

    # Version for annotators: no GPT-5 labels, just the identifying info
    annotator_df = sample_df[
        ["instance_id", "model_name", "arena", "round_number"]
    ].copy()
    annotator_df["a1_grounded"] = ""
    annotator_df["a1_hallucinated"] = ""
    annotator_df["a1_validated"] = ""
    annotator_df["a2_grounded"] = ""
    annotator_df["a2_hallucinated"] = ""
    annotator_df["a2_validated"] = ""
    annotator_df["a3_grounded"] = ""
    annotator_df["a3_hallucinated"] = ""
    annotator_df["a3_validated"] = ""

    annotator_path = outdir / "annotation_sample.csv"
    annotator_df.to_csv(annotator_path, index=False)

    # Version with GPT-5 labels for computing agreement after
    key_df = sample_df[
        [
            "instance_id",
            "model_name",
            "arena",
            "round_number",
            "gpt5_grounded",
            "gpt5_hallucinated",
            "gpt5_validated",
        ]
    ].copy()
    key_path = outdir / "annotation_sample_with_gpt5.csv"
    key_df.to_csv(key_path, index=False)

    print(f"Sampled {len(sample_df)} trajectories")
    print(f"  Models:  {sorted(sample_df['model_name'].unique())}")
    print(f"  Arenas:  {sorted(sample_df['arena'].unique())}")
    print()
    print("Distribution:")
    print(sample_df.groupby(["model_name", "arena"]).size().unstack(fill_value=0))
    print()
    print(f"Annotator sheet (no GPT-5 labels): {annotator_path}")
    print(f"Key with GPT-5 labels:             {key_path}")


if __name__ == "__main__":
    main()
