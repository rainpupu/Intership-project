from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.database.session import SessionLocal
from app.entity.db_models import (
    Cat,
    CatAuditRecord,
    CatIdentityEmbedding,
    CatObservation,
    RecognitionRecord,
)
from app.services.breed_name_service import to_chinese_breed_name
from app.services.individual_recognition_service import individual_recognition_service


DB_PATH = BASE_DIR / "data" / "cattrace.db"
STATIC_IMPORT_DIR = BASE_DIR / "static" / "cats" / "dataset_import"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

CAT_PROFILES: dict[str, dict[str, Any]] = {
    "三分白": {
        "location": "东温泉浴室附近",
        "last_seen_at": "2026-07-22 08:40",
        "previous_location": "梧桐大道树荫下",
        "previous_seen_at": "2026-07-20 18:15",
        "mood": "很放松",
        "tags": ["亲人", "安静", "已绝育"],
    },
    "妹妹": {
        "location": "一号楼前花园",
        "last_seen_at": "2026-07-22 09:25",
        "previous_location": "教学楼连廊",
        "previous_seen_at": "2026-07-19 17:30",
        "mood": "有点警觉",
        "tags": ["胆小", "温顺", "适合远观"],
    },
    "小笼包": {
        "location": "图书馆东侧长椅",
        "last_seen_at": "2026-07-21 16:20",
        "previous_location": "图书馆台阶旁",
        "previous_seen_at": "2026-07-18 11:10",
        "mood": "很放松",
        "tags": ["亲人", "贪吃", "常驻图书馆"],
    },
    "气球": {
        "location": "操场西门草坪",
        "last_seen_at": "2026-07-21 18:45",
        "previous_location": "体育馆入口",
        "previous_seen_at": "2026-07-17 19:05",
        "mood": "开心",
        "tags": ["活泼", "爱巡视", "已领养"],
    },
    "淡淡": {
        "location": "二号食堂后门",
        "last_seen_at": "2026-07-20 12:05",
        "previous_location": "二号食堂外卖柜旁",
        "previous_seen_at": "2026-07-16 12:30",
        "mood": "讨食",
        "tags": ["亲人", "贪吃", "橘猫"],
    },
    "焦糖": {
        "location": "校门东侧长椅",
        "last_seen_at": "2026-07-19 17:50",
        "previous_location": "行政楼花坛",
        "previous_seen_at": "2026-07-15 08:25",
        "mood": "很放松",
        "tags": ["稳重", "爱晒太阳", "亲人"],
    },
    "爆米花": {
        "location": "三号宿舍楼下",
        "last_seen_at": "2026-07-19 20:10",
        "previous_location": "宿舍区快递柜旁",
        "previous_seen_at": "2026-07-14 21:00",
        "mood": "好奇",
        "tags": ["话多", "亲人", "已领养"],
    },
    "狗蛋": {
        "location": "工程馆北门",
        "last_seen_at": "2026-07-18 10:35",
        "previous_location": "工程馆停车棚",
        "previous_seen_at": "2026-07-13 18:40",
        "mood": "很放松",
        "tags": ["胆大", "巡逻型", "已领养"],
    },
    "电动车": {
        "location": "电动车棚入口",
        "last_seen_at": "2026-07-18 15:30",
        "previous_location": "校医院旁小路",
        "previous_seen_at": "2026-07-12 09:50",
        "mood": "警觉",
        "tags": ["机敏", "常在车棚", "奶牛猫"],
    },
    "白衣": {
        "location": "校医院门口台阶",
        "last_seen_at": "2026-07-17 09:10",
        "previous_location": "银杏大道路口",
        "previous_seen_at": "2026-07-11 16:20",
        "mood": "安静",
        "tags": ["干净", "温顺", "白猫"],
    },
    "胖虎": {
        "location": "北门快递站旁",
        "last_seen_at": "2026-07-22 07:55",
        "previous_location": "学生服务中心后侧",
        "previous_seen_at": "2026-07-18 17:25",
        "mood": "正常",
        "tags": ["重点关注", "亲人", "需健康复查"],
    },
    "芝士挞": {
        "location": "南区花坛长椅",
        "last_seen_at": "2026-07-21 14:15",
        "previous_location": "南区教学楼入口",
        "previous_seen_at": "2026-07-16 10:05",
        "mood": "很放松",
        "tags": ["温柔", "爱睡觉", "白猫"],
    },
    "花耳朵": {
        "location": "老图书馆后花园",
        "last_seen_at": "2026-07-20 18:30",
        "previous_location": "老图书馆西侧小径",
        "previous_seen_at": "2026-07-15 19:20",
        "mood": "好奇",
        "tags": ["耳朵特征明显", "三花猫", "待补充信息"],
    },
    "豆豆": {
        "location": "一号楼前花园",
        "last_seen_at": "2026-07-22 13:40",
        "previous_location": "校友林石凳旁",
        "previous_seen_at": "2026-07-17 18:10",
        "mood": "开心",
        "tags": ["亲人", "已领养", "三花猫"],
    },
}


def _parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M")


def _parse_info(path: Path | None) -> dict[str, str]:
    if not path or not path.exists() or path.stat().st_size == 0:
        return {}

    content = path.read_text(encoding="utf-8-sig")
    data: dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or "：" not in line:
            continue
        key, value = line.split("：", 1)
        data[key.strip()] = value.strip()
    return data


def _normalize_health(value: str) -> str:
    text = value.strip()
    if not text:
        return "健康待确认"
    if text == "健康":
        return "健康良好"
    return text


def _normalize_breed(value: str, name: str) -> str:
    text = value.strip()
    if text == "狸花和彩狸":
        text = "狸花&彩狸"
    if not text and name == "花耳朵":
        text = "三花"
    return to_chinese_breed_name(text) or text or "待确认"


def _cat_code(index: int) -> str:
    return f"CAT-20260722-{index:03d}"


def _safe_slug(index: int, name: str) -> str:
    return f"{index:03d}-{name}"


def _copy_images(images: list[Path], target_dir: Path) -> tuple[list[str], list[Path]]:
    target_dir.mkdir(parents=True, exist_ok=True)
    urls: list[str] = []
    copied_paths: list[Path] = []
    for image_index, source in enumerate(images, start=1):
        suffix = source.suffix.lower() or ".jpg"
        target = target_dir / f"{image_index:02d}{suffix}"
        shutil.copy2(source, target)
        copied_paths.append(target)
        urls.append("/static/" + target.relative_to(BASE_DIR / "static").as_posix())
    return urls, copied_paths


def _clear_cat_data(db) -> None:
    db.query(CatIdentityEmbedding).delete(synchronize_session=False)
    db.query(CatObservation).delete(synchronize_session=False)
    db.query(CatAuditRecord).delete(synchronize_session=False)
    db.query(RecognitionRecord).delete(synchronize_session=False)
    db.query(Cat).delete(synchronize_session=False)
    db.commit()


def _backup_database() -> Path | None:
    db_path = BASE_DIR / "data" / "cattrace.db"
    if not db_path.exists():
        return None

    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"cattrace-before-cat-import-{datetime.now():%Y%m%d%H%M%S}.db"
    shutil.copy2(db_path, backup_path)
    return backup_path


def _remove_previous_import_images() -> None:
    if STATIC_IMPORT_DIR.exists():
        shutil.rmtree(STATIC_IMPORT_DIR)
    STATIC_IMPORT_DIR.mkdir(parents=True, exist_ok=True)


def _create_embeddings(db, cat: Cat, image_urls: list[str], image_paths: list[Path]) -> int:
    created = 0
    if not individual_recognition_service.is_available():
        return created

    for image_url, image_path in zip(image_urls, image_paths):
        try:
            embedding = individual_recognition_service.extract_embedding(image_path)
        except Exception as exc:
            print(f"[warn] skip embedding for {cat.name}: {image_path.name}: {exc}")
            continue

        db.add(
            CatIdentityEmbedding(
                cat_id=cat.id,
                embedding=embedding,
                image_url=image_url,
                source="dataset_import",
                created_by_id=None,
            )
        )
        created += 1
    return created


def _build_description(name: str, info: dict[str, str], profile: dict[str, Any]) -> str:
    if info.get("描述"):
        return info["描述"]
    tags = "、".join(profile["tags"][:3])
    return f"{name} 是校园猫数据集导入的猫咪档案，常出现在{profile['location']}，特征标签：{tags}。"


def _build_cat_payload(folder: Path, index: int) -> dict[str, Any]:
    txt_files = sorted(folder.glob("*.txt"))
    info = _parse_info(txt_files[0] if txt_files else None)
    images = sorted(
        [file for file in folder.iterdir() if file.is_file() and file.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}],
        key=lambda item: item.name.lower(),
    )

    name = folder.name
    profile = CAT_PROFILES[name]
    health_status = _normalize_health(info.get("健康状态", ""))
    return {
        "folder": folder,
        "images": images,
        "code": info.get("编号") or _cat_code(index),
        "name": name,
        "coat_color": _normalize_breed(info.get("毛色", ""), name),
        "age_stage": info.get("年龄阶段") or "年龄待确认",
        "gender": info.get("性别") or "性别待确认",
        "health_status": health_status,
        "mood_status": profile["mood"],
        "adoption_status": info.get("领养状态") or "待确认",
        "last_seen_location": profile["location"],
        "last_seen_at": _parse_time(profile["last_seen_at"]),
        "previous_location": profile["previous_location"],
        "previous_seen_at": _parse_time(profile["previous_seen_at"]),
        "description": _build_description(name, info, profile),
        "personality_tags": profile["tags"],
        "is_focus": health_status not in {"健康", "健康良好"},
    }


def _add_observations(db, cat: Cat, payload: dict[str, Any]) -> None:
    db.add(
        CatObservation(
            cat_id=cat.id,
            location=payload["last_seen_location"],
            mood_status=payload["mood_status"],
            health_status=payload["health_status"],
            observed_at=payload["last_seen_at"],
            description=None,
            created_by_id=None,
        )
    )
    db.add(
        CatObservation(
            cat_id=cat.id,
            location=payload["previous_location"],
            mood_status="状态稳定",
            health_status=payload["health_status"],
            observed_at=payload["previous_seen_at"],
            description=None,
            created_by_id=None,
        )
    )


def import_dataset(dataset_dir: Path) -> dict[str, Any]:
    if not dataset_dir.exists():
        raise FileNotFoundError(f"dataset dir not found: {dataset_dir}")

    cat_folders = sorted([item for item in dataset_dir.iterdir() if item.is_dir()], key=lambda item: item.name)
    if not cat_folders:
        raise RuntimeError(f"no cat folders found in {dataset_dir}")

    missing_profiles = [folder.name for folder in cat_folders if folder.name not in CAT_PROFILES]
    if missing_profiles:
        raise RuntimeError(f"missing cat profiles: {', '.join(missing_profiles)}")

    backup_path = _backup_database()
    _remove_previous_import_images()

    db = SessionLocal()
    imported = 0
    embeddings = 0
    try:
        _clear_cat_data(db)
        for index, folder in enumerate(cat_folders, start=1):
            payload = _build_cat_payload(folder, index)
            target_dir = STATIC_IMPORT_DIR / _safe_slug(index, payload["name"])
            image_urls, copied_paths = _copy_images(payload["images"], target_dir)
            cover_image = image_urls[0] if image_urls else ""

            cat = Cat(
                code=payload["code"],
                name=payload["name"],
                cover_image=cover_image,
                gallery_images=image_urls,
                coat_color=payload["coat_color"],
                age_stage=payload["age_stage"],
                gender=payload["gender"],
                personality_tags=payload["personality_tags"],
                health_status=payload["health_status"],
                mood_status=payload["mood_status"],
                adoption_status=payload["adoption_status"],
                last_seen_location=payload["last_seen_location"],
                last_seen_at=payload["last_seen_at"],
                description=payload["description"],
                is_focus=payload["is_focus"],
                created_by_id=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(cat)
            db.flush()

            _add_observations(db, cat, payload)
            db.add(
                CatAuditRecord(
                    cat_id=cat.id,
                    action="数据导入",
                    remark="从本地猫咪数据集重建猫咪档案。",
                    operator_id=None,
                    operator_name="数据导入脚本",
                    operated_at=datetime.now(),
                )
            )
            db.commit()

            cat_embeddings = _create_embeddings(db, cat, image_urls, copied_paths)
            embeddings += cat_embeddings
            db.commit()
            imported += 1
            print(f"[ok] {cat.code} {cat.name}: images={len(image_urls)}, embeddings={cat_embeddings}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return {"backup": str(backup_path) if backup_path else None, "cats": imported, "embeddings": embeddings}


def main() -> None:
    parser = argparse.ArgumentParser(description="Import local CatTrace cat dataset.")
    parser.add_argument("dataset_dir", type=Path)
    args = parser.parse_args()
    result = import_dataset(args.dataset_dir)
    print(result)


if __name__ == "__main__":
    main()
