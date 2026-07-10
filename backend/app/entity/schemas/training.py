"""
训练模块 Schema
"""

from typing import Optional
from pydantic import BaseModel, Field


class CreateTrainingRequest(BaseModel):
    """创建训练任务请求"""

    scene_id: int = Field(..., description="场景ID")
    model_name: str = Field("yolov11n", description="基础模型：yolov11n/s/m/l/x")
    epochs: int = Field(100, ge=1, le=10000, description="训练轮数")
    img_size: int = Field(640, ge=32, le=4096, description="图像尺寸")
    batch_size: int = Field(16, ge=1, le=256, description="批次大小")
    device: str = Field("cpu", description="训练设备：0/1/cpu")
    optimizer: str = Field("SGD", description="优化器：SGD/Adam/AdamW")
    lr0: float = Field(0.01, ge=0.00001, le=1.0, description="初始学习率")
    dataset_path: str = Field(..., description="数据集路径")
    data_yaml: str = Field(..., description="data.yaml 路径")


class ValidateModelRequest(BaseModel):
    """模型评估请求"""

    data_yaml: Optional[str] = Field(None, description="数据集配置文件路径（可选）")
    img_size: int = Field(640, description="图像尺寸")
    batch_size: int = Field(16, description="批次大小")


class DatasetValidateRequest(BaseModel):
    """数据集验证请求"""

    images_dir: str = Field(..., description="图像目录路径")
    labels_dir: str = Field(..., description="标注目录路径")
    class_names: str = Field(..., description="类别名称，逗号分隔")


class DatasetSplitRequest(BaseModel):
    """数据集划分请求"""

    images_dir: str = Field(..., description="图像目录路径")
    labels_dir: str = Field(..., description="标注目录路径")
    output_dir: str = Field(..., description="输出目录路径")
    train_ratio: float = Field(0.8, description="训练集比例")
    val_ratio: float = Field(0.1, description="验证集比例")
    test_ratio: float = Field(0.1, description="测试集比例")


class GenerateYamlRequest(BaseModel):
    """生成 data.yaml 配置请求"""

    output_path: str = Field(..., description="输出文件路径")
    class_names: str = Field(..., description="类别名称，逗号分隔")
    dataset_dir: str = Field(..., description="数据集根目录")


class CreateSceneRequest(BaseModel):
    """创建检测场景请求"""

    name: str = Field(..., description="场景标识")
    display_name: str = Field(..., description="场景显示名")
    description: str = Field("", description="场景描述")
    category: str = Field(..., description="场景分类")
    class_names: str = Field(..., description="类别名称，逗号分隔")
    class_names_cn: str = Field("", description="类别中文名，逗号分隔")


class DatasetUploadRequest(BaseModel):
    """数据集图片上传请求"""

    scene_id: int = Field(..., description="场景ID")
    dataset_name: str = Field("default", description="数据集名称")


class AutoLabelRequest(BaseModel):
    """自动标注请求"""

    scene_id: int = Field(..., description="场景ID")
    images_dir: str = Field(..., description="待标注图片目录")
    output_labels_dir: str = Field(..., description="标注输出目录")
    conf_threshold: float = Field(0.25, description="检测置信度阈值")
    image_size: int = Field(640, description="推理图像尺寸")


class DatasetInfo(BaseModel):
    """数据集信息"""

    name: str = Field(..., description="数据集名称")
    scene_id: int = Field(..., description="关联场景ID")
    total_images: int = Field(0, description="图片总数")
    labeled_count: int = Field(0, description="已标注图片数")
    unlabeled_count: int = Field(0, description="未标注图片数")
    train_count: int = Field(0, description="训练集数量")
    val_count: int = Field(0, description="验证集数量")
    test_count: int = Field(0, description="测试集数量")
    classes: list = Field([], description="类别列表")
    created_at: str = Field("", description="创建时间")
