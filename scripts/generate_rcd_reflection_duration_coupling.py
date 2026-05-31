from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / 'figures_jpg'
FIG_DIR.mkdir(parents=True, exist_ok=True)

def arrow(ax, x1,y1,x2,y2,color='#1f5a9d',lw=2.0,ms=14):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=ms,linewidth=lw,color=color))

fig, ax = plt.subplots(figsize=(14,8.2))
ax.set_xlim(0,14)
ax.set_ylim(0,8)
ax.axis('off')
ax.text(7,7.5,'RCD inside SADAR',ha='center',fontsize=24,fontweight='bold')
ax.text(7,7.15,'RCD names the duration coordinate when coupled to asymmetric reflection',ha='center',fontsize=12,color='#333')
# window
win = FancyBboxPatch((3.2,1.95),7.8,4.85,boxstyle='round,pad=0.04',linewidth=1.8,edgecolor='#2f68b0',facecolor='#eef5ff')
ax.add_patch(win)
ax.text(7.1,6.55,'declared window $\omega$',ha='center',fontsize=13,color='#2f68b0')
ax.text(1.6,6.15,'emitted\nduon ticks',ha='center',fontsize=12,color='#d55e00')
ax.text(12.3,6.15,'asymmetric\nreflected clicks',ha='center',fontsize=12,color='#1f5a9d')
# timelines
ys=[5.6,4.9,4.25,3.55,2.85]
starts=[2.2,2.9,3.7,4.4,5.1]
ends=[5.2,6.6,9.8,7.6,12.0]
for i,(y,xs,xe) in enumerate(zip(ys,starts,ends)):
    ax.plot([xs,xe],[y,y],color='#1f5a9d',lw=2.0)
    ax.scatter([xs],[y],s=55,color='#d55e00',zorder=3)
    ax.scatter([xe],[y],s=55,color='#1f5a9d',zorder=3)
    arrow(ax,xs+0.05,y,xe-0.12,y,'#1f5a9d',1.2,10)
    # visible duration segment within window
    vis_start=max(xs,3.2)
    vis_end=min(xe,11.0)
    ax.plot([vis_start,vis_end],[y-0.14,y-0.14],color='#7b4ab0',lw=2.4)
    ax.text((vis_start+vis_end)/2,y-0.35,r'$\min(D_e,|\omega|_e)$',ha='center',fontsize=10,color='#7b4ab0')
# formula box
box=FancyBboxPatch((1.4,0.45),11.2,1.0,boxstyle='round,pad=0.08',linewidth=1.5,edgecolor='#7b4ab0',facecolor='white')
ax.add_patch(box)
ax.text(7,1.05,r'$ADAR_e=(A_e,D_e,R^{asym}_e),\quad RCD_e=D_e\leftrightarrow R^{asym}_e$',ha='center',fontsize=13)
ax.text(7,0.73,r'windowed duration uses $\min(D_e(\partial F,\omega),|\omega|_e)$',ha='center',fontsize=11,color='#333')
fig.tight_layout()
fig.savefig(FIG_DIR / 'rcd_reflection_duration_coupling.jpg', dpi=220)
plt.close(fig)
