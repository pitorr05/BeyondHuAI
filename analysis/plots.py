"""Plots with explicit destinations; no manuscript discovery or artwork rendering."""

import json
from pathlib import Path
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize


def save(fig, output, name):
    for suffix in ["pdf", "png"]:
        fig.savefig(
            Path(output) / (name + "." + suffix),
            dpi=180,
            bbox_inches="tight",
            pad_inches=0.04,
        )
    plt.close(fig)


def heat(ax, frame, field, norm, title):
    table = frame.pivot(
        index="model_layer", columns="token_position", values=field
    ).sort_index()
    if table.isna().any().any():
        raise ValueError("Incomplete layer/position grid")
    im = ax.imshow(
        table.to_numpy(),
        origin="lower",
        aspect="auto",
        interpolation="nearest",
        norm=norm,
        cmap="RdBu_r",
        rasterized=True,
    )
    iy = np.linspace(0, len(table) - 1, min(5, len(table))).round().astype(int)
    ix = (
        np.linspace(0, len(table.columns) - 1, min(5, len(table.columns)))
        .round()
        .astype(int)
    )
    ax.set_yticks(iy, [str(table.index[i]) for i in iy])
    ax.set_xticks(ix, [str(table.columns[i]) for i in ix])
    ax.set(xlabel="Token position (zero-based)", ylabel="Layer", title=title)
    return im


def render_run(layer, cell, output):
    fields = [
        "human_mean_activation",
        "llm_mean_activation",
        "difference_llm_minus_human",
        "difference_absolute_activation",
        "difference_rms_activation",
        "cohens_d",
    ]
    with plt.rc_context({"font.size": 8, "pdf.fonttype": 42}):
        fig, axes = plt.subplots(3, 2, figsize=(8, 8), layout="constrained")
        shared = float(np.abs(cell[fields[:2]].to_numpy()).max())
        for i, (ax, field) in enumerate(zip(axes.flat, fields)):
            limit = max(shared if i < 2 else float(cell[field].abs().max()), 1e-12)
            im = heat(
                ax, cell, field, Normalize(-limit, limit), field.replace("_", " ")
            )
            fig.colorbar(im, ax=ax, fraction=0.04)
        save(fig, output, "activation_insights")
        fig, ax = plt.subplots(figsize=(5.5, 5))
        f = layer.sort_values("model_layer")
        ax.hlines(
            f.model_layer,
            f.bootstrap_95ci_low_difference,
            f.bootstrap_95ci_high_difference,
            color="#3479a8",
            lw=0.9,
        )
        ax.scatter(f.difference_llm_minus_human, f.model_layer, color="#144c76", s=12)
        ax.axvline(0, color="#777777", lw=0.7)
        ax.set(xlabel="Signed mean difference (LLM - human)", ylabel="Layer")
        save(fig, output, "layer_effects")


def render_archived(layers, cells, tables, output):
    audit = {}
    overview = tables["Table_1_Experimental_Overview.csv"]
    with plt.rc_context(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    ):
        exps = [
            f"{dataset}-{size}-n{n}"
            for size in ["0.5B", "1.5B", "7B"]
            for dataset, n in [("DetectRL", 274), ("HC3", 500)]
        ]
        for field, stem in [
            ("cohens_d", "diagnostic_cell_contrasts"),
            ("difference_llm_minus_human", "diagnostic_signed_maps"),
        ]:
            frames = [cells[cells.experiment == e] for e in exps]
            limit = max(float(f[field].abs().max()) for f in frames)
            fig, axes = plt.subplots(3, 2, figsize=(7.1, 6), layout="constrained")
            for ax, frame, exp in zip(axes.flat, frames, exps):
                im = heat(ax, frame, field, Normalize(-limit, limit), exp)
            fig.colorbar(
                im,
                ax=list(axes.flat),
                location="bottom",
                fraction=0.035,
                label=field.replace("_", " "),
            )
            save(fig, output, stem)
            audit[stem] = {"limits": [-limit, limit], "clipped_cells": 0}
        exps7 = ["HC3-7B-n500", "DetectRL-7B-n274", "RAID-7B-n500"]
        fig, axes = plt.subplots(3, 2, figsize=(7.1, 6), layout="constrained")
        for col, field in enumerate(
            ["difference_absolute_activation", "difference_rms_activation"]
        ):
            frames = [cells[cells.experiment == e] for e in exps7]
            limit = max(float(f[field].abs().max()) for f in frames)
            for row, (frame, exp) in enumerate(zip(frames, exps7)):
                im = heat(axes[row, col], frame, field, Normalize(-limit, limit), exp)
            fig.colorbar(
                im,
                ax=list(axes[:, col]),
                location="bottom",
                fraction=0.035,
                label=field.replace("_", " "),
            )
        save(fig, output, "diagnostic_magnitude_maps")
        frame = cells[cells.experiment == "HC3-7B-n500"]
        fig, axes = plt.subplots(2, 2, figsize=(7.1, 4.6), layout="constrained")
        for ax, field in zip(
            axes.flat,
            [
                "difference_llm_minus_human",
                "difference_absolute_activation",
                "difference_rms_activation",
                "cohens_d",
            ],
        ):
            limit = float(frame[field].abs().max())
            im = heat(
                ax, frame, field, Normalize(-limit, limit), field.replace("_", " ")
            )
            fig.colorbar(im, ax=ax, fraction=0.035)
        save(fig, output, "diagnostic_complete_hc3_7b")
        fig, axes = plt.subplots(
            1, 3, figsize=(7.1, 4.3), sharey=True, layout="constrained"
        )
        for ax, exp in zip(axes, exps7):
            f = layers[layers.experiment == exp].sort_values("model_layer")
            ax.hlines(
                f.model_layer,
                f.bootstrap_95ci_low_difference,
                f.bootstrap_95ci_high_difference,
                color="#3479a8",
                lw=0.8,
            )
            ax.scatter(
                f.difference_llm_minus_human, f.model_layer, color="#144c76", s=9
            )
            ax.axvline(0, color="#777777", lw=0.7)
            ax.set(title=exp, xlabel="Signed mean difference\n(LLM - human)")
            ax.grid(axis="y", alpha=0.12)
        axes[0].set_ylabel("Layer")
        save(fig, output, "diagnostic_layer_intervals_7b")
        fig, axes = plt.subplots(1, 3, figsize=(9, 3), layout="constrained")
        for ax, size in zip(axes, ["0.5B", "1.5B", "7B"]):
            experiments = (
                [f"DetectRL-{size}-n274"]
                + (["HC3-0.5B-n200"] if size == "0.5B" else [])
                + [f"HC3-{size}-n500"]
            )
            for color, exp in zip(["#25618b", "#bf712e", "#517a53"], experiments):
                f = layers[layers.experiment == exp].sort_values("model_layer")
                ax.plot(f.model_layer, f.cohens_d, label=exp, color=color, lw=1)
            ax.axhline(0, color="#888888", lw=0.5)
            ax.set(title="Qwen2.5 " + size, xlabel="Layer")
            ax.legend(fontsize=6)
        axes[0].set_ylabel("Layer-wise Cohen's d")
        save(fig, output, "Figure_A_Layer_Effect_Profiles")
        transfer = tables["Table_3_Layer_Profile_Transfer.csv"]
        f = transfer[
            transfer.experiment_a.str.startswith("DetectRL")
            & transfer.experiment_b.str.endswith("n500")
            & transfer.experiment_b.str.startswith("HC3")
        ]
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.bar(f.backbone, f.pearson_r, color="#25618b")
        ax.set(
            ylabel="Pearson correlation",
            ylim=(-0.2, 1.05),
            title="HC3–DetectRL layer-profile alignment",
        )
        save(fig, output, "Figure_B_Cross_Dataset_Stability")
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.bar(
            overview.experiment,
            overview.fraction_layers_ci_exclude_zero,
            color="#25618b",
        )
        ax.tick_params(axis="x", labelrotation=45, labelsize=6)
        ax.set(
            ylabel="Fraction of layers",
            ylim=(0, 1),
            title="Unadjusted intervals excluding zero",
        )
        save(fig, output, "Figure_C_Layer_CI_Coverage")
    (Path(output) / "figure_audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )
