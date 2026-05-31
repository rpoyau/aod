from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / 'figures_jpg' / 'sadar_boundary_relative_balance.png'
FIG.parent.mkdir(exist_ok=True)

# Figure 12: keep declaration text visually separate from topology drawings.
# Design rule: text scaffolds sit in the upper region of each panel; nodes/arrows
# sit below the declaration text. No text crosses a node circle or boundary curve.
fig, ax = plt.subplots(figsize=(12.4, 8.0))
ax.set_xlim(0, 12.4)
ax.set_ylim(0, 8.0)
ax.axis('off')

blue = '#1f4e79'
lt_blue = '#eaf2fb'
orange = '#b56a2a'
green = '#2f7d52'
purple = '#6f4aa5'
gray = '#4a4a4a'
light_gray = '#d0d0d0'

ax.text(6.2, 7.66, 'SADAR boundary-relative balance', ha='center', fontsize=20, fontweight='bold', color='#0f2538')
ax.text(6.2, 7.36, 'component balances + enclosing balance, all scoped by declared boundary/window', ha='center', fontsize=10, color='#2c3e50')

# Top panels: title plus clean node schematic.
panels = [
    (0.35, 4.05, 3.65, 2.85, '1. Component fields'),
    (4.25, 4.05, 3.65, 2.85, '2. Enclosing boundary'),
    (8.15, 4.05, 3.65, 2.85, '3. Phase bias and motion'),
]

for x, y, w, h, title in panels:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.08', fc='white', ec='#5b6770', lw=1.15))
    ax.text(x + 0.15, y + h - 0.26, title, fontsize=12, fontweight='bold', ha='left', color='#132f4c')


def draw_field(cx, cy, r, label='', vec_angle=0, vec_len=0.52, color=blue, label_y=None):
    ax.add_patch(Circle((cx, cy), r, fill=False, ec=gray, lw=1.35))
    ax.add_patch(Circle((cx, cy), 0.07, fc='white', ec='black', lw=1.0))
    for th in np.linspace(0, 2*np.pi, 8, endpoint=False):
        x1 = cx + r * 0.35 * np.cos(th); y1 = cy + r * 0.35 * np.sin(th)
        x2 = cx + r * 0.78 * np.cos(th); y2 = cy + r * 0.78 * np.sin(th)
        ax.plot([x1, x2], [y1, y2], color=light_gray, lw=0.75)
    vx = cx + vec_len * np.cos(vec_angle); vy = cy + vec_len * np.sin(vec_angle)
    ax.add_patch(FancyArrowPatch((cx, cy), (vx, vy), arrowstyle='-|>', mutation_scale=16, color=color, lw=1.7))
    if label:
        if label_y is None:
            label_y = cy - r - 0.28
        ax.text(cx, label_y, label, ha='center', fontsize=9, color='#111111')

# Panel 1 component fields
x0, y0, w, h, _ = panels[0]
# Top text line does not touch the drawings.
draw_field(x0 + 1.12, y0 + 1.38, 0.58, r'$F_1$', vec_angle=np.deg2rad(25), label_y=y0 + 0.46)
draw_field(x0 + 2.55, y0 + 1.38, 0.58, r'$F_2$', vec_angle=np.deg2rad(155), color='#b23a1b', label_y=y0 + 0.46)
ax.text(x0 + w/2, y0 + 0.17, 'each field has its own boundary/window balance', ha='center', fontsize=7.7, color='#2f3d4a')

# Panel 2 enclosing boundary
x0, y0, w, h, _ = panels[1]
ax.add_patch(Circle((x0 + 1.82, y0 + 1.30), 0.92, fill=False, ec=gray, lw=1.35))
draw_field(x0 + 1.38, y0 + 1.30, 0.32, '', vec_angle=np.deg2rad(20), vec_len=0.31)
draw_field(x0 + 2.24, y0 + 1.30, 0.32, '', vec_angle=np.deg2rad(160), vec_len=0.31, color='#b23a1b')
ax.add_patch(FancyArrowPatch((x0 + 1.72, y0 + 1.30), (x0 + 2.34, y0 + 1.54), arrowstyle='-|>', mutation_scale=17, lw=2.0, color=purple))
ax.text(x0 + w/2, y0 + 0.18, r'$\mathbf{A}_{F_1\parallel F_2}(B_{12})$', ha='center', fontsize=9.5, color=purple)

# Panel 3 phase bias and motion
x0, y0, w, h, _ = panels[2]
draw_field(x0 + 1.82, y0 + 1.28, 0.68, r'$\mathrm{motion}_F(B)=\mathbf{A}_F(B)$', vec_angle=0, vec_len=0.86, color='#b23a1b', label_y=y0 + 0.18)
for th in np.linspace(0, 2*np.pi, 8, endpoint=False):
    start = (x0 + 1.82 + 0.84*np.cos(th), y0 + 1.28 + 0.84*np.sin(th))
    end = (x0 + 1.82 + 1.05*np.cos(th), y0 + 1.28 + 1.05*np.sin(th))
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle='-|>', mutation_scale=10, color=blue, lw=1.0))

# Bottom formula strip, separated and current notation.
ax.add_patch(FancyBboxPatch((0.55, 0.55), 11.3, 2.55, boxstyle='round,pad=0.11', fc='#f7f8ff', ec='#335c99', lw=1.1))
ax.text(6.2, 2.75, r'$B=(\partial F,\omega)$', ha='center', fontsize=12.5, color='#111111')
ax.text(6.2, 2.20, r'$\mathbf{A}_F(B)=\sum_{e\in F(B)} C_{3,e}\,\rho^D_{\omega,e}(B)\,\Delta\chi^{\mathrm{lag}}_e(B)\,i_e(B)$', ha='center', fontsize=13.0, color='#111111')
ax.text(6.2, 1.58, r'$\mathfrak{S}_B(C)=p^D(C;B)\,A(C;B)$', ha='center', fontsize=13.0, color='#111111')
ax.text(6.2, 1.10, 'SADAR = Symmetry Attention-Duration-Asymmetric Reflection', ha='center', fontsize=9.7, color='#1f2d3a')
ax.text(6.2, 0.78, 'component projections are taken from the already-declared boundary/window attention vector', ha='center', fontsize=8.7, color='#2f3d4a')

fig.tight_layout(pad=0.4)
fig.savefig(FIG, dpi=220)
