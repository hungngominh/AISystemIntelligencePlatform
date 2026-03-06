"""
AI Engine - Notifier
Gửi thông báo qua Google Chat webhook (và/hoặc các kênh khác)
"""
import logging
from typing import Optional

import httpx

from src.config import settings

logger = logging.getLogger(__name__)

# Status emoji mapping
STATUS_EMOJI = {
    "ok": "✅",
    "warning": "⚠️",
    "critical": "🚨",
    "error": "❌",
}

STATUS_COLOR = {
    "ok": "#00C851",
    "warning": "#FFBB33",
    "critical": "#FF4444",
    "error": "#888888",
}


async def send_notification(
    status: str,
    summary: str,
    report: str,
    analysis_id: Optional[int] = None,
    source: str = "periodic",
    alert_name: Optional[str] = None,
):
    """
    Gửi thông báo đến tất cả kênh đã cấu hình.
    Hiện hỗ trợ: Google Chat webhook
    """
    tasks = []

    if settings.google_chat_webhook_url:
        tasks.append(
            _send_google_chat(
                status=status,
                summary=summary,
                report=report,
                analysis_id=analysis_id,
                source=source,
                alert_name=alert_name,
            )
        )

    if not tasks:
        logger.info("Không có webhook nào được cấu hình — bỏ qua notify")
        return

    import asyncio
    await asyncio.gather(*tasks, return_exceptions=True)


async def _send_google_chat(
    status: str,
    summary: str,
    report: str,
    analysis_id: Optional[int],
    source: str,
    alert_name: Optional[str],
):
    """
    Gửi Google Chat Card message.
    Tài liệu: https://developers.google.com/chat/api/guides/message-formats/cards
    """
    emoji = STATUS_EMOJI.get(status, "ℹ️")
    color = STATUS_COLOR.get(status, "#888888")

    # Tiêu đề
    if source == "alert" and alert_name:
        title = f"{emoji} Alert: {alert_name}"
    else:
        title = f"{emoji} AI Server Report — {status.upper()}"

    # Cắt report để không vượt quá giới hạn ký tự Google Chat (4096)
    report_preview = report[:1500] + ("..." if len(report) > 1500 else "")

    # Link back về AI Engine UI
    dashboard_url = f"http://localhost:{settings.ai_engine_port}"
    if analysis_id:
        dashboard_url += f"/analyses/{analysis_id}"

    payload = {
        "cardsV2": [
            {
                "cardId": f"ai-engine-{analysis_id or 0}",
                "card": {
                    "header": {
                        "title": title,
                        "subtitle": f"AI System Intelligence Platform",
                        "imageUrl": "https://fonts.gstatic.com/s/i/short-term/release/materialsymbolsoutlined/monitoring/default/48px.svg",
                        "imageType": "CIRCLE",
                    },
                    "sections": [
                        {
                            "header": "📋 Summary",
                            "collapsible": False,
                            "widgets": [
                                {"textParagraph": {"text": f"<b>{summary}</b>"}}
                            ],
                        },
                        {
                            "header": "📊 AI Analysis",
                            "collapsible": True,
                            "widgets": [
                                {"textParagraph": {"text": report_preview.replace("\n", "<br>")}}
                            ],
                        },
                        {
                            "widgets": [
                                {
                                    "buttonList": {
                                        "buttons": [
                                            {
                                                "text": "Xem chi tiết",
                                                "onClick": {
                                                    "openLink": {"url": dashboard_url}
                                                },
                                            }
                                        ]
                                    }
                                }
                            ]
                        },
                    ],
                },
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                settings.google_chat_webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code == 200:
                logger.info(f"✅ Google Chat notification sent (status={status})")
            else:
                logger.warning(f"Google Chat webhook returned {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.error(f"Google Chat send failed: {e}")


async def send_test_notification():
    """Gửi thông báo test để kiểm tra webhook."""
    await send_notification(
        status="ok",
        summary="Test notification từ AI Engine",
        report="## Test\nĐây là tin nhắn test từ AI System Intelligence Platform.\n\nNếu bạn thấy tin nhắn này, webhook đã được cấu hình đúng! ✅",
        analysis_id=0,
        source="test",
    )
