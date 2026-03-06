"""
AI Engine - Authentication
Cookie-based session login đơn giản dùng itsdangerous để sign cookie.
- Tất cả web routes (/  /chat  /analyses/*) đều yêu cầu login
- API internal (/api/webhooks/alertmanager, /health) KHÔNG cần auth (gọi từ Docker network)
- Session cookie tên: "ai_session", httponly, samesite=lax
"""
import hashlib
import hmac
from datetime import datetime, timezone
from functools import wraps
from typing import Optional

from fastapi import Request
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner

from src.config import settings

# Signer dùng secret key từ config
_signer = TimestampSigner(settings.auth_secret_key)

COOKIE_NAME = "ai_session"
COOKIE_VALUE = "authenticated"   # giá trị cố định, bảo mật nhờ chữ ký


def _hash_password(password: str) -> str:
    """SHA-256 hash để so sánh tránh timing attack."""
    return hashlib.sha256(password.encode()).hexdigest()


_PASSWORD_HASH = _hash_password(settings.auth_password)


def verify_credentials(username: str, password: str) -> bool:
    """Kiểm tra username + password."""
    username_ok = hmac.compare_digest(username, settings.auth_username)
    password_ok = hmac.compare_digest(_hash_password(password), _PASSWORD_HASH)
    return username_ok and password_ok


def make_session_cookie() -> str:
    """Tạo signed cookie value."""
    return _signer.sign(COOKIE_VALUE).decode()


def verify_session_cookie(cookie_value: Optional[str]) -> bool:
    """Kiểm tra cookie hợp lệ và chưa hết hạn."""
    if not cookie_value:
        return False
    try:
        _signer.unsign(cookie_value, max_age=settings.auth_session_max_age)
        return True
    except (BadSignature, SignatureExpired):
        return False


def is_authenticated(request: Request) -> bool:
    """Kiểm tra request có cookie hợp lệ không."""
    cookie = request.cookies.get(COOKIE_NAME)
    return verify_session_cookie(cookie)


def login_required(request: Request) -> Optional[RedirectResponse]:
    """
    Gọi ở đầu mỗi web route.
    Nếu chưa login → trả về RedirectResponse đến /login
    Nếu đã login → trả về None (tiếp tục bình thường)
    """
    if not is_authenticated(request):
        return RedirectResponse(url=f"/login?next={request.url.path}", status_code=302)
    return None
