import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
from matplotlib.lines import Line2D
import numpy as np
from pathlib import Path

OUT = Path('/mnt/data/work_v3976/manual/figures')
OUT.mkdir(parents=True, exist_ok=True)

# ---------- Tau sensor-wall setup and boundary stack ----------
fig = plt.figure(figsize=(14, 10), dpi=180)
fig.patch.set_facecolor('white')

def add_panel_border(ax):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.add_patch(Rectangle((0.005,0.005),0.99,0.99, fill=False, lw=1.2, ec='black'))

ax1 = fig.add_axes([0.035, 0.52, 0.93, 0.43])
add_panel_border(ax1)
ax1.text(0.025,0.94,'(a) Tau sensor-wall setup',fontsize=20,weight='bold',va='center')

# circles
cx, cy = 0.50, 0.53
r_outer, r_shed, r_tau = 0.23, 0.165, 0.095
ax1.add_patch(Circle((cx,cy), r_outer, fill=False, lw=1.7, ec='black'))
ax1.add_patch(Circle((cx,cy), r_shed, fill=False, lw=1.4, ec='black', ls=':'))
ax1.add_patch(Circle((cx,cy), r_tau, fill=False, lw=1.4, ec='black', ls=(0,(5,4))))
ax1.plot(cx, cy, marker='*', markersize=14, color='black')

# proton beam
ax1.add_patch(FancyArrowPatch((0.08, cy), (cx-0.02, cy), arrowstyle='-|>', mutation_scale=18, lw=1.6, color='black'))
ax1.text(0.08, cy+0.045, 'proton beam', fontsize=14, ha='left', va='bottom')
ax1.text(cx-0.05, cy-0.13, 'collision\ncenter', fontsize=12, ha='center')

# debris arrows
angles = np.deg2rad([20, 55, 115, 150, -25, -55])
for a in angles:
    end = (cx + 0.13*np.cos(a), cy + 0.13*np.sin(a))
    ax1.add_patch(FancyArrowPatch((cx,cy), end, arrowstyle='-|>', mutation_scale=13, lw=1.3, color='black'))
# missing burden dashed branch
ax1.add_patch(FancyArrowPatch((cx+0.045,cy-0.05),(0.77,0.32), arrowstyle='-|>', mutation_scale=14, lw=1.4, linestyle=(0,(5,4)), color='black'))

# leader lines / labels
labels = [
    ('sensor wall', (0.78,0.86), (cx+r_outer*0.72, cy+r_outer*0.70)),
    ('shedding\nboundary', (0.78,0.73), (cx+r_shed*0.75, cy+r_shed*0.70)),
    ('tau-candidate\nfield', (0.78,0.60), (cx+r_tau*0.75, cy+r_tau*0.30)),
    ('visible debris', (0.78,0.46), (cx+0.11, cy+0.02)),
    ('missing burden /\nlow-coupling branch', (0.78,0.29), (0.69,0.35)),
]
for txt, tpos, spos in labels:
    ax1.add_patch(FancyArrowPatch(tpos, spos, arrowstyle='->', mutation_scale=11, lw=1.1, color='black'))
    ax1.text(tpos[0]+0.01, tpos[1], txt, fontsize=13, ha='left', va='center')

ax1.text(0.08,0.16,'tau_TTL approx 0.29 ps', fontsize=16, ha='left')
ax1.text(0.50,0.07,'sensor records debris crossing the wall, not the complete tau field',fontsize=14,ha='center',style='italic')

ax2 = fig.add_axes([0.035, 0.08, 0.93, 0.38])
add_panel_border(ax2)
ax2.text(0.025,0.90,'(b) Boundary stack',fontsize=20,weight='bold',va='center')

nodes = [
    (r'$B_{\rm hard}$','proton-proton\ncollision'),
    (r'$B_{\tau}$','1:2:9 open\ncandidate'),
    (r'$B_{\rm sheddic}$',r'$X_{\rm shedding}=3$'),
    (r'$B_{\rm sensor}$','visible +\nmissing burden'),
    (r'$B_{\rm ext}$','quarantined\nexternal comparison')
]
xs = np.linspace(0.13,0.87,len(nodes))
y = 0.58
w,h = 0.105,0.15
for i,(lab,sub) in enumerate(nodes):
    x = xs[i]
    ax2.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle='round,pad=0.01,rounding_size=0.012',lw=1.2,ec='black',fc='white'))
    ax2.text(x,y,lab,fontsize=14,ha='center',va='center')
    ax2.text(x,y-0.19,sub,fontsize=12,ha='center',va='top')
    if i < len(nodes)-1:
        ax2.add_patch(FancyArrowPatch((x+w/2+0.01,y),(xs[i+1]-w/2-0.01,y),arrowstyle='-|>',mutation_scale=14,lw=1.2,color='black'))

ax2.add_patch(Rectangle((0.08,0.09),0.84,0.13, fill=False, lw=1.2, ec='black', ls=(0,(5,3))))
ax2.text(0.50,0.155,'anything fully retained inside the inner window is not directly recorded at the sensor wall',fontsize=12.5,ha='center',va='center',style='italic')
fig.savefig(OUT/'tau_sensor_wall_setup_and_boundary_stack.png', bbox_inches='tight')
plt.close(fig)

# ---------- Double-slit cross-return setup ----------
fig = plt.figure(figsize=(14, 8), dpi=180)
fig.patch.set_facecolor('white')
ax = fig.add_axes([0.04, 0.08, 0.92, 0.84])
ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
ax.add_patch(Rectangle((0.005,0.005),0.99,0.99, fill=False, lw=1.2, ec='black'))
ax.text(0.03,0.94,'Double-slit cross-return fixture',fontsize=20,weight='bold')
# left slit/gates
for y0, lab in [(0.68,r'$g_a$'),(0.42,r'$g_b$')]:
    ax.add_patch(FancyBboxPatch((0.10,y0-0.045),0.09,0.09,boxstyle='round,pad=0.01',lw=1.2,ec='black',fc='white'))
    ax.text(0.145,y0,lab,fontsize=16,ha='center',va='center')
    ax.add_patch(FancyArrowPatch((0.02,y0),(0.10,y0),arrowstyle='-|>',mutation_scale=15,lw=1.3,color='black'))
ax.text(0.02,0.79,'boundary\ngates',fontsize=13,ha='left')

# individual contributions
ax.add_patch(FancyBboxPatch((0.30,0.68-0.055),0.14,0.11,boxstyle='round,pad=0.01',lw=1.2,fc='white',ec='black'))
ax.text(0.37,0.68,r'$S_k^{(a)}$',fontsize=16,ha='center',va='center')
ax.add_patch(FancyBboxPatch((0.30,0.42-0.055),0.14,0.11,boxstyle='round,pad=0.01',lw=1.2,fc='white',ec='black'))
ax.text(0.37,0.42,r'$S_k^{(b)}$',fontsize=16,ha='center',va='center')
for y0 in [0.68,0.42]:
    ax.add_patch(FancyArrowPatch((0.19,y0),(0.30,y0),arrowstyle='-|>',mutation_scale=13,lw=1.2,color='black'))

# no-cross sum
ax.add_patch(FancyBboxPatch((0.53,0.60-0.055),0.18,0.11,boxstyle='round,pad=0.01',lw=1.2,fc='white',ec='black'))
ax.text(0.62,0.60,r'$T_k^0=S_k^{(a)}+S_k^{(b)}$',fontsize=14,ha='center',va='center')
ax.add_patch(FancyArrowPatch((0.44,0.68),(0.53,0.61),arrowstyle='-|>',mutation_scale=13,lw=1.2,color='black'))
ax.add_patch(FancyArrowPatch((0.44,0.42),(0.53,0.59),arrowstyle='-|>',mutation_scale=13,lw=1.2,color='black'))

# cross return dashed
ax.add_patch(FancyArrowPatch((0.145,0.68),(0.145,0.42),arrowstyle='<->',mutation_scale=13,lw=1.2,linestyle=(0,(5,3)),color='black',connectionstyle='arc3,rad=0.35'))

ax.text(0.855,0.54,'T_cross = T_no + C_cross',fontsize=11,ha='center',va='center')
ax.add_patch(FancyBboxPatch((0.75,0.54-0.055),0.21,0.11,boxstyle='round,pad=0.01',lw=1.2,fc='white',ec='black'))
ax.add_patch(FancyArrowPatch((0.71,0.60),(0.75,0.55),arrowstyle='-|>',mutation_scale=13,lw=1.2,color='black'))
ax.add_patch(FancyArrowPatch((0.27,0.54),(0.75,0.52),arrowstyle='-|>',mutation_scale=13,lw=1.2,linestyle=(0,(5,3)),color='black'))

# bins panel
bins = [-3,-2,-1,0,1,2,3]
vals = [20,58,80,96,80,58,20]
base_x, base_y = 0.22, 0.18
for i,b in enumerate(bins):
    x=base_x+i*0.08
    height=0.08+0.0016*vals[i]
    ax.add_patch(Rectangle((x,base_y),0.045,height,fill=False,lw=1.1,ec='black'))
ax.text(0.50,0.07,'fixture identity: T_cross - T_no-cross = C_cross',fontsize=15,ha='center')
ax.text(base_x+0.24,base_y+0.36,'reclosure bins',fontsize=13,ha='center')
fig.savefig(OUT/'double_slit_cross_return_setup.png', bbox_inches='tight')
plt.close(fig)
