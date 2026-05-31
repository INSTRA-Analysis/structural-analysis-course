"""
notebook_generator.py — Build a self-contained Jupyter notebook for the
simply supported beam analysis course.

The generated notebook:
  - Requires only numpy, scipy, and matplotlib (no course imports)
  - Uses the student's actual beam geometry and loads
  - Walks through every concept in lesson order with annotated code
  - Produces all plots inline

Usage:
    from notebook_generator import generate_notebook
    json_str = generate_notebook(geometry, loads)
    # offer json_str as a .ipynb download
"""

import json


# ---------------------------------------------------------------------------
# Cell builders
# ---------------------------------------------------------------------------

def _cell_id(n):
    return f"cell-{n:04d}"


def _md(n, text):
    """Markdown cell. text is a plain string — split into source lines."""
    lines = text.split("\n")
    source = [ln + "\n" for ln in lines[:-1]] + [lines[-1]]
    return {
        "cell_type": "markdown",
        "id": _cell_id(n),
        "metadata": {},
        "source": source,
    }


def _code(n, text):
    """Code cell. text is a plain string."""
    lines = text.split("\n")
    source = [ln + "\n" for ln in lines[:-1]] + [lines[-1]]
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": _cell_id(n),
        "metadata": {},
        "outputs": [],
        "source": source,
    }


# ---------------------------------------------------------------------------
# Geometry / loads → Python source strings
# ---------------------------------------------------------------------------

def _geometry_src(geometry):
    return (
        f'geometry = {{\n'
        f'    "L_total": {geometry["L_total"]},   # total beam length (m)\n'
        f'    "x_A"    : {geometry["x_A"]},        # pin support position (m)\n'
        f'    "x_B"    : {geometry["x_B"]},        # roller support position (m)\n'
        f'}}'
    )


def _loads_src(loads):
    if not loads:
        return "loads = []   # no loads defined"
    lines = ["loads = ["]
    for ld in loads:
        if ld["type"] == "point":
            lines.append(
                f'    {{"type": "point", "x": {ld["x"]}, '
                f'"magnitude": {ld["magnitude"]}}},  '
                f'# kN  (negative = downward)'
            )
        elif ld["type"] == "udl":
            lines.append(
                f'    {{"type": "udl", "x1": {ld["x1"]}, '
                f'"x2": {ld["x2"]}, "w": {ld["w"]}}},  '
                f'# kN/m  (negative = downward)'
            )
    lines.append("]")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_notebook(geometry, loads):
    """
    Generate a self-contained .ipynb for the given beam configuration.

    Parameters
    ----------
    geometry : dict  {"L_total": float, "x_A": float, "x_B": float}
    loads    : list of load dicts

    Returns
    -------
    str  — JSON content of a valid Jupyter notebook (nbformat 4)
    """
    cells = []
    n = [0]   # mutable counter

    def md(text):
        n[0] += 1
        cells.append(_md(n[0], text))

    def code(text):
        n[0] += 1
        cells.append(_code(n[0], text))

    geo_src   = _geometry_src(geometry)
    loads_src = _loads_src(loads)
    L   = geometry["L_total"]
    x_A = geometry["x_A"]
    x_B = geometry["x_B"]

    # ── Title ────────────────────────────────────────────────────────────────
    md("""\
# INSTRA Academy
## Simply Supported Beam Analysis — Course Notebook

This notebook is a self-contained companion to the INSTRA Academy interactive course.
It walks through every concept in lesson order, from beam definition to
the full Shear Force and Bending Moment diagrams, and finishes with
the principle of superposition.

**Beam configuration embedded from your course session:**
- Total length  : {L} m
- Pin support A : {x_A} m  from left end
- Roller support B : {x_B} m  from left end
- Loads defined : {n_loads}

Run each cell in order with **Shift + Enter**.
""".format(L=L, x_A=x_A, x_B=x_B, n_loads=len(loads)))

    # ── Dependencies ─────────────────────────────────────────────────────────
    md("## 0 — Dependencies")

    code("""\
import numpy as np
from scipy.integrate import cumulative_trapezoid
import matplotlib.pyplot as plt

# Plots appear inline in the notebook
%matplotlib inline
plt.rcParams.update({"figure.dpi": 120, "font.size": 10})""")

    # ── Section 1: Geometry ───────────────────────────────────────────────────
    md("""\
## 1 — Beam Geometry

Three numbers fully describe the beam:

```
x=0 ─── [left cantilever] ─── x_A ─── [interior span] ─── x_B ─── [right cantilever] ─── x=L
                                PIN                          ROLLER
```

- `x_A = 0`  → no left cantilever (A is at the free end)
- `x_B = L`  → no right cantilever (B is at the free end)""")

    code(geo_src + """

# ── Derived quantities ────────────────────────────────────────────────────
cantilever_left  = geometry["x_A"]
interior_span    = geometry["x_B"] - geometry["x_A"]
cantilever_right = geometry["L_total"] - geometry["x_B"]

print(f"Left cantilever  : {cantilever_left:.2f} m")
print(f"Interior span    : {interior_span:.2f} m")
print(f"Right cantilever : {cantilever_right:.2f} m")
print(f"Total length     : {geometry['L_total']:.2f} m")""")

    # ── Beam drawing helpers ──────────────────────────────────────────────────
    md("### Drawing helpers\nRun this cell once — the functions are reused in later plots.")

    code("""\
def draw_beam(ax, geometry):
    \"\"\"Draw beam axis, pin/roller supports, and shaded cantilever regions.\"\"\"
    L, x_A, x_B = geometry["L_total"], geometry["x_A"], geometry["x_B"]

    ax.plot([0, L], [0, 0], color="black", lw=4, solid_capstyle="round", zorder=3)

    if x_A > 0:
        ax.axvspan(0, x_A, alpha=0.08, color="orange")
    if x_B < L:
        ax.axvspan(x_B, L, alpha=0.08, color="orange")

    # Pin (solid triangle)
    size = 0.18
    ax.add_patch(plt.Polygon(
        [[x_A, 0], [x_A - size, -size*1.4], [x_A + size, -size*1.4]],
        closed=True, facecolor="#888", edgecolor="k", lw=0.8, zorder=4))
    ax.plot([x_A - size*1.3, x_A + size*1.3], [-size*1.4]*2, "k-", lw=1.5, zorder=4)

    # Roller (open triangle + circle)
    ax.add_patch(plt.Polygon(
        [[x_B, 0], [x_B - size, -size*1.4], [x_B + size, -size*1.4]],
        closed=True, facecolor="white", edgecolor="k", lw=0.8, zorder=4))
    ax.add_patch(plt.Circle((x_B, -size*1.95), size*0.5,
                             facecolor="white", edgecolor="k", lw=0.8, zorder=4))
    ax.plot([x_B - size*1.3, x_B + size*1.3], [-size*2.45]*2, "k-", lw=1.5, zorder=4)

    ax.text(x_A, -0.32, f"A ({x_A:.1f} m)", ha="center", va="top", fontsize=8, color="#555")
    ax.text(x_B, -0.32, f"B ({x_B:.1f} m)", ha="center", va="top", fontsize=8, color="#555")
    ax.set_xlim(-0.4, L + 0.4)
    ax.set_ylim(-0.7, 1.5)
    ax.axis("off")


def draw_loads(ax, loads, L_total, arrow_height=0.9):
    \"\"\"Draw point loads (arrows) and UDLs on the beam diagram.\"\"\"
    for load in loads:
        if load["type"] == "point":
            x, mag = load["x"], load["magnitude"]
            color  = "#1565C0" if mag < 0 else "#B71C1C"
            tip_y  = 0.02  if mag < 0 else -0.02
            tail_y = arrow_height if mag < 0 else -arrow_height
            ax.annotate(
                f"{abs(mag):.0f} kN",
                xy=(x, tip_y), xytext=(x, tail_y),
                ha="center", va="bottom" if mag < 0 else "top",
                fontsize=8, color=color, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.8, mutation_scale=14),
            )
        elif load["type"] == "udl":
            x1, x2, w = load["x1"], load["x2"], load["w"]
            color = "#1565C0" if w < 0 else "#B71C1C"
            tip_y  = 0.02  if w < 0 else -0.02
            tail_y = arrow_height * 0.75 if w < 0 else -arrow_height * 0.75
            for xi in np.linspace(x1, x2, max(3, int((x2-x1)/0.5))):
                ax.annotate("", xy=(xi, tip_y), xytext=(xi, tail_y),
                            arrowprops=dict(arrowstyle="-|>", color=color, lw=1.2, mutation_scale=10))
            ax.plot([x1, x2], [tail_y]*2, color=color, lw=2)
            ax.text((x1+x2)/2, tail_y + (0.12 if w < 0 else -0.18),
                    f"{abs(w):.1f} kN/m", ha="center", va="bottom", fontsize=8,
                    color=color, fontweight="bold")


def draw_reactions(ax, x_A, x_B, R_A, R_B, scale=None):
    \"\"\"Draw upward/downward reaction arrows proportional to their magnitude.\"\"\"
    max_R = max(abs(R_A), abs(R_B), 1e-3)
    if scale is None:
        scale = 0.8 / max_R
    for x_pos, R, label in [(x_A, R_A, f"R_A = {R_A:+.1f} kN"),
                              (x_B, R_B, f"R_B = {R_B:+.1f} kN")]:
        color  = "#2E7D32" if R >= 0 else "#C62828"
        tip_y  = -0.02 if R >= 0 else 0.02
        tail_y = -R * scale
        ax.annotate("", xy=(x_pos, tip_y), xytext=(x_pos, tail_y),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=2.2, mutation_scale=16))
        va      = "top" if R >= 0 else "bottom"
        label_y = tail_y + (-0.08 if R >= 0 else 0.08)
        ax.text(x_pos, label_y, label, ha="center", va=va,
                fontsize=8, color=color, fontweight="bold")


print("Drawing helpers defined.")""")

    # ── Draw geometry ─────────────────────────────────────────────────────────
    code("""\
fig, ax = plt.subplots(figsize=(12, 3))
draw_beam(ax, geometry)
ax.set_title(
    f"L = {geometry['L_total']:.1f} m  |  "
    f"Left cantilever = {cantilever_left:.1f} m  |  "
    f"Span = {interior_span:.1f} m  |  "
    f"Right cantilever = {cantilever_right:.1f} m",
    fontsize=10
)
plt.tight_layout()
plt.show()""")

    # ── Section 2: Loads ──────────────────────────────────────────────────────
    md("""\
## 2 — Loads

Loads are stored as a **list of dictionaries**.
Each dictionary has a `type` key (`"point"` or `"udl"`) plus the relevant parameters.

**Sign convention:**
- Downward forces (loads)  → **negative**
- Upward forces (reactions) → **positive**""")

    code(loads_src + """

# ── Summary ───────────────────────────────────────────────────────────────
print(f"Loads defined: {len(loads)}")
for i, ld in enumerate(loads):
    if ld["type"] == "point":
        print(f"  Load {i+1}: Point load  {ld['magnitude']:+.1f} kN  at x = {ld['x']:.2f} m")
    elif ld["type"] == "udl":
        P_eq = ld["w"] * (ld["x2"] - ld["x1"])
        xc   = (ld["x1"] + ld["x2"]) / 2
        print(f"  Load {i+1}: UDL  {ld['w']:+.1f} kN/m  from {ld['x1']:.1f} to {ld['x2']:.1f} m")
        print(f"           Equivalent: {P_eq:+.1f} kN at x = {xc:.2f} m")

total_load = sum(
    ld["magnitude"] if ld["type"] == "point"
    else ld["w"] * (ld["x2"] - ld["x1"])
    for ld in loads
)
print(f"Total vertical load: {total_load:+.1f} kN")""")

    code("""\
fig, ax = plt.subplots(figsize=(12, 3))
draw_beam(ax, geometry)
draw_loads(ax, loads, geometry["L_total"])
ax.set_title("Beam with applied loads", fontsize=10)
plt.tight_layout()
plt.show()""")

    # ── Section 3: Reactions ──────────────────────────────────────────────────
    md("""\
## 3 — Support Reactions

Two equilibrium equations give us the two unknown reactions R_A and R_B.

**Sum of moments about A = 0:**
$$R_B = -\\frac{\\sum P_i \\cdot (x_i - x_A)}{x_B - x_A}$$

**Sum of vertical forces = 0:**
$$R_A = -\\sum P_i - R_B$$

For a UDL the equivalent point load is $P = w(x_2 - x_1)$ acting at the centroid
$x_c = (x_1 + x_2) / 2$.

**Self-check:** $R_A + R_B + \\sum P_i = 0$""")

    code("""\
def compute_reactions(geometry, loads):
    \"\"\"
    Compute support reactions using static equilibrium.
    Returns R_A, R_B  (positive = upward, kN).
    \"\"\"
    x_A  = geometry["x_A"]
    x_B  = geometry["x_B"]
    span = x_B - x_A

    total_force = 0.0
    total_moment_about_A = 0.0

    for load in loads:
        if load["type"] == "point":
            P  = load["magnitude"]
            x  = load["x"]
            total_force          += P
            total_moment_about_A += P * (x - x_A)

        elif load["type"] == "udl":
            w, x1, x2 = load["w"], load["x1"], load["x2"]
            P_eq = w * (x2 - x1)                 # resultant
            xc   = (x1 + x2) / 2                 # centroid
            total_force          += P_eq
            total_moment_about_A += P_eq * (xc - x_A)

    # Solve the two equilibrium equations
    R_B = -total_moment_about_A / span            # ΣM_A = 0
    R_A = -total_force - R_B                      # ΣFy = 0
    return R_A, R_B


R_A, R_B = compute_reactions(geometry, loads)

print(f"Reaction at A  : R_A = {R_A:+.3f} kN  ({'upward' if R_A >= 0 else 'downward'})")
print(f"Reaction at B  : R_B = {R_B:+.3f} kN  ({'upward' if R_B >= 0 else 'downward'})")

# Self-check: sum of all vertical forces must be zero
residual = R_A + R_B + total_load
print(f"Equilibrium check ΣFy = {residual:.2e} kN  (should be ≈ 0)")""")

    code("""\
fig, ax = plt.subplots(figsize=(12, 3.5))
draw_beam(ax, geometry)
draw_loads(ax, loads, geometry["L_total"])
draw_reactions(ax, geometry["x_A"], geometry["x_B"], R_A, R_B)
ax.set_title(f"Reactions: R_A = {R_A:+.2f} kN  |  R_B = {R_B:+.2f} kN", fontsize=10)
plt.tight_layout()
plt.show()""")

    # ── Section 4: SFD ────────────────────────────────────────────────────────
    md("""\
## 4 — Shear Force Diagram

The shear force $V(x)$ at any section is the **algebraic sum of all vertical forces
to the left** of that section.

$$V(x) = \\sum_{\\text{forces left of } x} F_i$$

Rules:
- V = 0 at both free ends
- V jumps by the load magnitude at every point load
- V has a linear slope under a UDL (slope = w)
- V jumps upward at each reaction""")

    code("""\
def compute_shear(geometry, loads, R_A, R_B, n_points=500):
    \"\"\"
    Build the shear force array V(x) using the section-cut method.
    Returns x_array (m) and V (kN), both shape (n_points,).
    \"\"\"
    L   = geometry["L_total"]
    x_A = geometry["x_A"]
    x_B = geometry["x_B"]

    x_array = np.linspace(0, L, n_points)
    V       = np.zeros(n_points)

    for i, xi in enumerate(x_array):
        v = 0.0

        # Reactions (upward = positive)
        if xi >= x_A: v += R_A
        if xi >= x_B: v += R_B

        # Applied loads to the left of the cut
        for load in loads:
            if load["type"] == "point":
                if load["x"] <= xi:
                    v += load["magnitude"]
            elif load["type"] == "udl":
                x1, x2 = load["x1"], load["x2"]
                overlap_length = max(0, min(xi, x2) - x1)
                v += load["w"] * overlap_length

        V[i] = v

    return x_array, V


x, V = compute_shear(geometry, loads, R_A, R_B)

print(f"V at left tip  (x=0)   : {V[0]:+.4f} kN  (should be 0 — free end)")
print(f"V at right tip (x={geometry['L_total']:.1f}) : {V[-1]:+.4f} kN  (should be ≈ 0)")
print(f"V_max = {V.max():+.2f} kN  at x = {x[V.argmax()]:.2f} m")
print(f"V_min = {V.min():+.2f} kN  at x = {x[V.argmin()]:.2f} m")""")

    code("""\
fig, (ax_b, ax_s) = plt.subplots(2, 1, figsize=(12, 7),
                                  gridspec_kw={"height_ratios": [1, 2.2]})
fig.subplots_adjust(hspace=0.06)

draw_beam(ax_b, geometry)
draw_loads(ax_b, loads, geometry["L_total"])
draw_reactions(ax_b, geometry["x_A"], geometry["x_B"], R_A, R_B)
ax_b.tick_params(labelbottom=False)

ax_s.plot(x, V, "#1565C0", lw=2, label="V(x)")
ax_s.fill_between(x, V, 0, where=(V >= 0), color="#90CAF9", alpha=0.5, label="Positive shear")
ax_s.fill_between(x, V, 0, where=(V < 0),  color="#EF9A9A", alpha=0.5, label="Negative shear")
ax_s.axhline(0, color="k", lw=0.8)

# Mark V = 0 crossings (locations of maximum moment)
for idx in np.where(np.diff(np.sign(V)))[0]:
    ax_s.axvline(x[idx], color="red", ls="--", lw=1, alpha=0.7)
    ax_s.text(x[idx] + 0.1, V.min() * 0.8,
              f"V=0\\n({x[idx]:.2f}m)", fontsize=7.5, color="red")

ax_s.set_ylabel("Shear Force V (kN)", fontsize=9)
ax_s.set_xlabel("Position x (m)", fontsize=10)
ax_s.legend(fontsize=8, loc="upper right")
ax_s.grid(True, ls="--", alpha=0.4)
ax_s.set_xlim(ax_b.get_xlim())

fig.suptitle(
    f"Shear Force Diagram  |  R_A={R_A:+.1f} kN  |  R_B={R_B:+.1f} kN",
    fontsize=10
)
plt.tight_layout()
plt.show()""")

    # ── Section 5: BMD ────────────────────────────────────────────────────────
    md("""\
## 5 — Bending Moment Diagram

The bending moment is the **integral of the shear force** from the left end:

$$M(x) = \\int_0^x V(\\xi)\\, d\\xi$$

Implemented numerically using the trapezoidal rule.

Sign convention (sagging positive):
- **Sagging** (concave up, tension on bottom fibre) = **positive** — green fill
- **Hogging** (concave down, tension on top fibre) = **negative** — red fill

Key rule: **M is maximum (or minimum) where V = 0.**""")

    code("""\
def compute_moments(x_array, V):
    \"\"\"
    Integrate V(x) to obtain M(x) using the trapezoidal rule.
    M(0) = 0  (free left end).
    M[-1] should be ≈ 0 for a correctly balanced beam.
    \"\"\"
    M = cumulative_trapezoid(V, x_array, initial=0.0)
    return M


M = compute_moments(x, V)

print(f"M at left tip  (x=0)   : {M[0]:+.4f} kN·m  (should be 0 — free end)")
print(f"M at right tip (x={geometry['L_total']:.1f}) : {M[-1]:+.4f} kN·m  (should be ≈ 0)")
print(f"M_max (sagging) = {M.max():+.2f} kN·m  at x = {x[M.argmax()]:.2f} m")
print(f"M_min (hogging) = {M.min():+.2f} kN·m  at x = {x[M.argmin()]:.2f} m")""")

    code("""\
fig, (ax_b, ax_m) = plt.subplots(2, 1, figsize=(12, 7),
                                  gridspec_kw={"height_ratios": [1, 2.8]})
fig.subplots_adjust(hspace=0.06)

draw_beam(ax_b, geometry)
draw_loads(ax_b, loads, geometry["L_total"])
draw_reactions(ax_b, geometry["x_A"], geometry["x_B"], R_A, R_B)
ax_b.tick_params(labelbottom=False)

ax_m.plot(x, M, "#1B5E20", lw=2, label="M(x)")
ax_m.fill_between(x, M, 0, where=(M >= 0), color="#A5D6A7", alpha=0.5, label="Sagging (+)")
ax_m.fill_between(x, M, 0, where=(M < 0),  color="#FFCDD2", alpha=0.5, label="Hogging (−)")
ax_m.axhline(0, color="k", lw=0.8)

# Annotate peak values
for idx, clr in [(M.argmax(), "#1B5E20"), (M.argmin(), "#C62828")]:
    if abs(M[idx]) > 0.5:
        ax_m.plot(x[idx], M[idx], "o", color=clr, ms=7, zorder=5)
        ax_m.annotate(f"{M[idx]:+.1f} kN·m",
                      xy=(x[idx], M[idx]), xytext=(x[idx] + 0.25, M[idx]),
                      fontsize=8, color=clr,
                      arrowprops=dict(arrowstyle="->", color=clr, lw=0.8))

ax_m.set_ylabel("Bending Moment M (kN·m)", fontsize=9)
ax_m.set_xlabel("Position x (m)", fontsize=10)
ax_m.legend(fontsize=8, loc="upper right")
ax_m.grid(True, ls="--", alpha=0.4)
ax_m.set_xlim(ax_b.get_xlim())

fig.suptitle(
    f"Bending Moment Diagram  |  M_max={M.max():+.1f} kN·m  |  M_min={M.min():+.1f} kN·m",
    fontsize=10
)
plt.tight_layout()
plt.show()""")

    # ── Section 6: Full analysis ───────────────────────────────────────────────
    md("""\
## 6 — Complete Analysis

All three panels together: beam diagram, SFD, and BMD sharing the same x-axis.
This is the standard presentation in structural engineering reports.""")

    code("""\
fig = plt.figure(figsize=(12, 10))
gs  = fig.add_gridspec(3, 1, height_ratios=[1, 1.8, 1.8], hspace=0.06)
ax_b = fig.add_subplot(gs[0])
ax_s = fig.add_subplot(gs[1])
ax_m = fig.add_subplot(gs[2])

# ── Beam ──────────────────────────────────────────────────────────────────
draw_beam(ax_b, geometry)
draw_loads(ax_b, loads, geometry["L_total"])
draw_reactions(ax_b, geometry["x_A"], geometry["x_B"], R_A, R_B)
ax_b.tick_params(labelbottom=False)

# ── SFD ───────────────────────────────────────────────────────────────────
ax_s.plot(x, V, "#1565C0", lw=2)
ax_s.fill_between(x, V, 0, where=(V >= 0), color="#90CAF9", alpha=0.5)
ax_s.fill_between(x, V, 0, where=(V < 0),  color="#EF9A9A", alpha=0.5)
ax_s.axhline(0, color="k", lw=0.8)
ax_s.set_ylabel("V (kN)", fontsize=9)
ax_s.grid(True, ls="--", alpha=0.4)
ax_s.tick_params(labelbottom=False)

# ── BMD ───────────────────────────────────────────────────────────────────
ax_m.plot(x, M, "#1B5E20", lw=2)
ax_m.fill_between(x, M, 0, where=(M >= 0), color="#A5D6A7", alpha=0.5, label="Sagging (+)")
ax_m.fill_between(x, M, 0, where=(M < 0),  color="#FFCDD2", alpha=0.5, label="Hogging (−)")
ax_m.axhline(0, color="k", lw=0.8)
ax_m.set_ylabel("M (kN·m)", fontsize=9)
ax_m.set_xlabel("Position x (m)", fontsize=10)
ax_m.legend(fontsize=8)
ax_m.grid(True, ls="--", alpha=0.4)

# ── Shared x limits ────────────────────────────────────────────────────────
xlim = (x[0] - 0.3, x[-1] + 0.3)
for ax_ in [ax_b, ax_s, ax_m]:
    ax_.set_xlim(*xlim)

fig.suptitle(
    f"Complete Analysis   |   R_A={R_A:+.1f} kN   R_B={R_B:+.1f} kN   "
    f"M_max={M.max():+.1f} kN·m   M_min={M.min():+.1f} kN·m",
    fontsize=10, y=1.01
)
plt.tight_layout()
plt.show()""")

    # ── Section 7: Superposition ──────────────────────────────────────────────
    md("""\
## 7 — Superposition

For a linearly elastic beam, the total response to $n$ loads equals the
**sum of the individual responses** to each load applied separately:

$$R_A = \\sum_i R_{A,i} \\qquad V(x) = \\sum_i V_i(x) \\qquad M(x) = \\sum_i M_i(x)$$

This is valid when:
- Deformations are small (geometry does not change under load)
- Material is linearly elastic (stress ∝ strain)
- Supports are fixed (no settlement)""")

    code("""\
def reactions_for_load(geometry, load):
    \"\"\"Compute (R_A, R_B) due to a single load using moment equilibrium.\"\"\"
    x_A  = geometry["x_A"]
    x_B  = geometry["x_B"]
    span = x_B - x_A

    if load["type"] == "point":
        P  = load["magnitude"]
        moment_about_A = P * (load["x"] - x_A)
    elif load["type"] == "udl":
        w, x1, x2 = load["w"], load["x1"], load["x2"]
        P  = w * (x2 - x1)
        moment_about_A = P * ((x1 + x2) / 2 - x_A)
    else:
        return 0.0, 0.0

    R_B = -moment_about_A / span
    R_A = -P - R_B
    return R_A, R_B


def shear_for_load(geometry, load, R_A_load, R_B_load, x_array):
    \"\"\"V(x) contribution from one load using the section-cut method (vectorised).\"\"\"
    x_A, x_B = geometry["x_A"], geometry["x_B"]
    V = np.zeros(len(x_array))
    V += R_A_load * (x_array >= x_A)
    V += R_B_load * (x_array >= x_B)
    if load["type"] == "point":
        V += load["magnitude"] * (x_array >= load["x"])
    elif load["type"] == "udl":
        x1, x2 = load["x1"], load["x2"]
        V += load["w"] * np.maximum(np.minimum(x_array, x2) - x1, 0)
    return V


def moment_for_load(geometry, load, R_A_load, R_B_load, x_array):
    \"\"\"M(x) contribution from one load using the section-cut method (vectorised).\"\"\"
    x_A, x_B = geometry["x_A"], geometry["x_B"]
    M = np.zeros(len(x_array))
    M += R_A_load * np.maximum(x_array - x_A, 0)
    M += R_B_load * np.maximum(x_array - x_B, 0)
    if load["type"] == "point":
        M += load["magnitude"] * np.maximum(x_array - load["x"], 0)
    elif load["type"] == "udl":
        x1, x2 = load["x1"], load["x2"]
        xc     = np.minimum(x_array, x2)
        length = np.maximum(xc - x1, 0)
        M += load["w"] * length * (x_array - (x1 + xc) / 2)
    return M


# ── Run per-load analysis ─────────────────────────────────────────────────
n_pts = 500
x_sp  = np.linspace(0, geometry["L_total"], n_pts)

R_A_total = R_B_total = 0.0
V_total   = np.zeros(n_pts)
M_total   = np.zeros(n_pts)

contributions = []
print(f"{'Load':<50} {'R_A':>8} {'R_B':>8}")
print("-" * 70)
for i, load in enumerate(loads):
    R_Ai, R_Bi = reactions_for_load(geometry, load)
    Vi = shear_for_load(geometry, load, R_Ai, R_Bi, x_sp)
    Mi = moment_for_load(geometry, load, R_Ai, R_Bi, x_sp)
    contributions.append((load, R_Ai, R_Bi, Vi, Mi))
    R_A_total += R_Ai; R_B_total += R_Bi
    V_total   += Vi;   M_total   += Mi
    label = (f"Point {load['magnitude']:+.0f} kN @ x={load['x']:.1f} m"
             if load["type"] == "point"
             else f"UDL {load['w']:+.1f} kN/m ({load['x1']:.1f}–{load['x2']:.1f} m)")
    print(f"  {label:<48} {R_Ai:+8.3f} {R_Bi:+8.3f}")

print("-" * 70)
print(f"  {'TOTAL (superposition)':<48} {R_A_total:+8.3f} {R_B_total:+8.3f}")
print(f"  {'Direct calculation':<48} {R_A:+8.3f} {R_B:+8.3f}")""")

    code("""\
# ── Contribution plots ────────────────────────────────────────────────────
COLOURS = ["#1565C0", "#E65100", "#6A1B9A", "#00695C", "#AD1457", "#4E342E"]

fig, axes = plt.subplots(2, 2, figsize=(14, 9),
                         gridspec_kw={"hspace": 0.45, "wspace": 0.35})
(ax_v_each, ax_v_sum), (ax_m_each, ax_m_sum) = axes

for i, (ld, R_Ai, R_Bi, Vi, Mi) in enumerate(contributions):
    c = COLOURS[i % len(COLOURS)]
    label = (f"Point {ld['magnitude']:+.0f} kN @ {ld['x']:.1f} m"
             if ld["type"] == "point"
             else f"UDL {ld['w']:+.0f} kN/m ({ld['x1']:.0f}–{ld['x2']:.0f} m)")
    ax_v_each.plot(x_sp, Vi, color=c, lw=1.6, label=label)
    ax_m_each.plot(x_sp, Mi, color=c, lw=1.6, label=label)

for ax, ylabel, title in [
    (ax_v_each, "V (kN)",   "SFD — individual contributions"),
    (ax_m_each, "M (kN·m)", "BMD — individual contributions"),
]:
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel(ylabel, fontsize=9); ax.set_xlabel("x (m)", fontsize=9)
    ax.set_title(title, fontsize=9, fontweight="bold")
    ax.legend(fontsize=7); ax.grid(True, ls="--", alpha=0.35)

# Superposed totals
ax_v_sum.plot(x_sp, V_total, "#1565C0", lw=2)
ax_v_sum.fill_between(x_sp, V_total, 0, where=(V_total >= 0), color="#90CAF9", alpha=0.55)
ax_v_sum.fill_between(x_sp, V_total, 0, where=(V_total < 0),  color="#EF9A9A", alpha=0.55)
ax_v_sum.axhline(0, color="k", lw=0.8)
ax_v_sum.set_ylabel("V (kN)", fontsize=9); ax_v_sum.set_xlabel("x (m)", fontsize=9)
ax_v_sum.set_title("SFD — superposed total", fontsize=9, fontweight="bold")
ax_v_sum.grid(True, ls="--", alpha=0.35)

ax_m_sum.plot(x_sp, M_total, "#1B5E20", lw=2)
ax_m_sum.fill_between(x_sp, M_total, 0, where=(M_total >= 0), color="#A5D6A7", alpha=0.55, label="Sagging (+)")
ax_m_sum.fill_between(x_sp, M_total, 0, where=(M_total < 0),  color="#FFCDD2", alpha=0.55, label="Hogging (−)")
ax_m_sum.axhline(0, color="k", lw=0.8)
ax_m_sum.set_ylabel("M (kN·m)", fontsize=9); ax_m_sum.set_xlabel("x (m)", fontsize=9)
ax_m_sum.set_title("BMD — superposed total", fontsize=9, fontweight="bold")
ax_m_sum.legend(fontsize=8); ax_m_sum.grid(True, ls="--", alpha=0.35)

fig.suptitle(
    f"Superposition   |   R_A={R_A_total:+.1f} kN   R_B={R_B_total:+.1f} kN",
    fontsize=10, fontweight="bold", y=1.01
)
plt.tight_layout()
plt.show()""")

    # ── Notebook metadata ─────────────────────────────────────────────────────
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "version": "3.11.0",
            },
        },
        "cells": cells,
    }
    return json.dumps(notebook, indent=2, ensure_ascii=False)
