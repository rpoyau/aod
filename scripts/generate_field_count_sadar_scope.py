from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch, Ellipse, Arc

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / 'figures_jpg'
FIG_DIR.mkdir(exist_ok=True)
OUT = FIG_DIR / 'fixed_scope_field_count.png'

# Figure 11 is used in the core note at near full page width.  Keep the
# lower-row declaration boxes large enough that the equations and topology do
# not share the same visual lane.
fig, ax = plt.subplots(figsize=(16, 10.2), dpi=150)
ax.set_xlim(0, 16)
ax.set_ylim(0, 10.2)
ax.axis('off')

blue = '#1f4e8c'
dark = '#12264a'
green = '#2f7d4a'
orange = '#a65a22'
purple = '#5a4a8a'
grey = '#444444'
light_blue = '#f3f7ff'
light_green = '#f2fbf4'
light_orange = '#fff7f0'
light_purple = '#f7f5ff'

ax.text(8, 9.70, 'Fixed-scope field count and SADAR scope', ha='center', va='center',
        fontsize=25, fontweight='bold', color=dark)
ax.text(8, 9.32, 'scope -> retained fields -> returned-current channels -> field-count term',
        ha='center', fontsize=16, color=grey)


def box(x, y, w, h, title, body_lines, color, face, body_fs=11.3, line_step=0.31):
    bb = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.12',
                        linewidth=1.7, edgecolor=color, facecolor=face)
    ax.add_patch(bb)
    ax.text(x + 0.18, y + h - 0.28, title, ha='left', va='top',
            fontsize=14.6, fontweight='bold', color=dark)
    yy = y + h - 0.76
    for line in body_lines:
        ax.text(x + 0.20, yy, line, ha='left', va='top', fontsize=body_fs, color='black')
        yy -= line_step
    return bb

# --- Top-row declarations -------------------------------------------------
box(0.55, 6.10, 3.35, 2.60, '1. Scope',
    [r'$B=(\partial F,\omega)$', 'fixed boundary/window', 'all quantities use $B$'],
    blue, light_blue)

ax.add_patch(Circle((2.50, 6.68), 0.42, edgecolor=blue, facecolor='none', linewidth=2))
ax.text(2.50, 6.68, '$F$', ha='center', va='center', fontsize=16, fontweight='bold', color=dark)
ax.plot([1.98, 3.02], [6.08, 6.08], color=grey, lw=1.4)
ax.text(2.50, 5.90, r'$\omega$', ha='center', fontsize=12, color=grey)

box(4.70, 6.10, 3.40, 2.60, '2. Retained field family',
    [r'$F_B=\{F_1,\ldots,F_{n_F}\}$', r'$n_F(B)=|F_B|$'],
    blue, light_blue)
ax.add_patch(FancyBboxPatch((5.12, 6.24), 2.50, 0.88,
                            boxstyle='round,pad=0.02,rounding_size=0.18',
                            linewidth=1.4, edgecolor='#769bc4', facecolor='none'))
for (x, y, label) in [(5.45, 6.60, '$F_1$'), (6.18, 6.94, '$F_2$'), (6.98, 6.60, '$F_3$'), (7.48, 6.96, '$F_4$')]:
    ax.add_patch(Circle((x, y), 0.26, edgecolor=blue, facecolor='#edf3ff', linewidth=1.45))
    ax.text(x, y, label, ha='center', va='center', fontsize=12, color=dark)

box(9.15, 6.10, 3.85, 2.60, '3. Returned-current channels',
    [r'$ADAR_{i\leftarrow j}$', r'self terms: $i=j$', r'cross terms: $i\ne j$'],
    blue, light_blue)
ax.add_patch(Circle((10.25, 6.58), 0.30, edgecolor=blue, facecolor='#edf3ff', linewidth=1.6))
ax.text(10.25, 7.00, '$F_1$', ha='center', va='center', fontsize=12, color=dark)
ax.add_patch(Circle((11.88, 6.58), 0.30, edgecolor=blue, facecolor='#edf3ff', linewidth=1.6))
ax.text(11.88, 7.00, '$F_2$', ha='center', va='center', fontsize=12, color=dark)
ax.add_patch(FancyArrowPatch((10.53, 6.73), (11.58, 6.73), arrowstyle='->', mutation_scale=12, linewidth=1.5, color=grey))
ax.add_patch(FancyArrowPatch((11.58, 6.43), (10.53, 6.43), arrowstyle='->', mutation_scale=12, linewidth=1.5, color=grey))
ax.add_patch(Arc((10.25, 6.58), 0.86, 0.86, theta1=120, theta2=320, color=grey, lw=1.3))
ax.add_patch(Arc((11.88, 6.58), 0.86, 0.86, theta1=-60, theta2=140, color=grey, lw=1.3))

# --- Lower-row boxes.  Text is held in the upper half; drawings stay below. --
box(0.55, 1.45, 5.35, 3.25, '4. Field-count contribution',
    [r'$\mathcal{O}_{\partial F}(B)=n_F(B)\log n_F(B)$',
     'log base declared by calculation',
     r'monon anchor: $C_{\mathrm{mono}}=1$',
     r'coupled-field count starts at $n_F=2$'],
    orange, light_orange, body_fs=11.0, line_step=0.34)
# small symbolic count marker intentionally below the text lane
ax.add_patch(Circle((4.88, 2.18), 0.34, edgecolor=orange, facecolor='#fff4cf', linewidth=1.35))
ax.text(4.88, 2.18, '$n_F$', ha='center', va='center', fontsize=10.5, color='#7a4b00')

box(6.65, 1.45, 4.95, 3.25, 'Two-field declared scope',
    [r'$B_{12}=(\partial F_{12},\omega_{12})$',
     r'$F_{B_{12}}=\{F_1,F_2\}$',
     r'$n_F(B_{12})=2$',
     r'$\mathcal{O}_{\partial F}(B_{12})=2\log 2$'],
    green, light_green, body_fs=10.8, line_step=0.34)

# topology is cleanly separated from declarations
ax.add_patch(Ellipse((8.95, 2.05), 3.10, 0.88, edgecolor=blue, facecolor='none', linewidth=1.0, alpha=0.9))
ax.add_patch(Circle((8.16, 2.05), 0.39, edgecolor='#c07a1a', facecolor='#fff4cf', linewidth=1.5))
ax.text(8.16, 2.05, '$F_1$', ha='center', va='center', fontsize=11, color='#7a4b00')
ax.add_patch(Circle((10.22, 2.05), 0.25, edgecolor=purple, facecolor='#f5f1ff', linewidth=1.5))
ax.text(10.22, 1.53, '$F_2$', ha='center', fontsize=10, color=dark)
ax.add_patch(FancyArrowPatch((8.55, 2.15), (9.90, 2.15), arrowstyle='->', mutation_scale=11, linewidth=1.1, color=grey, alpha=0.85))

box(12.25, 1.45, 2.95, 3.25, 'Rule',
    ['field count != enclosure order', r'$n_F$ = retained fields', '$m$ = enclosure order', '$T$ = duration/count length'],
    purple, light_purple, body_fs=11.0, line_step=0.34)

# arrows
arrows = [
    ((3.90, 7.40), (4.70, 7.40)),
    ((8.10, 7.40), (9.15, 7.40)),
    ((11.05, 6.10), (11.05, 4.70)),
    ((5.90, 3.07), (6.65, 3.07)),
    ((11.60, 3.07), (12.25, 3.07)),
]
for a, b in arrows:
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle='->', mutation_scale=16, linewidth=1.6, color=grey))

ax.text(8, 0.62, 'Field-count scaling fixes the SADAR scope contribution; shell/enclosure routing is evaluated separately.',
        ha='center', fontsize=13.5, color=grey)
plt.tight_layout()
fig.savefig(OUT, bbox_inches='tight')
plt.close(fig)
print(OUT)
