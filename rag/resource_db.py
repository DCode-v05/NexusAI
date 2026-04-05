"""SQLite-backed resource store (aiosqlite).

Schema: resources(id, title, url, description, tags, domain, type)
"""
import json
import aiosqlite
from pathlib import Path
from dataclasses import dataclass

DB_PATH = Path(__file__).parent / "data" / "resources.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class Resource:
    id: int
    title: str
    url: str
    description: str
    tags: list[str]
    domain: str
    type: str  # "course" | "govt-scheme" | "job-listing" | "article"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT,
                description TEXT,
                tags TEXT,
                domain TEXT,
                type TEXT
            )
        """)
        await db.commit()


async def insert_resources(records: list[dict]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(
            "INSERT OR REPLACE INTO resources (id, title, url, description, tags, domain, type) VALUES (?,?,?,?,?,?,?)",
            [
                (
                    r["id"],
                    r["title"],
                    r.get("url", ""),
                    r.get("description", ""),
                    json.dumps(r.get("tags", [])),
                    r.get("domain", "general"),
                    r.get("type", "course"),
                )
                for r in records
            ],
        )
        await db.commit()


async def get_by_ids(ids: list[int]) -> list[Resource]:
    if not ids:
        return []
    placeholders = ",".join("?" * len(ids))
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            f"SELECT id, title, url, description, tags, domain, type FROM resources WHERE id IN ({placeholders})",
            ids,
        ) as cursor:
            rows = await cursor.fetchall()

    id_map = {r[0]: r for r in rows}
    result = []
    for rid in ids:
        if rid in id_map:
            r = id_map[rid]
            result.append(Resource(
                id=r[0], title=r[1], url=r[2],
                description=r[3], tags=json.loads(r[4] or "[]"),
                domain=r[5], type=r[6],
            ))
    return result
