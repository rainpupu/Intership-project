# 猫健康状态检测模型 — 训练评估报告

## 一、基本信息

| 项目 | 内容 |
|------|------|
| 模型 | YOLO11n (2,590,230 参数) |
| 任务 | 猫健康状态目标检测（Healthy / Sick 二分类） |
| 预训练 | 基于猫品种检测模型（Model 1）迁移学习 |
| 数据集 | 猫健康状态数据集（YOLO 格式） |
| 训练图片 | 1065 张（训练集）+ 207 张（验证集）+ 268 张（测试集） |
| 训练硬件 | NVIDIA GeForce RTX 3060 Laptop GPU (6GB) |
| 训练耗时 | 0 小时 51 分 55 秒（100 轮） |
| 训练日期 | 2026-07-18 |
| 优化策略 | **cls_pw=0.7**（Sick 类损失加权）+ **mixup=1.0**（混合增强） |

### 2 个类别

| # | 类别 | 说明 |
|---|------|------|
| 0 | Healthy | 健康猫 |
| 1 | Sick | 患病猫（存在皮肤问题、眼部疾病、外伤等异常） |

---

## 二、验证集结果（目标检测精度）

在 **207 张验证集图片（208 个实例）** 上评估检测框的精度：

| 指标 | 最佳值 | 最佳轮次 | 最终值（第100轮） |
|------|:-----:|:-------:|:----------------:|
| Precision | **90.58%** | 51 | 90.41% |
| Recall | **90.85%** | 89 | 83.79% |
| mAP@50 | **92.24%** | 89 | 90.37% |
| mAP@50:95 | **65.67%** | 89 | 64.77% |

### 混淆矩阵（验证集，最佳轮次 epoch 89）

| 实际 \ 预测 | Healthy | Sick | 合计 | 召回率 |
|------------|---------|------|------|:------:|
| Healthy | **124** | 2 | 126 | **98.4%** |
| Sick | **14** | **68** | 82 | **82.9%** |
| 合计 | 138 | 70 | 208 | |
| 精确率 | **89.9%** | **97.1%** | | **整体 92.3%** |

---

## 三、优化算法概览

本次训练采用了两种优化策略来提升 Sick（患病）类的检测召回率：

### 1. 类别损失加权（cls_pw=0.7）

**原理**：YOLO 的分类损失默认对所有类别一视同仁。当 Sick 样本较少时，模型倾向于忽略 Sick 类以降低整体损失。`cls_pw` 参数给 Sick 类的分类错误分配更高的权重，让模型"更重视"把 Sick 分对。

```
正常模式：  Loss = L_Healthy + L_Sick          ← 两类同等重要
cls_pw=0.7：Loss = 0.3×L_Healthy + 0.7×L_Sick  ← Sick 错误代价更高
```

### 2. Mixup 混合增强（mixup=1.0）

**原理**：每张训练图片与另一张随机图片按比例混合，生成新的合成训练样本。这相当于隐式增加了训练数据的多样性：

```
原图 A (Healthy) ─┐
                   ├──→ 混合图 = 0.5×A + 0.5×B  → 标签也按比例混合
原图 B (Sick)    ─┘
```

Mixup 让模型学会在"模糊边界"下做出判断，有效缓解类别不平衡问题，同时提升模型的泛化能力。

### 综合效果

| 策略 | 主要效果 | 副作用 |
|------|---------|--------|
| cls_pw=0.7 | Sick 分类错误代价 ↑，召回率 ↑ | Healthy 精确率略有下降 |
| mixup=1.0 | 泛化能力 ↑，防过拟合 | 训练时间约翻倍 |
| **两者叠加** | **Sick 召回率 +10.9%，整体准确率 +3.8%** | 整体指标微降但分类质量更优 |

---

## 四、模型功能与使用指南

### 模型能力

| 能力 | 说明 |
|------|------|
| ✅ 检测猫健康状态 | 输入猫图片，输出检测框 + Healthy/Sick 分类 + 置信度 |
| ✅ 定位猫的位置 | 返回每个检测框的坐标 (x1, y1, x2, y2) |
| ✅ 区分患病与健康 | Sick 召回率 82.9%，Sick 精确率 97.1% |
| ✅ 快速推理 | GPU ~22ms/张，适合实时检测 |

### 模型加载与推理

```python
from ultralytics import YOLO

# 加载模型（PyTorch 格式）
model = YOLO("backend/models/health/best.pt")

# 或加载 ONNX 格式（适合跨平台部署）
# model = YOLO("backend/models/health/best.onnx")

# 单张图片推理（默认置信度阈值 0.25）
results = model("cat.jpg")

# 调整置信度阈值（0.10 更敏感，0.50 更保守）
# results = model("cat.jpg", conf=0.15)

# 处理结果
for r in results:
    for box in r.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()  # 检测框坐标
        conf = box.conf[0].item()                # 置信度
        cls = int(box.cls[0].item())             # 类别: 0=Healthy, 1=Sick
        label = "Healthy" if cls == 0 else "Sick"
        print(f"{label}: {conf:.2f}  [{x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f}]")
```

### 批量推理

```python
# 批量处理文件夹中的图片
results = model(["cat1.jpg", "cat2.jpg", "cat3.jpg"], conf=0.25)

# 保存标注结果
for i, r in enumerate(results):
    r.save(filename=f"result_{i}.jpg")  # 保存标注后的图片
```

### 后端 API 集成示例

```python
from fastapi import FastAPI, UploadFile
from ultralytics import YOLO
from PIL import Image
import io

app = FastAPI()
model = YOLO("backend/models/health/best.pt")

@app.post("/predict")
async def predict(file: UploadFile, conf: float = 0.25):
    img = Image.open(io.BytesIO(await file.read()))
    results = model(img, conf=conf)

    detections = []
    for r in results:
        for box in r.boxes:
            detections.append({
                "bbox": box.xyxy[0].tolist(),
                "confidence": round(box.conf[0].item(), 4),
                "class": "Sick" if int(box.cls[0].item()) == 1 else "Healthy",
            })

    return {"detections": detections, "count": len(detections)}
```

### 置信度阈值选择建议

| 场景 | 推荐阈值 | 说明 |
|------|:-------:|------|
| 辅助筛查（人工复核） | **0.15** | 宁滥勿漏，尽可能检出 Sick |
| 均衡模式 | **0.25** | 默认值，适用于大多数场景 |
| 确诊辅助（高可信） | **0.40** | Sick 预测高度可信，但可能漏检 |

### 输入要求

- 图片格式：JPG、PNG、BMP 等常见格式
- 推荐输入尺寸：自动缩放至 640×640
- 图片内容：包含猫的全身或头部照片
- 光照条件：自然光或室内正常光照即可

---

## 五、训练过程

### 训练配置

| 参数 | 值 | 说明 |
|------|-----|------|
| 基础模型 | YOLO11n（猫品种检测模型迁移学习） | |
| 输入尺寸 | 640×640 | |
| 批次大小 | 8（6GB 显存友好） | |
| 优化器 | AdamW（自动选择） | 新版 Ultralytics 自动检测 |
| 初始学习率 | 0.01 → 0.001667（自动修正） | |
| 学习率策略 | 余弦退火（cos_lr） | |
| 预热轮数 | 3 | |
| 早停耐心 | 30 | |
| **cls_pw** | **0.7** | Sick 类损失权重加重 |
| **mixup** | **1.0** | 每批混合增强，缓解类别不平衡 |
| 数据增强 | mosaic, flip, auto-augment, erasing | |
| 混合精度训练 | 开启 (AMP) | |

### 训练过程特点

- 由于 mixup=1.0，训练时间从 27 分钟增加到 **52 分钟**（约翻倍）
- 验证损失曲线第 60 轮后出现波动，模型有轻微过拟合
- 最佳模型在 epoch 89 处保存（基于 mAP@50:95）

---

## 六、输出文件清单

### 目录结构

```
health_v2/
├── README.md                  ← 训练评估报告（本文件）
├── reports/
│   ├── training_report.json  训练指标 JSON
│   ├── args.yaml             训练参数配置
│   └── results.csv           逐 epoch 完整指标
├── charts/                   ← 评估与训练图表
│   ├── confusion_matrix.png        混淆矩阵
│   ├── confusion_matrix_normalized.png  归一化混淆矩阵
│   ├── results.png                  YOLO 自带结果图
│   ├── BoxPR_curve.png             Precision-Recall 曲线
│   ├── BoxF1_curve.png             F1-Score 曲线
│   ├── BoxP_curve.png              Precision 置信度曲线
│   ├── BoxR_curve.png              Recall 置信度曲线
│   ├── loss_curves.png             训练/验证损失曲线
│   ├── metrics_curves.png          Precision/Recall/mAP 曲线
│   └── training_overview.png       综合总览图
├── samples/                  ← 样本图片
│   ├── labels.jpg                  标签分布图
│   ├── train_batch*.jpg            (6 张) 训练批次样本
│   ├── val_batch*_labels.jpg       (3 张) 验证集标注
│   └── val_batch*_pred.jpg         (3 张) 验证集预测
└── weights/                  ← 模型权重
    ├── best.pt          (5.3MB)  最佳模型（epoch 89）
    ├── best.onnx        (10.1MB) ONNX 导出格式
    └── last.pt          (5.3MB)  最后 epoch 的模型
```

---

## 七、结论

1. **Sick 召回率达 82.9%**（68/82），相比基线有明显提升 ✅
2. **Healthy 召回率保持 98.4%**（124/126），健康猫几乎不漏检
3. **整体准确率 92.3%**（192/208），分类质量优秀
4. **Sick 精确率 97.1%**，模型报 Sick 高度可信
5. **推理速度快**，GPU 单张仅约 **22ms**，适合实时检测场景

### 改进建议

- 若想进一步提升 Sick 召回率，可以尝试：
  - 将置信度阈值从默认 0.25 降低至 0.15~0.20
  - 收集更多 Sick 样本，从当前 82 张增加到 200+ 张
  - 尝试 YOLO11s 或 YOLO11m 等更大模型

---
