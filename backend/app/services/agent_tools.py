"""Agent 工具定义。"""

import re
from pathlib import Path
from langchain_core.tools import tool
from sqlalchemy import String, func
from pydantic import BaseModel, Field


# ======== 工具输入模型 ========

class SearchCatsInput(BaseModel):
    keyword: str = Field(default="", description="搜索关键词（名称、编号）")
    coat_color: str = Field(default="", description="花色筛选")
    adoption_status: str = Field(default="", description="领养状态")
    limit: int = Field(default=10, description="返回数量上限")


class GetCatProfileInput(BaseModel):
    cat_id: int = Field(description="猫咪 ID")


class GetCatObservationsInput(BaseModel):
    cat_id: int = Field(description="猫咪 ID")
    limit: int = Field(default=10, description="返回条数上限")


class GetRecentEncountersInput(BaseModel):
    cat_id: int = Field(default=0, description="猫咪 ID，0 表示全部")
    days: int = Field(default=30, description="查询天数范围")


class RecommendAdoptionCatsInput(BaseModel):
    personality: str = Field(default="", description="偏好的猫咪性格")
    experience: str = Field(default="", description="养猫经验：新手/有经验")
    limit: int = Field(default=3, description="推荐数量上限")


class GetAttentionCatsInput(BaseModel):
    limit: int = Field(default=10, description="返回数量上限")


class QueryKnowledgeBaseInput(BaseModel):
    query: str = Field(description="检索关键词或问题")


# ======== 知识库加载 ========

_KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parents[3] / "knowledge" / "cat_knowledge_base.md"


def _load_knowledge_base() -> dict[str, str]:
    """从 cat_knowledge_base.md 读取知识库，按 ## 和 ### 小标题切分成条目。"""
    try:
        with open(_KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return {}

    entries: dict[str, str] = {}
    lines = content.split("\n")
    current_key = ""
    current_value: list[str] = []

    for line in lines:
        # 遇到 ## 或 ### 标题时创建新条目
        if line.startswith("### ") or line.startswith("## "):
            # 保存前一个条目
            if current_key and current_value:
                entries[current_key] = "\n".join(current_value).strip()
            # 提取标题文本（去掉 ##/### 前缀和章节编号如 "3.1 "）
            prefix_len = 4 if line.startswith("### ") else 3
            current_key = re.sub(r'^\d+\.\d+\s+', '', line[prefix_len:].strip())
            # 也去掉中文编号前缀如 "一、" "二、"
            current_key = re.sub(r'^[一二三四五六七八九十]+、\s*', '', current_key)
            current_value = [line]
        elif current_key:
            current_value.append(line)

    # 保存最后一个条目
    if current_key and current_value:
        entries[current_key] = "\n".join(current_value).strip()

    return entries


_KB: dict[str, str] | None = None


def _get_kb() -> dict[str, str]:
    global _KB
    if _KB is None:
        _KB = _load_knowledge_base()
    return _KB


# 同义词映射：用户常用说法 → 知识库标题
_SYNONYMS: dict[str, str] = {
    # 领养流程
    "领养流程": "线下领养流程",
    "怎么领养": "线下领养流程",
    "如何领养": "线下领养流程",
    "申请领养": "线下领养流程",
    "领养步骤": "线下领养流程",
    "领养申请": "线下领养流程",
    "领养准备": "领养前的自我评估",
    "领养条件": "领养前的自我评估",
    "领养评估": "领养前的自我评估",
    "能不能养猫": "领养前的自我评估",
    "养猫要多少钱": "领养前的自我评估",
    "养猫每月花费": "领养前的自我评估",
    # 云领养
    "云领养": "云领养说明",
    "云养猫": "云领养说明",
    "云助养": "云领养说明",
    "云养": "云领养说明",
    "什么是云领养": "云领养说明",
    # TNR / 流浪猫救助
    "TNR": "TNR 方法",
    "tnr": "TNR 方法",
    "流浪猫救助": "TNR 方法",
    "救助流浪猫": "TNR 方法",
    "怎么救流浪猫": "TNR 方法",
    "流浪猫怎么救": "TNR 方法",
    "诱捕": "TNR 方法",
    "抓捕流浪猫": "TNR 方法",
    "流浪猫调查": "流浪猫调查方法",
    "怎么调查流浪猫": "流浪猫调查方法",
    "校园流浪猫统计": "流浪猫调查方法",
    # 受伤猫咪
    "猫咪受伤": "受伤猫咪处理",
    "猫受伤了": "受伤猫咪处理",
    "流浪猫受伤": "受伤猫咪处理",
    "外伤": "受伤猫咪处理",
    "猫外伤": "受伤猫咪处理",
    "猫出血": "受伤猫咪处理",
    # 饮食
    "猫吃什么": "饮食",
    "喂猫": "饮食",
    "猫粮": "饮食",
    "猫不能吃什么": "饮食",
    "猫咪饮食": "饮食",
    "猫零食": "饮食",
    "干粮湿粮": "饮食",
    # 猫砂
    "猫砂": "猫砂与排泄",
    "铲屎": "猫砂与排泄",
    "排便": "猫砂与排泄",
    "猫砂盆": "猫砂与排泄",
    # 生活环境
    "猫住哪": "生活环境",
    "养猫环境": "生活环境",
    "窗户安全": "生活环境",
    "封窗": "生活环境",
    "封阳台": "生活环境",
    "猫爬架": "生活环境",
    # 睡眠
    "猫睡觉": "猫咪睡眠",
    "猫睡多久": "猫咪睡眠",
    "猫总睡觉": "猫咪睡眠",
    "猫经常睡觉": "猫咪睡眠",
    "猫怎么睡觉正常吗": "猫咪睡眠",
    "猫老睡觉": "猫咪睡眠",
    "猫咪作息": "猫咪睡眠",
    # 运动玩耍
    "猫运动": "猫咪运动和玩耍",
    "陪猫玩": "猫咪运动和玩耍",
    "逗猫": "猫咪运动和玩耍",
    "猫玩具": "猫咪运动和玩耍",
    # 清洁
    "猫洗澡": "猫咪清洁",
    "给猫洗澡": "猫咪清洁",
    "猫梳毛": "猫咪清洁",
    "猫剪指甲": "猫咪清洁",
    "猫刷牙": "猫咪清洁",
    "猫耳朵清理": "猫咪清洁",
    "猫多久洗一次澡": "猫咪清洁",
    # 情绪陪伴
    "猫的情绪": "猫咪情绪与陪伴",
    "猫陪伴": "猫咪情绪与陪伴",
    "多猫": "猫咪情绪与陪伴",
    "多猫家庭": "猫咪情绪与陪伴",
    "引入新猫": "猫咪情绪与陪伴",
    "猫焦虑": "猫咪情绪与陪伴",
    "猫孤独": "猫咪情绪与陪伴",
    # 疫苗
    "疫苗": "疫苗",
    "猫三联": "疫苗",
    "打疫苗": "疫苗",
    "接种": "疫苗",
    "狂犬": "疫苗",
    # 驱虫
    "驱虫": "驱虫",
    "除虫": "驱虫",
    "体外驱虫": "驱虫",
    "体内驱虫": "驱虫",
    # 绝育
    "绝育": "绝育",
    "猫绝育": "绝育",
    "公猫绝育": "绝育",
    "母猫绝育": "绝育",
    "猫做手术": "绝育",
    # 常见病症（基础）
    "猫癣": "常见病症",
    "猫生病": "常见病症",
    "耳螨": "常见病症",
    "猫口臭": "常见病症",
    "口炎": "常见病症",
    "口腔问题": "常见病症",
    "生病": "常见病症",
    # 就医信号
    "什么时候看医生": "就医信号",
    "就医": "就医信号",
    "看兽医": "就医信号",
    "猫咪生病怎么办": "就医信号",
    # 拍片
    "拍片": "猫咪拍片",
    "猫拍片子": "猫咪拍片",
    "X光": "猫咪拍片",
    "猫彩超": "猫咪拍片",
    "猫B超": "猫咪拍片",
    "猫拍片子": "猫咪拍片",
    "拍片子": "猫咪拍片",
    # 泌尿
    "猫尿不出来": "泌尿系统疾病",
    "猫尿血": "泌尿系统疾病",
    "猫膀胱": "泌尿系统疾病",
    "猫结石": "泌尿系统疾病",
    "猫尿路": "泌尿系统疾病",
    "猫尿闭": "泌尿系统疾病",
    "猫泌尿": "泌尿系统疾病",
    # 猫癣
    "猫掉毛": "猫癣",
    "猫皮肤": "猫癣",
    "猫脱毛": "猫癣",
    "猫长癣": "猫癣",
    # 猫瘟
    "猫瘟": "猫瘟",
    "FPV": "猫瘟",
    "猫细小": "猫瘟",
    "猫传染病": "猫瘟",
    # 猫鼻支
    "猫鼻支": "猫鼻支",
    "猫感冒": "猫鼻支",
    "猫流鼻涕": "猫鼻支",
    "猫打喷嚏": "猫鼻支",
    "FHV": "猫鼻支",
    "猫疱疹": "猫鼻支",
    # 传腹
    "猫传腹": "猫传腹",
    "FIP": "猫传腹",
    "猫腹水": "猫传腹",
    "猫冠状病毒": "猫传腹",
    "441": "猫传腹",
    # 呕吐
    "猫呕吐": "呕吐",
    "猫吐了": "呕吐",
    "猫吐毛": "呕吐",
    "猫吐黄水": "呕吐",
    "猫一直吐": "呕吐",
    # 腹泻
    "猫拉肚子": "腹泻",
    "猫拉稀": "腹泻",
    "猫软便": "腹泻",
    "猫便血": "腹泻",
    # 便秘
    "猫便秘": "便秘",
    "猫拉不出": "便秘",
    "猫不拉屎": "便秘",
    "猫排便困难": "便秘",
    # 中耳炎
    "猫中耳炎": "中耳炎",
    "猫歪头": "中耳炎",
    "猫耳朵炎症": "中耳炎",
    # 外伤出血
    "猫外伤处理": "外伤出血",
    "猫受伤流血": "外伤出血",
    "猫伤口": "外伤出血",
    # 中毒
    "猫中毒": "中毒",
    "猫吃了有毒的": "中毒",
    "猫中毒怎么办": "中毒",
    "百合": "中毒",
    "蚊香": "中毒",
    "猫菊酯": "中毒",
    "猫吃了百合": "中毒",
    # 心丝虫
    "猫心丝虫": "心丝虫病",
    "蚊子传播": "心丝虫病",
    # 瘫痪骨折
    "猫骨折": "瘫痪与骨折",
    "猫瘫痪": "瘫痪与骨折",
    "猫腿断了": "瘫痪与骨折",
    "猫摔伤": "瘫痪与骨折",
    "猫跛行": "瘫痪与骨折",
    # 应激
    "猫害怕": "猫咪应激反应",
    "猫怕人": "猫咪应激反应",
    "猫怕人怎么办": "猫咪应激反应",
    "猫胆小": "猫咪应激反应",
    "猫搬家": "猫咪应激反应",
    "猫躲起来": "猫咪应激反应",
    "猫应激": "猫咪应激反应",
    "猫紧张": "猫咪应激反应",
    # 行为解读
    "猫为什么咕噜": "猫咪行为解读",
    "猫为什么呼噜": "猫咪行为解读",
    "猫呼噜": "猫咪行为解读",
    "咕噜": "猫咪行为解读",
    "猫咪行为": "猫咪行为解读",
    "猫尾巴": "猫咪行为解读",
    "猫叫什么意思": "猫咪行为解读",
    "猫抓家具": "猫咪行为解读",
    "抓挠": "猫咪行为解读",
    # 误区
    "猫从高处跳": "常见误区",
    "猫坠楼": "常见误区",
    "猫喝牛奶": "常见误区",
    "牛奶给猫喝": "常见误区",
    "猫不需要遛吗": "常见误区",
    "猫需要遛吗": "常见误区",
    "猫不能喝牛奶吗": "常见误区",
    "猫不能喝牛奶": "常见误区",
    "猫能不能喝牛奶": "常见误区",
    # 幼猫
    "小猫怎么养": "幼猫护理",
    "幼猫": "幼猫护理",
    "小奶猫": "幼猫护理",
    "刚出生的小猫": "幼猫护理",
    "幼猫喂奶": "幼猫护理",
    "幼猫保暖": "幼猫护理",
    # 孕猫
    "怀孕母猫": "怀孕及哺乳母猫护理",
    "母猫怀孕": "怀孕及哺乳母猫护理",
    "猫怀孕": "怀孕及哺乳母猫护理",
    "猫生产": "怀孕及哺乳母猫护理",
    "猫哺乳": "怀孕及哺乳母猫护理",
    "猫接生": "怀孕及哺乳母猫护理",
    "遇到怀孕流浪猫": "遇到怀孕流浪母猫怎么办",
    "怀孕母猫怎么处理": "遇到怀孕流浪母猫怎么办",
    "怀孕流浪猫怎么救助": "遇到怀孕流浪母猫怎么办",
    "捡到怀孕的猫": "遇到怀孕流浪母猫怎么办",
    "孕猫救助": "遇到怀孕流浪母猫怎么办",
    "流浪猫怀孕了": "母猫绝育与引产",
    "怀孕猫要不要引产": "母猫绝育与引产",
    "引产还是生": "母猫绝育与引产",
    "不绝育会怎样": "绝育",
    "不绝育的后果": "绝育",
    "流浪猫繁殖": "母猫绝育与引产",
    # 猫条零食危害
    "猫条": "猫条与零食的危害",
    "猫条能吃吗": "猫条与零食的危害",
    "猫条有害吗": "猫条与零食的危害",
    "为什么不能喂猫条": "猫条与零食的危害",
    "零食对猫有害": "猫条与零食的危害",
    "湿粮包": "猫条与零食的危害",
    "猫零食": "猫条与零食的危害",
    # 母猫引产
    "母猫引产": "母猫绝育与引产",
    "怀孕母猫绝育": "母猫绝育与引产",
    "引产": "母猫绝育与引产",
    "流浪母猫怀孕": "母猫绝育与引产",
    "母猫怀孕了怎么办": "母猫绝育与引产",
    "流浪猫生小猫": "母猫绝育与引产",
    "猫引产": "母猫绝育与引产",
    "TNR引产": "母猫绝育与引产",
    # 科学投喂
    "流浪猫喂什么": "流浪猫科学投喂",
    "给流浪猫吃什么": "流浪猫科学投喂",
    "喂流浪猫": "流浪猫科学投喂",
    "怎么喂流浪猫": "流浪猫科学投喂",
    "流浪猫能喂猫条吗": "流浪猫科学投喂",
    "流浪猫不能吃什么": "流浪猫科学投喂",
    "流浪猫投喂": "流浪猫科学投喂",
    "投喂流浪猫注意事项": "流浪猫科学投喂",
    # 救助原则
    "救助原则": "救助原则与范围",
    "怎么救助流浪猫": "救助原则与范围",
    "弃养猫": "救助原则与范围",
    "遗弃猫": "救助原则与范围",
    "后院猫": "救助原则与范围",
    "救助范围": "救助原则与范围",
    "第一救助人": "救助原则与范围",
    "救助组织": "救助原则与范围",
    "虐猫": "救助原则与范围",
    "撸猫风险": "救助原则与范围",
    "摸流浪猫会得病吗": "救助原则与范围",
    "流浪猫抓伤": "救助原则与范围",
    # 更多绝育相关
    "猫为什么要绝育": "绝育",
    "绝育的好处": "绝育",
    "不绝育会怎样": "绝育",
    "TNR": "TNR 方法",

    # 新猫到家
    "新猫到家": "线下领养流程",
    "新猫准备": "线下领养流程",
    "接猫回家": "线下领养流程",
    # 新猫到家
    "新猫到家怎么办": "新猫到家过渡期",
    "新猫躲着": "新猫到家过渡期",
    "新猫适应": "新猫到家过渡期",
    "新猫叫": "新猫到家过渡期",
    "新猫不吃": "新猫到家过渡期",
    # 生命周期
    "猫能活多久": "猫咪生命周期",
    "猫寿命": "猫咪生命周期",
    "猫咪年龄": "猫咪生命周期",
    "猫老年": "猫咪生命周期",
    "老猫怎么养": "猫咪生命周期",
    "猫多大了算老": "猫咪生命周期",
    # 外出寄养
    "猫寄养": "猫咪外出与寄养",
    "寄养": "猫咪外出与寄养",
    "出门猫怎么办": "猫咪外出与寄养",
    "猫坐车": "猫咪外出与寄养",
    "过年猫怎么办": "猫咪外出与寄养",
    "航空箱": "猫咪外出与寄养",
    # 过敏
    "猫过敏": "人对猫过敏怎么办",
    "对猫过敏": "人对猫过敏怎么办",
    "养猫过敏": "人对猫过敏怎么办",
    "过敏能养猫吗": "人对猫过敏怎么办",
    # 植物
    "什么植物对猫有毒": "猫与室内植物安全",
    "猫能吃植物吗": "猫与室内植物安全",
    "猫和植物": "猫与室内植物安全",
    "对猫安全的植物": "猫与室内植物安全",
    # 流浪猫过冬
    "流浪猫冬天": "流浪猫冬季救助",
    "流浪猫过冬": "流浪猫冬季救助",
    "冬天流浪猫": "流浪猫冬季救助",
    "猫窝怎么做": "流浪猫冬季救助",
    "流浪猫冷": "流浪猫冬季救助",
    # 更多饮食
    "猫粮怎么选": "饮食",
    "怎么选猫粮": "饮食",
    "猫粮推荐": "饮食",
    "生骨肉": "饮食",
    "猫饭": "饮食",
    "自制猫饭": "饮食",
    "猫不吃东西": "饮食",
    "猫不吃粮": "饮食",
    # 更多排泄
    "猫乱拉": "猫砂与排泄",
    "猫乱尿": "猫砂与排泄",
    "猫不在猫砂盆": "猫砂与排泄",
    "猫砂选什么": "猫砂与排泄",
    # 封窗
    "养猫必须封窗吗": "生活环境",
    "猫跳楼": "生活环境",
    "猫坠楼": "生活环境",
}


def _ngrams(text: str, n: int) -> set[str]:
    """从文本中提取 n-gram，用于模糊匹配。"""
    clean = "".join(ch for ch in text if ch.isalnum() or ch.isspace())
    chars = clean.replace(" ", "")
    return {chars[i:i+n] for i in range(len(chars) - n + 1)}


def _match_knowledge(query: str, kb: dict[str, str]) -> str | None:
    """在知识库中匹配用户 query，返回匹配到的内容文本，未命中返回 None。"""

    # 1) 同义词精确映射（完整 query 匹配 → 映射到标题）
    query_stripped = query.strip()
    if query_stripped in _SYNONYMS:
        target_title = _SYNONYMS[query_stripped]
        if target_title in kb:
            return kb[target_title]

    # 也检查去掉"吗？呢！"等语气词后的 query
    query_clean = query_stripped.rstrip("？！吗呢啊吧")
    if query_clean and query_clean != query_stripped and query_clean in _SYNONYMS:
        target_title = _SYNONYMS[query_clean]
        if target_title in kb:
            return kb[target_title]

    # 2) 同义词子串匹配（检查每个同义 key 是否出现在 query 中）
    for syn_key, title in _SYNONYMS.items():
        if syn_key in query_stripped and title in kb:
            return kb[title]

    # 3) 直接子串匹配（解决 2-3 字 key 在 n-gram 中吃亏的问题）
    query_clean_nosp = "".join(ch for ch in query_stripped if ch.isalnum())
    for key in kb:
        key_clean = "".join(ch for ch in key if ch.isalnum())
        if len(key_clean) >= 2 and (key_clean in query_clean_nosp or query_clean_nosp in key_clean):
            return kb[key]

    # 4) 关键词重叠匹配（bigram + trigram 得分）
    q_bigrams = _ngrams(query_stripped, 2)
    q_trigrams = _ngrams(query_stripped, 3)

    best_score = 0
    best_key = None
    for key in kb:
        k_bigrams = _ngrams(key, 2)
        k_trigrams = _ngrams(key, 3)
        overlap_bi = len(q_bigrams & k_bigrams)
        overlap_tri = len(q_trigrams & k_trigrams)
        score = overlap_bi + overlap_tri * 2
        if score > best_score:
            best_score = score
            best_key = key

    # 短 key 只需 1 个重叠，长 key 需 2 个
    threshold = 1 if best_key and len(best_key) <= 3 else 2
    if best_score >= threshold and best_key and best_key in kb:
        return kb[best_key]

    return None


# ======== 工具函数 ========

@tool("search_cats", args_schema=SearchCatsInput)
def search_cats(keyword: str = "", coat_color: str = "", adoption_status: str = "", limit: int = 10) -> str:
    """搜索猫咪列表，支持按名称/编号/花色/领养状态筛选。"""
    from app.database.session import SessionLocal
    from app.entity.db_models import Cat
    db = SessionLocal()
    try:
        query = db.query(Cat)
        if keyword:
            query = query.filter((Cat.name.contains(keyword)) | (Cat.code.contains(keyword)))
        if coat_color:
            query = query.filter(Cat.coat_color.contains(coat_color))
        if adoption_status:
            query = query.filter(Cat.adoption_status == adoption_status)
        cats = query.limit(limit).all()
        if not cats:
            return "没有找到符合条件的猫咪。"
        lines = []
        for cat in cats:
            lines.append(
                f"- {cat.name}（{cat.code}）：{cat.coat_color} {cat.age_stage}{cat.gender}猫，"
                f"性格：{cat.personality_tags}，领养状态：{cat.adoption_status}，"
                f"最近出现：{cat.last_seen_at.strftime('%Y-%m-%d') if cat.last_seen_at else '未知'}"
            )
        return f"共找到 {len(lines)} 只猫咪：\n" + "\n".join(lines)
    finally:
        db.close()


@tool("get_cat_profile", args_schema=GetCatProfileInput)
def get_cat_profile(cat_id: int) -> str:
    """获取指定猫咪的完整档案。"""
    from app.database.session import SessionLocal
    from app.entity.db_models import Cat
    db = SessionLocal()
    try:
        cat = db.query(Cat).filter(Cat.id == cat_id).first()
        if not cat:
            return f"未找到 ID 为 {cat_id} 的猫咪。"
        return (
            f"【{cat.name}】\n"
            f"编号：{cat.code}\n"
            f"花色：{cat.coat_color} | 年龄：{cat.age_stage} | 性别：{cat.gender}\n"
            f"性格标签：{cat.personality_tags}\n"
            f"领养状态：{cat.adoption_status}\n"
            f"最近出现：{cat.last_seen_at.strftime('%Y-%m-%d') if cat.last_seen_at else '未知'}\n"
            f"简介：{cat.description or '暂无简介'}"
        )
    finally:
        db.close()


@tool("get_cat_observations", args_schema=GetCatObservationsInput)
def get_cat_observations(cat_id: int, limit: int = 10) -> str:
    """获取指定猫咪的状态观察记录时间线。"""
    from app.database.session import SessionLocal
    from app.entity.db_models import CatObservation
    db = SessionLocal()
    try:
        records = db.query(CatObservation).filter(CatObservation.cat_id == cat_id).order_by(CatObservation.observed_at.desc()).limit(limit).all()
        if not records:
            return "暂无该猫咪的状态记录。"
        lines = []
        for r in records:
            lines.append(
                f"- [{r.observed_at.strftime('%Y-%m-%d') if r.observed_at else '未知'}] "
                f"地点：{r.location or '未知'} | 情绪：{r.mood_status} | 健康：{r.health_status} | "
                f"{r.description or '无'}"
            )
        return f"最近 {len(records)} 条状态记录：\n" + "\n".join(lines)
    finally:
        db.close()


@tool("get_recent_encounters", args_schema=GetRecentEncountersInput)
def get_recent_encounters(cat_id: int = 0, days: int = 30) -> str:
    """获取近期猫咪出现事件记录。cat_id=0 表示查询全部。"""
    from datetime import datetime, timedelta
    from app.database.session import SessionLocal
    from app.entity.db_models import CatObservation
    db = SessionLocal()
    try:
        cutoff = datetime.now() - timedelta(days=days)
        query = db.query(CatObservation).filter(CatObservation.observed_at >= cutoff)
        if cat_id > 0:
            query = query.filter(CatObservation.cat_id == cat_id)
        records = query.order_by(CatObservation.observed_at.desc()).all()
        if not records:
            return "近期没有出现事件记录。"
        lines = []
        for r in records:
            lines.append(f"- [{r.observed_at.strftime('%Y-%m-%d %H:%M') if r.observed_at else '未知'}] 地点：{r.location or '未知'}（{r.health_status or '未记录'}）")
        return f"最近 {len(records)} 条出现记录：\n" + "\n".join(lines)
    finally:
        db.close()


@tool("recommend_adoption_cats", args_schema=RecommendAdoptionCatsInput)
def recommend_adoption_cats(personality: str = "", experience: str = "", limit: int = 3) -> str:
    """根据用户偏好推荐适合领养的猫咪。"""
    from app.database.session import SessionLocal
    from app.entity.db_models import Cat
    db = SessionLocal()
    try:
        query = db.query(Cat).filter(~Cat.adoption_status.in_(["已领养", "领养中"]))
        if experience == "新手":
            query = query.filter(Cat.age_stage == "成年").filter(func.cast(Cat.personality_tags, String).contains("亲人"))
        if personality:
            query = query.filter(func.cast(Cat.personality_tags, String).contains(personality))
        cats = query.limit(limit).all()
        if not cats:
            cats = db.query(Cat).filter(~Cat.adoption_status.in_(["已领养", "领养中"])).limit(limit).all()
        if not cats:
            return "当前没有可供领养的猫咪。"
        lines = []
        for cat in cats:
            lines.append(
                f"- {cat.name}（{cat.coat_color} {cat.age_stage}{cat.gender}猫）"
                f"：{cat.personality_tags}，{cat.description or '暂无简介'}"
            )
        response = f"为您推荐 {len(cats)} 只猫咪：\n" + "\n".join(lines)
        if experience == "新手":
            response += "\n\n温馨提示：作为新手领养人，建议选择性格亲人、成年的猫咪，它们通常更稳定好养。"
        return response
    finally:
        db.close()


@tool("get_attention_cats", args_schema=GetAttentionCatsInput)
def get_attention_cats(limit: int = 10) -> str:
    """获取需要重点关注的猫咪列表（健康异常、长期未出现等）。"""
    from app.database.session import SessionLocal
    from app.entity.db_models import Cat, CatObservation
    db = SessionLocal()
    try:
        cats = db.query(Cat).all()
        result = []
        for cat in cats:
            latest_obs = db.query(CatObservation).filter(CatObservation.cat_id == cat.id).order_by(CatObservation.observed_at.desc()).first()
            if latest_obs and latest_obs.health_status in ("需观察", "异常", "观察中", "需复查"):
                result.append((cat, f"健康需关注: {latest_obs.description or latest_obs.health_status}"))
        if not result:
            return "目前所有猫咪状态良好，无需特别关注。"
        lines = []
        for cat, reason in result[:limit]:
            lines.append(f"- {cat.name}：{reason}，最近出现：{cat.last_seen_at.strftime('%Y-%m-%d') if cat.last_seen_at else '未知'}")
        return f"以下 {len(lines)} 只猫咪需要关注：\n" + "\n".join(lines)
    finally:
        db.close()


@tool("query_knowledge_base", args_schema=QueryKnowledgeBaseInput)
def query_knowledge_base(query: str) -> str:
    """从知识库检索相关信息。"""
    kb = _get_kb()
    if not kb:
        return "请直接基于通用养猫常识回答用户，不要提及资料来源或检索过程。"

    result = _match_knowledge(query, kb)
    if result is not None:
        return result

    return "暂无匹配的知识库条目，建议结合通用养猫常识给出谨慎回答，并在医疗问题上提示咨询专业兽医。"
