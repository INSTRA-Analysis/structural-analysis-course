"""
InstraHub website — Flask development server.
Run:    python app.py
Browse: http://localhost:5000

InstraHub is the parent platform. It is organised into sections, each a Flask
blueprint so new sections (apps, services, …) can be added without disturbing
the others:

  hub      — the InstraHub platform: landing, about, section stubs   (/)
  academy  — INSTRA Academy: courses, the beam tool, Pyodide source  (/instra-academy)

The original flat /courses/... URLs are kept as permanent (301) redirects into
the academy blueprint so existing links and bookmarks never break.
"""

import os
from flask import (Flask, Blueprint, render_template, redirect,
                   url_for, abort, Response)

# ── Shared Python source served to the in-browser Pyodide tool ──────────────
SHARED_DIR = os.path.join(os.path.dirname(__file__), "..", "course", "shared")
PYSRC_WHITELIST = {"beam_solver.py", "notebook_generator.py"}

# ── Full INSTRA Academy curriculum ──────────────────────────────────────────
# Ordered by complexity: each course adds one new conceptual layer
# (DOFs, dimensions, or physics) without skipping steps.

COURSES = [

    # ── Beginner ───────────────────────────────────────────────────────────
    {
        "slug": "simply-supported-beam",
        "title": "Simply Supported Beam Analysis",
        "subtitle": "Interactive tool · Beginner · Free",
        "description": (
            "Build and use a complete beam analysis tool right in your browser — "
            "reactions, shear, bending moment and deflection — then write the Python "
            "behind it yourself. No prior Python knowledge required."
        ),
        "tags": ["Free", "Python", "Interactive", "Deflection", "Notebook"],
        "status": "available",
        "format": "Interactive tool",
        "lessons": 7,
        "level": "Beginner",
        "duration": "~2 hours",
        "dof": "— (equilibrium, no matrix)",
        "topics": [
            "Set up an overhanging beam — span, cantilevers and support positions — with live diagrams",
            "Apply point loads and a UDL using the correct sign convention",
            "Compute reactions, shear, bending moment and deflection, with diagrams",
            "Write the Python yourself — from filling blanks to rebuilding the solver",
            "Size the most economical section against deflection and bending-strength limits",
            "Export a self-contained Jupyter notebook of your model and analysis",
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


# ── InstraHub Apps catalogue ────────────────────────────────────────────────
# Native/desktop apps surfaced on InstraHub; the binaries are hosted on GitHub
# Releases (InstraHub is the storefront/landing, GitHub hosts the download).
STRUCTLAB = {
    "slug":         "structlab",
    "name":         "StructLab",
    "badge":        "by InstraHub",
    "tagline":      ("A 2D/3D structural analysis desktop app built on the Direct Stiffness "
                     "Method — frames, beams, trusses and design checks in one unified solver."),
    "version":      "v1.0.0",
    "platform":     "Windows",
    "license":      "GPL-3.0 · Free & open source",
    "repo_url":     "https://github.com/INSTRA-Analysis/StructLabApp",
    "releases_url": "https://github.com/INSTRA-Analysis/StructLabApp/releases/latest",
    "status":       "available",
}

APPS = [STRUCTLAB]


# ════════════════════════════════════════════════════════════════════════════
# Hub blueprint — the InstraHub platform
# ════════════════════════════════════════════════════════════════════════════
hub = Blueprint("hub", __name__)


@hub.route("/")
def index():
    return render_template("hub/index.html", courses=COURSES)


@hub.route("/about")
def about():
    return render_template("hub/about.html")


@hub.route("/apps")
def apps():
    return render_template("hub/apps.html", apps=APPS)


@hub.route("/apps/structlab")
def structlab():
    return render_template("hub/structlab.html", app=STRUCTLAB)


@hub.route("/services")
def services():
    return render_template(
        "hub/coming_soon.html",
        eyebrow="InstraHub · Services",
        title="Services",
        blurb=("Consulting and bespoke engineering software — built by practising "
               "structural engineers. Coming soon."),
    )


# ════════════════════════════════════════════════════════════════════════════
# Academy blueprint — INSTRA Academy (courses + the interactive tool)
# ════════════════════════════════════════════════════════════════════════════
academy = Blueprint("academy", __name__, url_prefix="/instra-academy")


@academy.route("/")
def home():
    return render_template("academy/index.html", courses=COURSES)


@academy.route("/courses")
def courses():
    return render_template("academy/courses.html", courses=COURSES)


@academy.route("/about")
def about():
    return render_template("academy/about.html")


@academy.route("/courses/simply-supported-beam")
def course_beam():
    course = next(c for c in COURSES if c["slug"] == "simply-supported-beam")
    return render_template("academy/course_beam.html", course=course)


@academy.route("/courses/simply-supported-beam/tool")
def course_beam_tool():
    """The in-house interactive beam analysis tool (Pyodide, client-side)."""
    return render_template("academy/beam_tool.html")


@academy.route("/courses/simply-supported-beam/tool/pysrc/<path:name>")
def beam_tool_pysrc(name):
    """
    Serve the canonical Python source modules to Pyodide running in the browser.
    Whitelisted to the shared physics/notebook modules only.
    """
    if name not in PYSRC_WHITELIST:
        abort(404)
    path = os.path.join(SHARED_DIR, name)
    if not os.path.isfile(path):
        abort(404)
    with open(path, "r", encoding="utf-8") as fh:
        return Response(fh.read(), mimetype="text/plain; charset=utf-8")


# ════════════════════════════════════════════════════════════════════════════
# App + legacy redirects
# ════════════════════════════════════════════════════════════════════════════
app = Flask(__name__)
app.register_blueprint(hub)
app.register_blueprint(academy)


# The original flat URLs are already public — 301-redirect them into the academy
# section so existing links, bookmarks and search results keep working.
@app.route("/courses")
def _legacy_courses():
    return redirect(url_for("academy.courses"), code=301)


@app.route("/courses/simply-supported-beam")
def _legacy_course_beam():
    return redirect(url_for("academy.course_beam"), code=301)


@app.route("/courses/simply-supported-beam/tool")
def _legacy_course_beam_tool():
    return redirect(url_for("academy.course_beam_tool"), code=301)


# ── Dev server ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
