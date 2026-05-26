"""Lesson 4 — Finding Support Reactions"""

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
from plot_helpers import draw_beam, draw_loads, draw_reactions
import beam_solver

st.set_page_config(page_title="L04 — Reactions", page_icon="⚖️", layout="wide")

st.title("Lesson 4 — Finding Support Reactions")
st.caption("Prerequisites: Lessons 1–3  ·  Time: ~60 minutes")
st.markdown("""
With the beam geometry and loads defined, we solve for the support reactions using
two equilibrium equations. Python makes this calculation instant and repeatable.
""")

# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## ⚖️ Theory — Static Equilibrium")
# ══════════════════════════════════════════════════════════════════════════════

col_l, col_r = st.columns([1, 1])
with col_l:
    st.markdown(r"""
**Two equations for two unknowns** (R_A and R_B):

**Sum of moments about A = 0:**
$$R_B = -\frac{\sum P_i \cdot (x_i - x_A)}{x_B - x_A}$$

**Sum of vertical forces = 0:**
$$R_A = -\sum P_i - R_B$$

For a **UDL**, replace it with an equivalent point load:
$$P_{equiv} = w \cdot (x_2 - x_1) \qquad x_c = \frac{x_1+x_2}{2}$$

**Self-check** — always verify:
$$R_A + R_B + \sum P_i = 0$$
""")

with col_r:
    st.markdown("""
**Key insight — cantilever loads:**

- Load at midspan → reactions are roughly equal
- Load on **left cantilever** → R_A increases, R_B can go **negative** (pulls roller down)
- Load directly over support A → all force goes to A, R_B = 0

Adjust the load below and watch the reactions change:
""")

st.markdown("---")
st.markdown("### Interactive Reaction Calculator")

geo_fixed = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}

col_ctrl, col_plot = st.columns([1, 2])

with col_ctrl:
    load_x   = st.slider("Load position x (m)", 0.0, 10.0, 5.0, 0.5)
    load_mag = st.slider("Load magnitude (kN)  negative = down", -100.0, 100.0, -30.0, 5.0)
    show_udl = st.checkbox("Add a full-span UDL of −4 kN/m")

    loads_demo = [{"type": "point", "x": load_x, "magnitude": load_mag}]
    if show_udl:
        loads_demo.append({"type": "udl", "x1": 0.0, "x2": 10.0, "w": -4.0})

    R_A, R_B = beam_solver.compute_reactions(geo_fixed, loads_demo)

    st.markdown("---")
    total_load = sum(
        ld["magnitude"] if ld["type"] == "point"
        else ld["w"] * (ld["x2"] - ld["x1"])
        for ld in loads_demo
    )
    st.markdown(f"""
| | Value |
|---|---|
| Total applied load | **{total_load:+.1f} kN** |
| Reaction R_A | **{R_A:+.2f} kN** {"⬆️" if R_A > 0 else "⬇️"} |
| Reaction R_B | **{R_B:+.2f} kN** {"⬆️" if R_B > 0 else "⬇️"} |
| Check R_A+R_B+loads | **{R_A+R_B+total_load:.2e} kN** ≈ 0 ✓ |
""")
    if R_B < 0:
        st.warning("R_B is negative — the roller is being pulled **downward**. "
                   "This means it must be anchored to the ground.")

with col_plot:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    draw_beam(ax, geo_fixed)
    draw_loads(ax, loads_demo, 10.0)
    draw_reactions(ax, 2.0, 8.0, R_A, R_B)
    ax.set_title(
        f"R_A = {R_A:+.2f} kN   |   R_B = {R_B:+.2f} kN",
        fontsize=11, pad=8
    )
    st.pyplot(fig, width='stretch')
    plt.close(fig)

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICE
# ══════════════════════════════════════════════════════════════════════════════

starter = """\
# Calculate reactions for this beam:
#   L = 10 m, pin A at 2 m, roller B at 8 m
#   Loads: -30 kN at x=3 m, -6 kN/m UDL from 4 m to 10 m

geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}

loads = [
    {"type": "point", "x": ___, "magnitude": ___},          # -30 kN at x=3
    {"type": "udl",   "x1": ___, "x2": ___, "w": ___},      # -6 kN/m from 4 to 10
]

# ── Extract support positions ─────────────────────────────────────────────
x_A  = geometry["x_A"]
x_B  = geometry["x_B"]
span = ___ - x_A                # interior span length

# ── Accumulate load contributions ─────────────────────────────────────────
total_force = 0.0
total_M_A   = 0.0              # total moment about A

for load in loads:
    if load["type"] == "point":
        P = load["magnitude"]
        x = load["x"]
        total_force += P
        total_M_A   += P * (x - ___)     # moment arm from A

    elif load["type"] == "udl":
        P_eq = load["w"] * (load["x2"] - load["x1"])   # equivalent point load
        x_c  = (load["x1"] + load["x2"]) / ___          # centroid (divide by what?)
        total_force += P_eq
        total_M_A   += P_eq * (x_c - x_A)

# ── Solve equilibrium ─────────────────────────────────────────────────────
R_B = -total_M_A / ___       # ΣM about A = 0
R_A = -___ - R_B             # ΣFy = 0

# ── Print results ─────────────────────────────────────────────────────────
print(f"Reaction R_A = {R_A:+.2f} kN")
print(f"Reaction R_B = {R_B:+.2f} kN")

# ── Self-check ────────────────────────────────────────────────────────────
residual = R_A + R_B + total_force
print(f"Check ΣFy   = {residual:.2e} kN  (should be ≈ 0)")
"""

solution = """\
geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
loads = [
    {"type": "point", "x": 3.0,  "magnitude": -30.0},
    {"type": "udl",   "x1": 4.0, "x2": 10.0, "w": -6.0},
]

x_A  = geometry["x_A"]
x_B  = geometry["x_B"]
span = x_B - x_A

total_force = 0.0
total_M_A   = 0.0

for load in loads:
    if load["type"] == "point":
        P = load["magnitude"]
        x = load["x"]
        total_force += P
        total_M_A   += P * (x - x_A)
    elif load["type"] == "udl":
        P_eq = load["w"] * (load["x2"] - load["x1"])
        x_c  = (load["x1"] + load["x2"]) / 2
        total_force += P_eq
        total_M_A   += P_eq * (x_c - x_A)

R_B = -total_M_A / span
R_A = -total_force - R_B

print(f"Reaction R_A = {R_A:+.2f} kN")
print(f"Reaction R_B = {R_B:+.2f} kN")

residual = R_A + R_B + total_force
print(f"Check ΣFy   = {residual:.2e} kN  (should be ≈ 0)")
"""

practice_block(
    key="L04",
    instructions="""
Calculate R_A and R_B for: L = 10 m, pin at 2 m, roller at 8 m,
with a **−30 kN load at x = 3 m** and a **−6 kN/m UDL from 4 m to 10 m**.
Fill in every `___` and verify equilibrium at the end.
""",
    starter_code=starter,
    solution_code=solution,
    expected_note="`R_A ≈ +55.0 kN  ·  R_B ≈ +41.0 kN`",
)

lesson_nav(
    prev_label="L03 — Loads",
    prev_page="pages/03_L03_Loads.py",
    next_label="L05 — Shear Force Diagram",
    next_page="pages/05_L05_Shear_Force.py",
)

