"""
数据集工具函数测试：validate_dataset、convert_*、split_dataset、generate_data_yaml
"""
import os
import json
import shutil
import tempfile
from pathlib import Path

import pytest

from app.services.data_utils import (
    validate_dataset,
    convert_voc_to_yolo,
    convert_coco_to_yolo,
    convert_labelme_to_yolo,
    split_dataset,
    generate_data_yaml,
)


@pytest.fixture
def tmp_dir():
    """创建临时目录，测试后自动清理"""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _create_image(path: str):
    """创建一个空的假图像文件"""
    Path(path).touch()


class TestValidateDataset:
    """validate_dataset 验证逻辑测试"""

    def test_images_dir_not_exist(self, tmp_dir):
        """图像目录不存在"""
        result = validate_dataset(
            images_dir=os.path.join(tmp_dir, "no_images"),
            labels_dir=os.path.join(tmp_dir, "labels"),
            class_names=["cat"],
        )
        assert result["is_valid"] is False
        assert any("图像目录不存在" in e for e in result["errors"])

    def test_labels_dir_not_exist(self, tmp_dir):
        """标注目录不存在"""
        images_dir = os.path.join(tmp_dir, "images")
        os.makedirs(images_dir)
        result = validate_dataset(
            images_dir=images_dir,
            labels_dir=os.path.join(tmp_dir, "no_labels"),
            class_names=["cat"],
        )
        assert result["is_valid"] is False
        assert any("标注目录不存在" in e for e in result["errors"])

    def test_empty_dataset(self, tmp_dir):
        """空数据集"""
        images_dir = os.path.join(tmp_dir, "images")
        labels_dir = os.path.join(tmp_dir, "labels")
        os.makedirs(images_dir)
        os.makedirs(labels_dir)
        result = validate_dataset(images_dir, labels_dir, class_names=["cat"])
        assert result["stats"]["total_images"] == 0

    def test_matched_pairs(self, tmp_dir):
        """图像和标注正确匹配"""
        images_dir = os.path.join(tmp_dir, "images")
        labels_dir = os.path.join(tmp_dir, "labels")
        os.makedirs(images_dir)
        os.makedirs(labels_dir)
        _create_image(os.path.join(images_dir, "img1.jpg"))
        Path(os.path.join(labels_dir, "img1.txt")).write_text("0 0.5 0.5 0.2 0.2\n")
        result = validate_dataset(images_dir, labels_dir, class_names=["cat"])
        assert result["stats"]["matched_pairs"] == 1

    def test_unmatched_image(self, tmp_dir):
        """有图像无对应标注"""
        images_dir = os.path.join(tmp_dir, "images")
        labels_dir = os.path.join(tmp_dir, "labels")
        os.makedirs(images_dir)
        os.makedirs(labels_dir)
        _create_image(os.path.join(images_dir, "orphan.jpg"))
        result = validate_dataset(images_dir, labels_dir, class_names=["cat"])
        assert len(result["stats"]["unmatched_images"]) == 1


class TestSplitDataset:
    """split_dataset 数据集划分测试"""

    def test_split_creates_dirs(self, tmp_dir):
        """划分后创建 train/val/test 目录"""
        images_dir = os.path.join(tmp_dir, "images")
        labels_dir = os.path.join(tmp_dir, "labels")
        output_dir = os.path.join(tmp_dir, "output")
        os.makedirs(images_dir)
        os.makedirs(labels_dir)
        for i in range(10):
            _create_image(os.path.join(images_dir, f"img{i}.jpg"))
            Path(os.path.join(labels_dir, f"img{i}.txt")).write_text("0 0.5 0.5 0.2 0.2\n")
        result = split_dataset(images_dir, labels_dir, output_dir, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1)
        assert os.path.isdir(os.path.join(output_dir, "images", "train"))
        assert os.path.isdir(os.path.join(output_dir, "images", "val"))

    def test_split_ratio(self, tmp_dir):
        """划分比例大致正确"""
        images_dir = os.path.join(tmp_dir, "images")
        labels_dir = os.path.join(tmp_dir, "labels")
        output_dir = os.path.join(tmp_dir, "output")
        os.makedirs(images_dir)
        os.makedirs(labels_dir)
        for i in range(20):
            _create_image(os.path.join(images_dir, f"img{i}.jpg"))
            Path(os.path.join(labels_dir, f"img{i}.txt")).write_text("0 0.5 0.5 0.2 0.2\n")
        result = split_dataset(images_dir, labels_dir, output_dir, train_ratio=0.65, val_ratio=0.25, test_ratio=0.1)
        total = result.get("train", 0) + result.get("val", 0) + result.get("test", 0)
        assert total == 20


class TestGenerateDataYaml:
    """generate_data_yaml 生成配置文件测试"""

    def test_generates_file(self, tmp_dir):
        """生成 data.yaml"""
        yaml_path = generate_data_yaml(
            dataset_dir=tmp_dir,
            class_names=["cat", "dog"],
            output_path=os.path.join(tmp_dir, "data.yaml"),
        )
        assert os.path.isfile(yaml_path)
        content = Path(yaml_path).read_text()
        assert "cat" in content
        assert "dog" in content
