"""
plot_helpers.py — Reusable drawing utilities for beam diagrams.

Introduced in Lesson 3. Extended in later lessons.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


# ---------------------------------------------------------------------------
# Beam diagram
# ---------------------------------------------------------------------------

def draw_beam(ax, geometry):
    """
    Draw the beam axis, supports (pin and roller), and shaded cantilever regions.

    Parameters
    ----------
    ax       : matplotlib Axes
    geometry : dict  {"L_total": float, "x_A": float, "x_B": float}
    """
    L   = geometry["L_total"]
    x_A = geometry["x_A"]
    x_B = geometry["x_B"]

    # Beam axis
    ax.plot([0, L], [0, 0], color="black", linewidth=4, solid_capstyle="round", zorder=3)

    # Shade cantilever regions
    if x_A > 0:
        ax.axvspan(0, x_A, alpha=0.08, color="orange", label="Left cantilever")
    if x_B < L:
        ax.axvspan(x_B, L, alpha=0.08, color="orange", label="Right cantilever")

    # Pin support at A (triangle, apex up)
    _draw_pin(ax, x_A)

    # Roller support at B (triangle + circle below)
    _draw_roller(ax, x_B)

    # Labels
    ax.text(x_A, -0.28, f"A\n({x_A:.1f} m)", ha="center", va="top", fontsize=8, color="#555")
    ax.text(x_B, -0.28, f"B\n({x_B:.1f} m)", ha="center", va="top", fontsize=8, color="#555")
    ax.text(0,    0.05, "0 m", ha="center", va="bottom", fontsize=7, color="#888")
    ax.text(L,    0.05, f"{L:.1f} m", ha="center", va="bottom", fontsize=7, color="#888")

    ax.set_xlim(-0.3, L + 0.3)
    ax.set_ylim(-0.6, 1.4)
    ax.axis("off")


def _draw_pin(ax, x):
    size = 0.18
    triangle = plt.Polygon(
        [[x, 0], [x - size, -size * 1.4], [x + size, -size * 1.4]],
        closed=True, facecolor="#888", edgecolor="black", linewidth=0.8, zorder=4
    )
    ax.add_patch(triangle)
    ax.plot([x - size * 1.3, x + size * 1.3], [-size * 1.4, -size * 1.4],
            color="black", linewidth=1.5, zorder=4)


def _draw_roller(ax, x):
    size = 0.18
    triangle = plt.Polygon(
        [[x, 0], [x - size, -size * 1.4], [x + size, -size * 1.4]],
        closed=True, facecolor="white", edgecolor="black", linewidth=0.8, zorder=4
    )
    ax.add_patch(triangle)
    circle = plt.Circle((x, -size * 1.4 - size * 0.55), size * 0.5,
                         facecolor="white", edgecolor="black", linewidth=0.8, zorder=4)
    ax.add_patch(circle)
    ax.plot([x - size * 1.3, x + size * 1.3],
            [-size * 1.4 - size * 1.1, -size * 1.4 - size * 1.1],
            color="black", linewidth=1.5, zorder=4)


# ---------------------------------------------------------------------------
# Load arrows
# ---------------------------------------------------------------------------

def draw_loads(ax, loads, L_total, arrow_height=0.9):
    """
    Draw all loads on the beam axis (point loads as arrows, UDLs as arrow arrays).

    Parameters
    ----------
    ax          : matplotlib Axes
    loads       : list of load dicts
    L_total     : float  (beam length, for UDL display scaling)
    arrow_height: float  (height of point load arrow in axis units)
    """
    for load in loads:
        if load["type"] == "point":
            _draw_point_load(ax, load["x"], load["magnitude"], arrow_height)
        elif load["type"] == "udl":
            _draw_udl(ax, load["x1"], load["x2"], load["w"], arrow_height)


def _draw_point_load(ax, x, magnitude, arrow_height):
    color = "#1565C0" if magnitude < 0 else "#B71C1C"
    label_y = arrow_height + 0.12 if magnitude > 0 else -arrow_height - 0.18
    tip_y   = 0.02 if magnitude < 0 else -0.02
    tail_y  = arrow_height if magnitude < 0 else -arrow_height

    ax.annotate(
        "", xy=(x, tip_y), xytext=(x, tail_y),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=1.8,
                        mutation_scale=14)
    )
    ax.text(x, label_y, f"{abs(magnitude):.0f} kN",
            ha="center", va="bottom", fontsize=8, color=color, fontweight="bold")


def _draw_udl(ax, x1, x2, w, arrow_height):
    color = "#1565C0" if w < 0 else "#B71C1C"
    n_arrows = max(3, int((x2 - x1) / 0.5))
    tip_y    = 0.02 if w < 0 else -0.02
    tail_y   = arrow_height * 0.75 if w < 0 else -arrow_height * 0.75

    for x_arr in np.linspace(x1, x2, n_arrows):
        ax.annotate("", xy=(x_arr, tip_y), xytext=(x_arr, tail_y),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.2,
                                   mutation_scale=10))
    ax.plot([x1, x2], [tail_y, tail_y], color=color, linewidth=2)
    ax.text((x1 + x2) / 2, tail_y + (0.12 if w < 0 else -0.18),
            f"{abs(w):.1f} kN/m", ha="center", va="bottom",
            fontsize=8, color=color, fontweight="bold")


# ---------------------------------------------------------------------------
# Reaction arrows
# ---------------------------------------------------------------------------

def draw_reactions(ax, x_A, x_B, R_A, R_B, scale=None):
    """
    Draw upward reaction arrows proportional to their magnitude.

    Parameters
    ----------
    ax         : matplotlib Axes
    x_A, x_B  : float  support positions
    R_A, R_B  : float  reaction values (positive = upward)
    scale      : float  pixels per kN; auto-scaled if None
    """
    max_R = max(abs(R_A), abs(R_B), 1e-3)
    if scale is None:
        scale = 0.8 / max_R

    for x_pos, R, label in [(x_A, R_A, f"R_A = {R_A:.1f} kN"),
                             (x_B, R_B, f"R_B = {R_B:.1f} kN")]:
        color  = "#2E7D32" if R >= 0 else "#C62828"
        # Upward reaction (R>0): tip just below beam, tail below → arrow points up
        # Downward reaction (R<0): tip just above beam, tail above → arrow points down
        tip_y  = -0.02 if R >= 0 else 0.02
        tail_y = -R * scale          # negative of R*scale: R>0 → tail below, R<0 → tail above
        ax.annotate("", xy=(x_pos, tip_y), xytext=(x_pos, tail_y),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=2.2,
                                   mutation_scale=16))
        va      = "top"    if R >= 0 else "bottom"
        label_y = tail_y + (-0.08 if R >= 0 else 0.08)
        ax.text(x_pos, label_y, label, ha="center", va=va, fontsize=8,
                color=color, fontweight="bold")


# ---------------------------------------------------------------------------
# SFD / BMD panels
# ---------------------------------------------------------------------------

def draw_sfd(ax, x, V, show_peaks=True):
    """Plot shear force diagram on the given Axes."""
    ax.plot(x, V, color="#1565C0", linewidth=1.8)
    ax.fill_between(x, V, 0, where=(V >= 0), color="#90CAF9", alpha=0.5)
    ax.fill_between(x, V, 0, where=(V < 0),  color="#EF9A9A", alpha=0.5)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Shear V (kN)", fontsize=9)
    ax.set_xlabel("Position x (m)", fontsize=9)
    ax.grid(True, linestyle="--", alpha=0.4)

    if show_peaks:
        _annotate_peak(ax, x, V, "V")


def draw_bmd(ax, x, M, show_peaks=True):
    """Plot bending moment diagram on the given Axes (sagging positive convention)."""
    ax.plot(x, M, color="#1B5E20", linewidth=1.8)
    ax.fill_between(x, M, 0, where=(M >= 0), color="#A5D6A7", alpha=0.5, label="Sagging (+)")
    ax.fill_between(x, M, 0, where=(M < 0),  color="#FFCDD2", alpha=0.5, label="Hogging (−)")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Moment M (kN·m)", fontsize=9)
    ax.set_xlabel("Position x (m)", fontsize=9)
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, linestyle="--", alpha=0.4)

    if show_peaks:
        _annotate_peak(ax, x, M, "M")


def _annotate_peak(ax, x, y, label):
    """Mark and label the maximum absolute value on a diagram."""
    idx = np.argmax(np.abs(y))
    ax.plot(x[idx], y[idx], "o", color="red", markersize=6, zorder=5)
    ax.annotate(
        f"{label}_max = {y[idx]:.1f}",
        xy=(x[idx], y[idx]),
        xytext=(x[idx] + 0.3, y[idx]),
        fontsize=8, color="red",
        arrowprops=dict(arrowstyle="->", color="red", lw=0.8)
    )
