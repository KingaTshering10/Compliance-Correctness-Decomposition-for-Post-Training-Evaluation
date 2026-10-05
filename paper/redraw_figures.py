"""Re-typeset Figures 4 and 5 using ONLY the supplied paper's plotted content.
Figure 4 uses the 16 printed counts and percentages.
Figure 5 uses original vector coordinates extracted from the supplied PDF;
no confidence intervals are calculated or inferred from experimental records.
"""
import json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle,Patch
R=pathlib.Path(__file__).parent
plt.rcParams.update({'font.family':'serif','font.serif':['DejaVu Serif'],'font.size':10,'pdf.fonttype':42,'ps.fonttype':42})
counts=[[3228,9924,251,3494],[368,14431,51,2877],[308,1919,990,2304],[111,2586,78,6220]]
shares=[[6.6,20.2,0.5,7.1],[0.7,29.4,0.1,5.9],[0.6,3.9,2.0,4.7],[0.2,5.3,0.2,12.7]]
colors={'compliance':'#d8e9f4','correctness':'#dcefe7','joint':'#e7def1','loss':'#f5dfda','unchanged':'#e9edef'}
cat=[['unchanged','compliance','correctness','joint'],['loss','unchanged','loss','correctness'],['loss','loss','unchanged','compliance'],['loss','loss','loss','unchanged']]
f,ax=plt.subplots(figsize=(6.3,3.0));f.subplots_adjust(left=.14,right=.98,top=.74,bottom=.25)
for i in range(4):
 for j in range(4):
  ax.add_patch(Rectangle((j-.5,i-.5),1,1,fc=colors[cat[i][j]],ec='white',lw=3))
  ax.text(j,i,f'{counts[i][j]:,}\n{shares[i][j]:.1f}%',ha='center',va='center',fontsize=10)
ax.set_xlim(-.5,3.5);ax.set_ylim(3.5,-.5);ax.set_yticks(range(4),[f'$E_{i}$' for i in range(1,5)])
ax.set_xticks(range(4),['$E_1$ wrong,\ninvalid','$E_2$ wrong,\nvalid','$E_3$ correct,\ninvalid','$E_4$ correct,\nvalid'])
ax.xaxis.tick_top();ax.tick_params(length=0);ax.set_ylabel('Pre-SFT state',fontsize=10);ax.set_title('Post-SFT state',pad=34,fontsize=10)
for s in ax.spines.values():s.set_visible(False)
f.legend([Patch(fc=colors[x]) for x in colors],['pure compliance gain','pure correctness gain','joint gain','loss or trade-off','unchanged'],loc='lower center',ncol=3,fontsize=10,frameon=False,columnspacing=1,handlelength=1)
f.savefig(R/'assets'/'figure04.pdf');plt.close(f)
D=json.load(open(R/'figure05_coordinates.json'))
names=D['names'];c=np.array(D['circles']);lo=np.array(D['lower']);hi=np.array(D['upper']);di=np.array(D['diamonds']);y=np.arange(13)
f,ax=plt.subplots(figsize=(6.3,3.65));f.subplots_adjust(left=.25,right=.98,top=.98,bottom=.24)
ax.errorbar(c,y,xerr=[c-lo,hi-c],fmt='o',markersize=3,color='#1f77b4',capsize=2,lw=.65,label='All deterministic pairs')
ax.scatter(di,y,marker='D',s=13,c='#1f77b4',label='Exclude either-stage ceiling hits')
ax.axvline(0,c='.4',lw=.7);ax.set_yticks(y,names,fontsize=10);ax.set_xlim(-33.5,5.2);ax.set_xticks(range(-30,6,5));ax.tick_params(axis='x',labelsize=10)
ax.set_xlabel('Post - pre functional pass@1 (pp)',fontsize=10);ax.grid(axis='x',color='.9',lw=.5);ax.set_axisbelow(True)
ax.spines['right'].set_visible(False);ax.spines['top'].set_visible(False)
h,l=ax.get_legend_handles_labels();f.legend([h[0],h[1]],[l[0],l[1]],loc='lower center',ncol=1,fontsize=10,frameon=False)
f.savefig(R/'assets'/'figure05.pdf');plt.close(f)
