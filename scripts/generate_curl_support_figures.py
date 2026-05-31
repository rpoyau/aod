from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch, Arc
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / 'figures_jpg'
FIG_DIR.mkdir(parents=True, exist_ok=True)

# ---------- helpers ----------
def rounded_box(ax, x, y, w, h, title, lines=None, edge='#2f5597', face='#ffffff', title_color=None, fs=8.5):
    title_color = title_color or edge
    p = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.05', linewidth=1.2, edgecolor=edge, facecolor=face)
    ax.add_patch(p)
    ax.text(x+w/2, y+h-0.18, title, ha='center', va='top', fontsize=fs, fontweight='bold', color=title_color)
    if lines:
        for i, line in enumerate(lines):
            ax.text(x+w/2, y+h-0.48-0.22*i, line, ha='center', va='top', fontsize=fs-1.2, color='#222222')
    return p

def arrow(ax, x1, y1, x2, y2, color='#555', lw=1.1, ms=10):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2), arrowstyle='-|>', mutation_scale=ms, linewidth=lw, color=color))

def swirl(ax, cx, cy, r=0.28, turns=2.0, color='#1f5fbf', lw=1.1):
    t = np.linspace(0, turns*2*np.pi, 160)
    rr = np.linspace(0.04, r, len(t))
    ax.plot(cx + rr*np.cos(t), cy + rr*np.sin(t), color=color, lw=lw)

# ---------- Figure 2: curl to duon current support ----------
fig, ax = plt.subplots(figsize=(14, 7.8))
ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.axis('off')
ax.text(8, 8.55, 'Curl to Duon Current Support', ha='center', va='center', fontsize=22, fontweight='bold')

steps = [
    ('1', 'BRANCH / HINGE / BRANCH', ['branch', 'hinge', 'branch']),
    ('2', 'CURL', ['returned closure', 'through hinge']),
    ('3', 'NESTED CURL', ['curl inside curl']),
    ('4', 'PIN-CURL', ['returned residue', 'seats hinge']),
    ('5', 'FIELD', ['declared boundary', 'retains current']),
    ('6', 'CYCLE', ['branch/hinge/branch', 'retained package']),
    ('7', 'DUON CURRENT', ['cycle support', 'carries hinge-current']),
    ('8', 'FIELD', ['region', 'boundary', 'window']),
]
coords = []
for i in range(4):
    coords.append((0.55 + i*3.9, 5.35))
for i in range(4):
    coords.append((0.55 + i*3.9, 2.55))

for idx, ((num, title, lines), (x,y)) in enumerate(zip(steps, coords)):
    rounded_box(ax, x, y, 3.15, 1.95, title, lines, edge='#2f5597' if idx>=4 else '#d55e00', face='#fbfcff', fs=8.0)
    # number dot
    ax.add_patch(Circle((x+0.22, y+1.70), 0.16, color='#f28c28' if idx<4 else '#174ea6'))
    ax.text(x+0.22, y+1.70, num, ha='center', va='center', fontsize=8, color='white', fontweight='bold')
    # inner sketch
    cx, cy = x+1.58, y+0.77
    if idx == 0:
        ax.plot([cx-1.0,cx-0.25], [cy, cy], color='#d55e00', lw=1.3)
        ax.plot([cx+0.25,cx+1.0], [cy, cy], color='#d55e00', lw=1.3)
        ax.add_patch(Circle((cx,cy),0.10, fill=False, edgecolor='#444', lw=1.0))
        arrow(ax, cx-0.7, cy+0.25, cx-0.25, cy+0.05, '#d55e00', 1.0, 8)
        arrow(ax, cx+0.7, cy-0.25, cx+0.25, cy-0.05, '#d55e00', 1.0, 8)
    elif idx == 1:
        ax.add_patch(Arc((cx-0.35, cy), 0.9, 1.0, theta1=270, theta2=90, color='#d55e00', lw=1.3))
        ax.add_patch(Arc((cx+0.35, cy), 0.9, 1.0, theta1=90, theta2=270, color='#d55e00', lw=1.3))
        ax.plot([cx, cx], [cy-0.62, cy+0.62], color='#aaa', lw=0.8, linestyle='--')
    elif idx == 2:
        for r in [0.25,0.45,0.65]:
            ax.add_patch(Circle((cx,cy),r, fill=False, edgecolor='#d55e00', lw=1.1))
    elif idx == 3:
        for r in [0.25,0.48,0.70]:
            ax.add_patch(Circle((cx,cy),r, fill=False, edgecolor='#1f5fbf', lw=1.0))
        ax.plot([cx-1.0,cx+1.0],[cy,cy], color='#1f5fbf', lw=1.2)
        ax.add_patch(Circle((cx,cy),0.07, color='#1f5fbf'))
    elif idx == 4:
        for r in [0.35,0.58]:
            ax.add_patch(Circle((cx,cy),r, fill=False, edgecolor='#1f5fbf', lw=1.1))
        ax.plot([cx-0.9,cx+0.9],[cy,cy], color='#1f5fbf', lw=1.1)
        ax.add_patch(Circle((cx,cy),0.08, color='#1f5fbf'))
    elif idx == 5:
        swirl(ax, cx-0.2, cy, 0.55, 2.0, '#1f5fbf', 1.1)
        arrow(ax, cx-0.95, cy+0.58, cx+0.95, cy+0.58, '#1f5fbf', 1.0, 8)
        arrow(ax, cx+0.95, cy-0.58, cx-0.95, cy-0.58, '#1f5fbf', 1.0, 8)
    elif idx == 6:
        for k in np.linspace(cx-0.9,cx+0.9,5):
            ax.add_patch(Circle((k,cy),0.18, fill=False, edgecolor='#1f5fbf', lw=1.2))
            arrow(ax, k-0.12, cy, k+0.16, cy, '#1f5fbf', 0.9, 6)
        ax.add_patch(FancyBboxPatch((cx-1.1, cy-0.35), 2.2, 0.7, boxstyle='round,pad=0.02', linewidth=0.8, edgecolor='#777', facecolor='none'))
    elif idx == 7:
        # field panel with region/boundary/window
        ax.add_patch(Circle((cx,cy),0.72, fill=False, edgecolor='#1f5fbf', lw=1.4))
        for r in [0.25,0.46,0.72]:
            ax.add_patch(Circle((cx,cy),r, fill=False, edgecolor='#a9c5f2', lw=0.9, linestyle='--'))
        ax.plot([cx-0.85,cx+0.85],[cy,cy], color='#663399', lw=1.1)
        ax.text(cx-0.55, cy-0.86, 'predecessor', ha='center', fontsize=6.5)
        ax.text(cx, cy-1.03, 'boundary', ha='center', fontsize=6.5)
        ax.text(cx+0.55, cy-0.86, 'horizon', ha='center', fontsize=6.5)

# arrows top row
for i in range(3):
    arrow(ax, coords[i][0]+3.2, coords[i][1]+0.98, coords[i+1][0]-0.10, coords[i+1][1]+0.98, '#666', 1.2, 12)
# turn arrow and bottom row
arrow(ax, coords[3][0]+1.55, coords[3][1]-0.08, coords[4][0]+1.55, coords[4][1]+2.02, '#666', 1.2, 12)
for i in range(4,7):
    arrow(ax, coords[i][0]+3.2, coords[i][1]+0.98, coords[i+1][0]-0.10, coords[i+1][1]+0.98, '#666', 1.2, 12)

# compact comb origin strip
strip = FancyBboxPatch((1.1,0.55),13.8,1.25, boxstyle='round,pad=0.08', linewidth=1.0, edgecolor='#335c99', facecolor='#f7f9ff')
ax.add_patch(strip)
ax.text(8,1.52,'Combinatoric origin of duon current', ha='center', fontsize=9, fontweight='bold', color='#335c99')
labels=['branch/hinge/branch','curl','nested curl','pin-curl','field','cycle','duon current','field']
xs=np.linspace(1.8,14.2,len(labels))
for x,label in zip(xs, labels):
    ax.text(x,0.95,label,ha='center',fontsize=6.5)
for i in range(len(xs)-1):
    arrow(ax,xs[i]+0.35,1.12,xs[i+1]-0.35,1.12,'#777',0.7,6)

fig.tight_layout()
fig.savefig(FIG_DIR / 'curl_to_duon_current_support.png', dpi=220)
plt.close(fig)

# ---------- Figure 4: shell families with distinct outer paths ----------
fig, ax = plt.subplots(figsize=(14,8.5))
ax.set_xlim(0,15.5)
ax.set_ylim(0,9)
ax.axis('off')
ax.text(7.75,8.55,'Curling-curl shell families',ha='center',fontsize=24,fontweight='bold', color='#1f2a44')
ax.text(7.75,8.15,'cycle -> inner enclosure -> core family -> outer shell path',ha='center',fontsize=11,color='#555')
# top layers
layers=[('Tetrion',['four-cycle closure','cycle term']),('Tetron',['inner four-seat enclosure','E4']),('Core families',['Dimonon 1:2','Tritrion 3:3','Tetratrion 3:4']),('Outer shell paths',['hexon 6','octon 8','decon 10'])]
for i,(title,lines) in enumerate(layers):
    x=0.65+i*3.75
    rounded_box(ax,x,6.5,3.0,1.4,title,lines,edge='#174ea6',face='#fbfcff',fs=9)
    if i<3:
        arrow(ax,x+3.05,7.2,x+3.65,7.2,'#777',1.0,12)
# enclosed names left-to-right
examples=[('Dimonhexon','1:2:6','hexon'),('Dimonocton','1:2:8','octon'),('Dimondecon','1:2:10','decon'),('Tritriohexon','3:3:6','hexon'),('Tetratriohexon','3:4:6','hexon')]
for idx,(name,num,shell) in enumerate(examples):
    x=0.65+idx*2.95
    rounded_box(ax,x,4.65,2.5,1.25,name,[num, shell+' path'],edge='#335c99',face='#ffffff',fs=8.5)
# distinct path diagrams
path_specs=[('C6 hexon',6,0.55),('C8 octon',8,0.75),('C10 decon',10,0.95)]
for idx,(label,n,radius) in enumerate(path_specs):
    cx=3.7+idx*3.2
    cy=2.85
    ax.text(cx,3.85,label,ha='center',fontsize=10,fontweight='bold')
    # core enclosure
    ax.add_patch(Circle((cx,cy),0.25,fill=False,edgecolor='#663399',lw=1.2))
    ax.add_patch(Circle((cx,cy),0.45,fill=False,edgecolor='#1f5fbf',lw=1.1))
    # outer shell with n beads
    ax.add_patch(Circle((cx,cy),radius,fill=False,edgecolor='#d09000',lw=1.6))
    for k in range(n):
        ang=2*np.pi*k/n
        ax.add_patch(Circle((cx+radius*np.cos(ang), cy+radius*np.sin(ang)),0.07,fill=True,edgecolor='#d09000',facecolor='#fff4d6',lw=0.8))
    # ttl arrow path
    arrow(ax,cx-radius-0.7,cy-1.05,cx+radius+0.7,cy-1.05,'#d55e00',1.3,12)
    ax.text(cx,cy-1.33,'lifted retention path' if n>6 else 'default closure',ha='center',fontsize=8,color='#444')
# legend strip
strip=FancyBboxPatch((0.7,0.55),14.0,0.95,boxstyle='round,pad=0.08',linewidth=1.1,edgecolor='#335c99',facecolor='#f7f9ff')
ax.add_patch(strip)
ax.text(7.75,1.08,'alpha outward dressing  |  Omega return dressing  |  polychiral return clocks  |  field outer dressing  |  retention-conditioned shell path',ha='center',fontsize=10)
fig.tight_layout()
fig.savefig(FIG_DIR / 'curling_curl_layers.png', dpi=220)
plt.close(fig)

# ---------- Seat-compatible retention figure ----------
fig, ax = plt.subplots(figsize=(14,7.8))
ax.set_xlim(0,14)
ax.set_ylim(0,8)
ax.axis('off')
ax.text(7,7.55,'Seat-compatible retention and outer path',ha='center',fontsize=22,fontweight='bold', color='#1f2a44')
ax.text(7,7.15,r'inner enclosure -> support enclosure -> retained $TTL_{\mathcal{C}}$ or sheddic path',ha='center',fontsize=11,color='#555')
# panels
panels=[('E4 tetron','inner four-seat enclosure',4,0.38),('C6 hexon','first outer enclosure',6,0.52),('C8 octon','lifted outer path',8,0.66),('C10 decon','higher outer path',10,0.78)]
for i,(title,subtitle,n,radius) in enumerate(panels):
    x=0.6+i*3.25
    # Top text panels stay fully above the topology row.
    rounded_box(ax,x,4.95,2.65,1.05,title,[subtitle],edge='#174ea6',face='#ffffff',fs=9)
    cx=x+1.33; cy=3.38
    ax.add_patch(Circle((cx,cy),0.22,fill=False,edgecolor='#663399',lw=1.2))
    ax.add_patch(Circle((cx,cy),radius,fill=False,edgecolor='#d09000',lw=1.5))
    for k in range(n):
        ang=2*np.pi*k/n
        ax.add_patch(Circle((cx+radius*np.cos(ang), cy+radius*np.sin(ang)),0.048,facecolor='#fff4d6',edgecolor='#d09000',lw=0.7))
    if i<3:
        arrow(ax,x+2.7,5.47,x+3.12,5.47,'#777',1.0,12)
# seat-compatible retention/fail lanes
rounded_box(ax,0.9,1.05,5.7,0.98,'retention held over window',[r'$TTL_{\mathcal{C}}(\partial F,\omega)\geq |\omega|$','route retained over window'],edge='#2f7d32',face='#f8fff8',fs=8.6)
arrow(ax,1.5,0.87,6.2,0.87,'#2f7d32',1.5,14)
rounded_box(ax,7.4,1.05,5.7,0.98,'retention shorter than window',[r'$TTL_{\mathcal{C}}(\partial F,\omega)< |\omega|$','route continues / re-entry / reclosure'],edge='#d55e00',face='#fff9f2',fs=8.6)
arrow(ax,8.0,0.87,12.7,0.87,'#d55e00',1.5,14)
# Formula strip
strip=FancyBboxPatch((0.9,0.18),12.2,0.52,boxstyle='round,pad=0.08',linewidth=1.0,edgecolor='#335c99',facecolor='#f7f9ff')
ax.add_patch(strip)
ax.text(7,0.44,r'$X_{\mathcal{C}}(B)=\operatorname{route}_{\mathcal{C}}(X_{\mathrm{shedding}}(B)),\quad \mathrm{SheddicPath}(X_{\mathrm{shedding}})\in\{E_2,\mathrm{C}_6,\mathrm{C}_8,\mathrm{C}_{10},\ldots,\mathrm{C}_{2n}\}$',ha='center',fontsize=9.2)
fig.tight_layout()
fig.savefig(FIG_DIR / 'support_enclosure_retention.png', dpi=220)
plt.close(fig)
