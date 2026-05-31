from pathlib import Path
import csv
import math
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / 'manual' / 'figures' / 'higgs'
DATA = ROOT / 'manual' / 'data' / 'higgs'
FIG.mkdir(parents=True, exist_ok=True)

BLUE = '#355C7D'
GREEN = '#3A7D44'
ORANGE = '#C46A2B'
PURPLE = '#6C4E9D'
GRAY = '#566573'

# Figure 1: yro saddle signature
fig, ax = plt.subplots(figsize=(7.0, 3.7))
labels = [r'$P^D_H-C_6$', r'$P^D_H-C_8$']
vals = [3, -3]
ax.axhline(0, color='0.25', lw=1)
ax.bar(labels, vals, color=[GREEN, ORANGE], width=0.52)
for i, v in enumerate(vals):
    ax.text(i, v + (0.18 if v >= 0 else -0.35), f'{v:+d}', ha='center', va='bottom' if v >= 0 else 'top', fontsize=12)
ax.set_ylabel('closure residual')
ax.set_title('Tritrioseptyro yro saddle signature')
ax.set_ylim(-4.5, 4.5)
ax.text(0.5, -4.1, r'$K_H^\star=3{:}3{:}7_{\rm yro}$,  $P^D_H=21$', ha='center', fontsize=10)
fig.tight_layout()
fig.savefig(FIG / 'higgs_yro_saddle_signature.png', dpi=220)
plt.close(fig)

# Figure 2: trace flow
fig, ax = plt.subplots(figsize=(7.4, 6.2))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')
steps = [
    ('1. Candidate', '$3{:}3{:}7_{\\rm yro}$'),
    ('2. Branch support', '$\\Pi=3^3+3=30$\n$RD=2\\Pi+1=61$'),
    ('3. Window', '$\\rho^D_\\omega=7$\n$C_{3,H}=3$'),
    ('4. Pressure', '$P^D_H=21$\n$Q^D_H=162$'),
    ('5. Saddle', '$C_6:+3$\n$C_8:-3$'),
    ('6. Frozen map', '$E_H^{(0)}=RD\\,2^{L+4}$\n$124.928\\,\\mathrm{GeV}$'),
]
ys = [0.86, 0.72, 0.58, 0.44, 0.30, 0.16]
box_w, box_h = 0.72, 0.105
x = 0.5
for idx, ((title, body), y) in enumerate(zip(steps, ys)):
    box = FancyBboxPatch((x-box_w/2, y-box_h/2), box_w, box_h, boxstyle='round,pad=0.018,rounding_size=0.018', lw=1.25, edgecolor=BLUE, facecolor='#F7FBFF')
    ax.add_patch(box)
    ax.text(x-0.31, y+0.024, title, ha='left', va='center', fontsize=9.5, color=BLUE, fontweight='bold')
    ax.text(x+0.08, y, body, ha='center', va='center', fontsize=10.0, linespacing=1.35)
    if idx < len(ys)-1:
        ax.add_patch(FancyArrowPatch((x, y-box_h/2-0.01),(x, ys[idx+1]+box_h/2+0.01), arrowstyle='->', mutation_scale=12, lw=1.2, color=GRAY))
ax.text(0.5, 0.035, 'Internal trace freezes before external LHC targets join.', ha='center', fontsize=10.5, color=GRAY)
ax.set_title('Tritrioseptyro trace flow', fontsize=13, color=BLUE, pad=10)
fig.tight_layout()
fig.savefig(FIG / 'higgs_tritrioseptyro_trace_flow.png', dpi=220)
plt.close(fig)

# Figure 3: Higgs mass comparison
rows = []
with open(DATA / 'higgs_external_lhc_mass_comparison_after_freeze.csv', newline='') as f:
    for r in csv.DictReader(f):
        rows.append(r)
labels = [
    'ATLAS+CMS\nRun 1',
    'CMS\nH→4ℓ',
    'ATLAS\nRun 1+2',
    'ATLAS\nH→γγ',
]
y = [float(r['mass_GeV']) for r in rows]
yerr = [float(r['sigma_GeV']) for r in rows]
pred = float(rows[0]['prediction_GeV'])
fig, ax = plt.subplots(figsize=(8.8, 4.7))
ax.errorbar(range(len(y)), y, yerr=yerr, fmt='o', capsize=5, lw=1.8, label='LHC target ± σ', color=BLUE)
ax.axhline(pred, linestyle='--', lw=1.8, color=ORANGE, label=f'frozen external map: {pred:.3f} GeV')
ax.set_xticks(range(len(y)))
ax.set_xticklabels(labels, rotation=25, ha='right')
ax.set_ylabel('mass (GeV)')
ax.set_title('Tritrioseptyro external-map Higgs mass comparison')
ax.legend(loc='lower right')
ax.grid(axis='y', alpha=0.2)
fig.tight_layout()
fig.savefig(FIG / 'higgs_mass_comparison.png', dpi=220)
plt.close(fig)
print('generated Higgs figures in', FIG)
