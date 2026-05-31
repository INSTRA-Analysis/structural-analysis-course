"""Lesson 3 — Placing Loads on the Beam"""

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
from plot_helpers import draw_beam, draw_loads
from styles import apply_styles, lesson_progress, in_practice, key_takeaways

st.set_page_config(page_title="L03 — Loads", page_icon="📦", layout="wide")
apply_styles()


def _loads_as_code(loads):
    """Format the loads list as valid Python code for the live display panel."""
    if not loads:
        return "loads = []"
    lines = ["loads = ["]
    for ld in loads:
        if ld["type"] == "point":
            lines.append(
                f'    {{"type": "point", '
                f'"x": {ld["x"]:.1f}, '
                f'"magnitude": {ld["magnitude"]:.1f}}},'
            )
        elif ld["type"] == "udl":
            lines.append(
                f'    {{"type": "udl", '
                f'"x1": {ld["x1"]:.1f}, '
                f'"x2": {ld["x2"]:.1f}, '
                f'"w": {ld["w"]:.1f}}},'
            )
    lines.append("]")
    return "\n".join(lines)

st.title("Lesson 3 — Placing Loads on the Beam")
lesson_progress(3, 7, "Prerequisites: L01–L02  ·  ~60 minutes")
st.markdown("""
Before calculating reactions, we need to describe the applied loads in Python.
We use **dictionaries** — a way to group related data under one name.
""")

# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📐 Theory — Sign Convention")
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
We must agree on signs before writing any equations. Throughout this course:

| Quantity | Positive | Negative |
|----------|----------|----------|
| Load | ↑ Upward | ↓ Downward (gravity) |
| Reaction | ↑ Upward | ↓ Downward |
| Bending moment | Sagging (concave up) | Hogging (concave down) |

So a **20 kN downward point load** is written as `magnitude = -20.0`.
""")

st.markdown("## 📐 Theory — Load Types and the Interactive Diagram")

# ── Read beam geometry set in Lesson 2 ───────────────────────────────────────
if "geometry" not in st.session_state:
    st.session_state.geometry = {"L_total": 10.0, "x_A": 2.0, "x_B": 8.0}
if "loads" not in st.session_state:
    st.session_state.loads = []

geometry = st.session_state.geometry
_L = geometry["L_total"]

col_ctrl, col_plot = st.columns([1, 2])

with col_ctrl:
    st.markdown("**Add loads to the beam:**")
    load_type = st.radio("Load type", ["Point load", "UDL"], horizontal=True)

    if load_type == "Point load":
        x_pos  = st.slider("Position x (m)", 0.0, _L, min(round(_L / 2, 1), _L), 0.5)
        mag    = st.slider("Magnitude (kN)  negative = down", -100.0, 100.0, -20.0, 5.0)
        new_load = {"type": "point", "x": x_pos, "magnitude": mag}
    else:
        x1 = st.slider("UDL start x1 (m)", 0.0, _L - 0.5, min(geometry["x_A"], _L - 0.5), 0.5)
        x2 = st.slider("UDL end   x2 (m)", x1 + 0.5, _L, min(geometry["x_B"], _L), 0.5)
        w  = st.slider("Intensity (kN/m)  negative = down", -40.0, 40.0, -5.0, 1.0)
        new_load = {"type": "udl", "x1": x1, "x2": min(x2, _L), "w": w}

    if "loads" not in st.session_state:
        st.session_state.loads = []

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Add load", type="primary"):
            st.session_state.loads.append(new_load)
    with col_b:
        if st.button("Clear all"):
            st.session_state.loads = []

with col_plot:
    fig, ax = plt.subplots(figsize=(9, 2.8))
    draw_beam(ax, geometry)
    if st.session_state.loads:
        draw_loads(ax, st.session_state.loads, 10.0)
        n = len(st.session_state.loads)
        ax.set_title(f"{n} load{'s' if n > 1 else ''} applied", fontsize=10)
    else:
        ax.set_title("Add loads using the controls →", fontsize=10, color="#888")
    st.pyplot(fig, width='stretch')
    plt.close(fig)

# ── Live Python representation — full width ────────────────────────────────
st.markdown("**Your `loads` list in Python:**")
st.code(_loads_as_code(st.session_state.loads), language="python")

st.markdown("---")

st.markdown("## 📐 Theory — Dictionaries and Lists")

col_l, col_r = st.columns([1, 1])
with col_l:
    st.markdown("""
A **dictionary** groups related data under one name:

```python
# A point load
load1 = {
    "type"      : "point",
    "x"         : 5.0,      # position (m)
    "magnitude" : -20.0     # kN (negative = downward)
}

# Access a value
print(load1["magnitude"])  # -20.0
```

A **UDL** has start, end, and intensity:

```python
load2 = {
    "type" : "udl",
    "x1"   : 2.0,    # start (m)
    "x2"   : 8.0,    # end (m)
    "w"    : -5.0    # kN/m (negative = downward)
}
```

Store all loads in a **list**:
```python
loads = [load1, load2]
print(f"Total loads: {len(loads)}")
```
""")

with col_r:
    st.markdown("""
Loop over all loads with a `for` loop:

```python
for load in loads:
    if load["type"] == "point":
        P = load["magnitude"]
        x = load["x"]
        print(f"Point load {P} kN at x={x} m")

    elif load["type"] == "udl":
        w  = load["w"]
        P_total = w * (load["x2"] - load["x1"])
        print(f"UDL: total force = {P_total} kN")
```

The equivalent point load for a UDL:
$$P_{equiv} = w \\times (x_2 - x_1)$$

It acts at the centroid:
$$x_{centroid} = \\frac{x_1 + x_2}{2}$$
""")

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICE
# ══════════════════════════════════════════════════════════════════════════════

starter = """\
# Build a load list for a specific scenario

loads = []    # start with an empty list

# --- Load 1: -30 kN point load at midspan (x = 5 m) ---
load1 = {
    "type"      : "point",
    "x"         : ___,        # position in metres
    "magnitude" : ___         # kN — downward so negative
}
loads.append(___)             # add load1 to the list

# --- Load 2: -4 kN/m UDL over the full beam (0 to 10 m) ---
load2 = {
    "type" : "udl",
    "x1"   : ___,             # start of UDL
    "x2"   : ___,             # end of UDL
    "w"    : ___              # kN/m — downward so negative
}
loads.append(___)             # add load2

# --- Load 3: -15 kN point load at the right cantilever tip (x = 9 m) ---
load3 = {"type": "point", "x": ___, "magnitude": ___}
loads.append(___)

# --- Print a summary of all loads ---
print(f"Total loads defined: {len(loads)}")
print()

for i, load in enumerate(loads):
    if load["type"] == "point":
        print(f"Load {i+1}: Point load  {load['magnitude']:+.0f} kN  at x = {load['x']:.1f} m")
    elif load["type"] == "udl":
        P_eq  = load["w"] * (load["x2"] - load["x1"])
        x_c   = (load["x1"] + load["x2"]) / 2
        print(f"Load {i+1}: UDL  {load['w']:+.0f} kN/m  from {load['x1']:.0f} to {load['x2']:.0f} m")
        print(f"          Equivalent point load: {P_eq:.0f} kN at x = {x_c:.1f} m")

# Total vertical load
total = sum(
    ld["magnitude"] if ld["type"] == "point"
    else ld["w"] * (ld["x2"] - ld["x1"])
    for ld in loads
)
print(f"\\nTotal vertical load: {total:.0f} kN")
"""

solution = """\
# Build a load list
loads = []

# Load 1: -30 kN point load at midspan
load1 = {"type": "point", "x": 5.0, "magnitude": -30.0}
loads.append(load1)

# Load 2: -4 kN/m UDL over the full beam
load2 = {"type": "udl", "x1": 0.0, "x2": 10.0, "w": -4.0}
loads.append(load2)

# Load 3: -15 kN point load at right cantilever tip
load3 = {"type": "point", "x": 9.0, "magnitude": -15.0}
loads.append(load3)

# Print summary
print(f"Total loads defined: {len(loads)}")
print()
for i, load in enumerate(loads):
    if load["type"] == "point":
        print(f"Load {i+1}: Point load  {load['magnitude']:+.0f} kN  at x = {load['x']:.1f} m")
    elif load["type"] == "udl":
        P_eq = load["w"] * (load["x2"] - load["x1"])
        x_c  = (load["x1"] + load["x2"]) / 2
        print(f"Load {i+1}: UDL  {load['w']:+.0f} kN/m  from {load['x1']:.0f} to {load['x2']:.0f} m")
        print(f"          Equivalent point load: {P_eq:.0f} kN at x = {x_c:.1f} m")

total = sum(
    ld["magnitude"] if ld["type"] == "point"
    else ld["w"] * (ld["x2"] - ld["x1"])
    for ld in loads
)
print(f"\\nTotal vertical load: {total:.0f} kN")
"""

in_practice(
    "In real practice, load cases are defined as data structures — dead load, imposed load, "
    "wind load — and combined programmatically. The same list-of-dicts pattern is used in "
    "OpenSeesPy, PyNite, and every parametric FEA workflow."
)

key_takeaways([
    "A dictionary groups related data under named keys — `load['magnitude']` is always clear",
    "Downward forces are **negative**; upward reactions will be **positive** — this must be consistent throughout",
    "A list of load dicts lets you loop over all loads with a single `for` statement",
    "The equivalent point load for a UDL is `P = w × (x2 − x1)` acting at the centroid",
])

practice_block(
    key="L03",
    instructions="""
Build a load list for a beam with three loads:
a **−30 kN point load at midspan** (x = 5 m),
a **−4 kN/m full-span UDL** (0 to 10 m),
and a **−15 kN point load at the right cantilever tip** (x = 9 m).
""",
    starter_code=starter,
    solution_code=solution,
    expected_note="`Total vertical load = −85 kN`",
)

lesson_nav(
    prev_label="L02 — Beam Geometry",
    prev_page="pages/02_L02_Beam_Geometry.py",
    next_label="L04 — Reactions",
    next_page="pages/04_L04_Reactions.py",
)

