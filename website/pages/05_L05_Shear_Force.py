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
from styles import apply_styles, lesson_progress, in_practice, key_takeaways
import beam_solver

st.set_page_config(page_title="L05 — Shear Force Diagram", page_icon="📊", layout="wide")
apply_styles()

if "geometry" not in st.session_state:
    st.session_state.geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
if "loads" not in st.session_state:
    st.session_state.loads = []

st.title("Lesson 5 — Shear Force Diagram")
lesson_progress(5, 7, "Prerequisites: L01–L04  ·  ~60 minutes")
st.markdown("""
The shear force at any section is the sum of all vertical forces to the **left** of that section.
Build the diagram by repeating this calculation at 500 points along the beam.
""")

# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📊 Theory — Interactive SFD")
# ══════════════════════════════════════════════════════════════════════════════

geo   = st.session_state.geometry
loads = st.session_state.loads

if not loads:
    st.info("No loads defined yet — set up your beam in **Lesson 2** and add loads in **Lesson 3**.")
else:
    R_A, R_B = beam_solver.compute_reactions(geo, loads)
    x, V     = beam_solver.compute_shear(geo, loads, R_A, R_B)

    show_zeros = st.checkbox("Mark V = 0 crossings", value=True)

    fig, (ax_b, ax_s) = plt.subplots(2, 1, figsize=(10, 6),
                                      gridspec_kw={"height_ratios": [1, 2.2]})
    fig.subplots_adjust(hspace=0.07)
    draw_beam(ax_b, geo)
    draw_loads(ax_b, loads, geo["L_total"])
    draw_reactions(ax_b, geo["x_A"], geo["x_B"], R_A, R_B)

    ax_s.plot(x, V, "#1565C0", lw=2.2)
    ax_s.fill_between(x, V, 0, where=(V >= 0), color="#90CAF9", alpha=0.5)
    ax_s.fill_between(x, V, 0, where=(V < 0),  color="#EF9A9A", alpha=0.5)
    ax_s.axhline(0, color="k", lw=0.8)

    if show_zeros:
        for idx in np.where(np.diff(np.sign(V)))[0]:
            ax_s.axvline(x[idx], color="red", ls="--", lw=1, alpha=0.7)
            ax_s.text(x[idx] + 0.1, V.min() * 0.85,
                      f"V=0\n({x[idx]:.1f}m)", fontsize=7.5, color="red")

    ax_s.set_ylabel("Shear V (kN)", fontsize=9)
    ax_s.set_xlabel("Position x (m)", fontsize=10)
    ax_s.grid(True, ls="--", alpha=0.4)
    ax_s.set_xlim(ax_b.get_xlim())
    ax_s.set_title("Shear Force Diagram", fontsize=9, pad=5)
    st.pyplot(fig, width='stretch')
    plt.close(fig)

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("R_A", f"{R_A:+.2f} kN")
    mc2.metric("R_B", f"{R_B:+.2f} kN")
    mc3.metric("V_max", f"{V.max():+.1f} kN")
    mc4.metric("V_min", f"{V.min():+.1f} kN")

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

in_practice(
    "Shear force governs the design of beam webs and connectors. In a steel beam, "
    "the web thickness is sized from V_max using the shear capacity formula. "
    "In a concrete beam, stirrups are spaced based on the shear envelope — exactly "
    "the diagram you have just plotted."
)

key_takeaways([
    "V = 0 at both free ends — guaranteed by equilibrium, not an assumption",
    "V **jumps** by the load magnitude at every point load, and by R_A or R_B at each support",
    "V has a **linear slope** under a UDL (slope = w, in kN/m)",
    "Where V = 0, the bending moment is at a local maximum — this is the critical section for design",
])

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

