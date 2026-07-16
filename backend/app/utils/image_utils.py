"""
图像处理工具函数
提供图片读取、裁剪、Base64 转换、URL 下载等基础功能
"""
import base64
import io
import os
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
import requests
from PIL import Image

from app.core.logger import get_logger

logger = get_logger("image_utils")

# 支持的图像格式
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def read_image(image_path: str) -> np.ndarray:
    """
    读取图片文件，返回 numpy 数组 (BGR 格式)

    Args:
        image_path: 图片文件路径

    Returns:
        numpy 数组，shape=(H, W, 3)
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件不存在: {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法读取图片: {image_path}")
    return img


def crop_region(
    image: np.ndarray,
    bbox: Tuple[float, float, float, float],
    padding: int = 0,
) -> np.ndarray:
    """
    从图片中裁剪指定区域

    Args:
        image: 原始图片 (numpy BGR)
        bbox: 边界框 [x1, y1, x2, y2]
        padding: 裁剪边距（像素）

    Returns:
        裁剪后的图片区域
    """
    h, w = image.shape[:2]
    x1, y1, x2, y2 = [int(v) for v in bbox]

    # 添加 padding，并限制在图片范围内
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(w, x2 + padding)
    y2 = min(h, y2 + padding)

    return image[y1:y2, x1:x2]


def encode_image_to_bytes(image: np.ndarray, format: str = ".jpg", quality: int = 95) -> bytes:
    """
    将 numpy 图片编码为字节流

    Args:
        image: numpy 图片数组
        format: 输出格式（.jpg/.png）
        quality: JPEG 质量（仅对 .jpg 有效）

    Returns:
        图片字节数据
    """
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality] if format in (".jpg", ".jpeg") else []
    success, buffer = cv2.imencode(format, image, encode_params)
    if not success:
        raise ValueError("图片编码失败")
    return buffer.tobytes()


def bytes_to_base64(data: bytes) -> str:
    """将字节数据转为 Base64 字符串"""
    return base64.b64encode(data).decode("utf-8")


def base64_to_image(b64_string: str) -> np.ndarray:
    """将 Base64 字符串解码为 numpy 图片"""
    if b64_string.startswith("data:image"):
        b64_string = b64_string.split(",", 1)[1]
    data = base64.b64decode(b64_string)
    nparr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Base64 解码失败")
    return img


def download_image(url: str, timeout: int = 30) -> np.ndarray:
    """
    从 URL 下载图片

    Args:
        url: 图片 URL
        timeout: 超时时间（秒）

    Returns:
        numpy 图片数组
    """
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        nparr = np.frombuffer(resp.content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("URL 图片解码失败")
        return img
    except requests.RequestException as e:
        raise ValueError(f"下载图片失败: {url}, 错误: {e}")


def get_image_size(image: np.ndarray) -> Tuple[int, int]:
    """获取图片尺寸 (width, height)"""
    h, w = image.shape[:2]
    return w, h


def resize_image(
    image: np.ndarray,
    target_size: Tuple[int, int],
    keep_ratio: bool = True,
) -> np.ndarray:
    """
    缩放图片

    Args:
        image: 原始图片
        target_size: 目标尺寸 (width, height)
        keep_ratio: 是否保持宽高比

    Returns:
        缩放后的图片
    """
    if keep_ratio:
        h, w = image.shape[:2]
        tw, th = target_size
        scale = min(tw / w, th / h)
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(image, (new_w, new_h))
    return cv2.resize(image, target_size)


def is_valid_image_file(file_path: str) -> bool:
    """检查是否为有效的图片文件"""
    ext = Path(file_path).suffix.lower()
    return ext in SUPPORTED_FORMATS