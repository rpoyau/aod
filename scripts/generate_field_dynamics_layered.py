#!/usr/bin/env python3
"""Generate the Layered Field Dynamics figure with AΩD structural labels."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

NAVY = '#0b1d34'
BLUE = '#173f6b'
MID = '#6e8198'
LIGHT = '#dfe6ee'
TEAL = '#0a6b73'
GRAY = '#b9c2cc'

fig, ax = plt.subplots(figsize=(10.24, 12.8), dpi=150)
ax.set_xlim(-1.35, 1.55)
ax.set_ylim(-1.45, 1.45)
ax.axis('off')
fig.patch.set_facecolor('white')

# Title
ax.text(0, 1.36, 'LAYERED FIELD DYNAMICS', ha='center', va='center', fontsize=24, fontweight='bold', color=NAVY)
ax.text(0, 1.29, 'core coupling, support/current lift, and exoshedding', ha='center', va='center', fontsize=14, color=BLUE)

# Boundaries
radii = np.linspace(0.13, 0.88, 8)
for i, r in enumerate(radii):
    lw = 1.1 if i not in (0, len(radii)-1) else 2.0
    color = MID if i % 2 else GRAY
    ax.add_patch(Circle((0,0), r, fill=False, lw=lw, ec=color, alpha=0.85))

# Core
ax.add_patch(Circle((0,0), 0.05, color=NAVY))
ax.text(0, -0.105, 'core', ha='center', va='top', fontsize=11, color=NAVY)

# Same-direction circulation arrows: all counterclockwise, no opposition.
def circular_arrow(radius, theta1, theta2, color=BLUE, lw=1.5, alpha=1.0):
    # small arc arrow from theta1 to theta2 in degrees
    t1, t2 = np.deg2rad(theta1), np.deg2rad(theta2)
    x1, y1 = radius*np.cos(t1), radius*np.sin(t1)
    x2, y2 = radius*np.cos(t2), radius*np.sin(t2)
    # approximate tangential arrow with connectionstyle arc3 small curve
    arr = FancyArrowPatch((x1,y1), (x2,y2), arrowstyle='-|>', mutation_scale=12,
                          connectionstyle=f'arc3,rad={0.18 if theta2>theta1 else -0.18}',
                          lw=lw, color=color, alpha=alpha)
    ax.add_patch(arr)

for idx, r in enumerate(radii[1:]):
    for base in [35, 120, 205, 290]:
        circular_arrow(r, base, base+24, color=BLUE, lw=1.1 + 0.1*idx, alpha=0.95)
for r in [0.18,0.23,0.28,0.34,0.42,0.52]:
    for base in [55,150,245,335]:
        circular_arrow(r, base, base+26, color=NAVY, lw=1.1, alpha=0.95)

# Inter-layer coupling channels (solid teal radial connectors)
for deg, r0, r1 in [(22,0.36,0.64),(62,0.46,0.78),(145,0.30,0.55),(215,0.42,0.68),(302,0.50,0.78)]:
    th = np.deg2rad(deg)
    x0,y0 = r0*np.cos(th), r0*np.sin(th)
    x1,y1 = r1*np.cos(th), r1*np.sin(th)
    ax.plot([x0,x1],[y0,y1], color=TEAL, lw=2.0)
    ax.scatter([x0,x1],[y0,y1], s=20, color=TEAL, zorder=5)

# Exoshedding / decoupling dashed arrows outward
for deg, r0, r1 in [(0,0.82,1.05),(45,0.70,0.98),(90,0.72,1.07),(135,0.72,0.98),(180,0.82,1.05),(225,0.72,0.98),(270,0.72,1.07),(315,0.72,0.98)]:
    th=np.deg2rad(deg)
    x0,y0=r0*np.cos(th), r0*np.sin(th)
    x1,y1=r1*np.cos(th), r1*np.sin(th)
    arr=FancyArrowPatch((x0,y0),(x1,y1),arrowstyle='-|>',mutation_scale=11,lw=1.2,color=TEAL,linestyle=(0,(4,3)),alpha=0.9)
    ax.add_patch(arr)

# Labels / callouts
def callout(text, xy, xytext, ha='left'):
    ax.annotate(text, xy=xy, xytext=xytext, textcoords='data', ha=ha, va='center',
                fontsize=10.5, color=NAVY,
                arrowprops=dict(arrowstyle='-', color=NAVY, lw=1.1, shrinkA=0, shrinkB=3))

callout('core coupling\nstrongest retained coupling;\nseeds retained circulation', (-0.17,0.13), (-1.18,0.95))
callout('inter-layer coupling\nretained transfer through\ndeclared channels', (0.55,0.67), (0.84,0.95))
callout('channel capacity\nradial channels store,\nbuffer, and transfer support', (-0.74,-0.53), (-1.18,-0.82))
callout('outer-layer coupling\nbroader retained circulation;\nredistribution and recycling', (0.0,-0.89), (-0.28,-1.16), ha='center')
callout('support/current lift\nexoshedding routes surplus\ntoward outer boundaries', (0.66,-0.55), (0.85,-0.86))

# Right inset boxes
for y, title, lines in [
    (0.50, 'A. LIFT / EXOSHEDDING VIEW', ['support/current lifts', 'from inner layers', 'along sheddic routes']),
    (-0.33, 'B. RADIAL CHANNEL /\nCAPACITY VIEW', ['channels provide', 'capacity, buffering,', 'and transfer'])]:
    box = FancyBboxPatch((1.02,y-0.28), 0.45, 0.56, boxstyle='round,pad=0.02', ec=MID, fc='white', lw=1.1)
    ax.add_patch(box)
    ax.text(1.245, y+0.21, title, ha='center', va='center', fontsize=9.3, color=BLUE, fontweight='bold')
    # mini diagram
    if y>0:
        for rr in [0.04,0.07,0.10,0.13]:
            ax.add_patch(Circle((1.15,y+0.02), rr, fill=False, lw=0.8, ec=BLUE))
        for dx in [0.05,0.10,0.15]:
            arr=FancyArrowPatch((1.28+dx,y-0.10),(1.28+dx,y+0.14),arrowstyle='-|>',mutation_scale=8,lw=1.0,color=BLUE)
            ax.add_patch(arr)
        for deg in [-35,0,35]:
            th=np.deg2rad(deg)
            arr=FancyArrowPatch((1.15+0.13*np.cos(th),y+0.02+0.13*np.sin(th)),(1.15+0.22*np.cos(th),y+0.02+0.22*np.sin(th)),arrowstyle='-|>',mutation_scale=7,lw=0.8,color=TEAL,linestyle=(0,(3,2)))
            ax.add_patch(arr)
    else:
        xs=np.linspace(1.13,1.33,5)
        for i,x in enumerate(xs):
            ax.plot([x,x+0.03*np.sin(i)],[y-0.14,y+0.14], color=BLUE, lw=1.0)
        for yy in [y-0.08,y,y+0.08]:
            arr=FancyArrowPatch((1.10,yy),(1.38,yy),arrowstyle='-|>',mutation_scale=8,lw=0.9,color=TEAL,linestyle=(0,(3,2)))
            ax.add_patch(arr)
    ax.text(1.245, y-0.20, '\n'.join(lines), ha='center', va='center', fontsize=8.4, color=NAVY)

# Legend
legend_y=-1.34
legend_x=-0.90
ax.text(legend_x-0.20, legend_y+0.10, 'Arrow key:', color=NAVY, fontsize=10, fontweight='bold', va='center')
arr=FancyArrowPatch((legend_x,legend_y+0.10),(legend_x+0.18,legend_y+0.10),arrowstyle='-|>',mutation_scale=12,lw=1.5,color=BLUE)
ax.add_patch(arr); ax.text(legend_x+0.23,legend_y+0.10,'circulation',fontsize=8.8,color=NAVY,va='center')
ax.plot([legend_x+0.65,legend_x+0.82],[legend_y+0.10,legend_y+0.10],color=TEAL,lw=2); ax.scatter([legend_x+0.65,legend_x+0.82],[legend_y+0.10,legend_y+0.10],s=15,color=TEAL); ax.text(legend_x+0.88,legend_y+0.10,'inter-layer coupling',fontsize=8.8,color=NAVY,va='center')
arr=FancyArrowPatch((legend_x,legend_y-0.02),(legend_x+0.18,legend_y-0.02),arrowstyle='-|>',mutation_scale=12,lw=1.2,color=TEAL,linestyle=(0,(4,3)))
ax.add_patch(arr); ax.text(legend_x+0.23,legend_y-0.02,'decoupling / lift',fontsize=8.8,color=NAVY,va='center')
ax.plot([legend_x+0.65,legend_x+0.82],[legend_y-0.02,legend_y-0.02],color=GRAY,lw=2); ax.text(legend_x+0.88,legend_y-0.02,'layer boundary',fontsize=8.8,color=NAVY,va='center')

plt.tight_layout(pad=0.3)
fig.savefig('figures_jpg/field_dynamics_layered.png', dpi=150, bbox_inches='tight')
