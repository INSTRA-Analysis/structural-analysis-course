"""Lesson 5 — Shear Force Diagram"""

import streamlit as st
import sys, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(BASE, "components"))
sys.path.insert(0, os.path.join(BASE, "..", "course", "shared"))

from code_runner import practice_block, lesson_nav
from plot_helpers import draw_beam, draw_loads, draw_reactions, draw_sfd
import beam_solver

st.set_page_config(page_title="L05 — Shear Force Diagram", page_icon="📊", layout="wide")

st.title("Lesson 5 — Shear Force Diagram")
st.caption("Prerequisites: Lessons 1–4  ·  Time: ~60 minutes")
st.markdown("""
The shear force at any section is the sum of all vertical forces to the **left** of that section.
Build the diagram by repeating this calculation at 500 points along the beam.
""")

# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📊 Theory — Interactive SFD")
# ══════════════════════════════════════════════════════════════════════════════

col_ctrl, col_plot = st.columns([1, 2])

with col_ctrl:
    st.markdown("**Beam geometry:**")
    L   = st.slider("L (m)", 5.0, 15.0, 10.0, 0.5, key="sfd_L")
    x_A = st.slider("Pin A (m)", 0.0, L * 0.45, 2.0, 0.5, key="sfd_xA")
    x_B = st.slider("Roller B (m)", x_A + 0.5, L, min(8.0, L), 0.5, key="sfd_xB")

    st.markdown("**Loads:**")
    P1  = st.slider("Point load at midspan (kN)", -80.0, 0.0, -20.0, 5.0)
    w1  = st.slider("Full-span UDL (kN/m)", -15.0, 0.0, 0.0, 1.0)
    P_tip = st.slider("Load at left cantilever tip (kN)", -40.0, 0.0, 0.0, 5.0)
    show_zeros = st.checkbox("Show V = 0 locations", value=True)

    geo   = {"L_total": L, "x_A": x_A, "x_B": x_B}
    loads = []
    mid   = (x_A + x_B) / 2
    if P1 != 0:
        loads.append({"type": "point", "x": mid, "magnitude": P1})
    if w1 != 0:
        loads.append({"type": "udl", "x1": 0.0, "x2": L, "w": w1})
    if P_tip != 0:
        loads.append({"type": "point", "x": 0.0, "magnitude": P_tip})

with col_plot:
    if not loads:
        st.info("Add a load using the sliders on the left to see the SFD.")
    else:
        R_A, R_B = beam_solver.compute_reactions(geo, loads)
        x, V     = beam_solver.compute_shear(geo, loads, R_A, R_B)

        fig, (ax_b, ax_s) = plt.subplots(2, 1, figsize=(9, 7),
                                          gridspec_kw={"height_ratios": [1, 2.2]})
        fig.subplots_adjust(hspace=0.06)

        draw_beam(ax_b, geo)
        draw_loads(ax_b, loads, L)
        draw_reactions(ax_b, x_A, x_B, R_A, R_B)

        ax_s.plot(x, V, "#1565C0", lw=2.2)
        ax_s.fill_between(x, V, 0, where=(V>=0), color="#90CAF9", alpha=0.5)
        ax_s.fill_between(x, V, 0, where=(V<0),  color="#EF9A9A", alpha=0.5)
        ax_s.axhline(0, color="k", lw=0.8)

        if show_zeros:
            zc = np.where(np.diff(np.sign(V)))[0]
            for idx in zc:
                ax_s.axvline(x[idx], color="red", ls="--", lw=1, alpha=0.7)
                ax_s.text(x[idx] + 0.1, V.min() * 0.85,
                          f"V=0\n({x[idx]:.1f}m)", fontsize=7.5, color="red")

        ax_s.set_ylabel("Shear V (kN)", fontsize=9)
        ax_s.set_xlabel("Position x (m)", fontsize=10)
        ax_s.grid(True, ls="--", alpha=0.4)
        ax_s.set_xlim(ax_b.get_xlim())
        ax_s.set_title(
            f"SFD  |  R_A={R_A:+.1f} kN  |  R_B={R_B:+.1f} kN  |  "
            f"V_max={V.max():+.1f}  V_min={V.min():+.1f} kN",
            fontsize=9, pad=5
        )
        st.pyplot(fig, width='stretch')
        plt.close(fig)

st.markdown("---")
st.markdown("""
**SFD rules to remember:**
- V = 0 at both **free ends** (left tip and right tip)
- V **jumps** at every point load (by the load magnitude)
- V **slopes** linearly under a UDL (slope = w)
- V **jumps up** at each reaction (by R_A or R_B)
- Where V = 0, the bending moment is at a **local maximum** — this is where we look for M_max
""")

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICE
# ══════════════════════════════════════════════════════════════════════════════

# Pre-define the reaction solver for the practice section
def _compute_reactions(geometry, loads):
    x_A, x_B = geometry["x_A"], geometry["x_B"]
    span = x_B - x_A
    total_F = total_M = 0.0
    for ld in loads:
        if ld["type"] == "point":
            P = ld["magnitude"]; total_F += P; total_M += P * (ld["x"] - x_A)
        elif ld["type"] == "udl":
            P = ld["w"] * (ld["x2"] - ld["x1"]); xc = (ld["x1"] + ld["x2"]) / 2
            total_F += P; total_M += P * (xc - x_A)
    R_B = -total_M / span; R_A = -total_F - R_B
    return R_A, R_B

starter = """\
import numpy as np

# Beam and loads (given — do not change)
geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
loads    = [{"type": "point", "x": 5.0, "magnitude": -30.0}]

# Reactions (given — do not change)
R_A, R_B = compute_reactions(geometry, loads)
print(f"R_A = {R_A:+.2f} kN,  R_B = {R_B:+.2f} kN")

# ── Build the shear force array ───────────────────────────────────────────
x_A  = geometry["x_A"]
x_B  = geometry["x_B"]
L    = geometry["L_total"]

n       = 500
x_array = np.linspace(___, L, n)       # 500 points from 0 to L
V       = np.zeros(___)                # start with all zeros

for i, xi in enumerate(x_array):
    v = 0.0

    # Add reactions (upward = positive)
    if xi >= x_A:
        v += ___        # add R_A
    if xi >= x_B:
        v += ___        # add R_B

    # Add loads to the left of xi
    for load in loads:
        if load["type"] == "point" and load["x"] <= xi:
            v += load["___"]    # add the load magnitude

    V[i] = v

# Print some key values
print(f"V at x=0    : {V[0]:+.2f} kN  (free end — should be 0)")
print(f"V at x=10 m : {V[-1]:+.2f} kN  (free end — should be ≈ 0)")
print(f"V_max       : {V.max():+.2f} kN  at x = {x_array[V.argmax()]:.2f} m")
print(f"V_min       : {V.min():+.2f} kN  at x = {x_array[V.argmin()]:.2f} m")

# ── Plot ──────────────────────────────────────────────────────────────────
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(x_array, V, "#1565C0", lw=2, label="V(x)")
ax.fill_between(x_array, V, 0, where=(V>=0), color="#90CAF9", alpha=0.5)
ax.fill_between(x_array, V, 0, where=(V<0),  color="#EF9A9A", alpha=0.5)
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel("Position x (m)")
ax.set_ylabel("Shear Force V (kN)")
ax.set_title("Shear Force Diagram — −30 kN at midspan")
ax.grid(True, ls="--", alpha=0.4)
plt.tight_layout()
plt.show()
"""

solution = """\
import numpy as np
import matplotlib.pyplot as plt

geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
loads    = [{"type": "point", "x": 5.0, "magnitude": -30.0}]

R_A, R_B = compute_reactions(geometry, loads)
print(f"R_A = {R_A:+.2f} kN,  R_B = {R_B:+.2f} kN")

x_A  = geometry["x_A"]
x_B  = geometry["x_B"]
L    = geometry["L_total"]
n    = 500

x_array = np.linspace(0, L, n)
V       = np.zeros(n)

for i, xi in enumerate(x_array):
    v = 0.0
    if xi >= x_A: v += R_A
    if xi >= x_B: v += R_B
    for load in loads:
        if load["type"] == "point" and load["x"] <= xi:
            v += load["magnitude"]
    V[i] = v

print(f"V at x=0    : {V[0]:+.2f} kN  (free end — should be 0)")
print(f"V at x=10 m : {V[-1]:+.2f} kN  (free end — should be ≈ 0)")
print(f"V_max       : {V.max():+.2f} kN  at x = {x_array[V.argmax()]:.2f} m")
print(f"V_min       : {V.min():+.2f} kN  at x = {x_array[V.argmin()]:.2f} m")

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(x_array, V, "#1565C0", lw=2)
ax.fill_between(x_array, V, 0, where=(V>=0), color="#90CAF9", alpha=0.5)
ax.fill_between(x_array, V, 0, where=(V<0),  color="#EF9A9A", alpha=0.5)
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel("Position x (m)")
ax.set_ylabel("Shear Force V (kN)")
ax.set_title("Shear Force Diagram — −30 kN at midspan")
ax.grid(True, ls="--", alpha=0.4)
plt.tight_layout()
plt.show()
"""

practice_block(
    key="L05",
    instructions="""
Build the shear force array step by step for a single **−30 kN load at midspan**.
The reactions are already computed for you via `compute_reactions()`.
Fill in the blanks `___` and run to see your SFD.
""",
    starter_code=starter,
    solution_code=solution,
    expected_note="`V_max ≈ +15 kN  ·  V_min ≈ −15 kN  ·  V crosses 0 at x = 5 m`",
    pre_defined={"compute_reactions": _compute_reactions},
)

lesson_nav(
    prev_label="L04 — Reactions",
    prev_page="pages/04_L04_Reactions.py",
    next_label="L06 — Bending Moment Diagram",
    next_page="pages/06_L06_Bending_Moment.py",
)

