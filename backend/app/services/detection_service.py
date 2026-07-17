"""检测服务（桩）"""
from app.core.logger import get_logger

logger = get_logger("detection")


class DetectionService:
    """检测服务类"""

    async def detect_single(self, **kwargs):
        raise NotImplementedError("检测服务待实现")

    async def detect_batch(self, **kwargs):
        raise NotImplementedError("批量检测待实现")

    async def detect_video(self, **kwargs):
        raise NotImplementedError("视频检测待实现")

    async def save_detection_result(self, **kwargs):
        raise NotImplementedError("结果保存待实现")

    def get_task_results(self, **kwargs):
        raise NotImplementedError("结果查询待实现")

    def get_task_list(self, **kwargs):
        raise NotImplementedError("任务列表待实现")


detection_service = DetectionService()