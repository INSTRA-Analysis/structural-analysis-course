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
from styles import apply_styles, lesson_progress, in_practice, key_takeaways
import beam_solver

st.set_page_config(page_title="L04 — Reactions", page_icon="⚖️", layout="wide")
apply_styles()

if "geometry" not in st.session_state:
    st.session_state.geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
if "loads" not in st.session_state:
    st.session_state.loads = []

st.title("Lesson 4 — Finding Support Reactions")
lesson_progress(4, 7, "Prerequisites: L01–L03  ·  ~60 minutes")
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

geo   = st.session_state.geometry
loads = st.session_state.loads

if not loads:
    st.info("No loads defined yet — set up your beam in **Lesson 2** and add loads in **Lesson 3**.")
else:
    R_A, R_B = beam_solver.compute_reactions(geo, loads)
    st.session_state.R_A = R_A
    st.session_state.R_B = R_B

    total_load = sum(
        ld["magnitude"] if ld["type"] == "point"
        else ld["w"] * (ld["x2"] - ld["x1"])
        for ld in loads
    )
    col_l, col_r = st.columns([1, 2])
    with col_l:
        mc1, mc2 = st.columns(2)
        mc1.metric("R_A", f"{R_A:+.2f} kN",
                   delta="upward" if R_A >= 0 else "downward")
        mc2.metric("R_B", f"{R_B:+.2f} kN",
                   delta="upward" if R_B >= 0 else "downward")
        st.metric("Total applied load", f"{total_load:+.1f} kN")
        st.caption(f"Equilibrium check ΣFy = {R_A + R_B + total_load:.2e} kN ≈ 0 ✓")
        if R_B < 0:
            st.warning("R_B is negative — the roller is being pulled downward.")
    with col_r:
        fig, ax = plt.subplots(figsize=(9, 3.2))
        draw_beam(ax, geo)
        draw_loads(ax, loads, geo["L_total"])
        draw_reactions(ax, geo["x_A"], geo["x_B"], R_A, R_B)
        ax.set_title(f"R_A = {R_A:+.2f} kN   |   R_B = {R_B:+.2f} kN", fontsize=10)
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

in_practice(
    "Before any FEA software existed, engineers computed reactions by hand using exactly "
    "these two equations. The software still solves the same linear system — your ten lines "
    "of Python are doing what a commercial package does for a simply supported beam."
)

key_takeaways([
    "Two equilibrium equations always suffice for a simply supported beam: ΣM = 0 gives R_B, then ΣFy = 0 gives R_A",
    "A load on the cantilever creates a moment about A that can make R_B **negative** — the roller is pulled down",
    "Always verify: `R_A + R_B + total_load = 0` — this self-check costs one line and catches every sign error",
    "The `compute_reactions` function is the core of the entire beam solver built in later lessons",
])

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

