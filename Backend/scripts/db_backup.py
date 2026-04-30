"""
MongoDB 資料庫備份與還原腳本。

用法：
    # 備份（dump）
    python scripts/db_backup.py dump

    # 還原（restore）
    python scripts/db_backup.py restore

    # 指定備份資料夾名稱
    python scripts/db_backup.py dump --name my_backup
    python scripts/db_backup.py restore --name my_backup

備份檔案存放於 Backend/db_dumps/ 目錄下，
每次 dump 會建立一個以時間戳命名的子資料夾（或自訂名稱），
每個集合匯出為一個 JSON 檔。
"""

import asyncio
import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

from bson import json_util
from motor.motor_asyncio import AsyncIOMotorClient

# 設定
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "myapp"
DUMP_ROOT = Path(__file__).parent.parent / "db_dumps"


def get_latest_dump_dir() -> Path | None:
    """取得最新的備份資料夾。"""
    if not DUMP_ROOT.exists():
        return None
    dirs = sorted(
        [d for d in DUMP_ROOT.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    return dirs[0] if dirs else None

async def dump(dump_dir: Path) -> None:
    """備份所有集合到指定資料夾。"""
    dump_dir.mkdir(parents=True, exist_ok=True)

    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    collections = await db.list_collection_names()
    print(f"資料庫: {DB_NAME}")
    print(f"備份路徑: {dump_dir}")
    print(f"集合數量: {len(collections)}\n")

    total_docs = 0
    for col_name in sorted(collections):
        collection = db[col_name]
        docs = []
        async for doc in collection.find({}):
            docs.append(doc)

        # 用 bson json_util 序列化（保留 ObjectId、datetime 等型別）
        file_path = dump_dir / f"{col_name}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                docs,
                f,
                default=json_util.default,
                ensure_ascii=False,
                indent=2,
            )

        total_docs += len(docs)
        print(f"  ✓ {col_name}: {len(docs)} 筆 → {file_path.name}")

    # 寫入備份資訊
    meta = {
        "database": DB_NAME,
        "timestamp": datetime.now().isoformat(),
        "collections": len(collections),
        "total_documents": total_docs,
    }
    with open(dump_dir / "_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n備份完成！共 {total_docs} 筆文件")
    client.close()


async def restore(dump_dir: Path) -> None:
    """從指定資料夾還原所有集合。"""
    if not dump_dir.exists():
        print(f"錯誤：備份資料夾不存在: {dump_dir}")
        sys.exit(1)

    json_files = list(dump_dir.glob("*.json"))
    json_files = [f for f in json_files if f.name != "_meta.json"]

    if not json_files:
        print(f"錯誤：備份資料夾中沒有 JSON 檔案: {dump_dir}")
        sys.exit(1)

    # 顯示備份資訊
    meta_path = dump_dir / "_meta.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        print(f"備份時間: {meta.get('timestamp', '未知')}")
        print(f"原始文件數: {meta.get('total_documents', '未知')}")
    print(f"備份路徑: {dump_dir}")
    print(f"JSON 檔案: {len(json_files)} 個\n")

    # 確認
    answer = input("確定要還原嗎？這會清除現有資料再匯入。(y/N): ").strip().lower()
    if answer != "y":
        print("已取消")
        return

    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    total_docs = 0
    for file_path in sorted(json_files):
        col_name = file_path.stem  # 檔名去掉 .json 就是集合名稱

        with open(file_path, "r", encoding="utf-8") as f:
            docs = json.load(f, object_hook=json_util.object_hook)

        if not docs:
            print(f"  ⊘ {col_name}: 0 筆（跳過）")
            continue

        # 清除現有資料再匯入
        collection = db[col_name]
        await collection.delete_many({})
        await collection.insert_many(docs)

        total_docs += len(docs)
        print(f"  ✓ {col_name}: {len(docs)} 筆已還原")

    print(f"\n還原完成！共 {total_docs} 筆文件")
    client.close()


def main():
    parser = argparse.ArgumentParser(description="MongoDB 資料庫備份與還原")
    parser.add_argument("action", choices=["dump", "restore"], help="dump=備份, restore=還原")
    parser.add_argument("--name", type=str, default=None, help="備份資料夾名稱（預設用時間戳）")
    args = parser.parse_args()

    if args.action == "dump":
        folder_name = args.name or datetime.now().strftime("%Y%m%d_%H%M%S")
        dump_dir = DUMP_ROOT / folder_name
        asyncio.run(dump(dump_dir))

    elif args.action == "restore":
        if args.name:
            dump_dir = DUMP_ROOT / args.name
        else:
            dump_dir = get_latest_dump_dir()
            if dump_dir is None:
                print(f"錯誤：找不到任何備份資料夾: {DUMP_ROOT}")
                sys.exit(1)
            print(f"使用最新備份: {dump_dir.name}\n")
        asyncio.run(restore(dump_dir))


if __name__ == "__main__":
    main()
