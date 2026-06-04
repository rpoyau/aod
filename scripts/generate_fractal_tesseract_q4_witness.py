from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures_jpg"
FIG_DIR.mkdir(parents=True, exist_ok=True)
OUT = FIG_DIR / "fractal_tesseract_q4_witness.jpg"

fig, ax = plt.subplots(figsize=(14, 7.2), dpi=220)
ax.set_xlim(0, 14)
ax.set_ylim(0, 7.2)
ax.axis('off')

blue = '#1f4e8c'
green = '#2f7d4a'
orange = '#b7791f'
purple = '#7a4cc2'
grey = '#666666'
dark = '#0f2b4c'

ax.text(7, 6.82, 'Fractal tesseract support with finite Q4 witness', ha='center', va='center', fontsize=21, fontweight='bold', color=dark)
ax.text(7, 6.48, 'Recursive cut gives support; duon current traverses and witnesses it.', ha='center', fontsize=10.5, color=grey)

def rbox(x, y, w, h, text, ec, fc):
    box = FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.05,rounding_size=0.08',ec=ec,fc=fc,lw=1.2)
    ax.add_patch(box)
    ax.text(x+w/2, y+h/2, text, ha='center', va='center', fontsize=11)
    return box

# Flow boxes
boxes = [
    (0.55,5.40,1.55,0.72,'Null\npotential','#555','#f5f5f5'),
    (2.55,5.40,1.25,0.72,'x -> x\n= x',blue,'#eef7ff'),
    (4.30,5.28,1.40,0.95,'branch /\nhinge /\nbranch',green,'#f2fbf4'),
    (6.18,5.28,1.75,0.95,'recursive\ncut-unspooling',orange,'#fff7eb'),
]
for b in boxes:
    rbox(*b)
for (x1,y1,x2,y2) in [(2.10,5.76,2.55,5.76),(3.80,5.76,4.30,5.76),(5.70,5.76,6.18,5.76)]:
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=14,lw=1.2,color=grey))

# Q4 cube witness
ax.text(10.0, 5.75, 'finite Q4 chart', ha='center', fontsize=14, color=purple, fontweight='bold')
# Draw a clean cube-like Q4 witness
front = np.array([[9.10,3.85],[10.70,3.85],[10.70,5.05],[9.10,5.05]])
back = front + np.array([0.55,0.45])
edges = [(0,1),(1,2),(2,3),(3,0)]
for arr in (front, back):
    for i,j in edges:
        ax.plot([arr[i,0],arr[j,0]],[arr[i,1],arr[j,1]], color=purple, lw=1.2, alpha=.85)
for i in range(4):
    ax.plot([front[i,0],back[i,0]],[front[i,1],back[i,1]], color=purple, lw=1.2, alpha=.85)
# middle connectors for four-edge witness feel
extra = np.array([[9.90,4.25],[11.25,4.25],[9.90,5.45],[11.25,5.45]])
for x,y in list(front)+list(back):
    ax.add_patch(Circle((x,y),0.06,fc=purple,ec=purple))
# label under cube with no crossing text
ax.text(10.05,3.45,'local witness of fractal tesseract support',ha='center',fontsize=9,color=grey)
# jitter group separated from cube
ax.text(12.30,5.25,'jittering:',ha='left',fontsize=10,color=orange)
ax.text(12.30,5.00,'unresolved successor movement',ha='left',fontsize=8.5,color=orange)
for x,y in [(12.1,4.35),(12.7,4.05),(11.9,3.65),(12.5,3.35)]:
    ax.text(x,y,'+',ha='center',va='center',fontsize=11,color=orange,alpha=.8)

# Clean arrow and phrase below flow, no overlap with cube
ax.add_patch(FancyArrowPatch((7.95,5.05),(9.15,4.85),arrowstyle='-|>',mutation_scale=12,lw=1.2,color=grey,connectionstyle='arc3,rad=-0.1'))
ax.text(7.25,4.70,'branch / hinge / branch support can cut again',ha='center',fontsize=8.5,color=grey)

# duon current box and path
ax.add_patch(FancyArrowPatch((10.00,3.30),(10.85,2.72),arrowstyle='-|>',mutation_scale=18,lw=1.5,color=purple,connectionstyle='arc3,rad=-0.25'))
rbox(10.55,2.15,2.40,0.70,'duon current\nD_i mu D_j',purple,'#f5f0ff')
for i,x in enumerate(np.linspace(10.65,12.25,5)):
    ax.add_patch(Circle((x,1.35),0.11,ec=purple,fc='white',lw=1.2))
ax.add_patch(FancyArrowPatch((10.50,1.05),(12.60,1.05),arrowstyle='-|>',mutation_scale=16,lw=1.4,color=purple))

# Bottom lock-in strip
strip = FancyBboxPatch((1.0,0.35),12.0,0.48,boxstyle='round,pad=0.04,rounding_size=0.08',ec=blue,fc='#f3f8ff',lw=1.1)
ax.add_patch(strip)
ax.text(7,0.59,'Corrected order: recursive cut -> fractal tesseract support; duon current -> finite carried witness.',ha='center',va='center',fontsize=9.5,color=dark,fontweight='bold')

fig.tight_layout(pad=0.2)
fig.savefig(OUT, dpi=220, bbox_inches='tight')
print(OUT)
