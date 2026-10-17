cd /data/SWIFT/aceGoc || exit 1

cat > vis/repre_insight.py <<'PY'
import argparse
import csv
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from tqdm import tqdm

from repre_vis import load_model_and_tokenizer


def select_texts(records, field, tokenizer, sample_size, truncate_len):
    texts = [
        r[field] for r in records
        if isinstance(r.get(field), str) and r[field].strip()
    ]
    # Giữ quy tắc sắp xếp theo độ dài như code RepreGuard gốc.
    texts.sort(key=len, reverse=True)

    selected = []
    for text in texts:
        ids = tokenizer(
            text, add_special_tokens=True, truncation=False
        )["input_ids"]
        if len(ids) >= truncate_len:
            selected.append(text)
        if len(selected) >= sample_size:
            break

    if len(selected) < sample_size:
        raise ValueError(
            f"{field}: chỉ có {len(selected)} mẫu đủ {truncate_len} token, "
            f"không đủ {sample_size}. Hãy giảm --sample_size."
        )
    return selected


def extract_activations(texts, extractor, hidden_layers, truncate_len, label):
    # Ba thống kê: mean có dấu (theo code gốc), mean absolute và RMS.
    result = {"mean": [], "abs": [], "rms": []}

    for text in tqdm(texts, desc=f"Extract {label}"):
        hs = extractor.batched_string_to_hiddens(
            train_inputs=[text],
            rep_token=0,
            hidden_layers=hidden_layers,
            batch_size=1,
            which_hidden_states=None
        )

        rows_mean, rows_abs, rows_rms = [], [], []
        for layer in hidden_layers:
            x = np.asarray(hs[layer])[0, :truncate_len, :]
            if x.shape[0] != truncate_len:
                raise ValueError(
                    f"{label}: nhận được {x.shape[0]} token, "
                    f"cần {truncate_len}. Kiểm tra tokenizer."
                )

            x = x.astype(np.float32, copy=False)
            rows_mean.append(x.mean(axis=-1, dtype=np.float32))
            rows_abs.append(np.abs(x).mean(axis=-1, dtype=np.float32))
            rows_rms.append(
                np.sqrt(np.mean(x * x, axis=-1, dtype=np.float32))
            )

        result["mean"].append(np.stack(rows_mean))
        result["abs"].append(np.stack(rows_abs))
        result["rms"].append(np.stack(rows_rms))

    for key in result:
        result[key] = np.stack(result[key]).astype(np.float32)

        if not np.isfinite(result[key]).all():
            raise ValueError(
                f"{label}/{key} có NaN hoặc Inf. Dừng để tránh kết luận sai."
            )

    return result


def effect_size(human, llm, axis=0):
    """Cohen's d: chiều dương nghĩa là activation nhóm LLM cao hơn."""
    n_h, n_l = human.shape[axis], llm.shape[axis]
    mean_h = human.mean(axis=axis)
    mean_l = llm.mean(axis=axis)
    diff = mean_l - mean_h

    var_h = human.var(axis=axis, ddof=1)
    var_l = llm.var(axis=axis, ddof=1)
    pooled_var = (
        (n_h - 1) * var_h + (n_l - 1) * var_l
    ) / max(n_h + n_l - 2, 1)

    pooled_std = np.sqrt(np.maximum(pooled_var, 0))
    eps = max(float(np.std(np.concatenate([
        human.reshape(-1), llm.reshape(-1)
    ]))) * 1e-6, 1e-12)

    d = diff / np.maximum(pooled_std, eps)
    return mean_h, mean_l, diff, d


def save_csv(path, rows, columns):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def draw_heatmap(ax, data, title, layer_numbers, cmap,
                 vmin=None, vmax=None, norm=None):
    image = ax.imshow(
        data, aspect="auto", interpolation="nearest",
        origin="upper", cmap=cmap, vmin=vmin, vmax=vmax, norm=norm
    )
    ax.set_title(title, fontsize=11)
    ax.set_ylabel("Transformer layer", fontsize=9)

    step = max(1, len(layer_numbers) // 7)
    ticks = np.arange(0, len(layer_numbers), step)
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"L{layer_numbers[i]}" for i in ticks])

    token_count = data.shape[1]
    x_ticks = np.arange(0, token_count, 30)
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_ticks)
    ax.set_xlabel("Token position")
    return image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_path", default="Qwen/Qwen2.5-0.5B-Instruct"
    )
    parser.add_argument(
        "--data_path", default="datasets/hc3_train_repre.json"
    )
    parser.add_argument("--sample_size", type=int, default=200)
    parser.add_argument("--truncate_len", type=int, default=210)
    parser.add_argument("--bootstrap_iter", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output_dir", default="results/insight/HC3_Qwen2.5_0.5B"
    )
    args = parser.parse_args()

    if args.sample_size < 2:
        raise ValueError("sample_size phải >= 2.")
    if args.bootstrap_iter < 100:
        raise ValueError("bootstrap_iter nên >= 100.")

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    print("Loading model and tokenizer...")
    model, extractor = load_model_and_tokenizer(args.model_path)
    model.eval()
    tokenizer = extractor.tokenizer

    with open(args.data_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    print(f"Dataset records: {len(records)}")

    human_texts = select_texts(
        records, "human_text", tokenizer,
        args.sample_size, args.truncate_len
    )
    llm_texts = select_texts(
        records, "direct_prompt", tokenizer,
        args.sample_size, args.truncate_len
    )
    print(
        f"Selected: Human={len(human_texts)}, "
        f"LLM={len(llm_texts)}, tokens/sample={args.truncate_len}"
    )

    # Tương tự cách chọn hidden_layers trong code RepreGuard đang dùng.
    hidden_layers = list(
        range(-1, -model.config.num_hidden_layers, -1)
    )
    layer_numbers = [
        model.config.num_hidden_layers + layer + 1
        for layer in hidden_layers
    ]

    human = extract_activations(
        human_texts, extractor, hidden_layers,
        args.truncate_len, "Human"
    )
    llm = extract_activations(
        llm_texts, extractor, hidden_layers,
        args.truncate_len, "LLM"
    )

    np.savez_compressed(
        out / "sample_activations.npz",
        human_mean=human["mean"],
        llm_mean=llm["mean"],
        human_abs=human["abs"],
        llm_abs=llm["abs"],
        human_rms=human["rms"],
        llm_rms=llm["rms"],
        layer_numbers=np.array(layer_numbers)
    )

    # Ma trận [layer, token] lấy trung bình trên các văn bản.
    mh = human["mean"].mean(axis=0)
    ml = llm["mean"].mean(axis=0)
    diff = ml - mh
    _, _, _, d_cell = effect_size(
        human["mean"], llm["mean"], axis=0
    )

    # Hai chỉ số độ lớn activation là phân tích bổ sung, không thay metric gốc.
    ah = human["abs"].mean(axis=0)
    al = llm["abs"].mean(axis=0)
    abs_diff = al - ah

    rh = human["rms"].mean(axis=0)
    rl = llm["rms"].mean(axis=0)
    rms_diff = rl - rh

    # Heatmap mean dùng chung thang màu giữa Human và LLM.
    pooled_means = np.concatenate([mh.ravel(), ml.ravel()])
    vmin, vmax = np.percentile(pooled_means, [1, 99])
    if not np.isfinite(vmin + vmax) or vmax <= vmin:
        vmin = float(pooled_means.min()) - 1e-8
        vmax = float(pooled_means.max()) + 1e-8

    def robust_limit(data):
        limit = float(np.percentile(np.abs(data), 99))
        return limit if np.isfinite(limit) and limit > 1e-12 else 1e-8

    diff_limit = robust_limit(diff)
    abs_limit = robust_limit(abs_diff)
    rms_limit = robust_limit(rms_diff)

    d_limit = robust_limit(d_cell)
    # Giới hạn màu nhằm dễ quan sát; d_cell thực tế không bị cắt.
    d_limit = min(max(d_limit, 0.5), 3.0)

    fig, axes = plt.subplots(
        6, 1, figsize=(13, 16), sharex=True, constrained_layout=True
    )

    plots = [
        (mh, "Human: mean signed activation (paper-style statistic)",
         "viridis", vmin, vmax, None),
        (ml, "LLM: mean signed activation (same scale as Human)",
         "viridis", vmin, vmax, None),
        (diff, "Difference: LLM minus Human mean activation",
         "coolwarm", None, None,
         TwoSlopeNorm(vmin=-diff_limit, vcenter=0, vmax=diff_limit)),
        (abs_diff, "Exploratory: difference in mean absolute activation",
         "coolwarm", None, None,
         TwoSlopeNorm(vmin=-abs_limit, vcenter=0, vmax=abs_limit)),
        (rms_diff, "Exploratory: difference in RMS activation",
         "coolwarm", None, None,
         TwoSlopeNorm(vmin=-rms_limit, vcenter=0, vmax=rms_limit)),
        (d_cell, "Descriptive Cohen's d: signed mean activation",
         "coolwarm", None, None,
         TwoSlopeNorm(vmin=-d_limit, vcenter=0, vmax=d_limit))
    ]

    for ax, (matrix, title, cmap, lo, hi, norm) in zip(axes, plots):
        im = draw_heatmap(
            ax, matrix, title, layer_numbers, cmap,
            vmin=lo, vmax=hi, norm=norm
        )
        fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01)

    fig.suptitle(
        "RepreGuard activation diagnostics — exploratory analysis",
        fontsize=13
    )
    axes[-1].set_xlabel("Token position")
    fig.savefig(out / "activation_insights.pdf", dpi=300)
    plt.close(fig)

    # Thống kê theo văn bản: mỗi văn bản là một đơn vị quan sát.
    # Lấy mean trên token trước để không coi 210 token là 210 mẫu độc lập.
    human_doc = human["mean"].mean(axis=2)  # [n_human, layer]
    llm_doc = llm["mean"].mean(axis=2)      # [n_llm, layer]

    mean_h, mean_l, layer_diff, d_layer = effect_size(
        human_doc, llm_doc, axis=0
    )

    boot = np.empty((args.bootstrap_iter, len(layer_numbers)))
    for b in range(args.bootstrap_iter):
        ih = rng.integers(0, len(human_doc), size=len(human_doc))
        il = rng.integers(0, len(llm_doc), size=len(llm_doc))
        boot[b] = llm_doc[il].mean(axis=0) - human_doc[ih].mean(axis=0)

    ci_low, ci_high = np.percentile(boot, [2.5, 97.5], axis=0)

    layer_rows = []
    for i, layer in enumerate(layer_numbers):
        layer_rows.append({
            "model_layer": int(layer),
            "n_human": len(human_doc),
            "n_llm": len(llm_doc),
            "human_mean_per_document": float(mean_h[i]),
            "llm_mean_per_document": float(mean_l[i]),
            "difference_llm_minus_human": float(layer_diff[i]),
            "cohens_d": float(d_layer[i]),
            "bootstrap_95ci_low_difference": float(ci_low[i]),
            "bootstrap_95ci_high_difference": float(ci_high[i])
        })

    layer_rows.sort(key=lambda row: row["model_layer"])
    save_csv(
        out / "layer_effects.csv",
        layer_rows,
        list(layer_rows[0].keys())
    )

    # Biểu đồ theo layer với khoảng tin cậy bootstrap cho hiệu số trung bình.
    order = np.argsort(layer_numbers)
    y = np.arange(len(order))
    ordered_diff = layer_diff[order]
    lower_err = np.maximum(
        ordered_diff - ci_low[order], 0
    )
    upper_err = np.maximum(
        ci_high[order] - ordered_diff, 0
    )

    fig, ax = plt.subplots(
        figsize=(10, max(5, len(layer_numbers) * 0.28)),
        constrained_layout=True
    )
    ax.errorbar(
        ordered_diff, y,
        xerr=np.vstack([lower_err, upper_err]),
        fmt="o", capsize=3
    )
    ax.axvline(0, color="black", linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels([f"L{layer_numbers[i]}" for i in order])
    ax.set_xlabel("Mean activation difference (LLM − Human), bootstrap 95% CI")
    ax.set_ylabel("Transformer layer")
    ax.set_title("Layer-level activation differences by document")
    fig.savefig(out / "layer_effects.pdf", dpi=300)
    plt.close(fig)

    # Bản đồ effect size theo token/layer — dữ liệu mô tả.
    cell_rows = []
    for li, layer in enumerate(layer_numbers):
        for ti in range(args.truncate_len):
            cell_rows.append({
                "model_layer": int(layer),
                "token_position": int(ti),
                "human_mean_activation": float(mh[li, ti]),
                "llm_mean_activation": float(ml[li, ti]),
                "difference_llm_minus_human": float(diff[li, ti]),
                "cohens_d": float(d_cell[li, ti]),
                "human_mean_absolute_activation": float(ah[li, ti]),
                "llm_mean_absolute_activation": float(al[li, ti]),
                "difference_absolute_activation": float(abs_diff[li, ti]),
                "difference_rms_activation": float(rms_diff[li, ti])
            })

    cell_rows.sort(key=lambda row: abs(row["cohens_d"]), reverse=True)
    columns = list(cell_rows[0].keys())
    save_csv(out / "token_layer_effects.csv", cell_rows, columns)
    save_csv(out / "top50_token_layer_effects.csv", cell_rows[:50], columns)

    metadata = {
        "model_path": args.model_path,
        "data_path": args.data_path,
        "sample_size_per_group": args.sample_size,
        "truncate_len": args.truncate_len,
        "hidden_layers": layer_numbers,
        "note": (
            "HC3/Qwen exploratory analysis. Mean signed activation follows "
            "the current RepreGuard visualization statistic. Absolute/RMS "
            "activation maps are exploratory additions, not the original "
            "RepreGuard method. Cohen's d maps are descriptive."
        ),
        "mean_activation_color_range_p01_p99": [
            float(vmin), float(vmax)
        ],
        "overall_mean_signed_activation": {
            "human": float(human["mean"].mean()),
            "llm": float(llm["mean"].mean()),
            "llm_minus_human": float(
                human["mean"].mean() * -1 + llm["mean"].mean()
            )
        }
    }
    with open(out / "analysis_summary.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    ranked = sorted(
        layer_rows, key=lambda row: abs(row["cohens_d"]), reverse=True
    )
    print("\nTop layers by absolute Cohen's d (descriptive only):")
    for row in ranked[:5]:
        print(
            f"L{row['model_layer']:>2}: "
            f"d={row['cohens_d']:.4f}, "
            f"delta={row['difference_llm_minus_human']:.6g}, "
            f"bootstrap CI=[{row['bootstrap_95ci_low_difference']:.6g}, "
            f"{row['bootstrap_95ci_high_difference']:.6g}]"
        )

    print("\nSaved outputs:")
    for filename in [
        "activation_insights.pdf",
        "layer_effects.pdf",
        "layer_effects.csv",
        "token_layer_effects.csv",
        "top50_token_layer_effects.csv",
        "sample_activations.npz",
        "analysis_summary.json"
    ]:
        print(out / filename)


if __name__ == "__main__":
    main()
PY

python -m py_compile vis/repre_insight.py || exit 1
echo "Created vis/repre_insight.py successfully."