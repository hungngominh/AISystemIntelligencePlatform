"""
AI Engine - Analyzer
Gửi metrics đến Claude API để phân tích và trả về báo cáo
"""
import json
import logging
from typing import Optional

import anthropic

from src.config import settings

logger = logging.getLogger(__name__)


def _build_client() -> anthropic.Anthropic:
    """
    Khởi tạo Anthropic client linh hoạt:
    - Nếu có ANTHROPIC_BASE_URL → dùng proxy (ví dụ: http://192.168.0.101:8000)
    - Nếu không có → dùng Anthropic trực tiếp với API key
    - Nếu có cả hai → ưu tiên base_url (proxy)
    """
    kwargs = {}

    if settings.anthropic_base_url:
        kwargs["base_url"] = settings.anthropic_base_url
        # Proxy thường không cần key thật, nhưng SDK bắt buộc có giá trị
        kwargs["api_key"] = settings.anthropic_api_key or "proxy-no-key-needed"
        logger.info(f"Dùng Anthropic proxy: {settings.anthropic_base_url}")
    else:
        kwargs["api_key"] = settings.anthropic_api_key
        logger.info("Dùng Anthropic API trực tiếp")

    return anthropic.Anthropic(**kwargs)


client = _build_client()


SYSTEM_PROMPT = """Bạn là một AI chuyên gia hệ thống (SRE/DevOps AI) được giao nhiệm vụ giám sát và phân tích trạng thái server.

Hệ thống đang monitor gồm:
- AIProjectMiddleware (.NET 9 Web API + PostgreSQL)
- multiAIAgents (Python CrewAI, GPT inference)
- Infrastructure: Docker containers trên Linux/Windows

Nguyên tắc phân tích:
1. Luôn đưa ra đánh giá rõ ràng: OK / WARNING / CRITICAL
2. Chỉ nêu vấn đề CÓ THẬT trong data, không phỏng đoán
3. Đề xuất action cụ thể, có thể thực hiện ngay
4. Ngắn gọn, súc tích — người đọc là kỹ sư
5. Nếu không có data (null/empty) thì ghi rõ "không có dữ liệu"

Format output: Markdown với các section: ## Tổng quan, ## Vấn đề phát hiện, ## Đề xuất action"""


def _format_metrics_for_prompt(metrics: dict) -> str:
    """Chuyển metrics dict thành text dễ đọc cho LLM."""
    lines = [f"**Thời điểm thu thập**: {metrics.get('collected_at', 'N/A')}", ""]

    infra = metrics.get("infrastructure", {})
    lines.append("### Infrastructure")
    lines.append(f"- CPU: {_fmt_pct(infra.get('cpu_usage_pct'))}%")
    lines.append(f"- Memory: {_fmt_pct(infra.get('memory_usage_pct'))}%")
    lines.append(f"- Disk: {_fmt_pct(infra.get('disk_usage_pct'))}%")
    lines.append("")

    api = metrics.get("api", {})
    lines.append("### API Performance")
    lines.append(f"- p95 Latency: {_fmt_val(api.get('p95_latency_seconds'))}s")
    lines.append(f"- Error Rate: {_fmt_pct(api.get('error_rate_pct'))}%")
    if api.get("requests_per_second"):
        lines.append(f"- RPS by endpoint: {json.dumps(api['requests_per_second'])}")
    lines.append("")

    queue = metrics.get("queue", {})
    lines.append("### Queue")
    if queue.get("backlog"):
        for k, v in queue["backlog"].items():
            lines.append(f"- {k}: {v:.0f} items")
    else:
        lines.append("- Không có dữ liệu queue")
    lines.append("")

    ai_costs = metrics.get("ai_costs", {})
    lines.append("### AI Costs & Performance")
    lines.append(f"- GPT p95 inference: {_fmt_val(ai_costs.get('gpt_p95_inference_seconds'))}s")
    if ai_costs.get("cost_last_hour_usd"):
        for k, v in ai_costs["cost_last_hour_usd"].items():
            lines.append(f"- Cost (1h): {k} = ${v:.4f}")
    if ai_costs.get("tokens_last_hour"):
        for k, v in ai_costs["tokens_last_hour"].items():
            lines.append(f"- Tokens (1h): {k} = {v:.0f}")
    lines.append("")

    db = metrics.get("database", {})
    lines.append("### Database")
    if db.get("locks"):
        for k, v in db["locks"].items():
            lines.append(f"- Lock {k}: {v:.0f}")
    else:
        lines.append("- Không có dữ liệu locks")
    lines.append("")

    targets = metrics.get("targets", [])
    lines.append("### Scrape Targets")
    for t in targets:
        status = "✅" if t.get("health") == "up" else "❌"
        lines.append(f"- {status} {t.get('job')} ({t.get('instance')}) — {t.get('lastError') or 'OK'}")
    lines.append("")

    active_alerts = metrics.get("active_alerts", [])
    lines.append(f"### Active Alerts ({len(active_alerts)} alerts)")
    for a in active_alerts:
        labels = a.get("labels", {})
        lines.append(f"- [{labels.get('severity','?').upper()}] {labels.get('alertname','?')}: {a.get('annotations',{}).get('summary','')}")
    lines.append("")

    logs = metrics.get("logs", {})
    errors = logs.get("recent_errors", [])
    lines.append(f"### Recent Errors (15 phút gần đây — {len(errors)} dòng)")
    for err in errors[:10]:  # Giới hạn 10 dòng
        lines.append(f"  > {err[:200]}")
    if len(errors) > 10:
        lines.append(f"  ... và {len(errors) - 10} dòng khác")
    lines.append("")

    containers = metrics.get("containers", {})
    if containers.get("memory_bytes"):
        lines.append("### Container Memory")
        for k, v in list(containers["memory_bytes"].items())[:8]:
            lines.append(f"- {k}: {v/1024/1024:.0f} MB")

    return "\n".join(lines)


def _fmt_pct(val) -> str:
    if val is None:
        return "N/A"
    return f"{val:.1f}"


def _fmt_val(val) -> str:
    if val is None:
        return "N/A"
    return f"{val:.3f}"


def analyze_metrics(metrics: dict, server_name: str = "Server") -> dict:
    """
    Phân tích metrics bằng Claude.
    Trả về: {"status": str, "summary": str, "report": str, "tokens": int}
    """
    metrics_text = _format_metrics_for_prompt(metrics)

    prompt = f"""Phân tích trạng thái server **{server_name}** dựa trên data sau:

{metrics_text}

Hãy:
1. Xác định status tổng thể: OK / WARNING / CRITICAL
2. Liệt kê các vấn đề phát hiện (nếu có)
3. Đề xuất action cụ thể

Bắt đầu response bằng một dòng: STATUS: OK | STATUS: WARNING | STATUS: CRITICAL"""

    try:
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens

        # Parse status từ dòng đầu
        status = "ok"
        lines = content.strip().split("\n")
        first_line = lines[0].upper()
        if "CRITICAL" in first_line:
            status = "critical"
        elif "WARNING" in first_line:
            status = "warning"

        # Summary = dòng đầu tiên có nội dung thực (sau STATUS line)
        summary = next((l for l in lines[1:] if l.strip()), content[:100])

        return {
            "status": status,
            "summary": summary.strip("# ").strip(),
            "report": content,
            "tokens": tokens,
        }
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return {
            "status": "error",
            "summary": f"Không thể phân tích: {e}",
            "report": f"**Lỗi khi gọi Claude API**: {e}",
            "tokens": 0,
        }


def analyze_alert(alert_name: str, alert_labels: dict, alert_annotations: dict, metrics: dict) -> dict:
    """
    Phân tích sâu một alert cụ thể.
    """
    metrics_text = _format_metrics_for_prompt(metrics)

    prompt = f"""Một alert vừa được kích hoạt:

**Alert**: {alert_name}
**Severity**: {alert_labels.get('severity', 'unknown')}
**Labels**: {json.dumps(alert_labels)}
**Summary**: {alert_annotations.get('summary', 'N/A')}
**Description**: {alert_annotations.get('description', 'N/A')}

**Context metrics tại thời điểm alert**:
{metrics_text}

Phân tích:
1. Nguyên nhân khả năng cao nhất
2. Mức độ ảnh hưởng (impact)
3. Các bước xử lý ngay lập tức (runbook)
4. Cách phòng tránh tái phát

Bắt đầu bằng: STATUS: CRITICAL hoặc STATUS: WARNING"""

    try:
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens
        lines = content.strip().split("\n")
        first_line = lines[0].upper()
        status = "warning"
        if "CRITICAL" in first_line:
            status = "critical"

        return {
            "status": status,
            "summary": f"Alert: {alert_name}",
            "report": content,
            "tokens": tokens,
        }
    except Exception as e:
        logger.error(f"Claude API alert analysis error: {e}")
        return {
            "status": "error",
            "summary": f"Alert analysis failed: {e}",
            "report": str(e),
            "tokens": 0,
        }


def chat_with_context(user_message: str, chat_history: list[dict], metrics_snapshot: Optional[dict] = None) -> dict:
    """
    Chat với AI về server. Có context metrics gần nhất.
    """
    system = SYSTEM_PROMPT
    if metrics_snapshot:
        metrics_text = _format_metrics_for_prompt(metrics_snapshot)
        system += f"\n\n---\n**Snapshot metrics gần nhất**:\n{metrics_text}"

    # Build message history
    messages = []
    for msg in chat_history[-10:]:  # Giới hạn 10 messages gần nhất
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        content = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return {"content": content, "tokens": tokens}
    except Exception as e:
        logger.error(f"Claude chat error: {e}")
        return {"content": f"Lỗi: {e}", "tokens": 0}
