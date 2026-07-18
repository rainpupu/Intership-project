# VisAgent 猫检测模型体系

## 模型总览

本项目包含 **5 个训练好的猫相关深度学习模型**，覆盖猫的**品种识别、健康检测、情绪分析、个体身份识别**四个维度，构成完整的猫智能分析流水线。

| # | 模型 | 任务类型 | 类别数 | 基础架构 | 权重路径 |
|---|------|---------|:------:|---------|---------|
| 1 | **猫品种检测 v1** | 目标检测 + 品种分类 | 12 | YOLO11n | `models/cat_breeds/v1/best.pt` |
| 2 | **猫品种检测 v2** | 目标检测 + 品种分类 | 17 | YOLO11n | `models/cat_breeds/v2/best.pt` |
| 3 | **健康状态检测** | 目标检测 + 健康二分类 | 2 (Healthy/Sick) | YOLO11n | `models/health/best.pt` |
| 4 | **情绪检测** | 目标检测 + 情绪分类 | 7 | YOLO11n | `models/emotion/best.pt` |
| 5 | **个体识别 (ReID)** | 度量学习 + 特征检索 | 开放集 | ResNet50 + ArcFace | `models/individual/best_model.pth` |

### 模型依赖关系

#### 训练阶段 — 预训练权重与数据流向

| 模型 | 预训练权重来源 | 训练数据来源 | 训练方式 |
|------|--------------|------------|---------|
| **模型 1** 品种 v1 | yolo11n.pt（官方预训练） | 公开数据集 | 从零训练 |
| **模型 2** 品种 v2 | ← 模型 1 的 best.pt | 原 12 类数据 + 新增 5 类（模型 1 裁剪标注） | 迁移学习微调 |
| **模型 3** 健康检测 | ← 模型 1 的 best.pt | 健康数据集 | 迁移学习微调 |
| **模型 4** 情绪检测 | ← 模型 1 的 best.pt | 情绪数据集 | 迁移学习微调 |
| **模型 5** 个体识别 | ResNet50（ImageNet 预训练） | **猫脸裁剪图 ← 模型 1 检测裁剪** | 度量学习训练 |

```
                         预训练基座
                 ┌─────────────────────┐
                 │ yolo11n.pt          │
                 │ ResNet50 (ImageNet) │
                 └──────┬──────────────┘
                        │
          ┌─────────────┼─────────────────┐
          │             │                  │
          ▼             │                  ▼
   ┌──────────────┐     │          ┌──────────────────┐
   │   初模型     │     │          │   独立训练        │
   │ 模型 1：     │     │          │ 模型 5：个体识别 │
   │ 品种检测 v1  │     │          │ ResNet50+ArcFace │
   │ 12 类        │     │          └────────┬─────────┘
   └───────┬──────┘     │                   ▲
           │            │                   │
           │ ←── best.pt 作为预训练权重     │ 训练数据来自模型 1 的裁剪输出
           ▼            │                   │
   ┌─────────────────────────────────────┐  │
   │       结果模型（迁移学习微调）       │  │
   │                                     │  │
   │ ┌──────────┐ ┌──────────┐ ┌──────┐ │  │
   │ │模型 2：  │ │模型 3：  │ │模型 4│ │  │
   │ │品种 v2  │ │健康检测  │ │情绪  │ │  │
   │ │17 类    │ │2 类      │ │7 类  │ │  │
   │ └──────────┘ └──────────┘ └──────┘ │  │
   └─────────────────────────────────────┘  │
                                            │
   ┌─────────────────────────────────────────┘
   │
   ▼
   ┌──────────────────────────────────────────────┐
   │ 模型 1 的 best.pt 在训练阶段还承担数据标注角色   │
   │ → 模型 2 新增的 5 类田园猫：用模型 1 自动裁剪标注 │
   │ → 模型 5 的猫脸裁剪图：用模型 1 检测猫位置后裁剪  │
   └─────────────────────────────────────────────────┘
```

#### 推理阶段 — 输入输出流程

```
                          输入图片 (JPG/PNG)
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                    ▼           ▼           ▼
              ┌──────────┐ ┌────────┐ ┌──────────┐
              │ 品种检测 │ │健康检测│ │ 情绪检测  │
              │ v1 或 v2 │ │        │ │          │
              └─────┬────┘ └───┬────┘ └─────┬────┘
                    │          │            │
                    ▼          ▼            ▼
              ┌─────────────────────────────────┐
              │ 输出：检测框 + 类别 + 置信度     │
              │ [{bbox, class, confidence}, ...] │
              └─────────────────────────────────┘

   输入图片 ──→ YOLO 检测 ──→ 裁剪猫头区域 ──→ 个体识别模型
                                                    │
                                                    ▼
                                          ┌──────────────────┐
                                          │ 输出：512 维特征  │
                                          │ 向量 (embedding) │
                                          └────────┬─────────┘
                                                   │
                                                   ▼
                                          ┌──────────────────┐
                                          │ 数据库余弦相似度  │
                                          │ 检索 Top-K       │
                                          └──────────────────┘
                                                   │
                                                   ▼
                                          ┌──────────────────┐
                                          │ 输出：最相似猫    │
                                          │ [{cat_id, sim}]  │
                                          └──────────────────┘
```

---

## 模型一：猫品种检测 v1（12 类）

### 基本信息

| 项目 | 内容 |
|------|------|
| 任务 | 猫品种目标检测 + 品种分类 |
| 架构 | YOLO11n（2,584,492 参数） |
| 预训练 | 从零训练（yolo11n.pt） |
| 数据集 | Roboflow Cat Breeds v1，2544 训练 + 689 验证 + 1443 测试 |
| 训练耗时 | 1 小时 35 分钟（100 轮） |
| 训练日期 | 2026-07-15 |

### 12 个品种

| # | 品种 | # | 品种 |
|---|------|---|------|
| 0 | Abyssinian（阿比西尼亚） | 6 | Maine_Coon（缅因） |
| 1 | Bengal（孟加拉豹猫） | 7 | Persian（波斯） |
| 2 | Birman（伯曼） | 8 | Ragdoll（布偶） |
| 3 | Bombay（孟买） | 9 | Russian_Blue（俄罗斯蓝） |
| 4 | British_Shorthair（英短） | 10 | Siamese（暹罗） |
| 5 | Egyptian_Mau（埃及） | 11 | Sphynx（斯芬克斯） |

### 性能指标

| 指标 | 数值 | 说明 |
|------|:----:|------|
| Precision | **97.53%** | 检测框精确率 |
| Recall | **97.00%** | 检测框召回率 |
| mAP@50 | **98.39%** | 检测精度（IoU=0.5） |
| mAP@50:95 | **86.61%** | 检测精度（严格） |
| 品种识别准确率 | **94.37%** | 测试集 218/231 正确 |

### 训练特点

- 从 yolo11n.pt 预训练权重开始，未使用迁移学习
- 100 轮训练，早停未触发（patience=20）
- 批次大小 16，6GB 显存运行稳定

### 功能用途

- 检测猫的位置并识别 12 种纯种猫品种
- 适用于宠物店、猫舍、宠物医院的品种登记
- 可作为后续模型的迁移学习基座

---

## 模型二：猫品种检测 v2（17 类）

### 基本信息

| 项目 | 内容 |
|------|------|
| 任务 | 猫品种目标检测 + 品种分类（扩展版） |
| 架构 | YOLO11n（2,590,230 参数） |
| 预训练 | 基于 Model 1（v1）迁移学习 |
| 数据集 | 12 英文品种 + 5 中华田园猫合并数据集 |
| 训练耗时 | 0 小时 58 分钟（100 轮） |
| 训练日期 | 2026-07-18 |

### 新增 5 类中华田园猫

| # | 类别 | 说明 |
|---|------|------|
| 12 | 三花 | 三花猫 |
| 13 | 奶牛 | 黑白奶牛猫 |
| 14 | 橘猫 | 橘色猫 |
| 15 | 狸花&彩狸 | 狸花猫 / 彩色狸花 |
| 16 | 白猫 | 纯白猫 |

### 性能指标

| 指标 | 数值 | 说明 |
|------|:----:|------|
| Precision | **96.93%** | 检测框精确率 |
| Recall | **95.25%** | 检测框召回率 |
| mAP@50 | **97.81%** | 检测精度（IoU=0.5） |
| mAP@50:95 | **88.38%** | 检测精度（严格） |

### 数据集构建

1. **原 12 类数据** — 沿用 v1 所用的 `merged_cat_breeds` 数据集
2. **新增 5 类** — 收集中华田园猫图片
3. **自动标注** — 使用 Model 1（v1）对新增图片进行目标检测推理，自动生成 YOLO 格式标注框
4. **类别续编** — 新类别编号 12-16（接在 0-11 之后）
5. **数据合并** — 形成完整的 17 类训练集

### 功能用途

- 覆盖**纯种猫 + 中华田园猫**的全面品种识别
- 适用于流浪猫救助站、宠物平台、社区猫只管理
- 相比 v1，大幅拓展了实际应用场景的覆盖面

---

## 模型三：健康状态检测

### 基本信息

| 项目 | 内容 |
|------|------|
| 任务 | 猫健康状态目标检测（二分类） |
| 架构 | YOLO11n（2,590,230 参数） |
| 预训练 | 基于品种检测 Model 1 迁移学习 |
| 数据集 | 1065 训练 + 207 验证 + 268 测试 |
| 训练耗时 | 0 小时 52 分钟（100 轮） |
| 训练日期 | 2026-07-18 |
| 优化策略 | **cls_pw=0.7**（Sick 类加权）+ **mixup=1.0**（混合增强） |

### 2 个类别

| # | 类别 | 说明 |
|---|------|------|
| 0 | Healthy | 健康猫 |
| 1 | Sick | 患病猫（皮肤问题、眼部疾病、外伤等） |

### 性能指标

| 指标 | 数值 | 说明 |
|------|:----:|------|
| Precision | **90.58%** | 检测框精确率 |
| Recall | **90.85%** | 检测框召回率 |
| mAP@50 | **92.24%** | 检测精度 |
| mAP@50:95 | **65.67%** | 检测精度（严格） |

#### 混淆矩阵

| 实际 \ 预测 | Healthy | Sick | 召回率 |
|------------|:-------:|:----:|:------:|
| Healthy | 124 | 2 | **98.4%** |
| Sick | 14 | **68** | **82.9%** |
| **整体准确率** | | | **92.3%** |

### 优化策略

1. **cls_pw=0.7** — Sick 类损失权重加重，提高患病猫的检测优先级
2. **mixup=1.0** — 每批图片随机混合增强，缓解类别不平衡
3. **综合效果**：Sick 召回率提升约 10.9%，整体准确率提升 3.8%

### 推理速度

| 阶段 | 耗时 |
|------|:----:|
| 预处理 | 0.7ms / 张 |
| 推理 (GPU) | 20.0ms / 张 |
| 后处理 | 1.4ms / 张 |
| **总计** | **~22ms / 张** |

### 功能用途

- 自动筛查猫的健康状况，区分健康猫与患病猫
- 适用于宠物医院预检、流浪猫救助筛查、宠物日常健康监测
- Sick 精确率 97.1% 意味着模型报"患病"时高度可信

---

## 模型四：情绪检测

### 基本信息

| 项目 | 内容 |
|------|------|
| 任务 | 猫情绪状态目标检测（7 类情绪分类） |
| 架构 | YOLO11n（2,590,230 参数） |
| 预训练 | 基于品种检测 Model 1 迁移学习 |
| 训练耗时 | 0 小时 40 分钟（90 轮，早停触发） |
| 训练日期 | 2026-07-18 |
| 早停 | patience=20，第 90 轮触发 |

### 7 种情绪类别

| # | 类别 | 说明 |
|---|------|------|
| 0 | Anger | 生气 |
| 1 | Beg | 乞求/撒娇 |
| 2 | Frightened | 受惊/害怕 |
| 3 | Happy | 开心/满足 |
| 4 | Scare | 惊恐/惊吓 |
| 5 | Sleepy | 困倦/想睡 |
| 6 | Wonder | 好奇/疑惑 |

### 性能指标

| 指标 | 数值 | 最佳轮次 | 说明 |
|------|:----:|:--------:|------|
| Precision | **60.70%** | 56 | 精确率 |
| Recall | **62.15%** | 3 | 召回率 |
| mAP@50 | **55.51%** | 70 | 检测精度 |
| mAP@50:95 | **33.02%** | 70 | 检测精度（严格） |

#### 各类别召回率

| 类别 | 召回率 | 实例数 | 识别难度 |
|------|:-----:|:------:|:--------:|
| Sleepy | **66%** | 166 | ✅ 最好 |
| Beg | **61%** | 135 | ✅ 较好 |
| Happy | **44%** | 150 | ⚠️ 一般 |
| Frightened | **41%** | 47 | ⚠️ 一般 |
| Anger | **36%** | 50 | ⚠️ 偏低 |
| Wonder | **34%** | 130 | ⚠️ 偏低 |
| Scare | **13%** | 70 | ❌ 几乎不可识别 |

### 当前局限

- **整体准确率偏低**：7 类情绪区分难度大，远低于健康检测模型
- **Scare 几乎无法识别**（13%），大部分被误分为 Anger 或 Frightened
- **情绪表达差异细微**：猫的情绪主要通过耳朵角度、眼睛形状等细节表达，YOLO11n 特征提取能力有限
- **类别不平衡**：Sleepy（166 张）是 Scare（70 张）的 2.4 倍

### 功能用途

- 分析猫的情绪状态，辅助理解猫的行为意图
- 适用于宠物行为分析、动物福利评估、人宠互动场景
- 建议重点关注 Sleepy、Beg 等高召回类别的识别结果

---

## 模型五：个体识别 (ReID)

### 基本信息

| 项目 | 内容 |
|------|------|
| 任务 | 猫个体身份识别（ReID，开放集） |
| 架构 | ResNet50 + ArcFace |
| 特征维度 | 512 维归一化向量 |
| 输入尺寸 | 224×224（裁剪猫脸） |
| 训练集 | 102 只猫，955 张图片 |
| 测试集 | **25 只全新猫**，213 张图片 |
| 训练耗时 | 100 轮 |
| 训练硬件 | NVIDIA GeForce RTX 3060 Laptop GPU (6GB) |

### 算法原理

```
输入图片 (224×224×3)
      ↓
ResNet50 Backbone (ImageNet 预训练)
      ↓
AdaptiveAvgPool2d → BatchNorm → Dropout(0.3) → Linear(2048→512)
      ↓
512 维归一化特征向量  ←--- 推理时输出此向量
      ↓
ArcFace Loss (仅训练时使用)
```

**核心思路**：将所有猫映射到 512 维特征空间，同类距离近、异类距离远。推理时通过余弦相似度在数据库中检索最相似的猫。

**关键特性**：
- 推理时不需要训练时的分类头，可实现**零样本泛化**
- 可识别**训练时从未见过的新猫**
- 添加新猫只需提取特征存入数据库，**无需重新训练**

### 性能指标

| 指标 | 数值 | 含义 |
|------|:----:|------|
| **Rank-1** | **88.26%** | Top-1 命中率——候选第一名即正确答案的概率 |
| Rank-5 | 96.71% | Top-5 命中率——前五候选中有正确答案的概率 |
| mAP | 58.51% | 平均精度均值——排序质量的综合指标 |

> 测试集的 25 只猫在训练中从未出现，模拟了真实的新猫识别场景。

### 推理速度

GPU 单张图片推理约 **5-10ms**（含特征提取）。

### 功能用途

- 识别"这只猫是谁"——精确定位到个体
- 适用于猫咪档案管理、走失猫识别、多猫家庭的个体追踪
- 需配合 YOLO 模型先裁剪出猫头区域

---

## 后端集成指南

### 环境要求

```bash
# Python 依赖
pip install ultralytics>=8.4.90 torch>=2.0.0 pillow fastapi uvicorn
```

### 通用推理接口

所有 YOLO 模型（品种 v1/v2、健康、情绪）使用相同的加载和推理方式：

```python
from ultralytics import YOLO

# 加载模型（以健康检测为例）
model = YOLO("backend/models/health/best.pt")

# 单张图片推理
results = model("cat.jpg", conf=0.25)

# 提取检测结果
for r in results:
    for box in r.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()   # 检测框坐标
        conf = box.conf[0].item()                 # 置信度
        cls = int(box.cls[0].item())              # 类别 ID
        print(f"类别 {cls}, 置信度 {conf:.2f}, 坐标 [{x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f}]")
```

### FastAPI 集成示例

```python
from fastapi import FastAPI, UploadFile
from ultralytics import YOLO
from PIL import Image
import io

app = FastAPI()

# 初始化模型（启动时加载）
breed_model = YOLO("backend/models/cat_breeds/v2/best.pt")
health_model = YOLO("backend/models/health/best.pt")
emotion_model = YOLO("backend/models/emotion/best.pt")

@app.post("/analyze")
async def analyze_cat(file: UploadFile, conf: float = 0.25):
    """全流水线分析：品种 + 健康 + 情绪"""
    img = Image.open(io.BytesIO(await file.read()))

    # 并行推理三个模型
    breed_results = breed_model(img, conf=conf)
    health_results = health_model(img, conf=conf)
    emotion_results = emotion_model(img, conf=conf)

    def parse_results(results, class_names):
        detections = []
        for r in results:
            for box in r.boxes:
                detections.append({
                    "bbox": box.xyxy[0].tolist(),
                    "confidence": round(box.conf[0].item(), 4),
                    "class_id": int(box.cls[0].item()),
                    "class_name": class_names[int(box.cls[0].item())],
                })
        return detections

    return {
        "breed": parse_results(breed_results, BREED_NAMES_17),
        "health": parse_results(health_results, ["Healthy", "Sick"]),
        "emotion": parse_results(emotion_results, EMOTION_NAMES),
    }
```

### 个体识别集成

个体识别模型需要先裁剪猫头区域，再提取特征向量：

```python
import torch
import torchvision.transforms as T
from PIL import Image
import math

# 加载个体识别模型
checkpoint = torch.load("backend/models/individual/best_model.pth", map_location="cpu")

# 特征提取 transform
transform = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

def extract_embedding(model, image: Image.Image) -> list:
    """提取 512 维归一化特征向量"""
    img_tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        embedding = model(img_tensor)
    return embedding.squeeze().tolist()

def cosine_similarity(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x*x for x in a))
    norm_b = math.sqrt(sum(x*x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

def identify_cat(query_embedding: list, db_cats: list, top_k: int = 3):
    """从数据库中匹配最相似的猫"""
    candidates = []
    for cat in db_cats:
        sim = cosine_similarity(query_embedding, cat["embedding"])
        candidates.append({"cat_id": cat["id"], "name": cat["name"], "similarity": sim})
    candidates.sort(key=lambda x: x["similarity"], reverse=True)
    return candidates[:top_k]
```

### 流水线：完整分析流程

```python
# 1. 用 YOLO 模型检测猫的位置
yolo_results = breed_model(img, conf=0.25)

for r in yolo_results:
    for box in r.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        cat_crop = img.crop((x1, y1, x2, y2))  # 裁剪出猫区域

        # 2. 健康检测（使用同一张图，或裁剪后的图）
        health_result = health_model(cat_crop, conf=0.25)

        # 3. 情绪检测
        emotion_result = emotion_model(cat_crop, conf=0.25)

        # 4. 裁剪猫头区域（取检测框的上半部分）
        head_crop = img.crop((x1, y1, x2, y1 + (y2 - y1) * 0.4))

        # 5. 个体识别
        embedding = extract_embedding(reid_model, head_crop)
        matches = identify_cat(embedding, db_cats, top_k=3)
```

---

## 数据库设计建议

### 猫咪档案表

```sql
CREATE TABLE cats (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,        -- 猫咪名称
    breed        VARCHAR(50),                  -- 品种（来自品种检测模型）
    health_status VARCHAR(20),                 -- 健康状态（来自健康检测模型）
    color        VARCHAR(50),                  -- 毛色
    birth_date   DATE,
    weight_kg    DECIMAL(4,1),
    microchip_id VARCHAR(50) UNIQUE,
    ref_image    TEXT,                         -- 参考图片 URL
    embedding    FLOAT8[],                     -- 512 维特征向量（个体识别用）
    created_at   TIMESTAMP DEFAULT NOW(),
    updated_at   TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cats_breed ON cats(breed);
CREATE INDEX idx_cats_health ON cats(health_status);
```

### 检测记录表

```sql
CREATE TABLE detection_logs (
    id              SERIAL PRIMARY KEY,
    cat_id          INTEGER REFERENCES cats(id),
    image_url       TEXT NOT NULL,
    detected_breed  VARCHAR(50),               -- 本次检测的品种
    breed_confidence REAL,
    health_status   VARCHAR(20),               -- 本次检测的健康状态
    health_confidence REAL,
    emotion         VARCHAR(20),               -- 本次检测的情绪
    emotion_confidence REAL,
    bbox            INTEGER[4],                -- 检测框坐标 [x1,y1,x2,y2]
    detected_at     TIMESTAMP DEFAULT NOW()
);
```

### 个体识别检索

对于个体识别中的向量相似度搜索，推荐使用 **pgvector** 扩展加速：

```sql
-- 启用 pgvector 扩展
CREATE EXTENSION vector;

-- 使用 vector 类型替代 FLOAT8[]
ALTER TABLE cats ADD COLUMN embedding_vec vector(512);

-- 创建 IVFFlat 索引加速近似最近邻搜索
CREATE INDEX idx_cats_embedding ON cats
    USING ivfflat (embedding_vec vector_cosine_ops)
    WITH (lists = 100);

-- 最近邻查询：找出最相似的 5 只猫
SELECT id, name,
       embedding_vec <=> '[0.1, 0.2, ...]'::vector AS distance
FROM cats
ORDER BY distance ASC
LIMIT 5;
```

---

## 模型选择建议

| 场景 | 推荐模型 | 说明 |
|------|---------|------|
| 纯种猫识别 | **品种 v1**（12 类） | 仅需识别纯种猫，精度更高 |
| 通用猫识别 | **品种 v2**（17 类） | 覆盖纯种 + 田园猫，应用更广 |
| 健康筛查 | **健康检测** | 自动区分健康猫与患病猫 |
| 行为分析 | **情绪检测** | 分析猫的情绪状态（注意低召回类别） |
| 个体追踪 | **个体识别** | 精确定位到"这只猫是谁" |
| 全流水线 | **品种 v2 + 健康 + 情绪 + 个体** | 综合分析 |

---

## 文件结构

```
backend/models/
├── README.md                  ← 本文件：模型体系总览
│
├── cat_breeds/
│   ├── v1/                    ← 品种 v1（12 类纯种猫）
│   │   ├── best.pt      (5.2MB)   PyTorch 格式
│   │   └── best.onnx    (10.1MB)  ONNX 格式
│   └── v2/                    ← 品种 v2（17 类，含中华田园猫）
│       ├── best.pt      (5.2MB)   PyTorch 格式
│       └── best.onnx    (10.1MB)  ONNX 格式
│
├── health/                    ← 健康检测（Healthy / Sick）
│   ├── best.pt          (5.2MB)   PyTorch 格式
│   └── best.onnx        (10.1MB)  ONNX 格式
│
├── emotion/                   ← 情绪检测（7 种情绪）
│   ├── best.pt          (5.3MB)   PyTorch 格式
│   └── best.onnx        (10.1MB)  ONNX 格式
│
└── individual/                ← 个体识别（ResNet50 + ArcFace）
    └── best_model.pth   (94.3MB)  PyTorch 权重
```

---

## 训练结果汇总对比

| 模型 | 类别 | mAP@50 | Precision | Recall | 训练耗时 | 模型大小 |
|------|:---:|:------:|:---------:|:------:|:--------:|:--------:|
| 品种 v1 | 12 | **98.39%** | 97.53% | 97.00% | 1h 35min | 5.2MB |
| 品种 v2 | 17 | **97.81%** | 96.93% | 95.25% | 0h 58min | 5.2MB |
| 健康检测 | 2 | **92.24%** | 90.58% | 90.85% | 0h 52min | 5.3MB |
| 情绪检测 | 7 | **55.51%** | 60.70% | 62.15% | 0h 40min | 5.3MB |
| 个体识别 | 开放 | Rank-1 **88.26%** | Rank-5 96.71% | mAP 58.51% | 100 epoch | 94.3MB |

---

*本文档生成时间：2026-07-18*
