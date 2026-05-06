from pathlib import Path
import csv
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / 'figures_jpg'
FIG_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = ROOT / 'wavelet_shedding_simulation.csv'
SUMMARY_PATH = ROOT / 'wavelet_shedding_summary.tex'

# -------------------------
# Figure 1: conceptual panel
# -------------------------
fig, ax = plt.subplots(figsize=(12, 6.5))
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis('off')

ax.text(7, 7.55, 'Wavelet-group lead-lag disturbance and shedding',
        ha='center', va='center', fontsize=20, fontweight='bold')
ax.text(7, 7.15, 'duon current -> disturbance span -> PADAR burden -> shedding -> reclosure',
        ha='center', va='center', fontsize=10)

xs = [1.4, 4.1, 6.8, 9.5, 12.2]
titles = [
    ('1', 'Carried wavelet group', 'segment of duon current'),
    ('2', 'Lead-lag span', 'asymmetric return extent'),
    ('3', 'PADAR burden', 'duration and chiral mismatch'),
    ('4', 'Shedding', 'excess span breaks'),
    ('5', 'Reclosure / decay path', 'shell reclosure or continuation'),
]

for x, (num, title, subtitle) in zip(xs, titles):
    box = FancyBboxPatch((x-1.15, 4.75), 2.3, 1.55, boxstyle='round,pad=0.08',
                         linewidth=1.2, facecolor='white', edgecolor='#335c99')
    ax.add_patch(box)
    circ = Circle((x-0.98, 6.12), 0.18, color='#174ea6')
    ax.add_patch(circ)
    ax.text(x-0.98, 6.12, num, color='white', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(x, 5.82, title, ha='center', va='center', fontsize=10, color='#174ea6', fontweight='bold')
    ax.text(x, 5.35, subtitle, ha='center', va='center', fontsize=8)

for i in range(4):
    ax.add_patch(FancyArrowPatch((xs[i]+1.20, 5.55), (xs[i+1]-1.20, 5.55),
                                 arrowstyle='-|>', mutation_scale=16, linewidth=1.3, color='#444444'))

# Panel sketches
# 1 carried wavelet group
x = xs[0]
for k in np.linspace(x-0.65, x+0.65, 5):
    ax.add_patch(Circle((k, 4.15), 0.08, fill=False, edgecolor='#663399', linewidth=1.4))
    ax.add_patch(FancyArrowPatch((k-0.08, 4.15), (k+0.10, 4.15), arrowstyle='-|>', mutation_scale=7, color='#663399'))
ax.plot(np.linspace(x-0.7, x+0.7, 100), 4.15+0.18*np.sin(np.linspace(0, 3*math.pi, 100)), color='#1f5fbf', lw=1.0)

# 2 lead-lag span
x = xs[1]
ax.add_patch(FancyArrowPatch((x-0.8, 4.35), (x-0.1, 4.2), arrowstyle='-|>', mutation_scale=13, color='#1f5fbf', linewidth=1.4))
ax.add_patch(FancyArrowPatch((x+0.8, 3.85), (x+0.1, 4.2), arrowstyle='-|>', mutation_scale=13, color='#d55e00', linewidth=1.4))
ax.annotate('', xy=(x-0.72, 3.65), xytext=(x+0.72, 3.65), arrowprops=dict(arrowstyle='<->', lw=1.4, color='#663399'))
ax.text(x, 3.45, 'span', ha='center', fontsize=9)

# 3 PADAR burden
x = xs[2]
for r in [0.22, 0.38, 0.56, 0.75]:
    ax.add_patch(Circle((x, 4.1), r, fill=False, edgecolor='#777777', linewidth=1.0, linestyle='--'))
ax.add_patch(FancyArrowPatch((x-0.9, 4.1), (x+0.9, 4.1), arrowstyle='-|>', mutation_scale=14, color='#444444'))
ax.text(x, 3.35, r'$P^{PADAR}_{W}$', ha='center', fontsize=12)

# 4 shedding
x = xs[3]
ax.add_patch(Circle((x-0.35, 4.1), 0.23, fill=False, edgecolor='#663399', linewidth=1.4))
ax.add_patch(FancyArrowPatch((x-0.1, 4.1), (x+0.72, 4.55), arrowstyle='-|>', mutation_scale=17, color='#d55e00', lw=1.7))
ax.add_patch(FancyArrowPatch((x-0.1, 4.1), (x+0.72, 3.65), arrowstyle='-|>', mutation_scale=17, color='#1f5fbf', lw=1.7))
ax.text(x+0.50, 4.75, 'outward', fontsize=8, color='#d55e00')
ax.text(x+0.48, 3.35, 'reclose', fontsize=8, color='#1f5fbf')

# 5 reclosure / decay
x = xs[4]
for k in range(4):
    ax.add_patch(Circle((x-0.55+0.32*k, 4.2), 0.12, fill=False, edgecolor='#663399', linewidth=1.2))
ax.add_patch(FancyArrowPatch((x-0.75, 3.45), (x+0.75, 3.45), arrowstyle='-|>', mutation_scale=14, color='#777777', lw=1.1, linestyle='--'))
ax.text(x, 3.2, 'decay path', ha='center', fontsize=8)

# formula strip
strip = FancyBboxPatch((0.7, 0.55), 12.6, 1.45, boxstyle='round,pad=0.10',
                       linewidth=1.1, facecolor='#f7f7ff', edgecolor='#335c99')
ax.add_patch(strip)
ax.text(7, 1.55, r'$P^{PADAR}_{W}(\partial F,\omega)=\sum_{e\in W} C_{3,e}\min(D_e(\partial F,\omega),|\omega|_e)|\Delta^{\chi lag}_e|$',
        ha='center', fontsize=13)
ax.text(7, 1.02, r'shed excess: $X_W=\max(0,P^{PADAR}_{W}-C^{close}_{W})$   |   local reclosure: $X_W^{reclose}=\lambda_{reclose} X_W$   |   outward shedding: $X_W^{out}=(1-\lambda_{reclose})X_W$',
        ha='center', fontsize=10)

fig.tight_layout()
fig.savefig(FIG_DIR / 'v39_15_wavelet_group_disturbance_shedding.png', dpi=220)
plt.close(fig)

# -------------------------
# Demonstration run
# -------------------------
T = 90
t = np.arange(T)
lead = 0.42 + 0.08*np.sin(2*np.pi*t/28) + 0.19*np.exp(-((t-28)/7)**2) + 0.13*np.exp(-((t-61)/8)**2)
lag = 0.38 + 0.07*np.cos(2*np.pi*(t+4)/31) - 0.10*np.exp(-((t-30)/8)**2) + 0.18*np.exp(-((t-56)/7)**2)
span = np.abs(lead-lag)
compat = 0.52 + 0.05*np.sin(2*np.pi*(t+8)/37)
eta_ret = 0.82
gamma_span = 0.55
lambda_reclose = 0.38
P = np.zeros(T)
shed = np.zeros(T)
outward = np.zeros(T)
reclose = np.zeros(T)
state = []
threshold = 0.09
for i in range(T):
    prev = P[i-1] if i else 0.0
    raw = eta_ret*prev + gamma_span*span[i]
    x = max(0.0, raw - compat[i])
    shed[i] = x
    P[i] = raw - x
    outward[i] = (1-lambda_reclose)*x
    reclose[i] = lambda_reclose*x
    state.append('reclosure' if reclose[i] > threshold else 'open')

fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
axs[0].plot(t, lead, label='lead component', lw=1.5)
axs[0].plot(t, lag, label='lag component', lw=1.5)
axs[0].set_ylabel('component')
axs[0].legend(loc='upper right', fontsize=8)
axs[0].set_title('Demonstration run: wavelet-group disturbance shedding')
axs[1].plot(t, span, label='lead-lag span', lw=1.5)
axs[1].plot(t, P, label='PADAR burden P_t', lw=1.5)
axs[1].plot(t, compat, label='closure compatibility', lw=1.5, linestyle='--')
axs[1].set_ylabel('burden')
axs[1].legend(loc='upper right', fontsize=8)
axs[2].bar(t, outward, label='outward shedding', alpha=0.7)
axs[2].bar(t, reclose, bottom=outward, label='local reclosure', alpha=0.7)
reclosures = np.array([i for i, s in enumerate(state) if s == 'reclosure'])
if len(reclosures):
    axs[2].scatter(reclosures, outward[reclosures]+reclose[reclosures]+0.015, s=25, marker='o', color='black', label='shell reclosure trigger')
axs[2].set_ylabel('shed excess')
axs[2].set_xlabel('tick')
axs[2].legend(loc='upper right', fontsize=8)
for ax in axs:
    ax.grid(True, alpha=0.25)
fig.tight_layout()
fig.savefig(FIG_DIR / 'v39_wavelet_disturbance_shedding_simulation.png', dpi=220)
plt.close(fig)

with open(CSV_PATH, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['tick','lead','lag','span','compatibility','padar_burden','shed_excess','outward_shedding','local_reclosure','state'])
    for i in range(T):
        w.writerow([i,lead[i],lag[i],span[i],compat[i],P[i],shed[i],outward[i],reclose[i],state[i]])

summary = {
    'ticks': T,
    'max_span': float(span.max()),
    'max_padar_burden': float(P.max()),
    'max_shed_excess': float(shed.max()),
    'total_outward_shedding': float(outward.sum()),
    'total_local_reclosure': float(reclose.sum()),
    'reclosure_count': int((np.array(state)=='reclosure').sum()),
    'first_reclosure_tick': int(reclosures[0]) if len(reclosures) else -1,
}
with open(SUMMARY_PATH, 'w') as f:
    f.write('\\begin{tabular}{lr}\n')
    f.write('\\toprule\n')
    rows = [
        ('Ticks', f"{summary['ticks']}"),
        ('Maximum lead-lag span', f"{summary['max_span']:.3f}"),
        ('Maximum PADAR burden', f"{summary['max_padar_burden']:.3f}"),
        ('Maximum shed excess', f"{summary['max_shed_excess']:.3f}"),
        ('Total outward shedding', f"{summary['total_outward_shedding']:.3f}"),
        ('Total local reclosure', f"{summary['total_local_reclosure']:.3f}"),
        ('Shell-reclosure trigger ticks', f"{summary['reclosure_count']}"),
        ('First reclosure tick', f"{summary['first_reclosure_tick'] if summary['first_reclosure_tick'] >= 0 else 'none'}"),
    ]
    for label, value in rows:
        f.write(f'{label} & {value} \\\\\n')
    f.write('\\bottomrule\n')
    f.write('\\end{tabular}\n')
