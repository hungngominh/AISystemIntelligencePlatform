"""
AI Engine - Scheduler
Chạy phân tích định kỳ cho TẤT CẢ servers đang enabled.
Mỗi server có job riêng, cache metrics riêng.
"""
import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.config import settings
from src.collector import collect_all_metrics
from src.analyzer import analyze_metrics
from src import database as db
from src.notifier import send_notification

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")

# Cache metrics theo server_id: {server_id: metrics_dict}
_metrics_cache: dict[int, dict] = {}


def get_latest_metrics(server_id: int) -> dict:
    return _metrics_cache.get(server_id, {})


def get_all_cached_metrics() -> dict[int, dict]:
    return _metrics_cache


async def run_analysis_for_server(server_id: int):
    """Phân tích một server cụ thể."""
    server = db.get_server(server_id)
    if not server or not server.get("enabled"):
        return

    server_name = server["name"]
    logger.info(f"⏱ Phân tích server [{server_id}] {server_name}...")

    try:
        metrics = await collect_all_metrics(
            prometheus_url=server["prometheus_url"],
            loki_url=server["loki_url"],
        )
        _metrics_cache[server_id] = metrics

        result = analyze_metrics(metrics, server_name=server_name)

        analysis_id = db.save_analysis(
            analysis_type="periodic",
            status=result["status"],
            summary=result["summary"],
            full_report=result["report"],
            raw_metrics=metrics,
            server_id=server_id,
            tokens_used=result["tokens"],
        )

        logger.info(f"✅ [{server_name}] #{analysis_id} — {result['status'].upper()}")

        if result["status"] in ("warning", "critical"):
            await send_notification(
                status=result["status"],
                summary=f"[{server_name}] {result['summary']}",
                report=result["report"],
                analysis_id=analysis_id,
                source="periodic",
            )

    except Exception as e:
        logger.error(f"Analysis failed for server [{server_id}] {server_name}: {e}", exc_info=True)


def _make_job_id(server_id: int) -> str:
    return f"periodic_analysis_server_{server_id}"


def sync_server_jobs():
    """
    Đồng bộ scheduler jobs với danh sách servers trong DB.
    - Server enabled → đảm bảo có job
    - Server disabled / bị xóa → remove job
    """
    enabled_servers = db.get_enabled_servers()
    enabled_ids = {s["id"] for s in enabled_servers}

    # Xóa jobs của servers không còn enabled
    for job in scheduler.get_jobs():
        if job.id.startswith("periodic_analysis_server_"):
            sid = int(job.id.split("_")[-1])
            if sid not in enabled_ids:
                job.remove()
                logger.info(f"Removed scheduler job for server_id={sid}")

    # Thêm jobs cho servers mới
    existing_job_ids = {j.id for j in scheduler.get_jobs()}
    for server in enabled_servers:
        job_id = _make_job_id(server["id"])
        if job_id not in existing_job_ids:
            scheduler.add_job(
                run_analysis_for_server,
                args=[server["id"]],
                trigger=IntervalTrigger(seconds=settings.analysis_interval_seconds),
                id=job_id,
                replace_existing=True,
                next_run_time=datetime.now(timezone.utc),
            )
            logger.info(f"Added scheduler job for server [{server['id']}] {server['name']}")


def start_scheduler():
    # Job định kỳ sync danh sách servers (mỗi 60s)
    scheduler.add_job(
        sync_server_jobs,
        trigger=IntervalTrigger(seconds=60),
        id="sync_server_jobs",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),
    )
    scheduler.start()
    logger.info(f"🕐 Scheduler started — interval={settings.analysis_interval_seconds}s")


def stop_scheduler():
    scheduler.shutdown(wait=False)
