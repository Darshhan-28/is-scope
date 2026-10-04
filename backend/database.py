"""SQLite access + schema for the prototype standards knowledge base."""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "standards.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS standards (
    standard_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    product_category TEXT NOT NULL,
    scope_summary TEXT NOT NULL,
    keywords TEXT NOT NULL,
    applicability_conditions TEXT NOT NULL,
    exclusions TEXT NOT NULL,
    covers TEXT NOT NULL,
    status TEXT NOT NULL,
    revision_year INTEGER NOT NULL,
    superseded_by TEXT,
    related TEXT NOT NULL,
    normative_references TEXT NOT NULL,
    test_methods TEXT NOT NULL,
    certification_flag INTEGER NOT NULL,
    role TEXT NOT NULL,
    is_synthetic_demo INTEGER NOT NULL
);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def row_to_standard(row: sqlite3.Row) -> dict:
    return {
        "standard_id": row["standard_id"],
        "title": row["title"],
        "product_category": row["product_category"],
        "scope_summary": row["scope_summary"],
        "keywords": row["keywords"].split(",") if row["keywords"] else [],
        "applicability_conditions": json.loads(row["applicability_conditions"] or "[]"),
        "exclusions": json.loads(row["exclusions"] or "[]"),
        "covers": json.loads(row["covers"] or "[]"),
        "status": row["status"],
        "revision_year": row["revision_year"],
        "superseded_by": row["superseded_by"],
        "related": json.loads(row["related"] or "[]"),
        "normative_references": json.loads(row["normative_references"] or "[]"),
        "test_methods": json.loads(row["test_methods"] or "[]"),
        "certification_flag": bool(row["certification_flag"]),
        "role": row["role"],
        "is_synthetic_demo": bool(row["is_synthetic_demo"]),
    }


def fetch_all_standards() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM standards ORDER BY standard_id").fetchall()
    conn.close()
    return [row_to_standard(r) for r in rows]


def fetch_standard(standard_id: str) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM standards WHERE standard_id = ?", (standard_id,)
    ).fetchone()
    conn.close()
    return row_to_standard(row) if row else None


def count_standards() -> int:
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) AS c FROM standards").fetchone()["c"]
    conn.close()
    return n
