"""
AI Engine - Analyzer
Gửi metrics đến Claude để phân tích.

Backend tự động chọn:
- Nếu ANTHROPIC_BASE_URL set → dùng httpx trực tiếp với /v1/chat/completions
  (tương thích Claudible proxy tại http://192.168.0.101:8000)
  Auth: ANTHROPIC_AUTH_TOKEN (sk-...) làm Bearer token
- Nếu ANTHROPIC_API_KEY set → dùng anthropic SDK trực tiếp
"""
import json
import logging
import httpx
from typing import Optional

from src.config import settings

logger = logging.getLogger(__name__)

_USE_PROXY = bool(settings.anthropic_base_url)

if _USE_PROXY:
    _PROXY_URL = settings.anthropic_base_url.rstrip("/") + "/v1/chat/completions"
    _PROXY_TOKEN = settings.anthropic_auth_token or ""
    logger.info(f"Analyzer: dùng proxy → {settings.anthropic_base_url}")
else:
    import anthropic as _anthropic_module
    _anthropic_client = _anthropic_module.Anthropic(api_key=settings.anthropic_api_key)
    logger.info("Analyzer: dùng Anthropic API trực tiếp")


# ── Call AI (unified) ─────────────────────────────────────────

def _call_ai(system: str, messages: list[dict], max_tokens: int = 1024) -> tuple[str, int]:
    """
    Gọi AI, trả về (content, tokens_used).
    """
    if _USE_PROXY:
        msgs = [{"role": "system", "content": system}] + messages
        resp = httpx.post(
            _PROXY_URL,
            headers={
                "Content-Type": "application/json",
                "Accept-Encoding": "identity",
                "Authorization": f"Bearer {_PROXY_TOKEN}",
            },
            json={
                "model": settings.claude_model,
                "max_tokens": max_tokens,
                "messages": msgs,
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens = (usage.get("prompt_tokens") or 0) + (usage.get("completion_tokens") or 0)
        return content, tokens
    else:
        response = _anthropic_client.messages.create(
            model=settings.claude_model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        content = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return content, tokens


# ── System prompt ─────────────────────────────────────────────

SYSTEM_PROMPT = """Bạn là một AI chuyên gia hệ thống (SRE/DevOps AI) được giao nhiệm vụ giám sát và phân tích trạng thái server.

Nguyên tắc phân tích:
1. Luôn đưa ra đánh giá rõ ràng: OK / WARNING / CRITICAL
2. Chỉ nêu vấn đề CÓ THẬT trong data, không phỏng đoán
3. Đề xuất action cụ thể, có thể thực hiện ngay
4. Ngắn gọn, súc tích — người đọc là kỹ sư
5. Nếu không có data (null/empty) thì ghi rõ "không có dữ liệu"

Format output: Markdown với các section: ## Tổng quan, ## Vấn đề phát hiện, ## Đề xuất action"""


# ── Helpers ───────────────────────────────────────────────────

def _fmt_pct(val) -> str:
    return "N/A" if val is None else f"{val:.1f}"


def _fmt_val(val) -> str:
    return "N/A" if val is None else f"{val:.3f}"


def _format_metrics_for_prompt(metrics: dict) -> str:
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
        icon = "✅" if t.get("health") == "up" else "❌"
        lines.append(f"- {icon} {t.get('job')} ({t.get('instance')}) — {t.get('lastError') or 'OK'}")
    if not targets:
        lines.append("- Không có dữ liệu scrape targets")
    lines.append("")

    active_alerts = metrics.get("active_alerts", [])
    lines.append(f"### Active Alerts ({len(active_alerts)} alerts)")
    for a in active_alerts:
        lbl = a.get("labels", {})
        lines.append(f"- [{lbl.get('severity','?').upper()}] {lbl.get('alertname','?')}: {a.get('annotations',{}).get('summary','')}")
    lines.append("")

    logs = metrics.get("logs", {})
    errors = logs.get("recent_errors", [])
    lines.append(f"### Recent Errors (15 phút gần đây — {len(errors)} dòng)")
    for err in errors[:10]:
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


# ── Public API ────────────────────────────────────────────────

def analyze_metrics(metrics: dict, server_name: str = "Server") -> dict:
    metrics_text = _format_metrics_for_prompt(metrics)
    prompt = f"""Phân tích trạng thái server **{server_name}** dựa trên data sau:

{metrics_text}

Hãy:
1. Xác định status tổng thể: OK / WARNING / CRITICAL
2. Liệt kê các vấn đề phát hiện (nếu có)
3. Đề xuất action cụ thể

Bắt đầu response bằng một dòng: STATUS: OK | STATUS: WARNING | STATUS: CRITICAL"""

    try:
        content, tokens = _call_ai(SYSTEM_PROMPT, [{"role": "user", "content": prompt}], max_tokens=1024)
        lines = content.strip().split("\n")
        first_line = lines[0].upper()
        status = "critical" if "CRITICAL" in first_line else "warning" if "WARNING" in first_line else "ok"
        summary = next((l for l in lines[1:] if l.strip()), content[:100])
        return {"status": status, "summary": summary.strip("# ").strip(), "report": content, "tokens": tokens}
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return {"status": "error", "summary": f"Không thể phân tích: {e}", "report": f"**Lỗi**: {e}", "tokens": 0}


def analyze_alert(alert_name: str, alert_labels: dict, alert_annotations: dict, metrics: dict) -> dict:
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
        content, tokens = _call_ai(SYSTEM_PROMPT, [{"role": "user", "content": prompt}], max_tokens=1500)
        lines = content.strip().split("\n")
        status = "critical" if "CRITICAL" in lines[0].upper() else "warning"
        return {"status": status, "summary": f"Alert: {alert_name}", "report": content, "tokens": tokens}
    except Exception as e:
        logger.error(f"Claude API alert error: {e}")
        return {"status": "error", "summary": f"Alert analysis failed: {e}", "report": str(e), "tokens": 0}


def chat_with_context(user_message: str, chat_history: list[dict], metrics_snapshot: Optional[dict] = None) -> dict:
    system = SYSTEM_PROMPT
    if metrics_snapshot:
        system += f"\n\n---\n**Snapshot metrics gần nhất**:\n{_format_metrics_for_prompt(metrics_snapshot)}"

    messages = [{"role": m["role"], "content": m["content"]} for m in chat_history[-10:]]
    messages.append({"role": "user", "content": user_message})

    try:
        content, tokens = _call_ai(system, messages, max_tokens=1024)
        return {"content": content, "tokens": tokens}
    except Exception as e:
        logger.error(f"Claude chat error: {e}")
        return {"content": f"Lỗi: {e}", "tokens": 0}
