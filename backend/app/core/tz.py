"""
东八区时区工具模块

提供统一的时区常量和时间获取函数，避免各模块重复定义 CST。
所有需要东八区时间的地方应从本模块导入。
"""
from datetime import datetime, timezone, timedelta

# 东八区时区常量（CST = China Standard Time）
CST = timezone(timedelta(hours=8))


def now_cst() -> datetime:
    """返回当前东八区时间（带时区信息）"""
    return datetime.now(CST)
