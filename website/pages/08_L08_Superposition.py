"""Lesson 8 — Superposition (Supplementary)"""

import streamlit as st
import sys, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(BASE, "components"))
sys.path.insert(0, os.path.join(BASE, "..", "course", "shared"))

from code_runner import lesson_nav
from plot_helpers import draw_beam, draw_loads, draw_reactions, draw_contributions
from styles import apply_styles, lesson_progress, in_practice, key_takeaways
import beam_solver

st.set_page_config(page_title="L08 — Superposition", page_icon="➕", layout="wide")
apply_styles()

if "geometry" not in st.session_state:
    st.session_state.geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
if "loads" not in st.session_state:
    st.session_state.loads = []

# ══════════════════════════════════════════════════════════════════════════════
st.title("Supplementary — The Principle of Superposition")
lesson_progress(8, 8, "Prerequisites: L04–L06  ·  Complementary")
st.markdown("""
The principle of superposition states that for a **linear elastic** structure,
the total response to multiple loads equals the **sum of the individual responses**
to each load applied separately.
""")

# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📐 Theory")
# ══════════════════════════════════════════════════════════════════════════════

col_l, col_r = st.columns(2)

with col_l:
    st.markdown(r"""
**Why it works**

For a linearly elastic beam the governing equations are linear.
If load $P_1$ produces reactions $R_{A,1}$, $R_{B,1}$ and diagrams $V_1(x)$, $M_1(x)$,
and load $P_2$ independently produces $R_{A,2}$, $R_{B,2}$, $V_2(x)$, $M_2(x)$, then
when both loads act together:

$$R_A = R_{A,1} + R_{A,2} \qquad R_B = R_{B,1} + R_{B,2}$$

$$V(x) = V_1(x) + V_2(x) \qquad M(x) = M_1(x) + M_2(x)$$

**Conditions for validity**

- Small deformations (geometry does not change under load)
- Linear elastic material (stress proportional to strain)
- Supports do not move under load

These conditions hold for the vast majority of everyday structural analysis.
""")

with col_r:
    st.markdown(r"""
**Why it is useful**

1. **Decompose complexity** — analyse each load independently,
   then add the results. Much easier to check by hand.

2. **Identify critical loads** — see which load dominates the
   reactions and which creates the peak moment.

3. **Sign checking** — if one load creates hogging where another
   creates sagging, the total moment is reduced. Superposition
   reveals this immediately.

4. **Standard load tables** — structural design tables list
   deflections and moments for standard load patterns (UDL, central
   point load, etc.). Superposition lets you combine them.

**The method**

For each load $i$:
$$R_{B,i} = -\frac{P_i \cdot (x_i - x_A)}{x_B - x_A}
\qquad R_{A,i} = -P_i - R_{B,i}$$

Sum all contributions to get the total.
""")

# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## Your Beam — Superposition Breakdown")
st.caption("Using the geometry from Lesson 2 and the loads from Lesson 3.")
# ══════════════════════════════════════════════════════════════════════════════

geo   = st.session_state.geometry
loads = st.session_state.loads

if not loads:
    st.info("No loads defined yet — set up your beam in **Lesson 2** and add loads in **Lesson 3**.")
elif len(loads) == 1:
    st.info("Superposition is most instructive with two or more loads. "
            "Go to **Lesson 3** and add a second load to see the breakdown.")
else:
    result = beam_solver.analyse_contributions(geo, loads)

    # ── Reaction breakdown table ──────────────────────────────────────────────
    st.markdown("### Reactions by superposition")

    header = "| Load | R_A (kN) | R_B (kN) |"
    sep    = "|------|----------|----------|"
    rows   = [header, sep]
    for c in result["contributions"]:
        rows.append(f"| {c['label']} | {c['R_A']:+.2f} | {c['R_B']:+.2f} |")
    rows.append(
        f"| **Total (sum)** | **{result['R_A']:+.2f}** | **{result['R_B']:+.2f}** |"
    )
    st.markdown("\n".join(rows))

    # Verify the superposition total matches direct calculation
    R_A_check, R_B_check = beam_solver.compute_reactions(geo, loads)
    st.caption(
        f"Direct calculation: R_A = {R_A_check:+.2f} kN · R_B = {R_B_check:+.2f} kN — "
        f"difference from superposition: {abs(result['R_A'] - R_A_check):.2e} kN ✓"
    )

    # ── Pre-superposition + cumulative SFD / BMD ──────────────────────────────
    st.markdown("### SFD and BMD — individual contributions vs total")
    st.markdown("""
The **left column** shows each load's contribution to the SFD and BMD independently.
The **right column** shows the superposed total — identical to what Lesson 5 and 6 produced directly.
""")

    fig = draw_contributions(result, figsize=(14, 9))
    st.pyplot(fig, width='stretch')
    plt.close(fig)

    # ── Per-load beam diagrams ────────────────────────────────────────────────
    st.markdown("### Per-load beam diagrams")
    st.markdown("Each load drawn alone on the beam, with its own reaction arrows.")

    n_loads = len(loads)
    cols = st.columns(min(n_loads, 3))
    for i, c in enumerate(result["contributions"]):
        with cols[i % 3]:
            fig_i, ax_i = plt.subplots(figsize=(5, 2.8))
            draw_beam(ax_i, geo)
            draw_loads(ax_i, [c["load"]], geo["L_total"])
            draw_reactions(ax_i, geo["x_A"], geo["x_B"], c["R_A"], c["R_B"])
            ax_i.set_title(
                f"{c['label']}\nR_A={c['R_A']:+.1f} kN  R_B={c['R_B']:+.1f} kN",
                fontsize=8, pad=4
            )
            st.pyplot(fig_i, width='stretch')
            plt.close(fig_i)

in_practice(
    "Standard structural design tables (e.g. SCI Blue Book, AISC Steel Manual) list "
    "reactions and moments for common load patterns — central point load, UDL, end moment. "
    "Engineers combine them using superposition instead of solving from scratch every time."
)

key_takeaways([
    "Total response = sum of individual responses — valid for any linear elastic structure",
    "Each load's R_A and R_B contribution can be read off a standard table and summed",
    "The contribution plots reveal which load dominates — useful for targeted design optimisation",
    "Superposition is not an approximation — for linear systems it is exact",
])

# ══════════════════════════════════════════════════════════════════════════════
lesson_nav(
    prev_label="L07 — Complete Analysis Tool",
    prev_page="pages/07_L07_Capstone.py",
)
