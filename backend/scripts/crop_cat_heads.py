"""
猫头裁剪脚本
用训练好的 YOLO 品种检测模型（Model 1），对个体数据集中的原图批量检测并裁剪猫头。

问题背景：
    cat_XXX/ 里的图片是未经裁剪的原图（猫只占画面的一部分），
    直接用于个体识别训练导致模型学到的是背景而非猫脸特征。

使用方法：
    python scripts/crop_cat_heads.py
        --input-dir   /e/program/second/data_root          # 原图目录
        --output-dir  /e/program/second/data_root_cropped   # 裁剪后输出目录
        --model       backend/models/cat_breeds/best.pt     # YOLO 模型路径
        --min-confidence 0.5                                # 最低检测置信度
        --padding    0.05                                   # 裁剪框向外扩比例
        --output-size 640                                   # 输出图片尺寸
"""

import os
import sys
import argparse
import math
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ── 缓存重定向 ──
CACHE_BASE = Path("E:/program/merged_cat_breeds/.cache")
CACHE_BASE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("ULTRALYTICS_CACHE_DIR", str(CACHE_BASE / "ultralytics"))
os.environ.setdefault("TORCH_HOME", str(CACHE_BASE / "torch"))
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_BASE / "matplotlib"))
for _dir in ["ultralytics", "torch", "matplotlib"]:
    (CACHE_BASE / _dir).mkdir(parents=True, exist_ok=True)

import cv2
import torch
import numpy as np
from tqdm import tqdm
from ultralytics import YOLO

# ── 支持的图片格式 ──
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def expand_bbox(x1, y1, x2, y2, img_w, img_h, padding=0.05):
    """
    将检测框向外扩展 padding 比例，保证猫头不会切掉耳朵/下巴。
    扩展后坐标限制在图片范围内。
    """
    box_w = x2 - x1
    box_h = y2 - y1
    expand_w = box_w * padding
    expand_h = box_h * padding

    new_x1 = max(0, int(x1 - expand_w))
    new_y1 = max(0, int(y1 - expand_h))
    new_x2 = min(img_w, int(x2 + expand_w))
    new_y2 = min(img_h, int(y2 + expand_h))

    return new_x1, new_y1, new_x2, new_y2


def process_cat_folder(
    cat_folder: Path,
    model: YOLO,
    output_root: Path,
    min_confidence: float,
    padding: float,
    output_size: int,
    stats: dict,
):
    """
    处理一只猫的所有图片：
      1. 用 YOLO 检测猫头
      2. 取置信度最高的检测框
      3. 裁剪并保存到输出目录
    """
    cat_id = cat_folder.name
    out_dir = output_root / cat_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # 收集所有图片
    image_paths = sorted([
        p for p in cat_folder.iterdir()
        if p.suffix.lower() in IMG_EXTS
    ])

    if not image_paths:
        stats["empty_folders"] += 1
        return

    folder_total = len(image_paths)
    folder_detected = 0
    folder_no_detection = []

    for img_path in image_paths:
        # ── 推理 ──
        results = model.predict(
            source=str(img_path),
            conf=min_confidence,
            iou=0.5,
            imgsz=640,
            device=0 if torch.cuda.is_available() else "cpu",
            verbose=False,
            max_det=5,  # 最多检测 5 个目标
        )

        # 读取原图尺寸
        orig = cv2.imread(str(img_path))
        if orig is None:
            stats["read_errors"] += 1
            continue
        img_h, img_w = orig.shape[:2]

        # ── 提取检测结果 ──
        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            folder_no_detection.append(img_path.name)
            stats["no_detection"] += 1
            continue

        # 取置信度最高的框（假设每张图只有一只目标猫）
        best_idx = int(boxes.conf.argmax())
        conf = float(boxes.conf[best_idx])
        cls_id = int(boxes.cls[best_idx])
        x1, y1, x2, y2 = map(float, boxes.xyxy[best_idx].tolist())

        # ── 扩展框并裁剪 ──
        x1, y1, x2, y2 = expand_bbox(x1, y1, x2, y2, img_w, img_h, padding)

        # 安全检查：裁剪区域必须至少 20×20 像素
        if (x2 - x1) < 20 or (y2 - y1) < 20:
            stats["crop_too_small"] += 1
            continue

        cropped = orig[y1:y2, x1:x2]

        # ── 缩放到统一尺寸（保持宽高比，填充黑边） ──
        h, w = cropped.shape[:2]
        scale = output_size / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(cropped, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

        # 填充到正方形（黑边，后续训练会用 Crop/Resize 处理）
        canvas = np.zeros((output_size, output_size, 3), dtype=np.uint8)
        y_offset = (output_size - new_h) // 2
        x_offset = (output_size - new_w) // 2
        canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized

        # ── 输出文件名：原文件名 + _crop + 置信度 ──
        stem = img_path.stem
        out_name = f"{stem}_crop_{conf:.2f}.jpg"
        out_path = out_dir / out_name
        cv2.imwrite(str(out_path), canvas, [cv2.IMWRITE_JPEG_QUALITY, 92])

        folder_detected += 1
        stats["total_cropped"] += 1

    # ── 记录这只猫的统计 ──
    stats["per_cat"][cat_id] = {
        "total": folder_total,
        "cropped": folder_detected,
        "no_detection": folder_no_detection,
    }

    if folder_detected == 0:
        stats["cats_with_zero_crops"] += 1
    else:
        stats["cats_with_crops"] += 1


def print_report(stats: dict, elapsed: float):
    """打印裁剪报告"""
    print(f"\n{'='*60}")
    print(f"  裁剪完成！")
    print(f"{'='*60}")
    print(f"  总耗时:           {elapsed:.1f} 秒")
    print(f"  总猫数:           {stats['total_cats']}")
    print(f"  总图片数:         {stats['total_images']}")
    print(f"  ────────────────────────────────────")
    print(f"  成功裁剪:         {stats['total_cropped']} 张")
    print(f"  无检测:           {stats['no_detection']} 张（需人工检查）")
    print(f"  读取失败:         {stats['read_errors']} 张")
    print(f"  裁剪太小:         {stats['crop_too_small']} 张")
    print(f"  ────────────────────────────────────")
    print(f"  有裁剪的猫:       {stats['cats_with_crops']} 只")
    print(f"  零裁剪的猫:       {stats['cats_with_zero_crops']} 只（需人工检查）")
    print(f"  空文件夹:         {stats['empty_folders']} 个")

    # 输出无检测的图片列表
    no_det_cats = {
        cid: info["no_detection"]
        for cid, info in stats["per_cat"].items()
        if info["no_detection"]
    }
    if no_det_cats:
        print(f"\n  ⚠️  以下猫的图片未检测到猫头（共 {sum(len(v) for v in no_det_cats.values())} 张）:")
        for cid, imgs in sorted(no_det_cats.items()):
            print(f"    {cid}: {', '.join(imgs[:5])}{'...' if len(imgs) > 5 else ''}")


def main():
    parser = argparse.ArgumentParser(
        description="用 YOLO 模型批量裁剪猫头（个体识别数据集预处理）"
    )
    parser.add_argument(
        "--input-dir", type=str,
        default="/e/program/second/data_root",
        help="个体数据集根目录（包含 cat_XXX 子文件夹）",
    )
    parser.add_argument(
        "--output-dir", type=str,
        default="/e/program/second/data_root_cropped",
        help="裁剪后输出目录",
    )
    parser.add_argument(
        "--model", type=str,
        default="E:/mycode/visagent/visagent/backend/runs/train_cat_breeds/cat_breeds_v1/weights/best.pt",
        help="YOLO 模型路径",
    )
    parser.add_argument(
        "--min-confidence", type=float, default=0.5,
        help="最低检测置信度（低于此值视为未检测到猫头）",
    )
    parser.add_argument(
        "--padding", type=float, default=0.05,
        help="检测框向外扩展比例（避免切掉耳朵/下巴）",
    )
    parser.add_argument(
        "--output-size", type=int, default=640,
        help="输出图片尺寸（正方形）",
    )
    parser.add_argument(
        "--device", type=str, default=None,
        help="推理设备（如 cuda:0 / cpu，默认自动选择）",
    )
    args = parser.parse_args()

    input_root = Path(args.input_dir)
    output_root = Path(args.output_dir)
    model_path = Path(args.model)

    # ── 校验 ──
    if not input_root.exists():
        print(f"❌ 输入目录不存在: {input_root}")
        sys.exit(1)
    if not model_path.exists():
        print(f"❌ 模型文件不存在: {model_path}")
        sys.exit(1)

    # ── 加载模型 ──
    print(f"\n{'='*60}")
    print(f"  猫头批量裁剪")
    print(f"{'='*60}")
    print(f"  输入:  {input_root}")
    print(f"  输出:  {output_root}")
    print(f"  模型:  {model_path}")
    print(f"  置信度阈值: {args.min_confidence}")
    print(f"  框扩展:     {args.padding*100:.0f}%")
    print(f"  输出尺寸:   {args.output_size}×{args.output_size}")

    device = args.device
    if device is None:
        device = 0 if torch.cuda.is_available() else "cpu"
    print(f"  设备:  {device}")

    print(f"\n  [加载模型] {model_path} ...")
    model = YOLO(str(model_path))
    print(f"  ✅ 模型加载完成，共 {len(model.names)} 类")

    # ── 扫描数据集 ──
    cat_folders = sorted([
        f for f in input_root.iterdir()
        if f.is_dir() and f.name.startswith("cat_")
    ])
    total_images = sum(
        len([p for p in f.iterdir() if p.suffix.lower() in IMG_EXTS])
        for f in cat_folders
    )
    print(f"\n  共 {len(cat_folders)} 只猫, {total_images} 张图片")

    # ── 创建输出目录 ──
    output_root.mkdir(parents=True, exist_ok=True)

    # ── 批量处理 ──
    stats = {
        "total_cats": len(cat_folders),
        "total_images": total_images,
        "total_cropped": 0,
        "no_detection": 0,
        "read_errors": 0,
        "crop_too_small": 0,
        "empty_folders": 0,
        "cats_with_crops": 0,
        "cats_with_zero_crops": 0,
        "per_cat": {},
    }

    start_time = datetime.now()
    print(f"\n  [处理中] 开始裁剪...\n")

    for cat_folder in tqdm(cat_folders, desc="裁剪进度", unit="cat"):
        process_cat_folder(
            cat_folder=cat_folder,
            model=model,
            output_root=output_root,
            min_confidence=args.min_confidence,
            padding=args.padding,
            output_size=args.output_size,
            stats=stats,
        )

    elapsed = (datetime.now() - start_time).total_seconds()

    # ── 生成报告 ──
    print_report(stats, elapsed)

    # ── 生成清洗后的索引文件（给训练脚本用） ──
    # 只保留有裁剪结果的猫
    valid_cats = [
        cid for cid, info in stats["per_cat"].items()
        if info["cropped"] >= 3
    ]
    invalid_cats = [
        cid for cid, info in stats["per_cat"].items()
        if info["cropped"] < 3
    ]

    index_path = output_root / "_crop_index.txt"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(f"# 猫头裁剪索引\n")
        f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 有效猫（≥3张裁剪）: {len(valid_cats)}\n")
        f.write(f"# 无效猫（<3张裁剪）: {len(invalid_cats)}\n")
        f.write(f"# 需检查猫（0张裁剪）: {stats['cats_with_zero_crops']}\n\n")
        f.write(f"VALID_CATS={valid_cats}\n")
        f.write(f"INVALID_CATS={invalid_cats}\n")
    print(f"\n  📋 索引文件: {index_path}")

    # ── 保存完整报告 ──
    import json
    report_path = output_root / "_crop_report.json"
    report_data = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input_dir": str(input_root),
        "output_dir": str(output_root),
        "model": str(model_path),
        "config": {
            "min_confidence": args.min_confidence,
            "padding": args.padding,
            "output_size": args.output_size,
        },
        "stats": {k: v for k, v in stats.items() if k != "per_cat"},
        "valid_cats_count": len(valid_cats),
        "invalid_cats_count": len(invalid_cats),
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    print(f"  📋 报告文件: {report_path}")

    # ── 提示下一步 ──
    print(f"\n{'='*60}")
    print(f"  下一步建议:")
    print(f"  1. 用裁剪后的数据重新训练个体识别模型:")
    print(f"     python scripts/train_individual.py --data {output_root}")
    if invalid_cats:
        print(f"  2. ⚠️  {len(invalid_cats)} 只猫裁剪结果不足3张，建议人工检查:")
        for cid in invalid_cats[:10]:
            info = stats["per_cat"].get(cid, {})
            print(f"     - {cid}: 原图{info.get('total', '?')}张, 成功裁剪{info.get('cropped', 0)}张")
        if len(invalid_cats) > 10:
            print(f"     ... 等 {len(invalid_cats)} 只")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
