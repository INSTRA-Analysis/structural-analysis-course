"""Lesson 2 — Your Beam on a Number Line"""

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
from plot_helpers import draw_beam
from styles import apply_styles, lesson_progress, in_practice, key_takeaways

st.set_page_config(page_title="L02 — Beam Geometry", page_icon="📐", layout="wide")
apply_styles()

# ── Header ─────────────────────────────────────────────────────────────────
st.title("Lesson 2 — Your Beam on a Number Line")
lesson_progress(2, 7, "Prerequisites: L01  ·  ~45 minutes")
st.markdown("""
The beam we analyse in this course has a **parametric** geometry — three numbers
fully describe it. Move the sliders below and watch the diagram update.
""")

# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📐 Theory — Beam Geometry")
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
```
x = 0 ── [left cantilever] ── x_A ── [interior span] ── x_B ── [right cantilever] ── x = L
                               PIN                        ROLLER
```

Three variables describe the entire beam:
- **`L_total`** — total length (m)
- **`x_A`** — position of the pin support from the left end (m)
- **`x_B`** — position of the roller support from the left end (m)

When `x_A = 0` there is no left cantilever. When `x_B = L_total` there is no right cantilever.
""")

# ── Persistent beam configuration — shared with Lessons 3 to 7 ───────────────
if "geometry" not in st.session_state:
    st.session_state.geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
if "loads" not in st.session_state:
    st.session_state.loads = []

col_ctrl, col_plot = st.columns([1, 2])

with col_ctrl:
    _g  = st.session_state.geometry
    L   = st.slider("Total length L (m)", 5.0, 20.0, _g["L_total"], 0.5)
    x_A = st.slider("Pin A position (m)", 0.0, L * 0.5, min(_g["x_A"], L * 0.5), 0.5)
    x_B_min = x_A + 0.5
    x_B = st.slider("Roller B position (m)", x_B_min, L, max(min(_g["x_B"], L), x_B_min), 0.5)

    # Persist on every rerun — all downstream lessons read this
    st.session_state.geometry = {"L_total": L, "x_A": x_A, "x_B": x_B}

    cant_L = x_A
    cant_R = L - x_B
    span   = x_B - x_A

    st.markdown("---")
    st.markdown(f"""
| Segment | Length |
|---------|--------|
| Left cantilever | **{cant_L:.1f} m** |
| Interior span | **{span:.1f} m** |
| Right cantilever | **{cant_R:.1f} m** |
| **Total** | **{L:.1f} m** |
""")
    st.success(f"Beam saved — Lessons 3–7 will use  L = {L:.1f} m · A = {x_A:.1f} m · B = {x_B:.1f} m")
    if cant_L == 0:
        st.info("No left cantilever — A is at the free end")
    if cant_R == 0:
        st.info("No right cantilever — B is at the free end")

with col_plot:
    geo = {"L_total": L, "x_A": x_A, "x_B": x_B}
    fig, ax = plt.subplots(figsize=(9, 3.2))
    draw_beam(ax, geo)
    ax.set_title(
        f"L = {L:.1f} m  |  Cantilever left = {cant_L:.1f} m  |  "
        f"Span = {span:.1f} m  |  Cantilever right = {cant_R:.1f} m",
        fontsize=9, pad=6
    )
    st.pyplot(fig, width='stretch')
    plt.close(fig)

st.markdown("---")

# ── NumPy section ──────────────────────────────────────────────────────────
st.markdown("## 📐 Theory — NumPy Arrays")

col_l, col_r = st.columns([1, 1])
with col_l:
    st.markdown("""
In the next lessons we will calculate shear force and bending moment at **hundreds
of points** along the beam. For that we need **NumPy** — a library for working with
arrays of numbers.

```python
import numpy as np

# 11 equally-spaced points from 0 to 10
x = np.linspace(0, 10, 11)
print(x)
# [ 0.  1.  2.  3.  4.  5.  6.  7.  8.  9. 10.]

# Operations apply to every element at once
print(x * 2)
# [ 0.  2.  4.  6.  8. 10. 12. 14. 16. 18. 20.]
```

**Key functions we will use:**

| Function | What it does |
|----------|-------------|
| `np.linspace(a, b, n)` | n points from a to b |
| `np.zeros(n)` | array of n zeros |
| `x[0]` | first element |
| `x[-1]` | last element |
| `x.max()` / `x.min()` | largest / smallest value |
""")

with col_r:
    st.markdown("**See linspace in action:**")
    n_pts = st.slider("Number of points", 3, 20, 6)
    import numpy as np
    x_demo = np.linspace(0, L, n_pts)
    st.markdown(f"`np.linspace(0, {L}, {n_pts})` produces:")
    st.code(str(np.round(x_demo, 2)), language=None)

    st.markdown("---")
    st.markdown("""
For smooth diagrams in later lessons we will use:
```python
x = np.linspace(0, L_total, 500)
```
That is 500 calculation points — invisible to the reader,
but it makes the curves perfectly smooth.
""")

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICE
# ══════════════════════════════════════════════════════════════════════════════

starter = """\
# Define the beam geometry
L_total = ___      # total length in metres (use 10.0)
x_A     = ___      # pin support position (use 2.0)
x_B     = ___      # roller support position (use 8.0)

# Calculate derived quantities
cantilever_left  = ___            # left cantilever length
cantilever_right = L_total - ___  # right cantilever length
interior_span    = ___ - x_A      # interior span

# Print a summary
print(f"Total length      : {L_total:.1f} m")
print(f"Left cantilever   : {cantilever_left:.1f} m")
print(f"Interior span     : {interior_span:.1f} m")
print(f"Right cantilever  : {cantilever_right:.1f} m")

# Find the midpoint of the interior span
midspan = x_A + interior_span / ___
print(f"Midspan position  : {midspan:.1f} m")

# Verify: left + span + right should equal L_total
total_check = cantilever_left + interior_span + cantilever_right
print(f"Check (should = {L_total}): {total_check:.1f}")
"""

solution = """\
# Define the beam geometry
L_total = 10.0     # total length in metres
x_A     = 2.0      # pin support position
x_B     = 8.0      # roller support position

# Calculate derived quantities
cantilever_left  = x_A
cantilever_right = L_total - x_B
interior_span    = x_B - x_A

# Print a summary
print(f"Total length      : {L_total:.1f} m")
print(f"Left cantilever   : {cantilever_left:.1f} m")
print(f"Interior span     : {interior_span:.1f} m")
print(f"Right cantilever  : {cantilever_right:.1f} m")

# Find the midpoint of the interior span
midspan = x_A + interior_span / 2
print(f"Midspan position  : {midspan:.1f} m")

# Verify: left + span + right should equal L_total
total_check = cantilever_left + interior_span + cantilever_right
print(f"Check (should = {L_total}): {total_check:.1f}")
"""

in_practice(
    "Every structural analysis program — OpenSeesPy, SAP2000, Tekla — stores geometry "
    "parametrically as node coordinates. The three-number beam dict you defined here is "
    "the same concept: describe the structure once, reuse everywhere."
)

key_takeaways([
    "Three numbers — `L_total`, `x_A`, `x_B` — fully describe any simply supported beam with cantilevers",
    "`x_A = 0` removes the left cantilever; `x_B = L_total` removes the right cantilever",
    "`np.linspace(0, L, 500)` generates the 500-point x-axis used in every diagram from L05 onwards",
    "This geometry dict is now saved in session state — all later lessons read it automatically",
])

practice_block(
    key="L02",
    instructions="""
Define the beam geometry for our default beam (L = 10 m, pin at 2 m, roller at 8 m)
and calculate the segment lengths. Fill in every `___`.
""",
    starter_code=starter,
    solution_code=solution,
    expected_note="`Interior span = 6.0 m  ·  Midspan position = 5.0 m  ·  Check = 10.0`",
)

lesson_nav(
    prev_label="L01 — Python as Your Calculator",
    prev_page="pages/01_L01_Python_Intro.py",
    next_label="L03 — Placing Loads",
    next_page="pages/03_L03_Loads.py",
)

