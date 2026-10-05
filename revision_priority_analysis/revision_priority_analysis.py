#!/usr/bin/env python3
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
CELL = pd.read_csv(ROOT/'artifacts/paired_cell_results.csv')
ITEM = pd.read_csv(ROOT/'artifacts/paired_items.csv', low_memory=False)
FUNC = pd.read_csv(ROOT/'artifacts/mbpp_functional_paired_items.csv')
CEIL = pd.read_csv(ROOT/'artifacts_v2/mbpp_generation_ceiling_audit.csv')
MAN = pd.read_csv(ROOT/'artifacts_v2/run_manifest_v2.csv')

# Absolute equal-cell levels
rows=[]
for ds,g in CELL.groupby('dataset'):
    rows.append([ds, *(100*g[c].mean() for c in ['pre_relaxed','post_relaxed','pre_format','post_format','pre_strict','post_strict'])])
rows.append(['Overall', *(100*CELL[c].mean() for c in ['pre_relaxed','post_relaxed','pre_format','post_format','pre_strict','post_strict'])])
pd.DataFrame(rows,columns=['Dataset','Pre C','Post C','Pre F','Post F','Pre S','Post S']).to_csv(OUT/'absolute_levels.csv',index=False)

# Parser sensitivity. Current = saved relaxed C. Strict = C only if F=1 = strict S.
# Maximally lenient is an algebraic upper-leniency bound: set C=1 whenever F=0.
def cell_delta(values_pre, values_post):
    tmp=ITEM[['model','dataset','config']].copy()
    tmp['pre']=values_pre; tmp['post']=values_post
    return 100*tmp.groupby(['model','dataset','config']).apply(lambda x: x.post.mean()-x.pre.mean(), include_groups=False).mean()
strict_dc=100*CELL.delta_strict.mean()
current_dc=100*CELL.delta_relaxed.mean()
df=100*CELL.delta_format.mean()
pre_len=np.where(ITEM.pre_format.eq(0),1,ITEM.pre_relaxed)
post_len=np.where(ITEM.post_format.eq(0),1,ITEM.post_relaxed)
len_dc=cell_delta(pre_len,post_len)
ps=pd.DataFrame([
    ['Strict extractor',strict_dc,df,df-strict_dc],
    ['Current relaxed extractor',current_dc,df,df-current_dc],
    ['Maximally lenient bound',len_dc,df,df-len_dc],
],columns=['Extractor','Delta C (pp)','Delta F (pp)','D (pp)'])
ps.to_csv(OUT/'parser_sensitivity.csv',index=False)

# Per-model and per-configuration deltas
x=CELL.assign(delta_C=100*CELL.delta_relaxed,delta_F=100*CELL.delta_format)
x['D']=x.delta_F-x.delta_C
x.groupby('model',as_index=False)[['delta_C','delta_F','D']].mean().to_csv(OUT/'per_model_deltas.csv',index=False)
x.groupby('config',as_index=False)[['delta_C','delta_F','D']].mean().to_csv(OUT/'per_configuration_deltas.csv',index=False)

# Transition taxonomy
state=lambda c,f: np.select([(c==0)&(f==0),(c==0)&(f==1),(c==1)&(f==0),(c==1)&(f==1)],['E1','E2','E3','E4'], default='')
pre=state(ITEM.pre_relaxed.values,ITEM.pre_format.values); post=state(ITEM.post_relaxed.values,ITEM.post_format.values)
def cat(a,b):
    m={('E1','E2'):'Pure compliance gain',('E3','E4'):'Pure compliance gain',
       ('E1','E3'):'Pure correctness gain',('E2','E4'):'Pure correctness gain',
       ('E1','E4'):'Joint gain',
       ('E2','E1'):'Pure compliance loss',('E4','E3'):'Pure compliance loss',
       ('E3','E1'):'Pure correctness loss',('E4','E2'):'Pure correctness loss',
       ('E4','E1'):'Joint loss',
       ('E2','E3'):'Trade-off',('E3','E2'):'Trade-off'}
    return 'Unchanged' if a==b else m.get((a,b),'Trade-off')
cc=pd.Series([cat(a,b) for a,b in zip(pre,post)])
order=['Pure compliance gain','Pure correctness gain','Joint gain','Pure compliance loss','Pure correctness loss','Joint loss','Trade-off','Unchanged']
out=[]
for k in order:
    n=int((cc==k).sum()); out.append([k,n,100*n/len(cc)])
pd.DataFrame(out,columns=['Category','Count','Share (%)']).to_csv(OUT/'transition_category_summary.csv',index=False)

# FDR McNemar counts
o=[]
for label,col,delta in [('Strict','mcnemar_q_strict','delta_strict'),('Correctness','mcnemar_q_relaxed','delta_relaxed'),('Compliance','mcnemar_q_format','delta_format')]:
    sig=CELL[col]<.05
    pos=int((sig & (CELL[delta]>0)).sum()); neg=int((sig & (CELL[delta]<0)).sum())
    o.append([label,pos,neg,pos+neg])
pd.DataFrame(o,columns=['Outcome','FDR significant positive','FDR significant negative','FDR significant total']).to_csv(OUT/'mcnemar_fdr_counts.csv',index=False)

# Partial correlation by residualization
def resid(y,X):
    X=np.asarray(X,float); X=np.c_[np.ones(len(X)),X]
    return y-X@np.linalg.lstsq(X,y,rcond=None)[0]
y=CELL.delta_relaxed.to_numpy(); z=CELL.delta_format.to_numpy()
base=CELL[['pre_relaxed','pre_format']].to_numpy()
r0=float(np.corrcoef(resid(y,base),resid(z,base))[0,1])
dummies=pd.get_dummies(CELL.dataset,drop_first=True,dtype=float).to_numpy()
r1=float(np.corrcoef(resid(y,np.c_[base,dummies]),resid(z,np.c_[base,dummies]))[0,1])
q=pd.qcut(CELL.delta_format,4,labels=['Q1 lowest','Q2','Q3','Q4 highest'])
qq=(CELL.assign(dF_bin=q,dC=100*CELL.delta_relaxed,dF=100*CELL.delta_format)
    .groupby('dF_bin',observed=True).agg(n=('dC','size'),mean_dF=('dF','mean'),mean_dC=('dC','mean')).reset_index())
qq.to_csv(OUT/'conditional_deltaC_by_deltaF_quartile.csv',index=False)

# Figure-3 numbers from deterministic MBPP pairs + ceiling audit
configs={'CoT','FS0','FS1','FS3','FS5','Zero'}
f=FUNC[FUNC.config.isin(configs)].copy()
rng=np.random.default_rng(42); out=[]
ceil=CEIL.set_index('model')
for model,g in f.groupby('model'):
    pre=g.pre_pass.to_numpy(float); post=g.post_pass.to_numpy(float); d=post-pre
    boots=np.empty(3000)
    for b in range(3000):
        idx=rng.integers(0,len(d),len(d)); boots[b]=100*d[idx].mean()
    lo,hi=np.percentile(boots,[2.5,97.5])
    nonhit=100*float(ceil.loc[model,'nonhit_delta_pass1']); nnh=int(ceil.loc[model,'nonhit_pair_n'])
    out.append([model,100*pre.mean(),100*post.mean(),100*d.mean(),lo,hi,nonhit,len(g),nnh])
mb=pd.DataFrame(out,columns=['model','pre_pass1_pct','post_pass1_pct','delta_pp','ci_lo_pp','ci_hi_pp','nonhit_delta_pp','n','n_nonhit']).sort_values('delta_pp')
mb.to_csv(OUT/'mbpp_figure3_numbers.csv',index=False)

# Dose metadata coverage and recipe aggregation
req=['sft_train_examples','sft_max_steps','train_batch','grad_accum']
av=MAN.dropna(subset=req).copy(); av['effective_batch']=av.train_batch*av.grad_accum; av['effective_epochs']=av.sft_max_steps*av.effective_batch/av.sft_train_examples
av.to_csv(OUT/'dose_available_manifest_rows.csv',index=False)
recipe=x.groupby(['model','dataset'],as_index=False)[['delta_C','delta_F','D']].mean().rename(columns={'delta_C':'dCpp','delta_F':'dFpp','D':'Dpp'})
dose=av.merge(recipe,on=['model','dataset'],how='left'); dose.to_csv(OUT/'dose_model_dataset_analysis.csv',index=False)
need=MAN[MAN[req].isna().any(axis=1)][['model','dataset']+req+['learning_rate','settings_recovery']]
need.to_csv(OUT/'dose_metadata_needed.csv',index=False)
stats={}
for yy in ['Dpp','dCpp','dFpp']:
    for xx in ['effective_epochs','sft_max_steps']:
        if len(dose)>=3:
            rho,p=spearmanr(dose[xx],dose[yy]); stats[f'{yy}~{xx}']={'n':len(dose),'spearman_rho':float(rho),'p':float(p)}
summary={'partial_corr_preC_preF':r0,'partial_corr_preC_preF_datasetFE':r1,'dose_available_model_dataset_rows':len(av),'dose_unique_recipes':len(dose),'mbpp_dose_rows':int((dose.dataset=='MBPP').sum()),'dose_stats':stats}
import json
(OUT/'analysis_summary.json').write_text(json.dumps(summary,indent=2))

# 300-item human validation sheet, 75/dataset, balanced across available pre-states as far as possible.
samples=[]; rng=np.random.default_rng(20260820)
for ds,g in ITEM[(ITEM.pre_completion.notna())].groupby('dataset'):
    g=g.copy(); g['_state']=state(g.pre_relaxed.values,g.pre_format.values)
    chosen=[]
    states=[s for s in ['E1','E2','E3','E4'] if (g._state==s).any()]
    base_n=75//len(states); rem=75-base_n*len(states)
    for i,s in enumerate(states):
        gg=g[g._state==s]; n=min(len(gg),base_n+(i<rem)); chosen.append(gg.iloc[rng.choice(len(gg),n,replace=False)])
    h=pd.concat(chosen)
    if len(h)<75:
        rest=g.drop(h.index); extra=rest.iloc[rng.choice(len(rest),75-len(h),replace=False)]; h=pd.concat([h,extra])
    samples.append(h.sample(frac=1,random_state=42).head(75))
val=pd.concat(samples).copy()
keep=['model','dataset','config','pair_index','pre_question','pre_gold','pre_completion','pre_pred','pre_relaxed','pre_format','pre_strict','pre_state']
val=val[keep]
for c in ['human_answer_annotator1','human_answerable_annotator1','human_answer_annotator2','human_answerable_annotator2','adjudicated_answer','extractor_agrees_adjudicated','annotator_notes']:
    val[c]=''
val.to_csv(OUT/'parser_validation_sample_300.csv',index=False)
print('wrote revision-priority analyses')
