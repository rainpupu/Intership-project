"""
猫品种检测模型 - 测试集评估脚本
对训练好的模型在测试集上进行评估（精度指标 + 全量预测）
"""

import os
import sys
import json
import csv
import math
from pathlib import Path
from datetime import datetime

import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from ultralytics import YOLO

# ============================================================
# 缓存重定向（避免C盘占用）
# ============================================================
CACHE_BASE = Path("E:/program/merged_cat_breeds/.cache")
CACHE_BASE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("ULTRALYTICS_CACHE_DIR", str(CACHE_BASE / "ultralytics"))
os.environ.setdefault("TORCH_HOME", str(CACHE_BASE / "torch"))
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_BASE / "matplotlib"))

for _dir in ["ultralytics", "torch", "matplotlib"]:
    (CACHE_BASE / _dir).mkdir(parents=True, exist_ok=True)

# ============================================================
# 配置
# ============================================================
DATASET_PATH = "E:/program/merged_cat_breeds/data.yaml"
MODEL_PATH = "E:/mycode/visagent/visagent/backend/runs/train_cat_breeds/cat_breeds_v1/weights/best.pt"
OUTPUT_DIR = Path("E:/mycode/visagent/visagent/backend/runs/train_cat_breeds/cat_breeds_v1/test_eval")
BACKEND_DIR = Path("E:/mycode/visagent/visagent/backend")
TRAIN_RESULTS_CSV = BACKEND_DIR / "runs/train_cat_breeds/cat_breeds_v1/results.csv"

BREED_NAMES = [
    "Abyssinian", "Bengal", "Birman", "Bombay",
    "British_Shorthair", "Egyptian_Mau", "Maine_Coon",
    "Persian", "Ragdoll", "Russian_Blue", "Siamese", "Sphynx",
]

NUM_SAMPLE_IMAGES = 32  # 展示的预测样例数量
CONFIDENCE_THRESHOLD = 0.25


def ensure_dir(d):
    Path(d).mkdir(parents=True, exist_ok=True)


# ============================================================
# 图表绘制
# ============================================================

def plot_per_class_ap(per_class_metrics, save_path, breed_names):
    """绘制每个品种的 AP 条形图"""
    classes = []
    ap50_vals = []
    ap50_95_vals = []

    for i, name in enumerate(breed_names):
        key = str(i)
        if key in per_class_metrics:
            classes.append(name)
            ap50_vals.append(per_class_metrics[key]["ap50"])
            ap50_95_vals.append(per_class_metrics[key]["ap50-95"])

    if not classes:
        print("  [WARN] No per-class metrics to plot")
        return

    x = np.arange(len(classes))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 6))
    bars1 = ax.bar(x - width / 2, ap50_vals, width, label="mAP@50", color="#2196F3", alpha=0.85)
    bars2 = ax.bar(x + width / 2, ap50_95_vals, width, label="mAP@50:95", color="#FF9800", alpha=0.85)

    ax.set_xlabel("Breed")
    ax.set_ylabel("AP")
    ax.set_title("Per-Class Average Precision on Test Set")
    ax.set_xticks(x)
    ax.set_xticklabels(classes, rotation=45, ha="right", fontsize=9)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, 1.05)

    # 在柱子上标注数值
    for bar in bars1:
        h = bar.get_height()
        if h > 0.01:
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.01, f"{h:.2f}",
                    ha="center", va="bottom", fontsize=7, rotation=90)
    for bar in bars2:
        h = bar.get_height()
        if h > 0.01:
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.01, f"{h:.2f}",
                    ha="center", va="bottom", fontsize=7, rotation=90)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [V] Per-class AP saved to {save_path}")


def plot_val_vs_test_comparison(val_metrics, test_metrics, save_path, breed_names):
    """验证集 vs 测试集 mAP 对比柱状图"""
    # 合并 per-class 数据
    breeds = breed_names
    val_ap50 = []
    test_ap50 = []
    has_data = False

    for i, name in enumerate(breeds):
        v = val_metrics.get(str(i), {}).get("ap50", None) if val_metrics else None
        t = test_metrics.get(str(i), {}).get("ap50", None) if test_metrics else None
        if v is not None and t is not None:
            val_ap50.append(v)
            test_ap50.append(t)
        else:
            val_ap50.append(0)
            test_ap50.append(0)
        if v is not None or t is not None:
            has_data = True

    if not has_data:
        print("  [WARN] No per-class comparison data available")
        return

    x = np.arange(len(breeds))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(x - width / 2, val_ap50, width, label="Validation Set", color="#4CAF50", alpha=0.8)
    ax.bar(x + width / 2, test_ap50, width, label="Test Set", color="#F44336", alpha=0.8)

    ax.set_xlabel("Breed")
    ax.set_ylabel("mAP@50")
    ax.set_title("Validation vs Test Set: Per-Class mAP@50 Comparison")
    ax.set_xticks(x)
    ax.set_xticklabels(breeds, rotation=45, ha="right", fontsize=9)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, 1.05)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [V] Val vs Test comparison saved to {save_path}")


def plot_summary_comparison(val_final, test_final, save_path):
    """四个主要指标的对比柱状图"""
    metrics = ["Precision", "Recall", "mAP@50", "mAP@50:95"]
    val_vals = [val_final.get(m, 0) for m in ["precision", "recall", "mAP50", "mAP50-95"]]
    test_vals = [test_final.get(m, 0) for m in ["precision", "recall", "mAP50", "mAP50-95"]]

    x = np.arange(len(metrics))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    bars1 = ax.bar(x - width / 2, val_vals, width, label="Validation", color="#4CAF50", alpha=0.85)
    bars2 = ax.bar(x + width / 2, test_vals, width, label="Test", color="#F44336", alpha=0.85)

    ax.set_ylabel("Score")
    ax.set_title("Validation vs Test Set: Metrics Comparison")
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, 1.05)

    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.01, f"{h:.3f}", ha="center", fontsize=8)
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.01, f"{h:.3f}", ha="center", fontsize=8)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [V] Summary comparison saved to {save_path}")


def create_prediction_grid(image_dir, breed_names, num_samples=32):
    """从预测结果目录创建拼贴图"""
    img_files = sorted(Path(image_dir).glob("*.jpg"))[:num_samples]
    if not img_files:
        return

    cols = 8
    rows = math.ceil(len(img_files) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 3, rows * 3))
    axes = axes.flatten() if rows > 1 else [axes] if cols == 1 else axes

    for i, ax in enumerate(axes):
        if i < len(img_files):
            img = Image.open(img_files[i])
            ax.imshow(img)
            ax.axis("off")
        else:
            ax.axis("off")

    plt.tight_layout()
    plt.savefig(Path(image_dir).parent / "prediction_grid.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [V] Prediction grid saved")


# ============================================================
# 主评估函数
# ============================================================

def evaluate_test_set():
    """在测试集上评估模型"""
    print("=" * 60)
    print("  测试集评估")
    print("=" * 60)

    # 检查模型
    if not Path(MODEL_PATH).exists():
        print(f"[ERROR] 模型文件不存在: {MODEL_PATH}")
        sys.exit(1)

    # 检查CUDA
    device = 0 if torch.cuda.is_available() else "cpu"
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        print(f"  GPU: {gpu_name} | CUDA: {torch.version.cuda}")
    else:
        print("  [WARN] 使用CPU")

    # 加载模型
    print(f"\n[Download] 加载模型: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)

    # ============================================================
    # 1. 测试集精度评估（使用已有标签）
    # ============================================================
    print(f"\n{'='*60}")
    print(f"  阶段1: 测试集精度评估 (231张有标签)")
    print(f"{'='*60}")

    ensure_dir(OUTPUT_DIR)

    # 检查测试集有多少有标签的图片
    test_label_dir = Path("E:/program/merged_cat_breeds/labels/test")
    test_img_dir = Path("E:/program/merged_cat_breeds/images/test")
    labeled_count = len(list(test_label_dir.glob("*.txt")))
    total_count = len(list(test_img_dir.glob("*.jpg")))
    print(f"  测试集: {total_count} 张图片, {labeled_count} 张有标签")

    val_results = model.val(
        data=DATASET_PATH,
        split="test",
        batch=16,
        device=device,
        workers=2,
        conf=CONFIDENCE_THRESHOLD,
        iou=0.5,
        imgsz=640,
        plots=True,
        save_json=False,
        save_hybrid=False,
    )

    # 提取测试集指标
    test_metrics = {}
    test_per_class = {}

    if hasattr(val_results, "metrics"):
        print("\n  [Metrics] 测试集总体指标:")
        for key, val in val_results.metrics.items():
            if isinstance(val, (int, float)):
                print(f"      {key}: {val:.4f}")
                test_metrics[key.replace("metrics/", "").replace("(B)", "")] = val

    # 提取 per-class AP
    if hasattr(val_results, "ap_class_index") and hasattr(val_results, "ap"):
        ap = val_results.ap  # [num_classes, 10] for 10 IoU thresholds
        ap_class = val_results.ap_class_index
        for idx, cls_id in enumerate(ap_class):
            ap50 = float(ap[idx, 0])  # IoU=0.5
            ap50_95 = float(np.mean([ap[idx, j] for j in range(10)]))
            test_per_class[str(cls_id)] = {
                "ap50": ap50,
                "ap50-95": ap50_95,
                "name": BREED_NAMES[cls_id] if cls_id < len(BREED_NAMES) else f"class_{cls_id}",
            }
            print(f"      {BREED_NAMES[cls_id]}: AP@50={ap50:.4f}, AP@50:95={ap50_95:.4f}")

    print(f"\n  有标签的测试图片被评估: {labeled_count} 张")

    # ============================================================
    # 2. 全量预测（1443张全部）
    # ============================================================
    print(f"\n{'='*60}")
    print(f"  阶段2: 全量预测 ({total_count}张)")
    print(f"{'='*60}")

    predict_dir = OUTPUT_DIR / "predictions"
    ensure_dir(predict_dir)

    # 分批预测（所有测试图片）
    results = model.predict(
        source=str(test_img_dir),
        conf=CONFIDENCE_THRESHOLD,
        iou=0.5,
        imgsz=640,
        device=device,
        save=True,
        project=str(OUTPUT_DIR),
        name="predictions",
        exist_ok=True,
        save_txt=True,
        save_conf=True,
    )

    # 统计预测结果
    pred_stats = {name: 0 for name in BREED_NAMES}
    confidences = []
    total_detections = 0

    for r in results:
        if r.boxes is not None and len(r.boxes) > 0:
            for cls_id, conf in zip(r.boxes.cls, r.boxes.conf):
                cls_id = int(cls_id)
                if cls_id < len(BREED_NAMES):
                    pred_stats[BREED_NAMES[cls_id]] += 1
                confidences.append(float(conf))
                total_detections += 1

    print(f"\n  总检测数: {total_detections}")
    print(f"  平均置信度: {np.mean(confidences):.4f}" if confidences else "  无检测结果")
    print(f"\n  各品种检测分布:")
    for name in BREED_NAMES:
        count = pred_stats[name]
        print(f"      {name}: {count} 次检测")

    # 保存预测统计
    with open(OUTPUT_DIR / "prediction_stats.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_images": total_count,
            "labeled_images": labeled_count,
            "total_detections": total_detections,
            "avg_confidence": round(float(np.mean(confidences)), 4) if confidences else 0,
            "per_breed_detections": pred_stats,
        }, f, indent=2, ensure_ascii=False)

    # ============================================================
    # 3. 生成对比图表
    # ============================================================
    print(f"\n{'='*60}")
    print(f"  阶段3: 生成对比报告")
    print(f"{'='*60}")

    # Per-class AP 条形图
    if test_per_class:
        plot_per_class_ap(test_per_class, OUTPUT_DIR / "per_class_ap_test.png", BREED_NAMES)

    # 读取训练过程中的验证集 per-class metrics
    # YOLO 在训练时不保存 per-class val AP，我们从最终模型重新验证一次
    print("\n  [Charts] 重新验证验证集以获取 per-class 对比数据...")
    val_on_val = model.val(
        data=DATASET_PATH,
        split="val",
        batch=16,
        device=device,
        workers=2,
        conf=CONFIDENCE_THRESHOLD,
        iou=0.5,
        imgsz=640,
        plots=False,
    )

    val_per_class = {}
    if hasattr(val_on_val, "ap_class_index") and hasattr(val_on_val, "ap"):
        ap = val_on_val.ap
        ap_class = val_on_val.ap_class_index
        for idx, cls_id in enumerate(ap_class):
            ap50 = float(ap[idx, 0])
            ap50_95 = float(np.mean([ap[idx, j] for j in range(10)]))
            val_per_class[str(cls_id)] = {
                "ap50": ap50,
                "ap50-95": ap50_95,
                "name": BREED_NAMES[cls_id] if cls_id < len(BREED_NAMES) else f"class_{cls_id}",
            }

    # 对比图
    if val_per_class and test_per_class:
        plot_val_vs_test_comparison(val_per_class, test_per_class,
                                     OUTPUT_DIR / "val_vs_test_comparison.png", BREED_NAMES)

    # 从 training_report.json 读取验证集 final 指标
    val_final_metrics = {}
    train_report_path = BACKEND_DIR / "runs/train_cat_breeds/cat_breeds_v1/training_report.json"
    if train_report_path.exists():
        with open(train_report_path) as f:
            train_report = json.load(f)
        val_final_metrics = train_report.get("final_metrics", {})

    # 测试集 final 指标
    test_final_metrics = {
        "precision": test_metrics.get("precision", 0),
        "recall": test_metrics.get("recall", 0),
        "mAP50": test_metrics.get("mAP50", 0),
        "mAP50-95": test_metrics.get("mAP50-95", 0),
    }

    # 对比柱状图
    if val_final_metrics and any(v > 0 for v in test_final_metrics.values()):
        plot_summary_comparison(val_final_metrics, test_final_metrics,
                                 OUTPUT_DIR / "val_vs_test_summary.png")

    # ============================================================
    # 4. 生成评估报告
    # ============================================================
    report = {
        "evaluation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": str(MODEL_PATH),
        "dataset": str(DATASET_PATH),
        "test_set": {
            "total_images": total_count,
            "labeled_images": labeled_count,
        },
        "test_metrics_summary": {
            "precision": round(test_final_metrics.get("precision", 0), 4),
            "recall": round(test_final_metrics.get("recall", 0), 4),
            "mAP50": round(test_final_metrics.get("mAP50", 0), 4),
            "mAP50-95": round(test_final_metrics.get("mAP50-95", 0), 4),
        },
        "val_metrics_summary": {
            "precision": round(val_final_metrics.get("precision", 0), 4),
            "recall": round(val_final_metrics.get("recall", 0), 4),
            "mAP50": round(val_final_metrics.get("mAP50", 0), 4),
            "mAP50-95": round(val_final_metrics.get("mAP50-95", 0), 4),
        },
        "per_class_test_metrics": test_per_class,
        "per_class_val_metrics": val_per_class,
        "prediction_stats": {
            "total_detections": total_detections,
            "avg_confidence": round(float(np.mean(confidences)), 4) if confidences else 0,
        },
    }

    report_path = OUTPUT_DIR / "test_evaluation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  [V] 评估报告已保存: {report_path}")

    # ============================================================
    # 5. 预测结果拼贴图
    # ============================================================
    create_prediction_grid(predict_dir, BREED_NAMES, NUM_SAMPLE_IMAGES)

    # ============================================================
    # 总结
    # ============================================================
    print(f"\n{'='*60}")
    print(f"  评估完成!")
    print(f"{'='*60}")
    print(f"  测试集 (231张有标签):")
    print(f"    Precision:  {test_final_metrics.get('precision', 0):.4f}")
    print(f"    Recall:     {test_final_metrics.get('recall', 0):.4f}")
    print(f"    mAP@50:     {test_final_metrics.get('mAP50', 0):.4f}")
    print(f"    mAP@50:95:  {test_final_metrics.get('mAP50-95', 0):.4f}")
    print(f"")
    print(f"  验证集 (689张):")
    print(f"    Precision:  {val_final_metrics.get('precision', 0):.4f}")
    print(f"    Recall:     {val_final_metrics.get('recall', 0):.4f}")
    print(f"    mAP@50:     {val_final_metrics.get('mAP50', 0):.4f}")
    print(f"    mAP@50:95:  {val_final_metrics.get('mAP50-95', 0):.4f}")
    print(f"")
    print(f"  全量预测: {total_detections} 个检测框 (平均置信度 {np.mean(confidences):.4f})" if confidences else "  全量预测: 无检测结果")
    print(f"")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"{'='*60}\n")

    return report


if __name__ == "__main__":
    evaluate_test_set()
