"""
AI Engine - API Server (FastAPI)
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from src.config import settings
from src.auth import COOKIE_NAME, is_authenticated, login_required, make_session_cookie, verify_credentials
from src import database as db
from src.analyzer import analyze_metrics, analyze_alert, chat_with_context
from src.collector import collect_all_metrics, check_server_connectivity
from src.notifier import send_test_notification
from src.scheduler import get_latest_metrics, get_all_cached_metrics, sync_server_jobs

logger = logging.getLogger(__name__)

app = FastAPI(title="AI System Intelligence Platform", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── Models ────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    server_id: int = 1


class ServerCreate(BaseModel):
    name: str
    prometheus_url: str
    loki_url: str
    description: str = ""


class ServerUpdate(BaseModel):
    name: Optional[str] = None
    prometheus_url: Optional[str] = None
    loki_url: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


# ── Auth helpers ──────────────────────────────────────────────

def _require_api_auth(request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")


# ── Health (no auth) ──────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# ── Login / Logout ────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/"):
    if is_authenticated(request):
        return RedirectResponse(url=next, status_code=302)
    from src.ui import render_login
    return render_login(next_url=next)


@app.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...), next: str = Form("/")):
    if verify_credentials(username, password):
        response = RedirectResponse(url=next if next.startswith("/") else "/", status_code=302)
        response.set_cookie(key=COOKIE_NAME, value=make_session_cookie(), httponly=True, samesite="lax", max_age=settings.auth_session_max_age)
        logger.info(f"Login OK: {username} from {request.client.host if request.client else '?'}")
        return response
    logger.warning(f"Login fail: {username} from {request.client.host if request.client else '?'}")
    from src.ui import render_login
    return HTMLResponse(content=render_login(error="Tên đăng nhập hoặc mật khẩu không đúng", next_url=next), status_code=401)


@app.get("/logout")
async def logout():
    r = RedirectResponse(url="/login", status_code=302)
    r.delete_cookie(COOKIE_NAME)
    return r


# ── Web UI pages ──────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, server_id: int = 0):
    if r := login_required(request):
        return r
    from src.ui import render_index
    return render_index(server_id=server_id)


@app.get("/analyses/{analysis_id}", response_class=HTMLResponse)
async def analysis_detail_page(request: Request, analysis_id: int):
    if r := login_required(request):
        return r
    from src.ui import render_analysis_detail
    return render_analysis_detail(analysis_id)


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, server_id: int = 1):
    if r := login_required(request):
        return r
    from src.ui import render_chat
    return render_chat(server_id=server_id)


@app.get("/servers", response_class=HTMLResponse)
async def servers_page(request: Request):
    if r := login_required(request):
        return r
    from src.ui import render_servers
    return render_servers()


# ── API: Servers CRUD ─────────────────────────────────────────

@app.get("/api/servers")
async def list_servers(request: Request):
    _require_api_auth(request)
    servers = db.get_all_servers()
    # Gắn thêm latest status từ cache
    cached = get_all_cached_metrics()
    for s in servers:
        sid = s["id"]
        m = cached.get(sid, {})
        s["last_collected_at"] = m.get("collected_at")
        # Lấy status từ analysis gần nhất
        recent = db.get_analyses(limit=1, server_id=sid)
        s["last_status"] = recent[0]["status"] if recent else None
        s["last_summary"] = recent[0]["summary"] if recent else None
    return {"items": servers}


@app.post("/api/servers", status_code=201)
async def create_server(request: Request, body: ServerCreate):
    _require_api_auth(request)
    server_id = db.create_server(
        name=body.name,
        prometheus_url=body.prometheus_url,
        loki_url=body.loki_url,
        description=body.description,
    )
    # Kích hoạt job ngay
    sync_server_jobs()
    return {"id": server_id, "message": "Server đã được thêm"}


@app.get("/api/servers/{server_id}")
async def get_server(request: Request, server_id: int):
    _require_api_auth(request)
    server = db.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server không tồn tại")
    return server


@app.patch("/api/servers/{server_id}")
async def update_server(request: Request, server_id: int, body: ServerUpdate):
    _require_api_auth(request)
    if not db.get_server(server_id):
        raise HTTPException(status_code=404, detail="Server không tồn tại")
    kwargs = body.model_dump(exclude_none=True)
    if "enabled" in kwargs:
        kwargs["enabled"] = 1 if kwargs["enabled"] else 0
    db.update_server(server_id, **kwargs)
    sync_server_jobs()
    return {"message": "Đã cập nhật"}


@app.delete("/api/servers/{server_id}")
async def delete_server(request: Request, server_id: int):
    _require_api_auth(request)
    if not db.get_server(server_id):
        raise HTTPException(status_code=404, detail="Server không tồn tại")
    db.delete_server(server_id)
    sync_server_jobs()
    return {"message": "Đã xóa"}


@app.get("/api/servers/{server_id}/ping")
async def ping_server(request: Request, server_id: int):
    """Kiểm tra kết nối Prometheus + Loki của server."""
    _require_api_auth(request)
    server = db.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server không tồn tại")
    result = await check_server_connectivity(server["prometheus_url"], server["loki_url"])
    return result


# ── API: Analyses ─────────────────────────────────────────────

@app.get("/api/analyses")
async def list_analyses(request: Request, limit: int = 20, type: Optional[str] = None, server_id: Optional[int] = None):
    _require_api_auth(request)
    return {"items": db.get_analyses(limit=limit, analysis_type=type, server_id=server_id)}


@app.get("/api/analyses/{analysis_id}")
async def get_analysis(request: Request, analysis_id: int):
    _require_api_auth(request)
    row = db.get_analysis_by_id(analysis_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return row


@app.post("/api/analyses/trigger")
async def trigger_analysis(request: Request, background_tasks: BackgroundTasks, server_id: int = 1):
    _require_api_auth(request)
    if not db.get_server(server_id):
        raise HTTPException(status_code=404, detail="Server không tồn tại")

    async def _run():
        from src.scheduler import run_analysis_for_server
        await run_analysis_for_server(server_id)

    background_tasks.add_task(_run)
    return {"message": f"Đang phân tích server_id={server_id}"}


# ── API: Metrics ──────────────────────────────────────────────

@app.get("/api/metrics/snapshot")
async def get_metrics_snapshot(request: Request, server_id: int = 1):
    _require_api_auth(request)
    m = get_latest_metrics(server_id)
    return m or {"message": "Chưa có snapshot"}


@app.post("/api/metrics/collect")
async def collect_metrics_now(request: Request, server_id: int = 1):
    _require_api_auth(request)
    server = db.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server không tồn tại")
    return await collect_all_metrics(server["prometheus_url"], server["loki_url"])


# ── API: Chat ─────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(request: Request, req: ChatRequest):
    _require_api_auth(request)
    session_id = req.session_id or str(uuid.uuid4())
    history = db.get_chat_history(session_id, limit=10)
    metrics = get_latest_metrics(req.server_id)
    result = chat_with_context(
        user_message=req.message,
        chat_history=history,
        metrics_snapshot=metrics if metrics else None,
    )
    db.save_chat_message(session_id, "user", req.message, server_id=req.server_id)
    db.save_chat_message(session_id, "assistant", result["content"], server_id=req.server_id)
    return {"session_id": session_id, "response": result["content"], "tokens_used": result["tokens"]}


# ── API: Notifications ────────────────────────────────────────

@app.post("/api/notifications/test")
async def test_notification(request: Request):
    _require_api_auth(request)
    await send_test_notification()
    return {"message": "Test notification đã được gửi"}


# ── Webhook: AlertManager (no auth — internal Docker network) ──

@app.post("/api/webhooks/alertmanager")
async def alertmanager_webhook(payload: dict, background_tasks: BackgroundTasks):
    alerts = payload.get("alerts", [])
    firing = [a for a in alerts if a.get("status") == "firing"]
    if not firing:
        return {"message": "No firing alerts"}

    async def _analyze():
        # Dùng server đầu tiên enabled (default server)
        servers = db.get_enabled_servers()
        server = servers[0] if servers else None
        if not server:
            return
        metrics = await collect_all_metrics(server["prometheus_url"], server["loki_url"])
        for alert in firing:
            labels = alert.get("labels", {})
            annotations = alert.get("annotations", {})
            alert_name = labels.get("alertname", "Unknown")
            result = analyze_alert(alert_name=alert_name, alert_labels=labels, alert_annotations=annotations, metrics=metrics)
            analysis_id = db.save_analysis(
                analysis_type="alert", status=result["status"],
                summary=result["summary"], full_report=result["report"],
                raw_metrics=metrics, server_id=server["id"],
                alert_name=alert_name, tokens_used=result["tokens"],
            )
            from src.notifier import send_notification
            await send_notification(
                status=result["status"],
                summary=f"[{server['name']}] {result['summary']}",
                report=result["report"], analysis_id=analysis_id,
                source="alert", alert_name=alert_name,
            )

    background_tasks.add_task(_analyze)
    return {"message": f"Đang phân tích {len(firing)} alert(s)"}


# ── Startup / Shutdown ────────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    from src.scheduler import start_scheduler
    start_scheduler()


@app.on_event("shutdown")
async def on_shutdown():
    from src.scheduler import stop_scheduler
    stop_scheduler()
