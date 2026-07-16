"""
猫个体识别 (Cat Individual ReID) 训练脚本
ResNet50 + ArcFace Loss

数据集格式:
    data_root/
        cat_001/            ← 文件夹名 = 猫ID
            xxxx.jpg        ← 裁剪好的猫脸图 (jpg/png 均可)
            xxxx.png
            ...
        cat_002/
            ...
        ...
"""

import os, sys, json, math, argparse, random
from pathlib import Path
from datetime import datetime

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as T
import torchvision.models as models
from PIL import Image
import numpy as np
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from tqdm import tqdm

# ============================================================
# 缓存重定向（避免 C 盘占用）
# ============================================================
CACHE_BASE = Path("E:/program/merged_cat_breeds/.cache")
CACHE_BASE.mkdir(parents=True, exist_ok=True)

# 强制重定向所有缓存和临时文件到 E 盘
# ★ 用直接赋值而非 setdefault：Windows 的 TEMP/TMP 在系统层已存在，setdefault 不会覆盖
for _k, _v in [
    ("TORCH_HOME",       CACHE_BASE / "torch"),
    ("MPLCONFIGDIR",     CACHE_BASE / "matplotlib"),
    ("HF_HOME",          CACHE_BASE / "huggingface"),
    ("XDG_CACHE_HOME",   CACHE_BASE),
    ("TMPDIR",           CACHE_BASE / "tmp"),
    ("TEMP",             CACHE_BASE / "tmp"),
    ("TMP",              CACHE_BASE / "tmp"),
    ("NUMEXPR_TEMP_DIR", CACHE_BASE / "tmp"),
    ("CUDA_CACHE_PATH",  CACHE_BASE / "cuda"),   # CUDA 内核编译缓存
    ("PYTHONPYCACHEPREFIX", CACHE_BASE / "pycache"),  # Python 字节码缓存
    ("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True"),  # 减少 CUDA 显存预分配导致的虚拟内存提交
    ("PYTORCH_TMPDIR",     CACHE_BASE / "tmp"),    # PyTorch 内部临时目录
    ("CUDA_CACHE_MAXSIZE", "268435456"),           # CUDA 内核缓存上限 256MB
    ("TOKENIZERS_CACHE",   CACHE_BASE / "huggingface"),  # HuggingFace tokenizers 缓存
    ("HF_DATASETS_CACHE",  CACHE_BASE / "huggingface" / "datasets"),  # HuggingFace datasets
]:
    os.environ[_k] = str(_v)

# 强制 Python 的 tempfile 模块使用 E 盘（它会在首次调用时缓存路径，
# 仅设 TEMP 环境变量可能不够——某些库在 env var 生效前就调用了 gettempdir）
tempfile.tempdir = str(CACHE_BASE / "tmp")

# 确保子目录存在
for _dir in ["torch", "matplotlib", "huggingface", "huggingface/datasets",
             "tmp", "cuda", "pycache"]:
    (CACHE_BASE / _dir).mkdir(parents=True, exist_ok=True)

print(f"  [Cache] 缓存目录: {CACHE_BASE}")

BACKEND_DIR = Path(__file__).parent.resolve()
DEFAULT_PROJECT = str(BACKEND_DIR / "runs" / "train_individual")


# ============================================================
# 1. ArcFace Loss
# ============================================================

class ArcFace(nn.Module):
    def __init__(self, embedding_dim, num_classes, s=64.0, m=0.5):
        super().__init__()
        self.s = s
        self.m = m
        self.cos_m = math.cos(m)
        self.sin_m = math.sin(m)
        self.th = math.cos(math.pi - m)
        self.mm = math.sin(math.pi - m) * m
        self.weight = nn.Parameter(torch.FloatTensor(num_classes, embedding_dim))
        nn.init.xavier_normal_(self.weight)

    def forward(self, embeddings, labels):
        w = F.normalize(self.weight)
        cos_theta = F.linear(embeddings, w).clamp(-1.0, 1.0)
        one_hot = torch.zeros_like(cos_theta).scatter_(1, labels.view(-1, 1).long(), 1)
        sin_theta = torch.sqrt(1.0 - cos_theta.pow(2))
        cos_theta_m = cos_theta * self.cos_m - sin_theta * self.sin_m
        cos_theta_m = torch.where(cos_theta > self.th, cos_theta_m, cos_theta - self.mm)
        output = (one_hot * cos_theta_m + (1 - one_hot) * cos_theta) * self.s
        return F.cross_entropy(output, labels)


# ============================================================
# 2. 模型定义
# ============================================================

class CatIndividualModel(nn.Module):
    """输入猫脸图 → 输出 L2 归一化的 512 维特征向量"""
    def __init__(self, embedding_dim=512, num_classes=None):
        super().__init__()
        backbone = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
        self.backbone = nn.Sequential(*list(backbone.children())[:-2])
        self.avgpool = nn.AdaptiveAvgPool2d(1)
        self.bn1 = nn.BatchNorm1d(2048)
        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(2048, embedding_dim)
        self.bn2 = nn.BatchNorm1d(embedding_dim)
        self.arcface = ArcFace(embedding_dim, num_classes) if num_classes else None

    def forward(self, x):
        x = self.backbone(x)
        x = self.avgpool(x).view(x.size(0), -1)
        x = self.bn1(x)
        x = self.dropout(x)
        x = self.bn2(self.fc(x))
        return F.normalize(x)


# ============================================================
# 3. 数据集
# ============================================================

class CatIndividualDataset(Dataset):
    """格式: root/cat_id/*.{jpg,png,...}"""
    def __init__(self, cat_ids, cat_to_paths, transform=None):
        self.samples = [(p, cid) for cid in cat_ids for p in cat_to_paths[cid]]
        self.transform = transform

    def __len__(self): return len(self.samples)
    def __getitem__(self, idx):
        path, cid = self.samples[idx]
        img = Image.open(path).convert('RGB')
        if self.transform: img = self.transform(img)
        return img, cid


# ============================================================
# 4. 检索指标评估
# ============================================================

def evaluate(model, loader, device):
    """计算 Rank-1, Rank-5, mAP"""
    model.eval()
    embs, labs = [], []
    with torch.no_grad():
        for imgs, lbls in loader:
            embs.append(model(imgs.to(device)).cpu())
            labs.append(lbls)
    embs = torch.cat(embs)
    labs = torch.cat(labs)
    N = len(labs)

    sim = torch.mm(embs, embs.T)
    ranks = sim.argsort(1, descending=True)

    r1 = sum(1 for i in range(N) if labs[ranks[i, 1 if ranks[i,0]==i else 0]] == labs[i]) / N
    r5 = sum(1 for i in range(N) if any(labs[t]==labs[i] for t in ranks[i,1:6] if t!=i)) / N

    ap = 0.0
    for i in range(N):
        same = (labs == labs[i]).nonzero(as_tuple=True)[0]
        ns = len(same) - 1
        if ns == 0: continue
        rel, prec = 0, []
        for j, idx in enumerate(ranks[i]):
            if idx == i: continue
            if labs[idx] == labs[i]: rel += 1; prec.append(rel / (j+1))
            if rel == ns: break
        if prec: ap += sum(prec) / ns
    return {'Rank-1': r1, 'Rank-5': r5, 'mAP': ap / N}


# ============================================================
# 5. 训练曲线绘制
# ============================================================

def plot_training_curves(history, save_dir):
    """绘制训练过程中的 Loss、Rank-1、Rank-5、mAP 曲线"""
    epochs = list(range(1, len(history['loss']) + 1))

    def smooth(values, weight=0.85):
        smoothed = []
        last = values[0]
        for v in values:
            smoothed_val = last * weight + (1 - weight) * v
            smoothed.append(smoothed_val)
            last = smoothed_val
        return smoothed

    # 1. Loss 曲线
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(epochs, history['loss'], alpha=0.3, color='#2196F3', label='Raw')
    ax.plot(epochs, smooth(history['loss']), linewidth=2, color='#2196F3', label='Smoothed')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('ArcFace Loss')
    ax.set_title('Training Loss')
    ax.legend()
    ax.grid(True, alpha=0.3)
    # 标注最佳值
    best_val = min(history['loss'])
    best_ep = np.argmin(history['loss']) + 1
    ax.annotate(f'Best: {best_val:.4f} @ epoch {best_ep}',
                xy=(best_ep, best_val), xytext=(best_ep + 2, best_val + 0.05),
                arrowprops=dict(arrowstyle='->', color='gray'), fontsize=9)
    plt.tight_layout()
    plt.savefig(Path(save_dir) / 'loss_curve.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  [V] Loss 曲线: {Path(save_dir) / 'loss_curve.png'}")

    # 2. Rank 指标曲线
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(epochs, history['r1'], color='#4CAF50', linewidth=2, label='Rank-1')
    ax.plot(epochs, history['r5'], color='#FF9800', linewidth=2, label='Rank-5')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Accuracy')
    ax.set_title('Retrieval Metrics')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.0)
    best_r1 = max(history['r1'])
    best_ep = np.argmax(history['r1']) + 1
    ax.annotate(f'Best Rank-1: {best_r1:.4f} @ epoch {best_ep}',
                xy=(best_ep, best_r1), xytext=(best_ep + 2, best_r1 - 0.08),
                arrowprops=dict(arrowstyle='->', color='gray'), fontsize=9)
    plt.tight_layout()
    plt.savefig(Path(save_dir) / 'rank_curves.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  [V] Rank 曲线: {Path(save_dir) / 'rank_curves.png'}")

    # 3. mAP 曲线
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(epochs, history['map'], color='#9C27B0', linewidth=2, label='mAP')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('mAP')
    ax.set_title('Mean Average Precision')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.0)
    best_map = max(history['map'])
    best_ep = np.argmax(history['map']) + 1
    ax.annotate(f'Best mAP: {best_map:.4f} @ epoch {best_ep}',
                xy=(best_ep, best_map), xytext=(best_ep + 2, best_map - 0.08),
                arrowprops=dict(arrowstyle='->', color='gray'), fontsize=9)
    plt.tight_layout()
    plt.savefig(Path(save_dir) / 'map_curve.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  [V] mAP 曲线: {Path(save_dir) / 'map_curve.png'}")

    # 4. 总览图
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    # Loss
    axes[0, 0].plot(epochs, smooth(history['loss']), color='#2196F3', linewidth=2)
    axes[0, 0].set_xlabel('Epoch'); axes[0, 0].set_ylabel('Loss')
    axes[0, 0].set_title('Training Loss'); axes[0, 0].grid(True, alpha=0.3)
    # Rank-1
    axes[0, 1].plot(epochs, history['r1'], color='#4CAF50', linewidth=2)
    axes[0, 1].set_xlabel('Epoch'); axes[0, 1].set_ylabel('Rank-1')
    axes[0, 1].set_title('Rank-1 Accuracy'); axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_ylim(0, 1.0)
    # Rank-5
    axes[1, 0].plot(epochs, history['r5'], color='#FF9800', linewidth=2)
    axes[1, 0].set_xlabel('Epoch'); axes[1, 0].set_ylabel('Rank-5')
    axes[1, 0].set_title('Rank-5 Accuracy'); axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_ylim(0, 1.0)
    # mAP
    axes[1, 1].plot(epochs, history['map'], color='#9C27B0', linewidth=2)
    axes[1, 1].set_xlabel('Epoch'); axes[1, 1].set_ylabel('mAP')
    axes[1, 1].set_title('Mean Average Precision'); axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_ylim(0, 1.0)

    plt.suptitle('Cat Individual ReID — Training Overview', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig(Path(save_dir) / 'training_overview.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  [V] 总览图: {Path(save_dir) / 'training_overview.png'}")
    print(f"  [V] 所有图表已保存至 {save_dir}/")


# ============================================================
# 6. 主训练函数
# ============================================================

def train(
    data_root, epochs=100, batch_size=64, lr=3e-4,
    embedding_dim=512, img_size=224, workers=2, device_id=0,
    project=DEFAULT_PROJECT, name=None, test_ratio=0.2,
):
    device = f"cuda:{device_id}" if torch.cuda.is_available() else "cpu"
    print(f"  设备: {device}")
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(device_id)}")

    # 输出目录
    if name is None:
        name = datetime.now().strftime("indiv_%Y%m%d_%H%M%S")
    save_dir = Path(project) / name
    save_dir.mkdir(parents=True, exist_ok=True)
    print(f"  保存: {save_dir}")

    # 读取数据集
    print(f"\n{'='*60}")
    print(f"  加载数据集: {data_root}")
    print(f"{'='*60}")
    root = Path(data_root)
    folders = sorted([f for f in root.iterdir() if f.is_dir()])
    print(f"  共 {len(folders)} 个文件夹")

    cat_to_paths = {}
    valid = []
    for f in folders:
        paths = sorted([str(p) for p in f.iterdir()
                       if p.suffix.lower() in ('.jpg','.jpeg','.png')])
        if len(paths) >= 5:
            cid = len(valid)
            cat_to_paths[cid] = paths
            valid.append((cid, f.name, len(paths)))

    print(f"  有效猫 (≥5张): {len(valid)}")
    for cid, name, cnt in valid:
        print(f"    {name}: {cnt} 张")

    n_cats = len(valid)
    if n_cats < 10:
        print("  ❌ 猫数量太少")
        return None

    # 猫层面划分训练/测试
    ids = list(range(n_cats))
    random.seed(42); random.shuffle(ids)
    n_test = max(1, int(n_cats * test_ratio))
    test_ids = set(ids[:n_test])
    train_ids = set(ids[n_test:])
    print(f"\n  训练: {len(train_ids)} 只猫 | 测试(未见过): {len(test_ids)} 只猫")

    # 训练集猫ID重映射为连续的 0~N-1（ArcFace 要求标签从0开始连续）
    train_label_map = {cid: i for i, cid in enumerate(sorted(train_ids))}
    train_ids_remapped = set(train_label_map.values())
    test_label_map  = {cid: i for i, cid in enumerate(sorted(test_ids))}
    test_ids_remapped = set(test_label_map.values())

    # 数据增强
    train_tfm = T.Compose([
        T.Resize((img_size, img_size)),
        T.RandomHorizontalFlip(0.5),
        T.RandomRotation(10),
        T.ColorJitter(0.2, 0.15),
        T.ToTensor(),
        T.Normalize([0.485,0.456,0.406], [0.229,0.224,0.225]),
    ])
    test_tfm = T.Compose([
        T.Resize((img_size, img_size)),
        T.ToTensor(),
        T.Normalize([0.485,0.456,0.406], [0.229,0.224,0.225]),
    ])

    # 用重映射后的ID重建 cat_to_paths，保证 key 连续
    train_cat_to_paths = {train_label_map[cid]: cat_to_paths[cid] for cid in train_ids}
    test_cat_to_paths  = {test_label_map[cid]:  cat_to_paths[cid] for cid in test_ids}

    train_ds = CatIndividualDataset(train_ids_remapped, train_cat_to_paths, train_tfm)
    test_ds  = CatIndividualDataset(test_ids_remapped,  test_cat_to_paths,  test_tfm)
    train_ld = DataLoader(train_ds, batch_size, True, num_workers=workers, pin_memory=True, drop_last=True)
    test_ld  = DataLoader(test_ds,  batch_size, False, num_workers=workers, pin_memory=True)

    print(f"  训练图片: {len(train_ds)} | 测试图片: {len(test_ds)}")

    # 初始化模型
    print(f"\n  [模型] ResNet50 (pretrained) + ArcFace (dim={embedding_dim}, classes={len(train_ids)})")
    model = CatIndividualModel(embedding_dim, len(train_ids)).to(device)

    opt = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, epochs)

    # 权重文件仅用于记录原始 arcface 分类头参数，后续推理用不到
    # 注意：arcface.weight 的 shape = (训练猫数量, 512)，测试集猫不在其中
    # 测试集评估的是模型对新猫的泛化能力（通过特征向量检索）

    # 训练
    print(f"\n{'='*60}")
    print(f"  训练开始 ({epochs} epochs)")
    print(f"{'='*60}")
    best_r1 = 0
    hist = {'loss':[], 'r1':[], 'r5':[], 'map':[]}

    for ep in range(epochs):
        model.train()
        loss_sum = 0
        pbar = tqdm(train_ld, desc=f"  Epoch [{ep+1}/{epochs}]", leave=False,
                    bar_format="{desc} |{bar}| {n_fmt}/{total_fmt} batches | loss: {postfix}")
        for imgs, lbls in pbar:
            imgs, lbls = imgs.to(device), lbls.to(device)
            opt.zero_grad()
            emb = model(imgs)
            loss = model.arcface(emb, lbls)
            loss.backward(); opt.step()
            loss_sum += loss.item()
            pbar.set_postfix(loss=f"{loss.item():.4f}")

        metrics = evaluate(model, test_ld, device)
        hist['loss'].append(loss_sum/len(train_ld))
        hist['r1'].append(metrics['Rank-1'])
        hist['r5'].append(metrics['Rank-5'])
        hist['map'].append(metrics['mAP'])

        print(f"  >>> Epoch [{ep+1:3d}/{epochs}]  "
              f"Loss: {hist['loss'][-1]:.4f}  "
              f"Rank-1: {metrics['Rank-1']:.4f}  "
              f"Rank-5: {metrics['Rank-5']:.4f}  "
              f"mAP: {metrics['mAP']:.4f}")

        if metrics['Rank-1'] > best_r1:
            best_r1 = metrics['Rank-1']
            torch.save({
                'epoch': ep,
                'model_state_dict': model.state_dict(),
                'embedding_dim': embedding_dim,
                'best_rank1': best_r1,
            }, save_dir / "best_model.pth")
            print(f"  ✅ 最佳模型 (Rank-1={best_r1:.4f})")

        sched.step()

    # 保存最终
    torch.save({
        'epoch': epochs-1,
        'model_state_dict': model.state_dict(),
        'embedding_dim': embedding_dim,
        'best_rank1': best_r1,
    }, save_dir / "final_model.pth")

    with open(save_dir / "history.json", 'w') as f:
        json.dump({
            'best_rank1': best_r1,
            'final_rank1': hist['r1'][-1],
            'final_rank5': hist['r5'][-1],
            'final_mAP': hist['map'][-1],
            'config': {'epochs':epochs, 'batch':batch_size, 'lr':lr,
                       'dim':embedding_dim, 'train_cats':len(train_ids),
                       'test_cats':len(test_ids)},
        }, f, indent=2)

    # 绘制训练曲线
    print(f"\n  [Chart] 绘制训练曲线...")
    plot_training_curves(hist, save_dir)

    # 生成训练报告 Markdown
    report_md = f"""# 猫个体识别训练报告

## 训练配置

| 参数 | 值 |
|---|---|
| 模型 | ResNet50 + ArcFace |
| 特征维度 | {embedding_dim} |
| 训练轮数 | {epochs} |
| 批次大小 | {batch_size} |
| 学习率 | {lr} |
| 输入尺寸 | {img_size}×{img_size} |

## 数据集

| 项目 | 数量 |
|---|---|
| 训练集猫数量 | {len(train_ids)} |
| 测试集猫数量 | {len(test_ids)} |
| 训练集图片 | {len(train_ds)} |
| 测试集图片 | {len(test_ds)} |

## 最佳结果

| 指标 | 数值 |
|---|---|
| **Rank-1** | **{best_r1:.4f}** |
| Rank-5 | {hist['r5'][-1]:.4f} |
| mAP | {hist['map'][-1]:.4f} |
| 最终 Loss | {hist['loss'][-1]:.4f} |

> 注意：测试集中的 {len(test_ids)} 只猫在训练时**完全未出现过**，Rank-1 反映模型对新猫的泛化能力。

## 输出文件

| 文件 | 说明 |
|---|---|
| `best_model.pth` | 最佳模型权重（基于 Rank-1） |
| `final_model.pth` | 最终 epoch 模型权重 |
| `training_history.json` | 训练历史数据 |
| `loss_curve.png` | Loss 曲线图 |
| `rank_curves.png` | Rank-1 / Rank-5 曲线图 |
| `map_curve.png` | mAP 曲线图 |
| `training_overview.png` | 四合一总览图 |
"""
    report_path = save_dir / "training_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_md)
    print(f"  [V] 训练报告: {report_path}")

    print(f"\n{'='*60}")
    print(f"  训练完成！")
    print(f"  最佳 Rank-1: {best_r1:.4f}（测试集 {len(test_ids)} 只猫均未在训练中出现）")
    print(f"  模型: {save_dir / 'best_model.pth'}")
    print(f"  图表: {save_dir}/loss_curve.png 等")
    print(f"  报告: {report_path}")
    print(f"{'='*60}")
    return model, hist


# ============================================================
# 命令行
# ============================================================

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--batch", type=int, default=64)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--dim", type=int, default=512)
    p.add_argument("--img-size", type=int, default=224)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--device", type=int, default=0)
    p.add_argument("--project", default=DEFAULT_PROJECT)
    p.add_argument("--name", default=None)
    p.add_argument("--test-ratio", type=float, default=0.2)
    args = p.parse_args()

    if not Path(args.data).exists():
        print(f"❌ 数据集不存在: {args.data}"); sys.exit(1)

    train(data_root=args.data, epochs=args.epochs, batch_size=args.batch,
          lr=args.lr, embedding_dim=args.dim, img_size=args.img_size,
          workers=args.workers, device_id=args.device, project=args.project,
          name=args.name, test_ratio=args.test_ratio)
