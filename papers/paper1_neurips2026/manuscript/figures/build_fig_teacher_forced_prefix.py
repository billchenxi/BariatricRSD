"""Explanatory figure for the teacher-forced prefix workflow-token variant.

Shows the two-stage offline pipeline used to assign a cluster ID to every
clip:
  Stage 1 (once, on training set): videos → phase-bigram TF-IDF → PCA →
    k-means → K centroids (frozen artifacts).
  Stage 2 (precomputed per (video, t)): take ground-truth phases from
    start to t, project through the frozen Stage-1 pipeline, snap to
    nearest centroid → integer cluster ID stored in a lookup table.

At training/inference the model just performs an O(1) lookup. The
"teacher" is the ground-truth phase labels driving Stage 2; the "force"
is that the model has no say in the cluster ID; the "prefix" is that
only phases observed up to t are used (not the full video).

Output:
  paper/figures/fig_teacher_forced_prefix.{png,pdf}
  paper/Formatting_Instructions_For_NeurIPS_2026/figures/fig_teacher_forced_prefix.{png,pdf}
"""
from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.path import Path as MplPath


HERE = Path(__file__).parent
ROOT = HERE.parent.parent
SUB = ROOT / "paper" / "Formatting_Instructions_For_NeurIPS_2026" / "figures"

CLUSTER_COLORS = ["#1d4ed8", "#0d9488", "#d97706", "#7c3aed", "#dc2626", "#0891b2"]


plt.rcParams.update({
    "figure.dpi": 180,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "font.family": "DejaVu Sans",
    "font.size": 8.0,
    "axes.labelsize": 8.4,
    "axes.titlesize": 9.2,
    "xtick.labelsize": 7.6,
    "ytick.labelsize": 7.6,
    "legend.fontsize": 7.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def stage1_panel(ax):
    """Schematic of Stage 1: build frozen cluster pipeline once on training set."""
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    ax.set_title("Stage 1 (offline, once on training set)", loc="left", fontweight="bold", pad=4)

    boxes = [
        (0.2, "N training\nvideos\n(full phase\nsequence)"),
        (2.1, "Phase-bigram\nTF-IDF\nvectorize"),
        (4.1, "PCA"),
        (5.6, "k-means\n(K = 6 for MB140,\nK = 4 for Cholec80)"),
        (8.1, "Frozen\nartifacts:\nvocab, IDF,\nPCA basis,\ncentroids"),
    ]
    widths = [1.6, 1.7, 1.2, 2.2, 1.7]
    y_center = 3.1
    for (x, label), w in zip(boxes, widths):
        face = "#e0f2fe" if "Frozen" in label else "#f8fafc"
        edge = "#0369a1" if "Frozen" in label else "#475569"
        bbox = FancyBboxPatch(
            (x, y_center - 1.0), w, 2.0,
            boxstyle="round,pad=0.05,rounding_size=0.12",
            facecolor=face, edgecolor=edge, linewidth=1.0,
        )
        ax.add_patch(bbox)
        ax.text(x + w / 2, y_center, label, ha="center", va="center", fontsize=7.6)

    arrow_starts = [(0.2 + 1.6, y_center), (2.1 + 1.7, y_center), (4.1 + 1.2, y_center), (5.6 + 2.2, y_center)]
    arrow_ends = [(2.1, y_center), (4.1, y_center), (5.6, y_center), (8.1, y_center)]
    for s, e in zip(arrow_starts, arrow_ends):
        ax.annotate("", xy=e, xytext=s,
                    arrowprops=dict(arrowstyle="->", color="#475569", lw=1.0))

    ax.text(5.0, 5.7, "Builds the cluster model. Run once. Frozen for the rest of the experiment.",
            ha="center", va="center", fontsize=7.4, color="#0f172a", style="italic")


def stage2_panel(ax, prefix_traj, centroids, cluster_traj, video_phases):
    """Stage 2 example: one video's projection wandering through centroid space."""
    ax.set_title(r"Stage 2 (precomputed per (video, $t$))   $-$   one example video",
                 loc="left", fontweight="bold", pad=4)
    K = centroids.shape[0]

    for k in range(K):
        ax.scatter(*centroids[k], s=420, marker="*", color=CLUSTER_COLORS[k],
                   edgecolor="black", linewidth=0.7, zorder=4)
        ax.text(centroids[k, 0] + 0.14, centroids[k, 1] + 0.10, f"k={k}",
                fontsize=7.2, color=CLUSTER_COLORS[k], fontweight="bold", zorder=5)

    ax.plot(prefix_traj[:, 0], prefix_traj[:, 1], color="#94a3b8",
            linewidth=1.3, alpha=0.7, zorder=2)

    sample_idx = np.linspace(0, len(prefix_traj) - 1, 5).astype(int)
    sample_labels = [r"$t_1$", r"$t_2$", r"$t_3$", r"$t_4$", r"$t_5$"]
    for idx, lab in zip(sample_idx, sample_labels):
        x, y = prefix_traj[idx]
        c = CLUSTER_COLORS[cluster_traj[idx]]
        ax.scatter(x, y, s=46, color=c, edgecolor="black", linewidth=0.5, zorder=5)
        ax.annotate(lab, xy=(x, y), xytext=(8, 8), textcoords="offset points",
                    fontsize=7.6, color="#0f172a")

    ax.set_xlabel("PCA dim 1")
    ax.set_ylabel("PCA dim 2")
    ax.grid(True, color="#e5e7eb", linewidth=0.7)
    ax.set_xlim(-2.6, 2.7)
    ax.set_ylim(-2.5, 2.6)

    # Inline legend INSIDE the panel (top-left area is empty)
    inset_text = (
        "Prefix at each $t$ (ground truth):\n"
        r"  $t_1$: Prep" + "\n"
        r"  $t_2$: Prep $\to$ Calot" + "\n"
        r"  $t_3$: Prep $\to$ Calot $\to$ Clip" + "\n"
        r"  $t_4$: + GB-Diss" + "\n"
        r"  $t_5$: + GB-Pkg"
    )
    ax.text(
        -2.45, 2.45, inset_text,
        ha="left", va="top", fontsize=6.8, color="#0f172a",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#f8fafc",
                  edgecolor="#cbd5e1", linewidth=0.7),
    )


def cluster_id_timeline_panel(ax, cluster_traj, oracle_id):
    """Show how cluster ID evolves over time vs the fixed oracle ID."""
    ax.set_title("Resulting workflow token over time", loc="left", fontweight="bold", pad=4)
    t = np.arange(len(cluster_traj))

    # teacher-forced prefix path
    ax.step(t, cluster_traj, where="post", color="#0d9488", linewidth=1.6,
            label="teacher-forced prefix\n(re-derived per clip)", zorder=3)
    for ti, ci in zip(t, cluster_traj):
        ax.scatter(ti, ci, s=18, color=CLUSTER_COLORS[ci], edgecolor="black",
                   linewidth=0.3, zorder=4)

    # oracle line (fixed for whole video)
    ax.axhline(oracle_id, color="#1d4ed8", linewidth=1.2, linestyle="--",
               label=f"oracle (full-video) = cluster {oracle_id}", zorder=2)

    ax.set_xlim(-0.5, len(cluster_traj) - 0.5)
    ax.set_ylim(-0.5, 5.5)
    ax.set_yticks(range(6))
    ax.set_yticklabels([f"k={i}" for i in range(6)])
    ax.set_xlabel("clip end time $t$  (clips along the surgery)")
    ax.set_ylabel("workflow token = cluster ID")
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.7)
    ax.legend(loc="lower right", frameon=False, handletextpad=0.5)

    # Annotate the change-points
    diff_idx = np.where(np.diff(cluster_traj) != 0)[0] + 1
    for di in diff_idx:
        ax.annotate("flip", xy=(di, cluster_traj[di]), xytext=(di, cluster_traj[di] + 0.55),
                    ha="center", fontsize=6.6, color="#7c2d12",
                    arrowprops=dict(arrowstyle="-", color="#7c2d12", lw=0.6))


def lookup_panel(ax):
    """Show the runtime O(1) table-lookup that the training loop performs."""
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.set_title("Training / inference: O(1) lookup, no online clustering", loc="left", fontweight="bold", pad=4)

    # Lookup table
    bbox = FancyBboxPatch((0.3, 0.6), 4.0, 2.8,
                          boxstyle="round,pad=0.05,rounding_size=0.12",
                          facecolor="#fef3c7", edgecolor="#b45309", linewidth=1.0)
    ax.add_patch(bbox)
    ax.text(2.3, 3.1, "prefix_clusters.json", ha="center", fontsize=8.0, fontweight="bold", color="#7c2d12")
    ax.text(2.3, 2.7, "(precomputed, ~2 MB)", ha="center", fontsize=7.0, color="#7c2d12", style="italic")
    rows = [
        '"0|0"   → 2',
        '"0|5"   → 2',
        '"0|10"  → 5',
        '"0|15"  → 5',
        '"0|20"  → 5',
        '   ...',
        '"139|22500" → 4',
    ]
    for i, row in enumerate(rows):
        ax.text(0.55, 2.4 - i * 0.27, row, ha="left", fontsize=7.0, family="monospace", color="#0f172a")

    # Arrow → embedding lookup
    ax.annotate("", xy=(5.5, 2.0), xytext=(4.4, 2.0),
                arrowprops=dict(arrowstyle="->", color="#475569", lw=1.2))
    ax.text(4.95, 2.2, "look up", ha="center", fontsize=7.0, color="#475569")

    # Embedding table
    bbox2 = FancyBboxPatch((5.5, 0.6), 4.2, 2.8,
                           boxstyle="round,pad=0.05,rounding_size=0.12",
                           facecolor="#dbeafe", edgecolor="#1e40af", linewidth=1.0)
    ax.add_patch(bbox2)
    ax.text(7.6, 3.1, "Learned embedding table  $\\mathbf{E} \\in \\mathbb{R}^{K \\times 768}$",
            ha="center", fontsize=8.0, fontweight="bold", color="#1e3a8a")
    for k in range(6):
        ax.scatter(5.95, 2.45 - k * 0.30, s=58, color=CLUSTER_COLORS[k],
                   edgecolor="black", linewidth=0.4)
        ax.text(6.20, 2.45 - k * 0.30, f"row k={k}: 768-dim cluster embedding",
                ha="left", va="center", fontsize=7.0, color="#0f172a")
    ax.text(7.6, 0.35,
            "Output: workflow token  $\\mathbf{e}_z = \\mathbf{E}[z, :]$  ($z$ from lookup)",
            ha="center", fontsize=7.4, color="#0f172a")


def main():
    rng = np.random.default_rng(7)

    # --- synthetic Stage-2 example ----------------------------------------
    # K = 6 centroids in 2D PCA space (rough mock-up of MB140 fold-0 cluster geometry)
    centroids = np.array([
        [-1.6,  0.9],   # k=0
        [-0.7, -1.2],   # k=1
        [ 0.4,  1.5],   # k=2
        [ 1.4, -0.4],   # k=3
        [-0.1,  0.0],   # k=4
        [ 1.1,  1.1],   # k=5
    ])

    # A prefix trajectory that wanders: starts near k=2, drifts toward k=4, ends near k=5
    n_steps = 16
    waypoints = np.array([
        centroids[2] + np.array([0.18, -0.10]),
        centroids[2] + np.array([0.10, -0.30]),
        centroids[4] + np.array([-0.20, 0.30]),
        centroids[4] + np.array([0.10, 0.05]),
        centroids[5] + np.array([-0.20, 0.05]),
        centroids[5] + np.array([0.05, -0.10]),
    ])
    # Smooth interpolation between waypoints
    ts = np.linspace(0, 1, n_steps)
    waypoint_ts = np.linspace(0, 1, len(waypoints))
    prefix_traj = np.stack([
        np.interp(ts, waypoint_ts, waypoints[:, 0]),
        np.interp(ts, waypoint_ts, waypoints[:, 1]),
    ], axis=1)
    prefix_traj += rng.normal(0, 0.05, prefix_traj.shape)

    # Assign each prefix to its nearest centroid
    cluster_traj = np.argmin(
        np.linalg.norm(prefix_traj[:, None, :] - centroids[None, :, :], axis=2),
        axis=1,
    )

    oracle_id = 5  # full-video cluster of this example surgery

    # Made-up phase-name list for the legend (Cholec-ish phases for illustration)
    phases = ["Prep", "Calot", "Clip", "GB-Diss", "GB-Pkg", "Clean", "GB-Retr"]

    # --- figure -----------------------------------------------------------
    fig = plt.figure(figsize=(10.8, 7.4))
    gs = fig.add_gridspec(
        nrows=3, ncols=2,
        height_ratios=[0.7, 1.5, 0.95],
        width_ratios=[1.15, 1.0],
        wspace=0.30, hspace=0.55,
        left=0.06, right=0.98, top=0.95, bottom=0.06,
    )

    ax_stage1 = fig.add_subplot(gs[0, :])
    stage1_panel(ax_stage1)

    ax_pca = fig.add_subplot(gs[1, 0])
    stage2_panel(ax_pca, prefix_traj, centroids, cluster_traj, phases)

    ax_time = fig.add_subplot(gs[1, 1])
    cluster_id_timeline_panel(ax_time, cluster_traj, oracle_id)

    ax_lookup = fig.add_subplot(gs[2, :])
    lookup_panel(ax_lookup)

    fig.text(
        0.5, 0.005,
        "Teacher-forced = the ground-truth phase labels (the “teacher”) drive Stage 2; the model has no say in the cluster ID.  "
        "Prefix = phases observed from start to $t$, not full video.  "
        "On a workflow-heterogeneous benchmark (MB140), prefix-cluster flips track real procedural variation; on a workflow-homogeneous one (Cholec80), they are mostly noise.",
        ha="center", fontsize=6.9, color="#374151",
    )

    SUB.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        out = HERE / f"fig_teacher_forced_prefix.{ext}"
        fig.savefig(out)
        shutil.copy2(out, SUB / out.name)
        print(f"wrote {out} and {SUB / out.name}")


if __name__ == "__main__":
    main()
