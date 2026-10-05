from __future__ import annotations
from pathlib import Path
import json, re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import MultipleLocator
from scipy.stats import spearmanr
import statsmodels.formula.api as smf

ROOT=Path(__file__).resolve().parent
ART=ROOT/'artifacts'
OUT=ROOT/'artifacts_ccd'
FIG=ROOT/'figures_ccd'
OUT.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)
SEED=42
B=10000

cells=pd.read_csv(ART/'paired_cell_results.csv')
items=pd.read_csv(ART/'paired_items.csv',low_memory=False)
mb=pd.read_csv(ART/'mbpp_functional_paired_items.csv')
mbcell=pd.read_csv(ART/'mbpp_functional_cell_results.csv')

# ---------- model metadata ----------
PARAM_B={
'Gemma 3 270M':0.27,'Gemma 3 1B':1.0,'Llama 3 8B':8.0,'Llama 3.1 8B':8.0,
'Llama 3.2 1B':1.0,'Llama 3.2 3B':3.0,'Qwen 2.5 0.5B':0.5,'Qwen 2.5 1.5B':1.5,
'Qwen 2.5 7B':7.0,'Qwen 3 0.6B':0.6,'Qwen 3 1.7B':1.7,'Qwen 3.5 0.8B':0.8,
'Qwen 3.5 2B':2.0,'Qwen 3.5 4B':4.0}

def family(s):
    return 'Gemma' if s.startswith('Gemma') else ('Llama' if s.startswith('Llama') else 'Qwen')

cells['params_b']=cells.model.map(PARAM_B)
cells['log10_params']=np.log10(cells.params_b)
cells['family']=cells.model.map(family)
cells['D']=cells.delta_format-cells.delta_relaxed
cells['D_pp']=100*cells.D

# ---------- pooled + within-dataset decoupling ----------
def decouple_row(name,g):
    x=g.delta_format.astype(float); y=g.delta_relaxed.astype(float)
    return {
        'dataset':name,'n_cells':int(len(g)),
        'pearson_r':float(x.corr(y)),
        'spearman_rho':float(spearmanr(x,y).statistic),
        'format_up_correct_up':int(((x>0)&(y>0)).sum()),
        'format_up_correct_nonpositive':int(((x>0)&(y<=0)).sum()),
        'format_nonpositive_correct_up':int(((x<=0)&(y>0)).sum()),
        'both_nonpositive':int(((x<=0)&(y<=0)).sum()),
        'key_quadrant_share':float(((x>0)&(y<=0)).mean()),
        'mean_D_pp':float(100*(x-y).mean()),
        'median_D_pp':float(100*(x-y).median()),
    }
within=[decouple_row('Pooled',cells)]
for ds in ['GSM8K','LogiQA','MBPP','StrategyQA']:
    within.append(decouple_row(ds,cells[cells.dataset==ds]))
within_df=pd.DataFrame(within)
within_df.to_csv(OUT/'within_dataset_decoupling.csv',index=False)

# functional MBPP decoupling counter-check
mbf=cells[cells.dataset=='MBPP'][['model','config','delta_format']].merge(
    mbcell[['model','config','delta_pass1']],on=['model','config'],how='inner',validate='one_to_one')
mbf['D_functional']=mbf.delta_format-mbf.delta_pass1
mbf_summary={
    'n_cells':int(len(mbf)),
    'pearson_r':float(mbf.delta_format.corr(mbf.delta_pass1)),
    'spearman_rho':float(spearmanr(mbf.delta_format,mbf.delta_pass1).statistic),
    'format_up_function_nonpositive_n':int(((mbf.delta_format>0)&(mbf.delta_pass1<=0)).sum()),
    'format_up_function_nonpositive_share':float(((mbf.delta_format>0)&(mbf.delta_pass1<=0)).mean()),
    'mean_D_functional_pp':float(100*mbf.D_functional.mean()),
}
(OUT/'mbpp_functional_decoupling.json').write_text(json.dumps(mbf_summary,indent=2))

# ---------- weighting sensitivity ----------
metrics=['strict','relaxed','format']
eq_cell={m:100*cells[f'delta_{m}'].mean() for m in metrics}
obs={m:100*(items[f'post_{m}'].astype(float)-items[f'pre_{m}'].astype(float)).mean() for m in metrics}
model_means=cells.groupby('model')[[f'delta_{m}' for m in metrics]].mean()
eq_model={m:100*model_means[f'delta_{m}'].mean() for m in metrics}
weight_rows=[]
for label,d in [('Equal-cell',eq_cell),('Observation-weighted',obs),('Equal-model',eq_model)]:
    weight_rows.append({'weighting':label,**d,'D':d['format']-d['relaxed']})
weight_df=pd.DataFrame(weight_rows)
weight_df.to_csv(OUT/'weighting_sensitivity.csv',index=False)

# ---------- hierarchical model/task bootstrap (transparent reimplementation) ----------
block=cells.groupby(['model','dataset'])[['delta_strict','delta_relaxed','delta_format','D']].mean().reset_index()
models=sorted(block.model.unique())
mb_by_model={m:g.reset_index(drop=True) for m,g in block.groupby('model')}
rng=np.random.default_rng(SEED)
boot={k:np.empty(B) for k in ['delta_strict','delta_relaxed','delta_format','D']}
for b in range(B):
    smp=rng.choice(models,size=len(models),replace=True)
    vals={k:[] for k in boot}
    for m in smp:
        gm=mb_by_model[m]
        idx=rng.integers(0,len(gm),size=len(gm))
        gg=gm.iloc[idx]
        for k in vals:
            vals[k].extend(gg[k].to_numpy())
    for k in boot:
        boot[k][b]=np.mean(vals[k])
hier=[]
for k,label in [('delta_strict','Strict'),('delta_relaxed','Correctness'),('delta_format','Compliance'),('D','D')]:
    lo,hi=np.quantile(boot[k],[.025,.975])*100
    mean=100*(cells[k].mean() if k!='D' else cells.D.mean())
    hier.append({'outcome':label,'mean_pp':mean,'ci_low_pp':lo,'ci_high_pp':hi})
hier_df=pd.DataFrame(hier)
hier_df.to_csv(OUT/'hierarchical_bootstrap_ccd.csv',index=False)

# ---------- leave-one-model-out ----------
lomo=[]
for m in sorted(cells.model.unique()):
    g=cells[cells.model!=m]
    r={'excluded_model':m,'cells':int(len(g))}
    for met in metrics:
        r[met]=100*g[f'delta_{met}'].mean()
    r['D']=r['format']-r['relaxed']
    lomo.append(r)
lomo_df=pd.DataFrame(lomo)
lomo_df.to_csv(OUT/'leave_one_model_out.csv',index=False)
lomo_summary={
    'D_min_pp':float(lomo_df.D.min()),'D_max_pp':float(lomo_df.D.max()),
    'strict_min_pp':float(lomo_df.strict.min()),'strict_max_pp':float(lomo_df.strict.max()),
    'correctness_min_pp':float(lomo_df.relaxed.min()),'correctness_max_pp':float(lomo_df.relaxed.max()),
    'compliance_min_pp':float(lomo_df.format.min()),'compliance_max_pp':float(lomo_df.format.max()),
}
(OUT/'leave_one_model_out_summary.json').write_text(json.dumps(lomo_summary,indent=2))

# ---------- explanatory model-clustered regression ----------
# Reference levels: GSM8K, CoT, Gemma. 14 model clusters -> exploratory association only.
fit=smf.ols('D_pp ~ C(dataset, Treatment(reference="GSM8K")) + C(config, Treatment(reference="CoT")) + log10_params + C(family, Treatment(reference="Gemma"))',data=cells).fit(
    cov_type='cluster',cov_kwds={'groups':cells.model})
ci=fit.conf_int()
reg_rows=[]
for term,val in fit.params.items():
    reg_rows.append({'term':term,'coef_pp':float(val),'se_cluster':float(fit.bse[term]),'ci_low_pp':float(ci.loc[term,0]),'ci_high_pp':float(ci.loc[term,1]),'p_cluster':float(fit.pvalues[term])})
reg_df=pd.DataFrame(reg_rows)
reg_df.to_csv(OUT/'explanatory_regression_clustered.csv',index=False)
reg_meta={'n_cells':int(fit.nobs),'n_model_clusters':int(cells.model.nunique()),'r_squared':float(fit.rsquared),'adj_r_squared':float(fit.rsquared_adj),'reference_dataset':'GSM8K','reference_config':'CoT','reference_family':'Gemma','note':'Exploratory OLS with model-clustered standard errors; cluster count is 14, so coefficient inference is interpreted cautiously.'}
(OUT/'explanatory_regression_meta.json').write_text(json.dumps(reg_meta,indent=2))

# ---------- MBPP status transition accounting ----------
def sclass(s):
    s=str(s)
    if s.startswith('syntax:') or s=='SyntaxError': return 'Syntax error'
    if s=='AssertionError': return 'Assertion failure'
    if s=='NameError': return 'NameError'
    if s=='TypeError': return 'TypeError'
    if s=='IndexError': return 'IndexError'
    if s=='missing_code': return 'Missing code'
    if s=='timeout': return 'Timeout'
    if s.startswith('blocked_'): return 'Safety block'
    if s=='saved_execution': return 'Saved execution label'
    if s=='passed': return 'Passed'
    return s
mb['pre_class']=mb.pre_status.map(sclass); mb['post_class']=mb.post_status.map(sclass)
pass_to_syntax=int(((mb.pre_pass==1)&(mb.post_class=='Syntax error')).sum())
syntax_to_pass=int(((mb.pre_class=='Syntax error')&(mb.post_pass==1)).sum())
net_pass_loss=int(mb.pre_pass.sum()-mb.post_pass.sum())
status_summary={
    'pre_pass_n':int(mb.pre_pass.sum()),'post_pass_n':int(mb.post_pass.sum()),'net_pass_loss':net_pass_loss,
    'pass_to_syntax_n':pass_to_syntax,'syntax_to_pass_n':syntax_to_pass,
    'net_pass_syntax_imbalance':pass_to_syntax-syntax_to_pass,
    'share_of_net_pass_loss_accounted_by_net_pass_syntax_imbalance':float((pass_to_syntax-syntax_to_pass)/net_pass_loss),
    'stable_pass':int(((mb.pre_pass==1)&(mb.post_pass==1)).sum()),
    'pass_to_fail':int(((mb.pre_pass==1)&(mb.post_pass==0)).sum()),
    'fail_to_pass':int(((mb.pre_pass==0)&(mb.post_pass==1)).sum()),
    'stable_fail':int(((mb.pre_pass==0)&(mb.post_pass==0)).sum()),
}
(OUT/'mbpp_pass_syntax_summary.json').write_text(json.dumps(status_summary,indent=2))
loss=mb[(mb.pre_pass==1)&(mb.post_pass==0)].post_class.value_counts()
gain=mb[(mb.pre_pass==0)&(mb.post_pass==1)].pre_class.value_counts()
classes=sorted(set(loss.index)|set(gain.index))
transition=pd.DataFrame({'failure_class':classes,'pass_to_failure':[int(loss.get(c,0)) for c in classes],'failure_to_pass':[int(gain.get(c,0)) for c in classes]})
transition['net_loss_contribution']=transition.pass_to_failure-transition.failure_to_pass
transition=transition.sort_values('net_loss_contribution',ascending=False)
transition.to_csv(OUT/'mbpp_pass_failure_transition_accounting.csv',index=False)

# ---------- figures ----------
plt.rcParams.update({'font.size':9,'axes.labelsize':10,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'axes.linewidth':0.8,'pdf.fonttype':42,'ps.fonttype':42})
styles={'GSM8K':('#0072B2','o'),'LogiQA':('#E69F00','s'),'MBPP':('#009E73','D'),'StrategyQA':('#CC79A7','^')}

# Figure 1 pooled publication scatter
x=100*cells.delta_format; y=100*cells.delta_relaxed
pear=float(cells.delta_format.corr(cells.delta_relaxed)); key=int(((cells.delta_format>0)&(cells.delta_relaxed<=0)).sum())
fig,ax=plt.subplots(figsize=(6.9,4.8))
xmin,xmax=-35,105; ymin,ymax=-105,65
ax.set_xlim(xmin,xmax); ax.set_ylim(ymin,ymax)
ax.add_patch(Rectangle((0,ymin),xmax,-ymin,facecolor='0.965',edgecolor='none',zorder=0))
ax.axhline(0,color='0.35',lw=.9); ax.axvline(0,color='0.35',lw=.9)
lo=max(xmin,ymin); hi=min(xmax,ymax)
ax.plot([lo,hi],[lo,hi],ls='--',lw=.8,color='0.65',zorder=0)
for ds in ['GSM8K','LogiQA','MBPP','StrategyQA']:
    g=cells[cells.dataset==ds]; color,marker=styles[ds]
    ax.scatter(100*g.delta_format,100*g.delta_relaxed,s=25,alpha=.68,label=ds,c=color,marker=marker,edgecolors='white',linewidths=.3,zorder=2)
ax.set_xlabel(r'$\Delta$ compliance (percentage points)')
ax.set_ylabel(r'$\Delta$ task/parser correctness (percentage points)')
ax.text(.985,.985,f'n = {len(cells)}\nPearson r = {pear:.2f}',transform=ax.transAxes,ha='right',va='top',fontsize=8.4,bbox=dict(boxstyle='round,pad=.3',fc='white',ec='0.8',lw=.6,alpha=.95))
ax.text(.985,.035,f'Compliance up, correctness <= 0\n{key}/{len(cells)} cells ({100*key/len(cells):.1f}%)',transform=ax.transAxes,ha='right',va='bottom',fontsize=8.4,fontweight='semibold',bbox=dict(boxstyle='round,pad=.3',fc='white',ec='0.7',lw=.6,alpha=.96))
ax.legend(loc='upper left',ncol=2,frameon=True,framealpha=.95,edgecolor='.85')
ax.xaxis.set_major_locator(MultipleLocator(20)); ax.yaxis.set_major_locator(MultipleLocator(20))
ax.grid(which='major',color='.91',lw=.5); ax.spines[['top','right']].set_visible(False)
fig.tight_layout(pad=.6)
fig.savefig(FIG/'fig1_ccd_decoupling.pdf',bbox_inches='tight'); fig.savefig(FIG/'fig1_ccd_decoupling.png',dpi=600,bbox_inches='tight'); plt.close(fig)

# Appendix dataset small multiples
fig,axs=plt.subplots(2,2,figsize=(7.0,6.2),sharex=True,sharey=True)
for ax,ds in zip(axs.flat,['GSM8K','LogiQA','MBPP','StrategyQA']):
    g=cells[cells.dataset==ds]; color,marker=styles[ds]
    ax.axhline(0,color='.45',lw=.75); ax.axvline(0,color='.45',lw=.75); ax.plot([lo,hi],[lo,hi],ls='--',lw=.65,color='.72')
    ax.scatter(100*g.delta_format,100*g.delta_relaxed,s=22,alpha=.72,c=color,marker=marker,edgecolors='white',linewidths=.25)
    r=float(g.delta_format.corr(g.delta_relaxed)); k=int(((g.delta_format>0)&(g.delta_relaxed<=0)).sum())
    ax.set_title(ds,fontsize=10,fontweight='semibold')
    ax.text(.97,.96,f'r={r:.2f}\n{k}/{len(g)} ({100*k/len(g):.1f}%)',transform=ax.transAxes,ha='right',va='top',fontsize=7.8,bbox=dict(boxstyle='round,pad=.2',fc='white',ec='.85',lw=.5,alpha=.94))
    ax.set_xlim(xmin,xmax); ax.set_ylim(ymin,ymax); ax.grid(color='.93',lw=.45); ax.spines[['top','right']].set_visible(False)
for ax in axs[-1,:]: ax.set_xlabel(r'$\Delta$ compliance (pp)')
for ax in axs[:,0]: ax.set_ylabel(r'$\Delta$ correctness (pp)')
fig.tight_layout(pad=.8)
fig.savefig(FIG/'figA1_within_dataset_decoupling.pdf',bbox_inches='tight'); fig.savefig(FIG/'figA1_within_dataset_decoupling.png',dpi=600,bbox_inches='tight'); plt.close(fig)

# Figure 2 transition matrix, pooled
states=['E1','E2','E3','E4']
mat=pd.crosstab(items.pre_state,items.post_state).reindex(index=states,columns=states,fill_value=0)
share=mat/len(items)
fig,ax=plt.subplots(figsize=(6.3,4.9))
arr=share.values.copy(); mask=np.eye(4,dtype=bool); plotarr=arr.copy(); plotarr[mask]=np.nan
im=ax.imshow(plotarr,cmap='Blues',vmin=0,vmax=np.nanmax(plotarr))
for i in range(4):
    ax.add_patch(Rectangle((i-.5,i-.5),1,1,facecolor='#eeeeee',edgecolor='white',lw=1.2))
for i in range(4):
    for j in range(4):
        pct=100*share.iloc[i,j]; count=int(mat.iloc[i,j]); color='black' if (i==j or pct<10.5) else 'white'
        ax.text(j,i,f'{count:,}\n{pct:.1f}%',ha='center',va='center',fontsize=9,color=color,fontweight='semibold' if i!=j else 'normal')
labels=[r'$E_1$ wrong / invalid',r'$E_2$ wrong / valid',r'$E_3$ correct / invalid',r'$E_4$ correct / valid']
ax.set_xticks(range(4),labels,rotation=18,ha='right'); ax.set_yticks(range(4),labels)
ax.set_xlabel('Post-training state'); ax.set_ylabel('Pre-training state')
cbar=fig.colorbar(im,ax=ax,fraction=.04,pad=.025); cbar.set_label('Share of all matched items (off-diagonal)',fontsize=8.5); cbar.ax.tick_params(labelsize=7.5)
fig.tight_layout(pad=.6)
fig.savefig(FIG/'fig2_ccd_transition_matrix.pdf',bbox_inches='tight'); fig.savefig(FIG/'fig2_ccd_transition_matrix.png',dpi=600,bbox_inches='tight'); plt.close(fig)

# Figure 3 MBPP heterogeneity with paired bootstrap CIs for raw deterministic delta and non-hit point
# reuse ceiling proxy logic from prior analysis
paired=items
det=['Zero','CoT','FS0','FS1','FS3','FS5']
tok=paired[(paired.dataset=='MBPP')&paired.config.isin(det)][['model','config','pair_index','pre_tokens','post_tokens']]
fun=mb[mb.config.isin(det)].copy()
j=fun.merge(tok,on=['model','config','pair_index'],how='left',validate='one_to_one')
caps={}
for m,g in tok.groupby('model'):
    vals=pd.concat([pd.to_numeric(g.pre_tokens,errors='coerce'),pd.to_numeric(g.post_tokens,errors='coerce')]).dropna(); caps[m]=float(vals.max())
j['cap']=j.model.map(caps); j['pre_hit']=np.isclose(pd.to_numeric(j.pre_tokens,errors='coerce'),j.cap,equal_nan=False); j['post_hit']=np.isclose(pd.to_numeric(j.post_tokens,errors='coerce'),j.cap,equal_nan=False)
rng=np.random.default_rng(SEED)
plotrows=[]
for m,g in j.groupby('model'):
    d=(g.post_pass-g.pre_pass).to_numpy(float); raw=100*d.mean()
    idx=rng.integers(0,len(d),size=(3000,len(d))); boots=100*d[idx].mean(axis=1); lo_ci,hi_ci=np.quantile(boots,[.025,.975])
    keep=~(g.pre_hit|g.post_hit); non=100*(g.loc[keep,'post_pass']-g.loc[keep,'pre_pass']).mean()
    plotrows.append({'model':m,'raw':raw,'lo':lo_ci,'hi':hi_ci,'nonhit':non})
ph=pd.DataFrame(plotrows).sort_values('raw')
fig,ax=plt.subplots(figsize=(6.8,5.2)); yp=np.arange(len(ph))
ax.axvline(0,color='.4',lw=.8)
ax.hlines(yp,ph.raw,ph.nonhit,color='.78',lw=1.1,zorder=1)
ax.errorbar(ph.raw,yp,xerr=[ph.raw-ph.lo,ph.hi-ph.raw],fmt='o',ms=4.5,capsize=2.2,lw=.8,label='All deterministic pairs',zorder=3)
ax.scatter(ph.nonhit,yp,marker='D',s=24,label='Exclude either-stage ceiling hits',zorder=4)
ax.set_yticks(yp,ph.model); ax.set_xlabel('Post - pre functional pass@1 (pp)'); ax.grid(axis='x',color='.92',lw=.5); ax.spines[['top','right']].set_visible(False); ax.legend(loc='lower right',frameon=False,fontsize=7.7)
fig.tight_layout(pad=.6)
fig.savefig(FIG/'fig3_mbpp_heterogeneity.pdf',bbox_inches='tight'); fig.savefig(FIG/'fig3_mbpp_heterogeneity.png',dpi=600,bbox_inches='tight'); plt.close(fig)

# Appendix LOMO D plot
pl=lomo_df.sort_values('D')
fig,ax=plt.subplots(figsize=(6.7,4.7)); yp=np.arange(len(pl)); full=100*cells.D.mean()
ax.axvline(full,color='.35',ls='--',lw=.9,label=f'Full sample: {full:.1f} pp')
ax.scatter(pl.D,yp,s=28,zorder=3); ax.set_yticks(yp,pl.excluded_model); ax.set_xlabel(r'Compliance-minus-correctness contrast $D$ (pp)'); ax.grid(axis='x',color='.92',lw=.5); ax.spines[['top','right']].set_visible(False); ax.legend(frameon=False,loc='lower right',fontsize=8)
fig.tight_layout(pad=.6); fig.savefig(FIG/'figA2_leave_one_model_out.pdf',bbox_inches='tight'); fig.savefig(FIG/'figA2_leave_one_model_out.png',dpi=600,bbox_inches='tight'); plt.close(fig)

# Appendix MBPP pass/failure accounting: top classes by absolute net contribution
tr=transition.copy(); tr['absnet']=tr.net_loss_contribution.abs(); tr=tr.sort_values('absnet',ascending=False).head(8).sort_values('net_loss_contribution')
fig,ax=plt.subplots(figsize=(6.8,4.5)); yp=np.arange(len(tr))
ax.barh(yp,tr.pass_to_failure,label='Pass -> failure'); ax.barh(yp,-tr.failure_to_pass,label='Failure -> pass')
ax.set_yticks(yp,tr.failure_class); ax.axvline(0,color='.35',lw=.8); ax.set_xlabel('Paired transition count (reverse transitions shown left)'); ax.legend(frameon=False,fontsize=8); ax.grid(axis='x',color='.93',lw=.5); ax.spines[['top','right']].set_visible(False)
fig.tight_layout(pad=.6); fig.savefig(FIG/'figA3_mbpp_failure_accounting.pdf',bbox_inches='tight'); fig.savefig(FIG/'figA3_mbpp_failure_accounting.png',dpi=600,bbox_inches='tight'); plt.close(fig)

# summary object
summary={'within_dataset':within,'mbpp_functional_decoupling':mbf_summary,'weighting':weight_rows,'hierarchical':hier,'leave_one_out':lomo_summary,'regression_meta':reg_meta,'mbpp_pass_syntax':status_summary}
(OUT/'ccd_revision_summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
