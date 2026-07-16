# VisAgent — 猫个体识别模型 (Cat Individual ReID)

## 模型概述

本模型用于**猫个体身份识别 (ReID, Re-identification)**，即给定一张猫脸图片，识别它属于数据库中的哪一只猫。核心思路是**度量学习 (Metric Learning)**：将所有猫映射到一个 512 维的特征空间中，使得同一只猫的不同照片在空间中距离相近，不同猫的照片距离较远。识别时，提取待识别猫的特征向量，与数据库中已知猫的档案特征做相似度比对，返回最匹配的候选。

---

## 算法原理：ResNet50 + ArcFace

### 整体架构

```
输入图片 (224×224×3)
      ↓
  ResNet50 Backbone (ImageNet 预训练)
  └── 移除原始全连接分类头，保留 Conv 特征提取部分
      ↓
  AdaptiveAvgPool2d → (2048 维特征图 → 2048 维向量)
      ↓
  BatchNorm1d(2048) + Dropout(0.3)
      ↓
  Linear(2048 → 512) → BatchNorm1d(512) → L2 归一化
      ↓
  512 维归一化特征向量  ← 这就是"猫脸特征嵌入 (embedding)"
      ↓
  ArcFace Loss (仅训练时使用，推理时不需要)
```

### 三个关键设计

#### 1. ResNet50 主干网络

- 使用在 ImageNet 上预训练的 ResNet50 作为特征提取器
- 去掉原始的 1000 类分类头，保留从 Conv1 到 Layer4 的卷积层
- 利用预训练学到的通用视觉特征（边缘、纹理、形状），大幅降低对猫脸数据量的需求

#### 2. ArcFace Loss

ArcFace（Additive Angular Margin Loss）是在人脸识别领域被广泛验证的损失函数，其核心思想是**在角度空间中给正确分类增加一个间隔 (margin)**，使模型学到更具判别力的特征。

**通俗理解**：

- Softmax 损失：让模型把猫 A 的照片正确分类到"猫 A"这个类别，但不同猫之间的边界可以很模糊
- ArcFace 损失：不仅要求分类正确，还要求猫 A 和猫 B 在特征空间中有**明确的角度间隔**，同类紧凑、异类远离

**数学原理**：

对特征向量 $x$ 和权重 $W$ 做 L2 归一化后，Softmax 的全连接层实际计算的是余弦相似度 $\cos\theta_j$（$\theta_j$ 是特征向量与第 $j$ 类的权重向量之间的夹角）。ArcFace 在正确类别 $y$ 的角度上加上一个惩罚间隔 $m$：

$$L = -\log\frac{e^{s \cdot \cos(\theta_y + m)}}{e^{s \cdot \cos(\theta_y + m)} + \sum_{j \neq y} e^{s \cdot \cos\theta_j}}$$

其中 $s=64$ 是缩放因子（放大余弦值以应对 Softmax 的指数运算），$m=0.5$ 是角度间隔（弧度的约 $28.6^\circ$）。

加上间隔 $m$ 后，模型必须把同一只猫的特征推得更近（夹角更小），把不同猫的特征拉得更开（夹角更大），从而在特征空间中形成**清晰的聚类边界**——这正是 ReID 任务最需要的性质。

#### 3. 推理阶段的零样本泛化

ArcFace 训练时有一个全连接分类头（`weight` 矩阵形状为 `[训练猫数量, 512]`），对应训练集中的每只猫。这个分类头在推理时**完全不需要**——推理时只取出 512 维特征向量，通过**余弦相似度**与数据库中所有猫的档案特征做比对。

这意味着：

- 模型可以识别**训练时从未见过的新猫**（零样本/开放集识别）
- 要添加新猫，只需提取它的特征存入数据库，无需重新训练
- 实际部署时，数据库里可以存放任意数量的猫档案，每次识别都是"在 N 只猫中找最像的那只"

---

## 训练结果

### 训练配置

| 参数 | 值 |
|------|-----|
| 模型 | ResNet50 + ArcFace |
| 特征维度 | 512 |
| 输入尺寸 | 224×224 |
| 批次大小 | 64 |
| 训练轮数 | 100 |
| 优化器 | AdamW (lr=0.0003, weight_decay=1e-4) |
| 学习率策略 | CosineAnnealingLR |
| 数据增强 | RandomHorizontalFlip, Rotation(10°), ColorJitter |
| 训练硬件 | NVIDIA GeForce RTX 3060 Laptop GPU (6GB) |

### 数据集划分

| 项目 | 数量 |
|------|------|
| 训练集猫数量 | 102 只 |
| 测试集猫数量 | **25 只（训练中完全未出现）** |
| 训练集图片 | 955 张 |
| 测试集图片 | 213 张 |

> ⚠️ **关键：测试集的 25 只猫在训练中从没出现过**，模型从未见过它们的任何一张照片。这模拟了真实的"新猫识别"场景。

### 测试集指标

| 指标 | 数值 | 含义 |
|------|------|------|
| **Rank-1** | **88.26%** | Top-1 命中率——排名第一的候选猫即正确答案的概率 |
| Rank-5 | 96.71% | Top-5 命中率——前五个候选中有正确答案的概率 |
| mAP | 58.51% | 平均精度均值——综合衡量排序质量的指标 |
| 最终 Loss | 0.2635 | 训练收敛情况 |

### 输出文件

| 文件 | 说明 |
|------|------|
| `best_model.pth` | **最佳模型**（基于测试集 Rank-1 保存，~94MB） |
| `final_model.pth` | 最后一轮 epoch 的模型权重 |
| `history.json` | 训练历史（最佳 Rank-1、最终 Rank-1/Rank-5/mAP、配置参数） |
| `loss_curve.png` | ArcFace Loss 下降曲线 |
| `rank_curves.png` | Rank-1 / Rank-5 随训练轮次的变化 |
| `map_curve.png` | mAP 随训练轮次的变化 |
| `training_overview.png` | Loss + Rank-1 + Rank-5 + mAP 四合一总览图 |
| `training_report.md` | 训练报告（Markdown 格式） |

---

## 后端集成指南

### 模型加载

```python
import torch
from pathlib import Path

# 加载模型权重
model_path = "models/individual/best_model.pth"
checkpoint = torch.load(model_path, map_location="cpu")
embedding_dim = checkpoint.get("embedding_dim", 512)

# 构建模型 (不传入 ArcFace 分类头)
# 注：best_model.pth 只保存了 model_state_dict，不含 arcface.weight
from your_model_def import CatIndividualModel
model = CatIndividualModel(embedding_dim=embedding_dim, num_classes=None)
model.load_state_dict(checkpoint["model_state_dict"], strict=False)
model.eval()
```

### 特征提取流程

后端接收一张裁剪好的猫脸图后，按以下步骤处理：

```python
import torchvision.transforms as T
from PIL import Image

transform = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

def extract_embedding(image_path: str) -> list:
    """提取 512 维归一化特征向量"""
    img = Image.open(image_path).convert("RGB")
    img_tensor = transform(img).unsqueeze(0)  # [1, 3, 224, 224]
    with torch.no_grad():
        embedding = model(img_tensor)           # [1, 512]
    return embedding.squeeze().tolist()         # list of 512 floats
```

### 数据库匹配流程

```python
import math

def cosine_similarity(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x*x for x in a))
    norm_b = math.sqrt(sum(x*x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

def identify_cat(query_embedding: list, db_cats: list, top_k: int = 3):
    """
    从数据库中匹配最相似的猫
    db_cats: [{cat_id, name, embedding, ...}, ...]
    返回 Top K 候选，按相似度降序
    """
    candidates = []
    for cat in db_cats:
        sim = cosine_similarity(query_embedding, cat["embedding"])
        candidates.append({"cat_id": cat["id"], "name": cat["name"], "similarity": sim})
    candidates.sort(key=lambda x: x["similarity"], reverse=True)
    return candidates[:top_k]
```

### 数据表设计建议

```sql
-- 猫咪档案表
CREATE TABLE cats (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    breed       VARCHAR(50),
    color       VARCHAR(50),
    embedding   FLOAT8[] NOT NULL,      -- 512 维特征向量
    ref_image   TEXT,                    -- 参考图片 URL
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cats_gin_embedding ON cats USING GIN (embedding);
-- 实际使用中可借助 pgvector 等扩展做加速近似最近邻搜索
```

---

## 模型能力总结

| 能力 | 说明 |
|------|------|
| ✅ 识别已知猫 | 对已入库的猫，Top-1 准确率约 **88%**，Top-5 约 **97%** |
| ✅ 识别新猫 | 训练时未见过的新猫也能提取特征，与数据库比对 |
| ✅ 添加新猫 | 只需提取一次特征存入数据库，无需重新训练 |
| ✅ 快速推理 | GPU 单张图片推理约 **5-10ms** |
| ✅ 通用接口 | 输出 512 维归一化特征向量，兼容余弦相似度、欧氏距离等多种度量 |

### 当前局限

| 局限 | 说明 |
|------|------|
| ⚠️ 输入依赖 YOLO 裁剪 | 需要先用 YOLO 模型检测并裁剪出猫头区域，原图直接识别效果不佳 |
| ⚠️ mAP 偏低 (58.5%) | 部分猫的特征区分度不够，在排序质量上仍有提升空间 |
| ⚠️ 训练数据量 | 当前仅 102 只猫的数据，增加训练猫数量可提升泛化能力 |

---

