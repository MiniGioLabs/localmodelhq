"""SQLite database with aiosqlite."""

import aiosqlite
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
_db_path: str | None = None

def _get_db_path() -> str:
    global _db_path
    if _db_path is None:
        _db_path = str(Path(__file__).parent.parent.parent / "localmodelhq.db")
    return _db_path

async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(_get_db_path())
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    return db

async def init_db():
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS benchmark_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_tag TEXT NOT NULL,
                model_name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'benchmark',
                prompt TEXT NOT NULL,
                response TEXT,
                duration_ms REAL,
                tokens_per_sec REAL,
                total_tokens INTEGER,
                first_token_ms REAL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS model_installs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_tag TEXT NOT NULL,
                model_name TEXT NOT NULL,
                installed_at TEXT DEFAULT (datetime('now'))
            );
        """)
        await db.commit()
        logger.info("Database initialized")
    finally:
        await db.close()
