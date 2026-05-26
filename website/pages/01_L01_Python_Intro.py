"""Lesson 1 — Python as Your Calculator"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "components"))
from code_runner import practice_block, lesson_nav

st.set_page_config(page_title="L01 — Python as Your Calculator", page_icon="🐍", layout="wide")

# ── Header ─────────────────────────────────────────────────────────────────
st.title("Lesson 1 — Python as Your Calculator")
st.caption("Prerequisites: none  ·  Time: ~45 minutes")
st.markdown("""
As a structural engineer you already calculate things every day — section properties,
reactions, moments. Python lets you do the same calculations, but store, reuse, and
automate them. Let's start with something you know: a rectangular cross-section.
""")

# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📐 Theory — Variables and Arithmetic")
# ══════════════════════════════════════════════════════════════════════════════

col_ctrl, col_result = st.columns([1, 1])

with col_ctrl:
    st.markdown("""
**A variable** is a named box that holds a value.
You assign it with `=`:

```python
b = 200    # width in mm
d = 450    # depth in mm
```

**Python arithmetic operators:**

| Symbol | Meaning       | Example     |
|--------|---------------|-------------|
| `+`    | Addition      | `3 + 2`     |
| `-`    | Subtraction   | `10 - 4`    |
| `*`    | Multiplication| `b * d`     |
| `/`    | Division      | `9 / 4`     |
| `**`   | Power         | `d ** 3`    |

**f-strings** embed variable values in text:
```python
print(f"Area = {A} mm²")
```
""")

with col_result:
    st.markdown("**Try different section dimensions:**")
    b = st.slider("Width b (mm)", 100, 600, 200, 10)
    d = st.slider("Depth d (mm)", 100, 900, 450, 10)

    A = b * d
    I = (b * d**3) / 12
    Z = I / (d / 2)
    ratio = d / b

    st.markdown("---")
    st.markdown(f"""
| Property | Value |
|----------|-------|
| Area A | **{A:,.0f} mm²** |
| Second moment of area I | **{I:,.0f} mm⁴** |
| Section modulus Z | **{Z:,.0f} mm³** |
| Depth-to-width ratio d/b | **{ratio:.2f}** |
""")
    if d >= b:
        st.success(f"d/b = {ratio:.2f}  ✓  The section is deeper than wide (good for a beam)")
    else:
        st.warning(f"d/b = {ratio:.2f}  ⚠ The section is wider than deep — consider rotating it")

st.markdown("---")

# ── Concept: if / else ─────────────────────────────────────────────────────
st.markdown("## 📐 Theory — Making Decisions with `if / else`")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("""
Python can make decisions based on conditions:

```python
if d > b:
    print("Section is deeper than wide — OK")
else:
    print("Section is wider than deep — check!")
```

The **indentation** (spaces at the start of the line) is mandatory.
It tells Python which lines are inside the `if`.

Comparison operators:

| Symbol | Meaning |
|--------|---------|
| `>`    | Greater than |
| `<`    | Less than |
| `>=`   | Greater than or equal |
| `==`   | Equal to |
| `!=`   | Not equal to |
""")

with col_right:
    st.markdown("**See `if/else` in action:**")
    test_b = st.number_input("b (mm)", 50, 800, 200, key="if_b")
    test_d = st.number_input("d (mm)", 50, 1200, 300, key="if_d")

    st.markdown("**Python runs this code:**")
    code_shown = f"""b = {test_b}
d = {test_d}
if d > b:
    print("Section OK: d={test_d} > b={test_b}")
else:
    print("WARNING: d={test_d} < b={test_b} — consider rotating")"""
    st.code(code_shown, language="python")
    st.markdown("**Result:**")
    if test_d > test_b:
        st.success(f"Section OK: d={test_d} > b={test_b}")
    else:
        st.error(f"WARNING: d={test_d} < b={test_b} — consider rotating")

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICE SECTION
# ══════════════════════════════════════════════════════════════════════════════

starter = """\
# --- A steel beam cross-section ---
# Fill in the blanks (replace ___ with the correct value or expression)

b = ___          # width in mm  (try 254)
d = ___          # depth in mm  (try 254 — a square section)
E = 210_000      # Young's modulus in N/mm² (steel, do not change)

# Calculate section properties
A = b * ___                   # area = width × depth
I = (b * d ** ___) / 12       # I = b×d³ / 12
Z = I / (d / ___)             # Z = I / (d/2)

# Calculate flexural rigidity EI (in N·mm²)
EI = ___ * I

# Print results
print(f"Width  b  = {b} mm")
print(f"Depth  d  = {d} mm")
print(f"Area   A  = {A:,.0f} mm²")
print(f"I         = {I:,.0f} mm⁴")
print(f"Z         = {Z:,.0f} mm³")
print(f"EI        = {EI:.3e} N·mm²")

# Check d/b ratio
if d >= b:
    print("Depth check: OK")
else:
    print("Depth check: Consider rotating section")
"""

solution = """\
# --- A steel beam cross-section ---
b = 254          # width in mm
d = 254          # depth in mm
E = 210_000      # Young's modulus in N/mm² (steel)

# Calculate section properties
A  = b * d
I  = (b * d ** 3) / 12
Z  = I / (d / 2)
EI = E * I

# Print results
print(f"Width  b  = {b} mm")
print(f"Depth  d  = {d} mm")
print(f"Area   A  = {A:,.0f} mm²")
print(f"I         = {I:,.0f} mm⁴")
print(f"Z         = {Z:,.0f} mm³")
print(f"EI        = {EI:.3e} N·mm²")

# Check d/b ratio
if d >= b:
    print("Depth check: OK")
else:
    print("Depth check: Consider rotating section")
"""

practice_block(
    key="L01",
    instructions="""
Calculate the cross-section properties and flexural rigidity for a **254 × 254 mm steel section**.
Fill in every `___` with the correct value or expression.
All the formulas are in the theory section above.
""",
    starter_code=starter,
    solution_code=solution,
    expected_note="`EI ≈ 8.77 × 10¹⁰ N·mm²`  (the flexural stiffness of this section)",
)

lesson_nav(
    next_label="L02 — Beam Geometry",
    next_page="pages/02_L02_Beam_Geometry.py",
)
