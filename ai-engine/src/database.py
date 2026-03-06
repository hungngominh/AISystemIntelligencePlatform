"""
AI Engine - Database
SQLite via sqlite-utils
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import sqlite_utils

from src.config import settings


def get_db() -> sqlite_utils.Database:
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite_utils.Database(settings.db_path)
    _ensure_tables(db)
    return db


def _ensure_tables(db: sqlite_utils.Database):
    # ── servers ──────────────────────────────────────────────
    if "servers" not in db.table_names():
        db["servers"].create(
            {
                "id": int,
                "name": str,           # tên hiển thị, ví dụ "Production VPS"
                "prometheus_url": str, # http://host:9090
                "loki_url": str,       # http://host:3100
                "description": str,    # ghi chú tuỳ ý
                "enabled": int,        # 1 = active, 0 = disabled
                "created_at": str,
            },
            pk="id",
        )
        # Seed server mặc định từ config (có thể là localhost hoặc docker internal)
        db["servers"].insert({
            "name": "Default Server",
            "prometheus_url": settings.default_prometheus_url,
            "loki_url": settings.default_loki_url,
            "description": "Server mặc định (từ cấu hình ban đầu)",
            "enabled": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    # ── analyses ─────────────────────────────────────────────
    if "analyses" not in db.table_names():
        db["analyses"].create(
            {
                "id": int,
                "server_id": int,
                "created_at": str,
                "analysis_type": str,  # "periodic" | "alert" | "chat"
                "status": str,         # "ok" | "warning" | "critical" | "error"
                "summary": str,
                "full_report": str,
                "raw_metrics": str,
                "alert_name": str,
                "tokens_used": int,
            },
            pk="id",
            foreign_keys=[("server_id", "servers", "id")],
        )
        db["analyses"].create_index(["server_id", "created_at"])
        db["analyses"].create_index(["analysis_type"])
    else:
        # Migration: thêm server_id nếu DB cũ chưa có
        cols = {c.name for c in db["analyses"].columns}
        if "server_id" not in cols:
            db["analyses"].add_column("server_id", int, fk="servers", fk_col="id")

    # ── chat_messages ─────────────────────────────────────────
    if "chat_messages" not in db.table_names():
        db["chat_messages"].create(
            {
                "id": int,
                "server_id": int,
                "session_id": str,
                "role": str,
                "content": str,
                "created_at": str,
            },
            pk="id",
        )
        db["chat_messages"].create_index(["session_id"])
    else:
        cols = {c.name for c in db["chat_messages"].columns}
        if "server_id" not in cols:
            db["chat_messages"].add_column("server_id", int)


# ── Server CRUD ───────────────────────────────────────────────

def get_all_servers() -> list[dict]:
    db = get_db()
    return list(db["servers"].rows_where(order_by="id"))


def get_server(server_id: int) -> Optional[dict]:
    db = get_db()
    rows = list(db["servers"].rows_where("id = ?", [server_id]))
    return rows[0] if rows else None


def get_enabled_servers() -> list[dict]:
    db = get_db()
    return list(db["servers"].rows_where("enabled = 1", order_by="id"))


def create_server(name: str, prometheus_url: str, loki_url: str, description: str = "") -> int:
    db = get_db()
    db["servers"].insert({
        "name": name,
        "prometheus_url": prometheus_url.rstrip("/"),
        "loki_url": loki_url.rstrip("/"),
        "description": description,
        "enabled": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return db.execute("SELECT last_insert_rowid()").fetchone()[0]


def update_server(server_id: int, **kwargs) -> bool:
    db = get_db()
    allowed = {"name", "prometheus_url", "loki_url", "description", "enabled"}
    data = {k: v for k, v in kwargs.items() if k in allowed}
    if not data:
        return False
    if "prometheus_url" in data:
        data["prometheus_url"] = data["prometheus_url"].rstrip("/")
    if "loki_url" in data:
        data["loki_url"] = data["loki_url"].rstrip("/")
    db["servers"].update(server_id, data)
    return True


def delete_server(server_id: int):
    db = get_db()
    db["servers"].delete_where("id = ?", [server_id])


# ── Analysis CRUD ─────────────────────────────────────────────

def save_analysis(
    analysis_type: str,
    status: str,
    summary: str,
    full_report: str,
    raw_metrics: dict,
    server_id: int = 1,
    alert_name: Optional[str] = None,
    tokens_used: int = 0,
) -> int:
    db = get_db()
    db["analyses"].insert({
        "server_id": server_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "analysis_type": analysis_type,
        "status": status,
        "summary": summary,
        "full_report": full_report,
        "raw_metrics": json.dumps(raw_metrics, ensure_ascii=False),
        "alert_name": alert_name or "",
        "tokens_used": tokens_used,
    })
    return db.execute("SELECT last_insert_rowid()").fetchone()[0]


def get_analyses(limit: int = 20, analysis_type: Optional[str] = None, server_id: Optional[int] = None) -> list[dict]:
    db = get_db()
    conditions = []
    params = []
    if analysis_type:
        conditions.append("analysis_type = ?")
        params.append(analysis_type)
    if server_id is not None:
        conditions.append("server_id = ?")
        params.append(server_id)
    where = " AND ".join(conditions) if conditions else None
    return list(db["analyses"].rows_where(where, params, order_by="created_at desc", limit=limit))


def get_analysis_by_id(analysis_id: int) -> Optional[dict]:
    db = get_db()
    rows = list(db["analyses"].rows_where("id = ?", [analysis_id]))
    return rows[0] if rows else None


# ── Chat CRUD ─────────────────────────────────────────────────

def save_chat_message(session_id: str, role: str, content: str, server_id: int = 1):
    db = get_db()
    db["chat_messages"].insert({
        "server_id": server_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


def get_chat_history(session_id: str, limit: int = 20) -> list[dict]:
    db = get_db()
    return list(db["chat_messages"].rows_where(
        "session_id = ?", [session_id],
        order_by="created_at",
        limit=limit,
    ))
