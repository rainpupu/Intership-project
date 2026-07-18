"""
猫品种分类训练脚本 (12种猫品种)
基于 Ultralytics YOLOv11 目标检测

数据集: E:/program/merged_cat_breeds
训练记录和图表将保存在 runs/train_cat_breeds/ 目录下
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# ============================================================
# 缓存目录重定向（避免占用 C 盘）
# ============================================================
# 将所有 AI 相关缓存指向 E 盘数据集目录下的 .cache 文件夹
CACHE_BASE = Path("E:/program/merged_cat_breeds/.cache")
CACHE_BASE.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("ULTRALYTICS_CACHE_DIR", str(CACHE_BASE / "ultralytics"))
os.environ.setdefault("TORCH_HOME", str(CACHE_BASE / "torch"))
os.environ.setdefault("HF_HOME", str(CACHE_BASE / "huggingface"))
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_BASE / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_BASE))

# 确保缓存子目录存在
for _dir in ["ultralytics", "torch", "huggingface", "matplotlib"]:
    (CACHE_BASE / _dir).mkdir(parents=True, exist_ok=True)

print(f"  [Cache] 缓存目录(C盘免占): {CACHE_BASE}")

import torch
import matplotlib
matplotlib.use("Agg")  # 非交互式后端，避免 GUI 依赖
import matplotlib.pyplot as plt
import numpy as np

from ultralytics import YOLO

# ============================================================
# 配置
# ============================================================

DATASET_PATH = "E:/program/merged_cat_breeds/data.yaml"
DEFAULT_EPOCHS = 100
DEFAULT_IMG_SIZE = 640
DEFAULT_BATCH = 16
DEFAULT_MODEL = "yolo11n.pt"  # 预训练模型: yolo11n/s/m/l/x.pt
DEFAULT_DEVICE = 0  # GPU 设备 ID
DEFAULT_WORKERS = 2  # Windows 建议 0-2，Linux 可更高

# 脚本所在目录（backend/）
BACKEND_DIR = Path(__file__).parent.resolve()
DEFAULT_PROJECT = str(BACKEND_DIR / "runs" / "train_cat_breeds")

# 品种名称
BREED_NAMES = [
    "Abyssinian", "Bengal", "Birman", "Bombay",
    "British_Shorthair", "Egyptian_Mau", "Maine_Coon",
    "Persian", "Ragdoll", "Russian_Blue", "Siamese", "Sphynx",
    "三花", "奶牛", "橘猫", "狸花&彩狸", "白猫",
]

# ============================================================
# 绘图工具
# ============================================================


def smooth_curve(values, weight=0.85):
    """指数移动平均平滑曲线"""
    smoothed = []
    last = values[0]
    for v in values:
        smoothed_val = last * weight + (1 - weight) * v
        smoothed.append(smoothed_val)
        last = smoothed_val
    return smoothed


def plot_training_curves(history: dict, save_dir: str, breed_names: list = None):
    """
    绘制训练过程中的各项指标曲线

    Args:
        history: 训练历史数据字典 (来自 YOLO 训练结果)
        save_dir: 保存目录
        breed_names: 品种名称列表 (用于绘制每个品种的 AP 曲线)
    """
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # 提取指标
    epochs = list(range(1, len(history.get("train/loss", [])) + 1))

    # ------------------- 1. Loss 曲线 -------------------
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 训练损失
    if "train/loss" in history:
        train_loss = history["train/loss"]
        axes[0].plot(epochs, train_loss, "b-", alpha=0.3, label="Raw")
        axes[0].plot(epochs, smooth_curve(train_loss), "b-", linewidth=2, label="Smoothed")
        axes[0].set_xlabel("Epoch")
        axes[0].set_ylabel("Box Loss")
        axes[0].set_title("Training Box Loss")
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

    # 验证损失
    if "val/loss" in history:
        val_loss = history["val/loss"]
        axes[1].plot(epochs, val_loss, "r-", alpha=0.3, label="Raw")
        axes[1].plot(epochs, smooth_curve(val_loss), "r-", linewidth=2, label="Smoothed")
        axes[1].set_xlabel("Epoch")
        axes[1].set_ylabel("Val Box Loss")
        axes[1].set_title("Validation Box Loss")
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_dir / "loss_curves.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [[V]] Loss curves saved to {save_dir / 'loss_curves.png'}")

    # ------------------- 2. 精度指标曲线 -------------------
    has_metrics = any(k in history for k in ["metrics/precision", "metrics/recall", "metrics/mAP50", "metrics/mAP50-95"])

    if has_metrics:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        metrics_config = [
            ("metrics/precision", "Precision", axes[0, 0], "b"),
            ("metrics/recall", "Recall", axes[0, 1], "g"),
            ("metrics/mAP50", "mAP@50", axes[1, 0], "orange"),
            ("metrics/mAP50-95", "mAP@50:95", axes[1, 1], "r"),
        ]

        for key, label, ax, color in metrics_config:
            if key in history:
                values = history[key]
                ax.plot(epochs, values, color=color, alpha=0.3, label="Raw")
                ax.plot(epochs, smooth_curve(values), color=color, linewidth=2, label="Smoothed")
                ax.set_xlabel("Epoch")
                ax.set_ylabel(label)
                ax.set_title(f"{label} over Epochs")
                ax.legend()
                ax.grid(True, alpha=0.3)
                # 标注最佳值
                best_val = max(values)
                best_epoch = np.argmax(values) + 1
                ax.annotate(
                    f"Best: {best_val:.4f} @ epoch {best_epoch}",
                    xy=(best_epoch, best_val),
                    xytext=(best_epoch + 2, best_val - 0.05),
                    arrowprops=dict(arrowstyle="->", color="gray"),
                    fontsize=9,
                )

        plt.tight_layout()
        plt.savefig(save_dir / "metrics_curves.png", dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  [[V]] Metrics curves saved to {save_dir / 'metrics_curves.png'}")

    # ------------------- 3. 学习率曲线 -------------------
    if "lr" in history:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(epochs, history["lr"], "purple", linewidth=2)
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Learning Rate")
        ax.set_title("Learning Rate Schedule")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(save_dir / "lr_curve.png", dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  [[V]] LR curve saved to {save_dir / 'lr_curve.png'}")

    # ------------------- 4. 综合总览图 -------------------
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    # 左上: Loss
    if "train/loss" in history:
        ax = axes[0, 0]
        ax.plot(epochs, smooth_curve(history["train/loss"]), "b-", linewidth=2, label="Train Loss")
        if "val/loss" in history:
            ax.plot(epochs, smooth_curve(history["val/loss"]), "r-", linewidth=2, label="Val Loss")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Loss")
        ax.set_title("Loss")
        ax.legend()
        ax.grid(True, alpha=0.3)

    # 右上: Precision/Recall
    for key, label, color in [("metrics/precision", "Precision", "b"), ("metrics/recall", "Recall", "g")]:
        if key in history:
            axes[0, 1].plot(epochs, smooth_curve(history[key]), color=color, linewidth=2, label=label)
    axes[0, 1].set_xlabel("Epoch")
    axes[0, 1].set_ylabel("Score")
    axes[0, 1].set_title("Precision & Recall")
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # 左下: mAP
    for key, label, color in [("metrics/mAP50", "mAP@50", "orange"), ("metrics/mAP50-95", "mAP@50:95", "r")]:
        if key in history:
            axes[1, 0].plot(epochs, smooth_curve(history[key]), color=color, linewidth=2, label=label)
    axes[1, 0].set_xlabel("Epoch")
    axes[1, 0].set_ylabel("mAP")
    axes[1, 0].set_title("Mean Average Precision")
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # 右下: 学习率
    if "lr" in history:
        axes[1, 1].plot(epochs, history["lr"], "purple", linewidth=2)
        axes[1, 1].set_xlabel("Epoch")
        axes[1, 1].set_ylabel("LR")
        axes[1, 1].set_title("Learning Rate")
        axes[1, 1].grid(True, alpha=0.3)

    plt.suptitle("Training Overview", fontsize=14, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig(save_dir / "training_overview.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [[V]] Training overview saved to {save_dir / 'training_overview.png'}")

    # ------------------- 5. 每个品种的 AP 曲线 (如可用) -------------------
    # Ultralytics 在训练过程中不逐品种输出 AP，我们可以在训练完成后从验证结果中获取
    # 这里留作扩展

    print(f"  [[V]] All charts saved to {save_dir}/")


def save_training_report(history: dict, best_metrics: dict, save_dir: str, elapsed_time: float):
    """保存训练报告 JSON"""
    report = {
        "training_completed": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_time_seconds": round(elapsed_time, 2),
        "elapsed_time_str": f"{int(elapsed_time // 3600)}h {int((elapsed_time % 3600) // 60)}m {int(elapsed_time % 60)}s",
        "epochs": len(history.get("train/loss", [])),
        "best_metrics": {},
    }

    # 最佳指标
    metric_keys = [
        ("metrics/precision", "precision"),
        ("metrics/recall", "recall"),
        ("metrics/mAP50", "mAP50"),
        ("metrics/mAP50-95", "mAP50-95"),
    ]
    for key, name in metric_keys:
        if key in history:
            values = history[key]
            best_idx = int(np.argmax(values))
            report["best_metrics"][name] = {
                "value": round(float(values[best_idx]), 4),
                "epoch": int(best_idx + 1),
            }

    # 最终指标
    report["final_metrics"] = {}
    for key, name in metric_keys:
        if key in history:
            report["final_metrics"][name] = round(float(history[key][-1]), 4)

    # 写入文件
    report_path = Path(save_dir) / "training_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  [[V]] Training report saved to {report_path}")
    return report


# ============================================================
# 主训练函数
# ============================================================


def train_yolo(
    data: str = DATASET_PATH,
    model_name: str = DEFAULT_MODEL,
    epochs: int = DEFAULT_EPOCHS,
    img_size: int = DEFAULT_IMG_SIZE,
    batch: int = DEFAULT_BATCH,
    device: int = DEFAULT_DEVICE,
    workers: int = DEFAULT_WORKERS,
    project: str = DEFAULT_PROJECT,
    name: str = None,
    patience: int = 20,
    augment: bool = True,
    resume: bool = False,
    pretrained: bool = True,
    lr0: float = 0.01,
    lrf: float = 0.01,
    warmup_epochs: float = 3.0,
    cos_lr: bool = True,
    val: bool = True,
    save_period: int = 10,
    exist_ok: bool = False,
):
    """
    训练 YOLO 猫品种分类模型

    Args:
        data: 数据集配置路径
        model_name: 预训练模型名称或路径
        epochs: 训练轮数
        img_size: 输入图像大小
        batch: 批次大小
        device: 设备 ID (GPU)
        workers: 数据加载线程数
        project: 项目保存目录
        name: 实验名称 (自动生成如果为 None)
        patience: 早停耐心值
        augment: 是否使用数据增强
        resume: 是否从断点恢复
        pretrained: 是否使用预训练权重
        lr0: 初始学习率
        lrf: 最终学习率比例
        warmup_epochs: 预热轮数
        cos_lr: 是否使用余弦退火学习率
        val: 是否每个 epoch 验证
        save_period: 每 N 个 epoch 保存一次模型
        exist_ok: 是否允许覆盖已有实验目录

    Returns:
        results: YOLO 训练结果对象
        history: 训练的完整指标记录
    """
    # ---------- 设备检查 ----------
    if torch.cuda.is_available():
        device_count = torch.cuda.device_count()
        if device >= device_count:
            print(f"  ⚠️ 指定的 GPU {device} 不可用，使用 GPU 0")
            device = 0
        gpu_name = torch.cuda.get_device_name(device)
        print(f"  ✅ 使用 GPU: {gpu_name} (设备 {device})")
        print(f"  ✅ CUDA 版本: {torch.version.cuda}")
    else:
        print("  ⚠️ CUDA 不可用，使用 CPU (训练会很慢)")
        device = "cpu"

    # ---------- 自动命名 ----------
    if name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_short = Path(model_name).stem
        name = f"{model_short}_e{epochs}_b{batch}_{timestamp}"

    # ---------- 初始化模型 ----------
    print(f"\n{'='*60}")
    print(f"  猫品种检测训练启动")
    print(f"{'='*60}")
    print(f"  模型:      {model_name}")
    print(f"  数据集:    {data}")
    # 从 data.yaml 读取实际品种数
    import yaml
    try:
        with open(data, "r", encoding="utf-8") as f:
            data_cfg = yaml.safe_load(f)
        nc = data_cfg.get("nc", "?")
    except Exception:
        nc = "?"
    print(f"  品种数:    {nc} (猫品种)")
    print(f"  训练轮数:  {epochs}")
    print(f"  批次大小:  {batch}")
    print(f"  图像尺寸:  {img_size}")
    print(f"  设备:      {device}")
    print(f"  保存目录:  {project}/{name}")
    print(f"{'='*60}\n")

    # 加载模型
    if pretrained:
        print("  [Download]  加载预训练模型...")
        model = YOLO(model_name)
    else:
        print("  [New]  从头初始化模型...")
        # 从配置文件创建模型
        model = YOLO(f"{Path(model_name).stem}.yaml")

    # ---------- 开始训练 ----------
    start_time = datetime.now()

    results = model.train(
        data=data,
        epochs=epochs,
        imgsz=img_size,
        batch=batch,
        device=device,
        workers=workers,
        project=project,
        name=name,
        patience=patience,
        augment=augment,
        resume=resume,
        pretrained=pretrained,
        lr0=lr0,
        lrf=lrf,
        warmup_epochs=warmup_epochs,
        cos_lr=cos_lr,
        val=val,
        save_period=save_period,
        exist_ok=exist_ok,
        deterministic=False,  # 允许一定随机性以获得更好性能
        amp=True,  # 混合精度训练加速
    )

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n  ✅ 训练完成! 耗时: {int(elapsed//3600)}h {int((elapsed%3600)//60)}m {int(elapsed%60)}s")

    # ---------- 获取实际输出目录 ----------
    # Ultralytics 可能会在 project 前加上 task 前缀（如 runs/detect/）
    # 所以从 trainer.save_dir 获取实际路径最可靠
    if hasattr(model, "trainer") and hasattr(model.trainer, "save_dir"):
        save_dir = Path(model.trainer.save_dir)
    else:
        # 兼容：自己在项目/名称下找结果目录
        save_dir = Path(project) / name
        # 也搜索默认的 detect 子目录
        alt_dir = Path("runs") / "detect" / project / name
        if alt_dir.exists() and not save_dir.exists():
            save_dir = alt_dir

    print(f"  数据保存目录: {save_dir}")

    # ---------- 提取训练历史 ----------
    print("\n  [Charts]  整理训练记录...")

    # Ultralytics 的结果对象
    history = {}

    # 尝试从 results 中获取指标
    if hasattr(results, "metrics"):
        print("  [Metrics]  最终验证指标:")
        for key, val in results.metrics.items():
            if isinstance(val, (int, float)):
                print(f"      {key}: {val:.4f}")

    # 从 CSV 日志中读取是最可靠的方式
    csv_path = save_dir / "results.csv"
    if csv_path.exists():
        print(f"  [Read]  从 results.csv 读取指标...")
        import csv
        try:
            with open(csv_path, "r") as f:
                reader = csv.DictReader(f)
                csv_data = list(reader)

            if csv_data:
                # 映射 Ultralytics CSV 列名
                col_mapping = {
                    "train/box_loss": "train/loss",
                    "train/cls_loss": "train/cls_loss",
                    "train/dfl_loss": "train/dfl_loss",
                    "metrics/precision(B)": "metrics/precision",
                    "metrics/recall(B)": "metrics/recall",
                    "metrics/mAP50(B)": "metrics/mAP50",
                    "metrics/mAP50-95(B)": "metrics/mAP50-95",
                    "val/box_loss": "val/loss",
                    "val/cls_loss": "val/cls_loss",
                    "val/dfl_loss": "val/dfl_loss",
                    "lr/pg0": "lr",
                }

                for raw_col, nice_col in col_mapping.items():
                    if raw_col in csv_data[0]:
                        history[nice_col] = [float(row[raw_col]) for row in csv_data]

                print(f"      [V] 读取了 {len(csv_data)} 个 epoch 的 {len(history)} 项指标")
        except Exception as e:
            print(f"      ⚠️ 读取 CSV 出错: {e}")

    # ---------- 绘制训练曲线 ----------
    if history:
        print("\n  [Charts]  绘制训练曲线...")
        plot_training_curves(history, str(save_dir), breed_names=BREED_NAMES)

        # 保存训练报告
        best_metrics = {}
        save_training_report(history, best_metrics, str(save_dir), elapsed)
    else:
        print("\n  ⚠️ 没有历史数据可绘图")
        # 保存基本信息
        save_training_report(
            {"train/loss": []},
            {},
            str(save_dir),
            elapsed,
        )

    # ---------- 导出模型 ----------
    print("\n  [Export]  导出模型...")

    # 保存 PyTorch 模型副本到固定位置
    best_pt = save_dir / "weights" / "best.pt"
    if best_pt.exists():
        # 复制到固定位置方便后续使用
        import shutil
        final_model_path = save_dir.parent / "best_cat_breed_model.pt"
        shutil.copy(best_pt, final_model_path)
        print(f"      [V] 最佳模型复制到: {final_model_path}")

    # 导出 ONNX 格式
    try:
        onnx_path = save_dir / "weights" / "best.onnx"
        if not onnx_path.exists():
            print("      [Convert]  导出 ONNX 格式...")
            model.export(format="onnx", imgsz=img_size)
            print(f"      [V] ONNX 模型导出成功")
    except Exception as e:
        print(f"      ⚠️ ONNX 导出失败: {e}")

    print(f"\n{'='*60}")
    print(f"  [Done]  训练完成!")
    print(f"  结果目录: {save_dir}")
    print(f"  模型权重: {save_dir / 'weights' / 'best.pt'}")
    print(f"  图表目录: {save_dir}/loss_curves.png 等")
    print(f"{'='*60}\n")

    return results, history


# ============================================================
# 参数解析 / 主入口
# ============================================================


def parse_args():
    parser = argparse.ArgumentParser(
        description="YOLOv11 猫品种分类训练脚本 (12 品种)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--data", type=str, default=DATASET_PATH, help="数据集 data.yaml 路径")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="预训练模型 (yolo11n/s/m/l/x.pt)")
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS, help="训练轮数")
    parser.add_argument("--img-size", type=int, default=DEFAULT_IMG_SIZE, help="输入图像尺寸")
    parser.add_argument("--batch", type=int, default=DEFAULT_BATCH, help="批次大小")
    parser.add_argument("--device", type=int, default=DEFAULT_DEVICE, help="GPU 设备 ID")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="数据加载线程数 (Windows 建议 0-2)")
    parser.add_argument("--project", type=str, default=DEFAULT_PROJECT, help="项目保存目录（默认: backend/runs/train_cat_breeds）")
    parser.add_argument("--name", type=str, default=None, help="实验名称 (自动生成)")
    parser.add_argument("--patience", type=int, default=20, help="早停耐心值 (0=禁用)")
    parser.add_argument("--no-augment", action="store_true", help="禁用数据增强")
    parser.add_argument("--resume", action="store_true", help="从断点恢复训练")
    parser.add_argument("--no-pretrained", action="store_true", help="不使用预训练权重")
    parser.add_argument("--cos-lr", action="store_true", default=True, help="使用余弦退火学习率")
    parser.add_argument("--lr0", type=float, default=0.01, help="初始学习率")
    parser.add_argument("--save-period", type=int, default=10, help="每 N 轮保存一次权重")
    parser.add_argument("--exist-ok", action="store_true", help="允许覆盖已有实验目录")
    return parser.parse_args()


def main():
    args = parse_args()

    # 检查数据集
    if not os.path.exists(args.data):
        print(f"❌ 数据集配置文件不存在: {args.data}")
        # 尝试修正路径
        alt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.data)
        if os.path.exists(alt_path):
            args.data = alt_path
            print(f"   [V] 找到替代路径: {args.data}")
        else:
            sys.exit(1)

    # 检查预训练模型
    if not args.no_pretrained:
        if not os.path.exists(args.model):
            # 可能只是模型名称 (如 yolo11n.pt)，会自动下载
            print(f"  [Download]  预训练模型 {args.model} 将由 Ultralytics 自动下载")

    # 开始训练
    results, history = train_yolo(
        data=args.data,
        model_name=args.model,
        epochs=args.epochs,
        img_size=args.img_size,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        project=args.project,
        name=args.name,
        patience=args.patience,
        augment=not args.no_augment,
        resume=args.resume,
        pretrained=not args.no_pretrained,
        lr0=args.lr0,
        cos_lr=args.cos_lr,
        save_period=args.save_period,
        exist_ok=args.exist_ok,
    )


if __name__ == "__main__":
    main()
