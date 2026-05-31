"""Lesson 6 — Bending Moment Diagram"""

import streamlit as st
import sys, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import cumulative_trapezoid

BASE = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(BASE, "components"))
sys.path.insert(0, os.path.join(BASE, "..", "course", "shared"))

from code_runner import practice_block, lesson_nav
from plot_helpers import draw_beam, draw_loads, draw_reactions
from styles import apply_styles, lesson_progress, in_practice, key_takeaways
import beam_solver

st.set_page_config(page_title="L06 — Bending Moment Diagram", page_icon="📈", layout="wide")
apply_styles()

if "geometry" not in st.session_state:
    st.session_state.geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
if "loads" not in st.session_state:
    st.session_state.loads = []

st.title("Lesson 6 — Bending Moment Diagram")
lesson_progress(6, 7, "Prerequisites: L01–L05  ·  ~75 minutes")
st.markdown("""
The bending moment at any section is the **integral of the shear force** from the left end.
This is the last piece of the analysis — and the most structurally significant.
""")

# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📈 Theory — Interactive Beam + SFD + BMD")
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(r"""
**Fundamental relationship:**
$$\frac{dM}{dx} = V(x) \quad\Rightarrow\quad M(x) = \int_0^x V(\xi)\, d\xi$$

**Key rules:**
- M = 0 at both **free ends** (cantilever tips)
- M is **maximum where V = 0**
- **Sagging** (concave up) = positive — blue fill
- **Hogging** (concave down) = negative — red fill
""")

geo   = st.session_state.geometry
loads = st.session_state.loads

if not loads:
    st.info("No loads defined yet — set up your beam in **Lesson 2** and add loads in **Lesson 3**.")
else:
    col_opt, _ = st.columns([1, 3])
    with col_opt:
        show_peaks = st.checkbox("Annotate peak values", value=True)
        show_vzero = st.checkbox("Mark V = 0 lines", value=True)

    try:
        res = beam_solver.analyse(geo, loads)
        R_A, R_B = res["R_A"], res["R_B"]
        x, V, M  = res["x"], res["V"], res["M"]

        fig, (ax_b, ax_m) = plt.subplots(2, 1, figsize=(10, 7),
                                           gridspec_kw={"height_ratios": [1, 2.8]})
        fig.subplots_adjust(hspace=0.08)

        draw_beam(ax_b, geo)
        draw_loads(ax_b, loads, geo["L_total"])
        draw_reactions(ax_b, geo["x_A"], geo["x_B"], R_A, R_B)
        ax_b.tick_params(labelbottom=False)

        ax_m.plot(x, M, "#1B5E20", lw=2)
        ax_m.fill_between(x, M, 0, where=(M >= 0), color="#A5D6A7", alpha=0.5, label="Sagging (+)")
        ax_m.fill_between(x, M, 0, where=(M < 0),  color="#FFCDD2", alpha=0.5, label="Hogging (−)")
        ax_m.axhline(0, color="k", lw=0.8)
        ax_m.set_ylabel("M (kN·m)", fontsize=9)
        ax_m.set_xlabel("Position x (m)", fontsize=10)
        ax_m.legend(fontsize=8)
        ax_m.grid(True, ls="--", alpha=0.4)

        # Mark where V=0 (= where M is at a local extreme)
        if show_vzero:
            for idx in np.where(np.diff(np.sign(V)))[0]:
                ax_m.axvline(x[idx], color="red", ls=":", lw=1, alpha=0.7)
                ax_m.text(x[idx] + 0.1, ax_m.get_ylim()[0] * 0.85,
                          f"M_ext\n({x[idx]:.1f}m)", fontsize=7.5, color="red")

        if show_peaks:
            for idx, clr in [(M.argmax(), "#1B5E20"), (M.argmin(), "#C62828")]:
                if abs(M[idx]) > 0.5:
                    ax_m.plot(x[idx], M[idx], "o", color=clr, ms=6, zorder=5)
                    ax_m.annotate(f"{M[idx]:+.1f}",
                                  xy=(x[idx], M[idx]),
                                  xytext=(x[idx] + 0.25, M[idx]),
                                  fontsize=8, color=clr)

        xlim = (x[0] - 0.3, x[-1] + 0.3)
        ax_b.set_xlim(*xlim)
        ax_m.set_xlim(*xlim)

        fig.suptitle(
            f"R_A={R_A:+.1f} kN  |  R_B={R_B:+.1f} kN  |  "
            f"M_max={M.max():+.1f} kN·m  |  M_min={M.min():+.1f} kN·m",
            fontsize=9, y=1.01
        )
        st.pyplot(fig, width='stretch')
        plt.close(fig)

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("R_A",   f"{R_A:+.2f} kN")
        mc2.metric("R_B",   f"{R_B:+.2f} kN")
        mc3.metric("M_max", f"{M.max():+.1f} kN·m", delta="Sagging")
        mc4.metric("M_min", f"{M.min():+.1f} kN·m", delta="Hogging")

    except Exception as e:
        st.error(f"Calculation error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
in_practice(
    "M_max directly determines the section you need. For steel: `Z_required = M_max / f_y`. "
    "For concrete: the reinforcement area comes from M_max via the design moment capacity. "
    "Getting M_max right is the central goal of every beam analysis."
)

key_takeaways([
    "M = 0 at both free ends — a free end has no restraint, so no moment can develop there",
    "M = ∫V dx — bending moment is the running total of shear force from the left end",
    "**Sagging** (+) occurs in the span; **hogging** (−) in cantilever regions and over internal supports",
    "M is always maximum (or minimum) at a V = 0 crossing — use the SFD to find critical sections",
])

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICE
# ══════════════════════════════════════════════════════════════════════════════

def _analyse(geometry, loads, n=500):
    return beam_solver.analyse(geometry, loads, n)

starter = """\
import numpy as np
import matplotlib.pyplot as plt

# --- Given: beam and loads ---
geometry = {"L_total": 12.0, "x_A": 3.0, "x_B": 9.0}
loads    = [{"type": "udl", "x1": 0.0, "x2": 12.0, "w": -10.0}]

# --- Step 1: run the full analysis ---
results = analyse(geometry, loads)   # returns dict: R_A, R_B, x, V, M

R_A = results["___"]    # extract reaction at A
R_B = results["R_B"]
x   = results["x"]
V   = results["V"]
M   = results["___"]    # extract moment array

print(f"R_A = {R_A:+.2f} kN")
print(f"R_B = {R_B:+.2f} kN")

# --- Step 2: find key moment values ---
M_max_value = M.___()             # maximum value of M
M_max_pos   = x[M.___max()]       # x-position where M is maximum

print(f"M_max = {M_max_value:+.2f} kN·m  at x = {M_max_pos:.2f} m")
print(f"M at x=0    : {M[0]:+.4f} kN·m  (should be ≈ 0)")
print(f"M at x=12 m : {M[___]:+.4f} kN·m  (should be ≈ 0)")

# --- Step 3: plot the BMD ---
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(x, M, "#1B5E20", lw=2.2, label="M(x)")
ax.fill_between(x, M, 0, where=(M >= 0), color="#A5D6A7", alpha=0.5, label="Sagging (+)")
ax.fill_between(x, M, 0, where=(M < ___),  color="#FFCDD2", alpha=0.5, label="Hogging (−)")
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel("Position x (m)")
ax.set_ylabel("Bending Moment M (kN·m)")
ax.set_title("BMD — −10 kN/m UDL over 12 m beam")
ax.legend()
ax.grid(True, ls="--", alpha=0.4)
plt.tight_layout()
plt.show()
"""

solution = """\
import numpy as np
import matplotlib.pyplot as plt

geometry = {"L_total": 12.0, "x_A": 3.0, "x_B": 9.0}
loads    = [{"type": "udl", "x1": 0.0, "x2": 12.0, "w": -10.0}]

results = analyse(geometry, loads)
R_A = results["R_A"]
R_B = results["R_B"]
x   = results["x"]
V   = results["V"]
M   = results["M"]

print(f"R_A = {R_A:+.2f} kN")
print(f"R_B = {R_B:+.2f} kN")

M_max_value = M.max()
M_max_pos   = x[M.argmax()]
print(f"M_max = {M_max_value:+.2f} kN·m  at x = {M_max_pos:.2f} m")
print(f"M at x=0    : {M[0]:+.4f} kN·m  (should be ≈ 0)")
print(f"M at x=12 m : {M[-1]:+.4f} kN·m  (should be ≈ 0)")

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(x, M, "#1B5E20", lw=2.2, label="M(x)")
ax.fill_between(x, M, 0, where=(M >= 0), color="#A5D6A7", alpha=0.5, label="Sagging (+)")
ax.fill_between(x, M, 0, where=(M < 0),  color="#FFCDD2", alpha=0.5, label="Hogging (−)")
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel("Position x (m)")
ax.set_ylabel("Bending Moment M (kN·m)")
ax.set_title("BMD — −10 kN/m UDL over 12 m beam")
ax.legend()
ax.grid(True, ls="--", alpha=0.4)
plt.tight_layout()
plt.show()
"""

practice_block(
    key="L06",
    instructions="""
Run the complete analysis for a **12 m beam** (pin at 3 m, roller at 9 m)
with a **−10 kN/m full-span UDL**. The `analyse()` function does all the work —
you just need to extract the results and plot the BMD.
""",
    starter_code=starter,
    solution_code=solution,
    expected_note="`M_max ≈ +45 kN·m  ·  M at both free ends ≈ 0`",
    pre_defined={"analyse": _analyse},
)

lesson_nav(
    prev_label="L05 — Shear Force",
    prev_page="pages/05_L05_Shear_Force.py",
    next_label="L07 — Complete Tool",
    next_page="pages/07_L07_Capstone.py",
)

