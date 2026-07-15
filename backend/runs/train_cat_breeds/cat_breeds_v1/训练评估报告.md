# 猫品种检测模型 — 训练评估报告

## 一、基本信息

| 项目 | 内容 |
|------|------|
| 模型 | YOLOv11n (2,584,492 参数) |
| 数据集 | 12 种猫品种（Roboflow Cat Breeds v1） |
| 训练图片 | 2544 张（训练集）+ 689 张（验证集） |
| 测试图片 | 1443 张（其中 231 张有标签） |
| 训练硬件 | NVIDIA GeForce RTX 3060 Laptop GPU (6GB) |
| 训练耗时 | 1 小时 35 分 27 秒（100 轮） |
| 训练日期 | 2026-07-15 |

### 12 个品种

| # | 品种 | 英文名 |
|---|------|--------|
| 0 | 阿比西尼亚猫 | Abyssinian |
| 1 | 孟加拉猫 | Bengal |
| 2 | 伯曼猫 | Birman |
| 3 | 孟买猫 | Bombay |
| 4 | 英国短毛猫 | British_Shorthair |
| 5 | 埃及猫 | Egyptian_Mau |
| 6 | 缅因猫 | Maine_Coon |
| 7 | 波斯猫 | Persian |
| 8 | 布偶猫 | Ragdoll |
| 9 | 俄罗斯蓝猫 | Russian_Blue |
| 10 | 暹罗猫 | Siamese |
| 11 | 斯芬克斯猫 | Sphynx |

---

## 二、验证集结果（目标检测精度）

在 689 张验证集图片上评估框的精度：

| 指标 | 最佳值 | 最佳轮次 | 最终值（第100轮） |
|------|-------|---------|----------------|
| Precision | **97.53%** | 78 | 97.17% |
| Recall | **97.00%** | 98 | 96.89% |
| mAP@50 | **98.39%** | 71 | 97.98% |
| mAP@50:95 | **86.61%** | 83 | 86.13% |

> mAP@50 = IoU 阈值 0.5 时的平均精度均值
> mAP@50:95 = IoU 阈值 0.5~0.95 的平均精度均值（更严格的指标）

---

## 三、测试集结果（品种分类准确率）

由于测试集中 231 张有标签图片的**边界框坐标与原始图片不匹配**（Roboflow 预处理导致坐标偏移），因此改用**品种识别准确率**来评估。

在 **231 张有标签的测试图片** 上：

| 总体指标 | 值 |
|---------|-----|
| **品种识别准确率** | **94.37%（218/231）** |
| 平均置信度 | 0.904 |

### 各品种准确率

```
Abyssinian          :  90.48%  (19/21)  ██████████████████░░
Bengal              :  90.48%  (19/21)  ██████████████████░░
Birman              :  88.46%  (23/26)  █████████████████░░░
Bombay              : 100.00%  (21/21)  ████████████████████
British_Shorthair   : 100.00%  (11/11)  ████████████████████
Egyptian_Mau        : 100.00%  (13/13)  ████████████████████
Maine_Coon          : 100.00%  (18/18)  ████████████████████
Persian             :  95.00%  (19/20)  ███████████████████░
Ragdoll             :  83.33%  (15/18)  ████████████████░░░░
Russian_Blue        :  96.30%  (26/27)  ███████████████████░
Siamese             :  95.00%  (19/20)  ███████████████████░
Sphynx              : 100.00%  (15/15)  ████████████████████
```

### 错误分类详情（13 个）

| 图片 | 真实品种 | 预测品种 | 置信度 |
|------|---------|---------|-------|
| Abyssinian_221 | Abyssinian | Egyptian_Mau | 0.929 |
| Abyssinian_8 | Abyssinian | Egyptian_Mau | 0.643 |
| Bengal_133 | Bengal | British_Shorthair | 0.553 |
| Bengal_180 | Bengal | Egyptian_Mau | 0.881 |
| Birman_133 | Birman | Siamese | 0.661 |
| Birman_94 | Birman | Siamese | 0.865 |
| Birman_98 | Birman | Ragdoll | 0.801 |
| Persian_89 | Persian | Ragdoll | 0.791 |
| Ragdoll_170 | Ragdoll | Birman | 0.665 |
| Ragdoll_58 | Ragdoll | Persian | 0.389 |
| Ragdoll_93 | Ragdoll | Birman | 0.918 |
| Russian_Blue_237 | Russian_Blue | British_Shorthair | 0.879 |
| Siamese_24 | Siamese | Russian_Blue | 0.446 |

> 错误主要集中在外观相似的品种之间：Birman↔Siamese、Ragdoll↔Birman、Abyssinian↔Egyptian_Mau

---

## 四、训练过程

### 损失曲线

- 训练损失（box_loss + cls_loss + dfl_loss）在整个训练过程中持续下降
- 验证损失在第 60 轮后趋于平稳
- 学习率采用余弦退火策略，从 0.01 逐渐衰减

### 指标曲线

- Precision 从第 1 轮的 ~27% 提升至第 78 轮的峰值 **97.5%**
- Recall 从第 1 轮的 ~50% 提升至第 98 轮的峰值 **97.0%**
- mAP@50 从第 1 轮的 ~0.32 提升至第 71 轮的峰值 **0.984**

### 训练参数

| 参数 | 值 |
|------|-----|
| 输入尺寸 | 640×640 |
| 批次大小 | 16 |
| 优化器 | auto (SGD) |
| 初始学习率 | 0.01 |
| 学习率策略 | 余弦退火 |
| 预热轮数 | 3 |
| 早停耐心 | 20 |
| 数据增强 | mosaic, mixup, copy-paste, auto-augment |
| 混合精度训练 | 开启 (AMP) |

---

## 五、输出文件清单

### 模型权重

```
weights/
├── best.pt          (5.2MB)  ← 最佳模型（PyTorch 格式）
├── best.onnx        (10.1MB) ← ONNX 导出格式
└── last.pt          (5.2MB)  ← 最后 epoch 的模型
```

### 训练图表

| 文件 | 说明 |
|------|------|
| `loss_curves.png` | 训练/验证损失曲线 |
| `metrics_curves.png` | Precision/Recall/mAP@50/mAP@50:95 曲线 |
| `training_overview.png` | 综合总览图 |
| `lr_curve.png` | 学习率变化曲线 |
| `results.png` | YOLO 自带结果图 |
| `confusion_matrix.png` | 验证集混淆矩阵 |
| `BoxPR_curve.png` | Precision-Recall 曲线 |

### 测试评估

| 文件 | 说明 |
|------|------|
| `test_eval/classification_report.json` | 分类准确率数据 |
| `test_eval/per_breed_accuracy.png` | 各品种准确率条形图 |
| `test_eval/label_verification.png` | 预测 vs 真实标签对比 |
| `test_eval/prediction_grid.png` | 32张预测样例拼贴 |
| `test_eval/prediction_stats.json` | 全量预测统计 |
| `test_eval/test_evaluation_report.json` | 完整评估报告 |
| `test_eval/predictions/` | 每张测试图片的预测结果 |

### 数据文件

| 文件 | 说明 |
|------|------|
| `results.csv` | 逐 epoch 的完整训练指标 |
| `training_report.json` | 训练简要报告 |
| `args.yaml` | 训练参数配置 |

---

## 六、结论

1. **目标检测精度高**：验证集 mAP@50 达 **98.4%**，模型能准确定位并识别 12 种猫品种
2. **品种分类准确率高**：测试集 **94.4%** 的品种识别准确率
3. **模型轻量**：YOLOv11n 仅 260 万参数，适合部署在边缘设备
4. **推理速度快**：GPU 上单张图片推理仅约 **3ms**

---

*报告生成时间：2026-07-15*
*数据路径：E:/mycode/visagent/visagent/backend/runs/train_cat_breeds/cat_breeds_v1/*
