"""
INSTRA website — Flask development server.
Run: python app.py
Browse: http://localhost:5000
"""

import os
from flask import Flask, render_template, abort, Response

app = Flask(__name__)

# ── Config ─────────────────────────────────────────────────────────────────
# The beam tool now runs in-house (Pyodide, client-side) — no external Streamlit
# app. The canonical Python physics lives in ../course/shared and is served to
# the browser via the whitelisted `pysrc` route below.
SHARED_DIR = os.path.join(os.path.dirname(__file__), "..", "course", "shared")

# Only these modules may be fetched into Pyodide — never an arbitrary path.
PYSRC_WHITELIST = {"beam_solver.py", "notebook_generator.py"}

# ── Full INSTRA Academy curriculum ──────────────────────────────────────────
# Ordered by complexity: each course adds one new conceptual layer
# (DOFs, dimensions, or physics) without skipping steps.

COURSES = [

    # ── Beginner ───────────────────────────────────────────────────────────
    {
        "slug": "simply-supported-beam",
        "title": "Simply Supported Beam Analysis",
        "subtitle": "7 lessons · Beginner · Free",
        "description": (
            "Build a complete beam analysis tool from scratch in Python. "
            "Reactions, shear force, bending moment — all with live interactive widgets. "
            "No prior Python knowledge required."
        ),
        "tags": ["Free", "Python", "Reactions", "SFD", "BMD"],
        "status": "available",
        "lessons": 7,
        "level": "Beginner",
        "duration": "~4 hours",
        "dof": "— (equilibrium, no matrix)",
        "topics": [
            "Python variables, functions, and NumPy arrays",
            "Beam geometry — span, cantilevers, support positions",
            "Point loads and UDL — sign convention and placement",
            "Support reactions from equilibrium (ΣFy = 0, ΣM = 0)",
            "Shear Force Diagram from first principles",
            "Bending Moment Diagram by numerical integration",
            "Complete parametric analysis tool with PDF export",
        ],
    },
    {
        "slug": "2d-truss",
        "title": "2D Truss Analysis",
        "subtitle": "Coming soon · Beginner",
        "description": (
            "Introduction to the Direct Stiffness Method using the simplest structural element. "
            "Build a 2D pin-jointed truss assembler — local stiffness matrices, coordinate "
            "transformation, global assembly, and member force recovery. No bending, "
            "so every concept is as clear as it can be."
        ),
        "tags": ["Python", "Direct Stiffness Method", "Truss", "Matrix Assembly"],
        "status": "coming_soon",
        "lessons": None,
        "level": "Beginner",
        "duration": None,
        "dof": "2 DOF/node (u, v) — axial only",
        "topics": [],
    },

    # ── Intermediate ────────────────────────────────────────────────────────
    {
        "slug": "continuous-beam",
        "title": "Continuous Beam Analysis",
        "subtitle": "Coming soon · Intermediate",
        "description": (
            "Extend from single-span to multi-span beams using the Euler-Bernoulli beam element. "
            "Assemble the global stiffness matrix, apply internal supports and settlement, "
            "and extract reactions, rotations, and moment diagrams for continuous structures."
        ),
        "tags": ["Python", "Direct Stiffness Method", "Continuous Beam", "Euler-Bernoulli"],
        "status": "coming_soon",
        "lessons": None,
        "level": "Intermediate",
        "duration": None,
        "dof": "2 DOF/node (w, θ) — bending + rotation",
        "topics": [],
    },
    {
        "slug": "2d-portal-frame",
        "title": "2D Portal Frame Analysis",
        "subtitle": "Coming soon · Intermediate",
        "description": (
            "Combine axial and bending behaviour in a single 2D frame element. "
            "Assemble portal frames with sway, apply horizontal and vertical loads, "
            "and extract the full shear, axial force, and bending moment diagrams."
        ),
        "tags": ["Python", "FEM", "Portal Frame", "Sway Analysis", "2D Transformation"],
        "status": "coming_soon",
        "lessons": None,
        "level": "Intermediate",
        "duration": None,
        "dof": "3 DOF/node (u, v, θ) — axial + bending",
        "topics": [],
    },

    # ── Advanced ────────────────────────────────────────────────────────────
    {
        "slug": "3d-space-frame",
        "title": "3D Space Frame with Truss Roof",
        "subtitle": "Coming soon · Advanced",
        "description": (
            "Step into three dimensions. Build a 3D frame with a pin-jointed truss roof — "
            "6 DOF per node, full 3D element transformation matrices, and combined "
            "frame/truss behaviour in a single global model."
        ),
        "tags": ["Python", "3D FEM", "Space Frame", "Truss Roof", "6-DOF"],
        "status": "coming_soon",
        "lessons": None,
        "level": "Advanced",
        "duration": None,
        "dof": "6 DOF/node (u, v, w, θx, θy, θz) — full 3D",
        "topics": [],
    },
    {
        "slug": "3d-moment-frame",
        "title": "3D Moment Frame",
        "subtitle": "Coming soon · Advanced",
        "description": (
            "Full 3D moment-resisting frame analysis under gravity and lateral loads. "
            "Apply code-based load combinations, extract displacement envelopes, "
            "and check inter-storey drift against design limits."
        ),
        "tags": ["Python", "3D FEM", "Moment Frame", "Lateral Loads", "Code Checks"],
        "status": "coming_soon",
        "lessons": None,
        "level": "Advanced",
        "duration": None,
        "dof": "6 DOF/node — full moment continuity",
        "topics": [],
    },
    {
        "slug": "structural-dynamics",
        "title": "Structural Dynamics",
        "subtitle": "Coming soon · Advanced",
        "description": (
            "From SDOF oscillator to multi-storey building. Compute natural frequencies "
            "and mode shapes via eigenvalue analysis, then apply the response spectrum "
            "method for seismic loading. Modal superposition visualised interactively."
        ),
        "tags": ["Python", "Dynamics", "Modal Analysis", "Eigenvalues", "Seismic"],
        "status": "coming_soon",
        "lessons": None,
        "level": "Advanced",
        "duration": None,
        "dof": "6 DOF/node + time domain",
        "topics": [],
    },
]


# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", courses=COURSES)


@app.route("/courses")
def courses():
    return render_template("courses.html", courses=COURSES)


@app.route("/courses/simply-supported-beam")
def course_beam():
    course = next(c for c in COURSES if c["slug"] == "simply-supported-beam")
    return render_template("course_beam.html", course=course)


@app.route("/courses/simply-supported-beam/tool")
def course_beam_tool():
    """The in-house interactive beam analysis tool (Pyodide, client-side)."""
    return render_template("beam_tool.html")


@app.route("/courses/simply-supported-beam/tool/pysrc/<path:name>")
def beam_tool_pysrc(name):
    """
    Serve the canonical Python source modules to Pyodide running in the browser.

    Whitelisted to the shared physics/notebook modules only — `name` is matched
    against PYSRC_WHITELIST so no arbitrary file can be read.
    """
    if name not in PYSRC_WHITELIST:
        abort(404)
    path = os.path.join(SHARED_DIR, name)
    if not os.path.isfile(path):
        abort(404)
    with open(path, "r", encoding="utf-8") as fh:
        source = fh.read()
    # text/plain so the browser fetch() returns the raw source for Pyodide.FS.
    return Response(source, mimetype="text/plain; charset=utf-8")


@app.route("/about")
def about():
    return render_template("about.html")


# ── Dev server ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)
