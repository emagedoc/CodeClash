# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "pyarrow", "numpy"]
# ///
"""
Compute inter-annotator agreement (Fleiss' kappa among human annotators)
and human-model agreement (Cohen's kappa between human majority vote and GPT-5).

Two modes:

  1) Standalone CSV (all-in-one):
     uv run compute_agreement.py annotations.csv

     Expects columns: instance_id, model_name, arena,
       a1_grounded, a1_hallucinated, a1_validated,
       a2_grounded, a2_hallucinated, a2_validated,
       a3_grounded, a3_hallucinated, a3_validated,
       gpt5_grounded, gpt5_hallucinated, gpt5_validated

  2) Human annotations CSV + GPT-5 parquet (join on instance_id):
     uv run python compute_agreement.py annotations.csv --parquet llm_as_judge/aggregated_results.parquet

     The CSV needs: instance_id, a1_grounded, a1_hallucinated, a1_validated, ...
     GPT-5 labels are pulled from the parquet automatically.
"""

import argparse
import pandas as pd
import numpy as np
from itertools import combinations


QUESTIONS = ["grounded", "hallucinated", "validated"]
ANNOTATORS = ["a1", "a2", "a3"]


def parse_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    return str(val).strip().lower() == "true"


def cohens_kappa(y1, y2):
    """Cohen's kappa for two binary raters."""
    y1, y2 = np.array(y1, dtype=int), np.array(y2, dtype=int)
    n = len(y1)
    po = np.sum(y1 == y2) / n
    p1 = np.mean(y1)
    p2 = np.mean(y2)
    pe = p1 * p2 + (1 - p1) * (1 - p2)
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def fleiss_kappa(ratings_matrix):
    """
    Fleiss' kappa for multiple raters.
    ratings_matrix: (n_subjects, n_categories) — counts of raters per category.
    """
    n_subjects, n_categories = ratings_matrix.shape
    n_raters = ratings_matrix.sum(axis=1)[0]

    p_j = ratings_matrix.sum(axis=0) / (n_subjects * n_raters)
    P_i = (ratings_matrix ** 2).sum(axis=1) - n_raters
    P_i = P_i / (n_raters * (n_raters - 1))

    P_bar = P_i.mean()
    Pe_bar = (p_j ** 2).sum()

    if Pe_bar == 1.0:
        return 1.0
    return (P_bar - Pe_bar) / (1 - Pe_bar)


def kappa_interpretation(k):
    if k < 0:
        return "poor"
    elif k < 0.20:
        return "slight"
    elif k < 0.40:
        return "fair"
    elif k < 0.60:
        return "moderate"
    elif k < 0.80:
        return "substantial"
    else:
        return "almost perfect"


def extract_gpt5_labels(parquet_path):
    """Extract the 3 binary GPT-5 labels from the full parquet."""
    df = pd.read_parquet(parquet_path)
    h_cols = [c for c in df.columns if c.startswith("h_")]
    result = pd.DataFrame({
        "instance_id": df["instance_id"],
        "gpt5_grounded": df["edits_motivated_by_insights"],
        "gpt5_hallucinated": df[h_cols].sum(axis=1) > 0,
        "gpt5_validated": df["edits_tested_with_simulations"],
    })
    return result


def detect_annotators(df):
    """Auto-detect annotator prefixes from columns like a1_grounded, a2_grounded, etc."""
    prefixes = set()
    for col in df.columns:
        for q in QUESTIONS:
            if col.endswith(f"_{q}") and col != f"gpt5_{q}":
                prefix = col[: -len(f"_{q}")]
                prefixes.add(prefix)
    return sorted(prefixes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", help="Path to human annotations CSV")
    parser.add_argument(
        "--parquet",
        default=None,
        help="Path to GPT-5 parquet (if GPT-5 labels not in CSV)",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.csv)

    # If parquet provided, join GPT-5 labels
    if args.parquet:
        gpt5_df = extract_gpt5_labels(args.parquet)
        # Drop any existing gpt5 columns from CSV to avoid conflicts
        gpt5_cols_in_csv = [c for c in df.columns if c.startswith("gpt5_")]
        if gpt5_cols_in_csv:
            df = df.drop(columns=gpt5_cols_in_csv)
        df = df.merge(gpt5_df, on="instance_id", how="left")
        n_matched = df["gpt5_grounded"].notna().sum()
        print(f"Joined GPT-5 labels from parquet: {n_matched}/{len(df)} matched")

    # Auto-detect annotators
    annotators = detect_annotators(df)
    if not annotators:
        print("ERROR: No annotator columns found (expected pattern: a1_grounded, etc.)")
        return
    print(f"Detected {len(annotators)} annotators: {annotators}")

    # Parse booleans
    for col in df.columns:
        if any(col.startswith(f"{a}_") for a in annotators) or col.startswith("gpt5_"):
            df[col] = df[col].apply(parse_bool)

    # Drop rows where any annotator or GPT-5 label is missing
    required_cols = []
    for a in annotators:
        for q in QUESTIONS:
            required_cols.append(f"{a}_{q}")
    for q in QUESTIONS:
        required_cols.append(f"gpt5_{q}")
    before = len(df)
    df = df.dropna(subset=required_cols)
    if len(df) < before:
        print(f"Dropped {before - len(df)} rows with missing labels")

    n = len(df)
    n_annotators = len(annotators)

    if "model_name" in df.columns:
        print(f"Models: {sorted(df['model_name'].unique())}")
    if "arena" in df.columns:
        print(f"Arenas: {sorted(df['arena'].unique())}")
    print(f"Trajectories: {n}")
    print()

    # ── Per-question results ──
    for q in QUESTIONS:
        human_cols = [f"{a}_{q}" for a in annotators]
        gpt5_col = f"gpt5_{q}"

        human_labels = df[human_cols].values.astype(int)  # (n, k)
        gpt5_labels = df[gpt5_col].values.astype(int)

        # Human majority vote
        majority = (human_labels.sum(axis=1) >= (n_annotators / 2)).astype(int)

        # ── Fleiss' kappa ──
        n_true = human_labels.sum(axis=1)
        n_false = n_annotators - n_true
        ratings = np.column_stack([n_false, n_true])
        fk = fleiss_kappa(ratings)

        # ── Pairwise Cohen's kappa among humans ──
        pairwise = []
        pair_labels = []
        for i, j in combinations(range(n_annotators), 2):
            k = cohens_kappa(human_labels[:, i], human_labels[:, j])
            pairwise.append(k)
            pair_labels.append(f"{annotators[i]} vs {annotators[j]}")
        mean_pairwise = np.mean(pairwise)

        # ── Human majority vs GPT-5 ──
        hm_kappa = cohens_kappa(majority, gpt5_labels)
        hm_agree_pct = np.mean(majority == gpt5_labels) * 100

        # ── Base rates ──
        human_positive_rate = majority.mean() * 100
        gpt5_positive_rate = gpt5_labels.mean() * 100

        print(f"{'=' * 60}")
        print(f"  Question: {q.upper()}")
        print(f"{'=' * 60}")
        print(f"  Human majority positive rate: {human_positive_rate:.1f}%")
        print(f"  GPT-5 positive rate:          {gpt5_positive_rate:.1f}%")
        print()
        print(f"  Inter-annotator (Fleiss' κ):   {fk:.3f} ({kappa_interpretation(fk)})")
        print(f"  Inter-annotator (mean pairwise Cohen's κ): {mean_pairwise:.3f}")
        for idx, label in enumerate(pair_labels):
            print(f"    {label}: κ = {pairwise[idx]:.3f}")
        print()
        print(f"  Human majority vs GPT-5:")
        print(f"    Agreement:   {hm_agree_pct:.1f}%")
        print(f"    Cohen's κ:   {hm_kappa:.3f} ({kappa_interpretation(hm_kappa)})")
        print()

    # ── Summary table ──
    print(f"{'=' * 60}")
    print(f"  SUMMARY (n={n})")
    print(f"{'=' * 60}")
    print(f"  {'Question':<15} {'Fleiss κ':>10} {'Human-GPT5 κ':>14} {'Agreement':>10}")
    print(f"  {'-'*15} {'-'*10} {'-'*14} {'-'*10}")
    for q in QUESTIONS:
        human_cols = [f"{a}_{q}" for a in annotators]
        human_labels = df[human_cols].values.astype(int)
        gpt5_labels = df[f"gpt5_{q}"].values.astype(int)
        majority = (human_labels.sum(axis=1) >= (n_annotators / 2)).astype(int)

        n_true = human_labels.sum(axis=1)
        n_false = n_annotators - n_true
        ratings = np.column_stack([n_false, n_true])
        fk = fleiss_kappa(ratings)
        hm_kappa = cohens_kappa(majority, gpt5_labels)
        hm_agree = np.mean(majority == gpt5_labels) * 100

        print(f"  {q:<15} {fk:>10.3f} {hm_kappa:>14.3f} {hm_agree:>9.1f}%")
    print()


if __name__ == "__main__":
    main()
