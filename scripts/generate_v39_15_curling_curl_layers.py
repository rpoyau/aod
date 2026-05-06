from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / 'figures_jpg'
FIG_DIR.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(14, 8.5))
ax.set_xlim(0, 15.2)
ax.set_ylim(0, 9)
ax.axis('off')

ax.text(7, 8.45, 'Curling-curl shell families', ha='center', va='center', fontsize=24, fontweight='bold', color='#1f2a44')
ax.text(7, 8.03, 'cycle -> inner cage -> core family -> outer shell path', ha='center', va='center', fontsize=12, color='#444')

def box(x, y, w, h, title, lines, edge='#335c99', face='#fbfcff'):
    patch = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.08', linewidth=1.4, edgecolor=edge, facecolor=face)
    ax.add_patch(patch)
    ax.text(x+0.25, y+h-0.35, title, ha='left', va='center', fontsize=12.5, fontweight='bold', color=edge)
    for i, line in enumerate(lines):
        ax.text(x+0.25, y+h-0.75-0.36*i, line, ha='left', va='center', fontsize=10.5, color='#222')
    return patch

# Top role boxes
roles = [
    (0.7, 6.05, 3.1, 1.60, 'Tetrion', ['four-cycle closure', 'cycle term']),
    (4.35, 6.05, 3.1, 1.60, 'Tetron', ['default inner cage', 'four seats / E4']),
    (8.0, 6.05, 3.1, 1.60, 'Core families', ['Dimonon 1:2', 'Tritrion 3:3', 'Tetratrion 3:4']),
    (11.65, 6.05, 3.1, 1.60, 'Outer shell paths', ['hexon 6', 'octon 8', 'decon 10']),
]
for r in roles:
    box(*r)

for x1, x2 in [(3.85,4.30),(7.50,7.95),(11.20,11.60)]:
    ax.add_patch(FancyArrowPatch((x1,6.90),(x2,6.90), arrowstyle='-|>', mutation_scale=14, linewidth=1.2, color='#555'))

# Row of caged examples
examples = [
    (0.7, 4.35, 'Dimonhexon', '1:2:6', 'Dimon + hexon'),
    (3.4, 4.35, 'Dimonocton', '1:2:8', 'Dimon + octon'),
    (6.1, 4.35, 'Dimondecon', '1:2:10', 'Dimon + decon'),
    (8.8, 4.35, 'Tritriohexon', '3:3:6', 'Tritrio + hexon'),
    (11.75, 4.35, 'Tetratriohexon', '3:4:6', 'Tetratrio + hexon'),
]
for x,y,name,num,sub in examples:
    box(x,y,2.25,1.35,name,[num,sub], edge='#174ea6')

# Polychiral shell drawing
center_y = 2.4
for i, (x, label) in enumerate([(2.2,'alpha outward'),(5.0,'Omega return'),(7.8,'polychiral clocks'),(10.6,'TTL path')]):
    ax.add_patch(Circle((x, center_y), 0.55, fill=False, edgecolor='#d09000', linewidth=1.6))
    ax.add_patch(Circle((x, center_y), 0.32, fill=False, edgecolor='#777', linewidth=1.2))
    ax.add_patch(Circle((x, center_y), 0.14, fill=False, edgecolor='#663399', linewidth=1.5))
    if i == 0:
        ax.add_patch(FancyArrowPatch((x-1.0, center_y), (x-0.55, center_y), arrowstyle='-|>', mutation_scale=16, color='#1f5fbf', lw=1.6))
    elif i == 1:
        ax.add_patch(FancyArrowPatch((x+1.0, center_y), (x+0.55, center_y), arrowstyle='-|>', mutation_scale=16, color='#663399', lw=1.6))
    elif i == 2:
        ax.add_patch(FancyArrowPatch((x-0.85, center_y+0.45), (x+0.85, center_y+0.45), arrowstyle='-|>', mutation_scale=12, color='#d09000', lw=1.4))
        ax.add_patch(FancyArrowPatch((x+0.85, center_y-0.45), (x-0.85, center_y-0.45), arrowstyle='-|>', mutation_scale=12, color='#d09000', lw=1.4))
    else:
        ax.add_patch(FancyArrowPatch((x-0.95, center_y-0.65), (x+0.95, center_y-0.65), arrowstyle='-|>', mutation_scale=14, color='#d55e00', lw=1.6))
    ax.text(x, center_y-0.95, label, ha='center', va='top', fontsize=10)

# Bottom lock-in strip
strip = FancyBboxPatch((0.8,0.55),13.6,0.9, boxstyle='round,pad=0.08', linewidth=1.2, edgecolor='#335c99', facecolor='#f7f9ff')
ax.add_patch(strip)
ax.text(7,1.05, 'Tetron is the inner cage. Hexon / octon / decon are outer shell paths. Polychiral shell dressing is the field outer dressing.',
        ha='center', va='center', fontsize=11, color='#222')

fig.tight_layout()
fig.savefig(FIG_DIR / 'v39_15_curling_curl_layers.png', dpi=220)
plt.close(fig)
