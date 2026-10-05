#!/usr/bin/env python3
"""Dose sensitivity for CCD once run-level SFT metadata are complete.

Required manifest columns per model x dataset recipe:
  model, dataset, sft_train_examples, sft_max_steps, train_batch, grad_accum
Optional: learning_rate and other recipe metadata.
The script aggregates the 9 inference configurations within each recipe first,
so inference configurations are not treated as independent training-dose observations.
"""
from pathlib import Path
import pandas as pd
from scipy.stats import spearmanr
import statsmodels.formula.api as smf

ROOT=Path(__file__).resolve().parents[1]
manifest=pd.read_csv(ROOT/'artifacts_v2/run_manifest_v2.csv')
cells=pd.read_csv(ROOT/'artifacts/paired_cell_results.csv')
req=['sft_train_examples','sft_max_steps','train_batch','grad_accum']
miss=manifest[req].isna().any(axis=1)
if miss.any():
    raise SystemExit(
        f"Dose analysis not run: {miss.sum()}/{len(manifest)} model-dataset recipes "
        "lack one or more required dose fields. Fill revision_priority_analysis/dose_metadata_needed.csv "
        "and merge those values into artifacts_v2/run_manifest_v2.csv first."
    )
manifest['effective_batch']=manifest.train_batch*manifest.grad_accum
manifest['effective_epochs']=manifest.sft_max_steps*manifest.effective_batch/manifest.sft_train_examples
recipe=(cells.groupby(['model','dataset'],as_index=False)
        .agg(delta_C=('delta_relaxed','mean'),delta_F=('delta_format','mean')))
recipe['D']=recipe.delta_F-recipe.delta_C
recipe[['delta_C','delta_F','D']]*=100
m=recipe.merge(manifest[['model','dataset','sft_max_steps','effective_epochs']],on=['model','dataset'],how='inner')
for y in ['D','delta_C','delta_F']:
    for x in ['effective_epochs','sft_max_steps']:
        rho,p=spearmanr(m[x],m[y])
        print(f'{y} ~ {x}: n={len(m)}, Spearman rho={rho:.3f}, p={p:.4g}')
# Descriptive adjusted model; use only after checking sample size/coverage.
if len(m)>=20:
    fit=smf.ols('D ~ effective_epochs + C(dataset)',data=m).fit(cov_type='cluster',cov_kwds={'groups':m.model})
    print(fit.summary())
mbpp=m[m.dataset.eq('MBPP')]
print(f'MBPP dose recipes: n={len(mbpp)}')
if len(mbpp)>=6:
    print('MBPP Spearman:', spearmanr(mbpp.effective_epochs,mbpp.D))
