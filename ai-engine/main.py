"""
AI Engine - Entry Point
"""
import logging
import sys
from pathlib import Path

import uvicorn

# Thêm parent dir vào path để import src.*
sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings
from src.api import app


def setup_logging():
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("🚀 AI System Intelligence Platform starting...")
    logger.info(f"   Prometheus: {settings.default_prometheus_url}")
    logger.info(f"   Loki:       {settings.default_loki_url}")
    logger.info(f"   Port:       {settings.ai_engine_port}")
    logger.info(f"   Interval:   {settings.analysis_interval_seconds}s")
    logger.info(f"   Model:      {settings.claude_model}")
    logger.info(f"   Auth:       ✅ enabled (user: {settings.auth_username})")
    if settings.anthropic_base_url:
        logger.info(f"   AI Proxy:   {settings.anthropic_base_url}")
    if settings.google_chat_webhook_url:
        logger.info("   GG Chat:    ✅ configured")
    else:
        logger.info("   GG Chat:    ⚠️  not configured")
    logger.info("=" * 50)


if __name__ == "__main__":
    setup_logging()
    uvicorn.run(
        "main:app",
        host=settings.ai_engine_host,
        port=settings.ai_engine_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )
