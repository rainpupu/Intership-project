# -*- coding: utf-8 -*-
"""
数据库种子数据模块
在应用启动时自动检查并创建默认数据（检测场景等）
"""
from app.core.logger import get_logger

logger = get_logger("seed")


DEFAULT_SCENES = [
    {
        "name": "coco",
        "display_name": "COCO 通用目标检测",
        "description": "基于 COCO 数据集的 80 类通用目标检测，涵盖人、车辆、动物、家具等常见物体",
        "category": "common",
        "class_names": [
            "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
            "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
            "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
            "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
            "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
            "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
            "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
            "chair", "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop",
            "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
            "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
            "toothbrush",
        ],
        "class_names_cn": {
            "person": "人", "bicycle": "自行车", "car": "汽车", "motorcycle": "摩托车",
            "airplane": "飞机", "bus": "公交车", "train": "火车", "truck": "卡车", "boat": "船",
            "traffic light": "红绿灯", "fire hydrant": "消防栓", "stop sign": "停止标志",
            "parking meter": "停车计时器", "bench": "长椅", "bird": "鸟", "cat": "猫",
            "dog": "狗", "horse": "马", "sheep": "羊", "cow": "牛", "elephant": "大象",
            "bear": "熊", "zebra": "斑马", "giraffe": "长颈鹿", "backpack": "背包",
            "umbrella": "雨伞", "handbag": "手提包", "tie": "领带", "suitcase": "行李箱",
            "frisbee": "飞盘", "skis": "滑雪板", "snowboard": "滑雪板", "sports ball": "运动球",
            "kite": "风筝", "baseball bat": "棒球棒", "baseball glove": "棒球手套",
            "skateboard": "滑板", "surfboard": "冲浪板", "tennis racket": "网球拍",
            "bottle": "瓶子", "wine glass": "酒杯", "cup": "杯子", "fork": "叉子",
            "knife": "刀", "spoon": "勺子", "bowl": "碗", "banana": "香蕉", "apple": "苹果",
            "sandwich": "三明治", "orange": "橙子", "broccoli": "西兰花", "carrot": "胡萝卜",
            "hot dog": "热狗", "pizza": "披萨", "donut": "甜甜圈", "cake": "蛋糕",
            "chair": "椅子", "couch": "沙发", "potted plant": "盆栽", "bed": "床",
            "dining table": "餐桌", "toilet": "马桶", "tv": "电视", "laptop": "笔记本",
            "mouse": "鼠标", "remote": "遥控器", "keyboard": "键盘", "cell phone": "手机",
            "microwave": "微波炉", "oven": "烤箱", "toaster": "烤面包机", "sink": "水槽",
            "refrigerator": "冰箱", "book": "书", "clock": "时钟", "vase": "花瓶",
            "scissors": "剪刀", "teddy bear": "泰迪熊", "hair drier": "吹风机",
            "toothbrush": "牙刷",
        },
    },
    {
        "name": "remote_sensing",
        "display_name": "遥感目标检测",
        "description": "遥感图像中的目标检测，包括飞机、船舶、储油罐、车辆等",
        "category": "remote_sensing",
        "class_names": [
            "airplane", "ship", "storage-tank", "baseball-diamond", "tennis-court",
            "basketball-court", "ground-track-field", "harbor", "bridge", "vehicle",
        ],
        "class_names_cn": {
            "airplane": "飞机", "ship": "船舶", "storage-tank": "储油罐",
            "baseball-diamond": "棒球场", "tennis-court": "网球场",
            "basketball-court": "篮球场", "ground-track-field": "田径场",
            "harbor": "港口", "bridge": "桥梁", "vehicle": "车辆",
        },
    },
    {
        "name": "traffic",
        "display_name": "交通场景检测",
        "description": "交通场景中的车辆、行人、交通标志等目标检测",
        "category": "traffic",
        "class_names": [
            "car", "bus", "truck", "motorcycle", "bicycle", "person",
            "traffic light", "traffic sign", "stop sign", "parking meter",
        ],
        "class_names_cn": {
            "car": "汽车", "bus": "公交车", "truck": "卡车", "motorcycle": "摩托车",
            "bicycle": "自行车", "person": "行人", "traffic light": "红绿灯",
            "traffic sign": "交通标志", "stop sign": "停止标志", "parking meter": "停车计时器",
        },
    },
    {
        "name": "agriculture",
        "display_name": "农业病害检测",
        "description": "农作物病虫害检测，适用于农田、果园等场景",
        "category": "agriculture",
        "class_names": [
            "healthy", "leaf-blight", "rust", "mildew", "scab", "insect-damage",
            "nutrient-deficiency",
        ],
        "class_names_cn": {
            "healthy": "健康", "leaf-blight": "叶枯病", "rust": "锈病",
            "mildew": "霉病", "scab": "疮痂病", "insect-damage": "虫害",
            "nutrient-deficiency": "营养缺乏",
        },
    },
    {
        "name": "traffic_light",
        "display_name": "交通灯检测",
        "description": "车载影像交通灯状态识别（红/黄/绿/未亮灯）",
        "category": "traffic",
        "class_names": ["Red", "Yellow", "Green", "Off"],
        "class_names_cn": {
            "Red": "红灯", "Yellow": "黄灯", "Green": "绿灯", "Off": "未亮灯",
        },
    },
]


def seed_scenes(db_session) -> int:
    """
    初始化默认检测场景（如果表为空）

    在应用启动时调用，确保新安装的系统至少有基本场景可用。
    场景已存在时不会重复创建。

    Args:
        db_session: SQLAlchemy Session

    Returns:
        本次新创建的场景数量
    """
    from app.entity.db_models import DetectionScene

    existing_count = db_session.query(DetectionScene).count()
    if existing_count > 0:
        logger.info(f"检测场景已存在 {existing_count} 个，跳过种子数据初始化")
        return 0

    created = 0
    for scene_data in DEFAULT_SCENES:
        scene = DetectionScene(
            name=scene_data["name"],
            display_name=scene_data["display_name"],
            description=scene_data["description"],
            category=scene_data["category"],
            class_names=scene_data["class_names"],
            class_names_cn=scene_data["class_names_cn"],
            is_active=True,
        )
        db_session.add(scene)
        created += 1
        logger.info(f"创建默认检测场景: {scene_data['display_name']}")

    db_session.commit()
    logger.info(f"种子数据初始化完成，共创建 {created} 个检测场景")
    return created
