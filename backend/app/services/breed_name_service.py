from __future__ import annotations

from typing import Any


BREED_NAME_ZH: dict[str, str] = {
    "abyssinian": "阿比西尼亚猫",
    "bengal": "孟加拉猫",
    "birman": "伯曼猫",
    "bombay": "孟买猫",
    "britishshorthair": "英国短毛猫",
    "egyptianmau": "埃及猫",
    "mainecoon": "缅因猫",
    "persian": "波斯猫",
    "ragdoll": "布偶猫",
    "russianblue": "俄罗斯蓝猫",
    "siamese": "暹罗猫",
    "sphynx": "斯芬克斯猫",
    "三花": "三花猫",
    "奶牛": "奶牛猫",
    "橘猫": "橘猫",
    "狸花&彩狸": "狸花猫/彩狸",
    "狸花彩狸": "狸花猫/彩狸",
    "白猫": "白猫",
}


def _normalize_key(name: str) -> str:
    return (
        name.strip()
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")
        .replace("/", "")
        .lower()
    )


def to_chinese_breed_name(name: Any) -> str:
    if name is None:
        return ""

    raw = str(name).strip()
    if not raw:
        return ""

    if raw in BREED_NAME_ZH:
        return BREED_NAME_ZH[raw]

    normalized = _normalize_key(raw)
    return BREED_NAME_ZH.get(normalized, raw)


def normalize_breed_text(text: str) -> str:
    normalized = text
    replacements = {
        "Abyssinian": "阿比西尼亚猫",
        "Bengal": "孟加拉猫",
        "Birman": "伯曼猫",
        "Bombay": "孟买猫",
        "British_Shorthair": "英国短毛猫",
        "British Shorthair": "英国短毛猫",
        "Egyptian_Mau": "埃及猫",
        "Egyptian Mau": "埃及猫",
        "Maine_Coon": "缅因猫",
        "Maine Coon": "缅因猫",
        "Persian": "波斯猫",
        "Ragdoll": "布偶猫",
        "Russian_Blue": "俄罗斯蓝猫",
        "Russian Blue": "俄罗斯蓝猫",
        "Siamese": "暹罗猫",
        "Sphynx": "斯芬克斯猫",
    }
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return normalized


def normalize_breed_candidates(value: Any) -> Any:
    if isinstance(value, list):
        return [normalize_breed_candidates(item) for item in value]

    if isinstance(value, dict):
        normalized = {key: normalize_breed_candidates(item) for key, item in value.items()}
        breed_name = normalized.get("breedName")
        if breed_name:
            normalized["breedName"] = to_chinese_breed_name(breed_name)
        if normalized.get("name"):
            normalized_name = to_chinese_breed_name(normalized["name"])
            if (
                normalized_name != normalized["name"]
                or normalized.get("modelType") == "breed"
                or str(normalized.get("catId", "")).startswith("breed-")
            ):
                normalized["name"] = normalized_name
        return normalized

    if isinstance(value, str):
        return normalize_breed_text(value)

    return value
