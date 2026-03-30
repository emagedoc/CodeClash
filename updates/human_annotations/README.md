# Human Annotation Validation

Three authors independently annotated 100 randomly sampled trajectories on three binary questions:

- **Grounded**: Are the edits grounded in analysis of previous rounds or testing?
- **Hallucinated**: Are there hallucinated or unsubstantiated claims about why a round was lost?
- **Validated**: Are the edits validated by simulations or unit tests?

## Files

| File | Description |
|---|---|
| `annotation_sample.csv` | Human annotations from 3 annotators (a1, a2, a3) |
| `annotation_sample_with_gpt5.csv` | GPT-5's labels for the same 100 trajectories |
| `compute_agreement.py` | Computes Fleiss' kappa (inter-annotator) and Cohen's kappa (human majority vs GPT-5) |
| `sample_for_annotation.py` | How the 100 trajectories were sampled (stratified by model and arena) |

## Reproducing the agreement table

```bash
# Merge human + GPT-5 labels, then compute agreement
uv run --with pandas --with numpy python3 -c "
import pandas as pd
annot = pd.read_csv('annotation_sample.csv')
gpt5 = pd.read_csv('annotation_sample_with_gpt5.csv')
merged = annot.merge(gpt5[['instance_id','gpt5_grounded','gpt5_hallucinated','gpt5_validated']], on='instance_id')
merged.to_csv('/tmp/merged.csv', index=False)
"
uv run compute_agreement.py /tmp/merged.csv
```

## Notes

- `sample_for_annotation.py` was used to draw the sample from the full evaluation parquet (not included here due to size). The CSVs above are self-contained for reproducing agreement numbers.
- Annotators worked from `annotation_sample.csv` (without GPT-5 labels) to avoid bias.
