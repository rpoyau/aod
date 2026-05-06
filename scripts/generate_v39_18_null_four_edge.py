from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / 'figures_jpg'
FIG_DIR.mkdir(exist_ok=True)
out = FIG_DIR / 'v39_18_null_four_edge_x_witness.png'

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 10,
})
fig, ax = plt.subplots(figsize=(12, 5.8), dpi=220)
ax.set_xlim(0, 12)
ax.set_ylim(0, 6)
ax.axis('off')

# Panel backgrounds
panels = [(0.25,0.55,3.35,5.0), (3.85,0.55,4.1,5.0), (8.25,0.55,3.5,5.0)]
for x,y,w,h in panels:
    rect = FancyBboxPatch((x,y), w,h, boxstyle='round,pad=0.02,rounding_size=0.08',
                          fc='#fbfbfd', ec='#b9c0cc', lw=1.2)
    ax.add_patch(rect)

# Panel 1: primitive simultaneity
ax.text(1.925,5.25,'1  Null potential',ha='center',va='center',fontsize=12,fontweight='bold')
ax.text(1.925,4.65,r'$x\succ x=x$',ha='center',va='center',fontsize=18)
ax.text(1.925,4.12,'same occurrence held in identity\nwhile cut-running presents',ha='center',va='center',fontsize=9)
# central x circle
circ = Circle((1.925,2.7),0.62,fc='#eef5ff',ec='#2f5f9f',lw=1.6)
ax.add_patch(circ)
ax.text(1.925,2.7,r'$x$',ha='center',va='center',fontsize=24)
# small null halo
for r, alpha in [(0.95,0.55),(1.22,0.30)]:
    halo = Circle((1.925,2.7),r,fc='none',ec='#6f8fbf',lw=1.0,alpha=alpha)
    ax.add_patch(halo)
ax.text(1.925,1.20,'retained occurrence',ha='center',va='center',fontsize=9)

# Arrow to panel 2
ax.add_patch(FancyArrowPatch((3.42,3.0),(3.77,3.0),arrowstyle='-|>',mutation_scale=18,lw=1.5,color='#555'))

# Panel 2: Q4 degree 4 witness
ax.text(5.9,5.25,'2  Four-edge $x$ witness',ha='center',va='center',fontsize=12,fontweight='bold')
ax.text(5.9,4.72,r'$\epsilon\in\{0,1\}^4$',ha='center',va='center',fontsize=15)
center = np.array([5.9,2.85])
# neighbors: directions
neighbors = {
    r'$\epsilon\oplus e_1$': np.array([5.9,4.10]),
    r'$\epsilon\oplus e_2$': np.array([7.05,2.85]),
    r'$\epsilon\oplus e_3$': np.array([5.9,1.60]),
    r'$\epsilon\oplus e_4$': np.array([4.75,2.85]),
}
for label, pos in neighbors.items():
    ax.add_patch(FancyArrowPatch(center, pos, arrowstyle='<->', mutation_scale=13, lw=1.4, color='#2d6a8e'))
    c = Circle(pos,0.22,fc='#fff7e6',ec='#c78f2b',lw=1.2)
    ax.add_patch(c)
    ax.text(pos[0], pos[1]+0.42, label, ha='center', va='center', fontsize=9)
# center vertex
c0 = Circle(center,0.34,fc='#eaf8ef',ec='#2f7d4f',lw=1.6)
ax.add_patch(c0)
ax.text(center[0],center[1],r'$x_\epsilon$',ha='center',va='center',fontsize=14)
# Edge labels
ax.text(5.55,3.53,r'$a_1$',fontsize=9,color='#2d6a8e')
ax.text(6.55,3.02,r'$a_2$',fontsize=9,color='#2d6a8e')
ax.text(5.55,2.10,r'$a_3$',fontsize=9,color='#2d6a8e')
ax.text(5.08,3.02,r'$a_4$',fontsize=9,color='#2d6a8e')
ax.text(5.9,0.98,r'$\deg_{Q_4}(x_\epsilon)=4$',ha='center',va='center',fontsize=14)

# Arrow to panel 3
ax.add_patch(FancyArrowPatch((7.92,3.0),(8.15,3.0),arrowstyle='-|>',mutation_scale=18,lw=1.5,color='#555'))

# Panel 3: monon fibre over four edges
ax.text(10.0,5.25,'3  Monon fibre',ha='center',va='center',fontsize=12,fontweight='bold')
ax.text(10.0,4.72,r'$Q_4\times\{-1,0,+1\}_\mu$',ha='center',va='center',fontsize=15)
# draw base four-edge cross small
base = np.array([10.0,2.7])
for pos in [np.array([10.0,3.55]),np.array([10.85,2.7]),np.array([10.0,1.85]),np.array([9.15,2.7])]:
    ax.add_patch(FancyArrowPatch(base,pos,arrowstyle='-',lw=1.1,color='#4d6f99'))
    ax.add_patch(Circle(pos,0.13,fc='#fff7e6',ec='#c78f2b',lw=1))
ax.add_patch(Circle(base,0.20,fc='#eaf8ef',ec='#2f7d4f',lw=1.2))
# vertical fibre
f_y = [1.45,2.70,3.95]
f_labels = [r'$-1$', r'$0$', r'$+1$']
for y,lbl in zip(f_y,f_labels):
    ax.add_patch(Circle((10.95,y),0.18,fc='#f4eefb',ec='#7c5ca3',lw=1.2))
    ax.text(11.28,y,lbl,ha='left',va='center',fontsize=10)
ax.plot([10.95,10.95],[1.45,3.95],color='#7c5ca3',lw=1.0,ls='--')
ax.text(10.0,0.96,'four tesseract edges\nplus ternary hinge fibre',ha='center',va='center',fontsize=10)

# bottom lock-in
lock = FancyBboxPatch((0.95,0.08),10.1,0.36,boxstyle='round,pad=0.025,rounding_size=0.07',
                      fc='#eef7ff',ec='#6493bd',lw=1)
ax.add_patch(lock)
ax.text(6.0,0.26,'Retained x in the finite Q4 witness has four Hamming-1 tesseract edges; the monon hinge remains the ternary fibre.',
        ha='center',va='center',fontsize=9)

fig.tight_layout(pad=0.2)
fig.savefig(out, bbox_inches='tight')
print(out)
