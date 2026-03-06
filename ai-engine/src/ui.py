"""
AI Engine - Web UI (Multi-server)
Tailwind CDN + Alpine.js CDN — không cần build step
"""
import json
import uuid
from typing import Optional
from src import database as db
from src.config import settings


# ─────────────────────────────────────────────────────────────
# Base layout
# ─────────────────────────────────────────────────────────────

def _base_layout(title: str, content: str, active_nav: str = "") -> str:
    nav_items = [
        ("Dashboard", "/", "dashboard"),
        ("Servers", "/servers", "servers"),
        ("Chat", "/chat", "chat"),
    ]
    nav_html = ""
    for label, href, key in nav_items:
        cls = "bg-indigo-700 text-white" if active_nav == key else "text-gray-300 hover:bg-gray-700 hover:text-white"
        nav_html += f'<a href="{href}" class="px-3 py-2 rounded-md text-sm font-medium {cls}">{label}</a>'

    return f"""<!DOCTYPE html>
<html lang="vi" class="h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — AI Monitor</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        [x-cloak]{{display:none!important}}
        .prose h2{{font-size:1.2rem;font-weight:700;margin-top:1.25rem;margin-bottom:.4rem;color:#e2e8f0}}
        .prose h3{{font-size:1rem;font-weight:600;margin-top:1rem;margin-bottom:.25rem;color:#cbd5e0}}
        .prose ul{{list-style:disc;padding-left:1.5rem;color:#a0aec0}}
        .prose li{{margin:.15rem 0}}
        .prose p{{color:#a0aec0;margin:.4rem 0}}
        .prose code{{background:#2d3748;padding:.1rem .3rem;border-radius:.25rem;font-size:.85em;color:#68d391}}
        .prose strong{{color:#e2e8f0}}
        .prose blockquote{{border-left:3px solid #4a5568;padding-left:1rem;color:#718096}}
        .s-ok{{background-color:#276749;color:#9ae6b4}}
        .s-warning{{background-color:#744210;color:#fbd38d}}
        .s-critical{{background-color:#742a2a;color:#feb2b2}}
        .s-error{{background-color:#374151;color:#9ca3af}}
        ::-webkit-scrollbar{{width:6px}}
        ::-webkit-scrollbar-track{{background:#1a202c}}
        ::-webkit-scrollbar-thumb{{background:#4a5568;border-radius:3px}}
    </style>
</head>
<body class="h-full bg-gray-900 text-gray-100">
<nav class="bg-gray-800 border-b border-gray-700">
    <div class="max-w-7xl mx-auto px-4">
        <div class="flex items-center justify-between h-14">
            <div class="flex items-center space-x-4">
                <span class="text-indigo-400 font-bold">🤖 AI Monitor</span>
                <div class="flex space-x-1">{nav_html}</div>
            </div>
            <div class="flex items-center space-x-2">
                <button onclick="triggerAnalysis()" id="trigger-btn"
                    class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-md transition">
                    ▶ Phân tích ngay
                </button>
                <a href="/logout" class="px-3 py-1.5 bg-gray-700 hover:bg-red-900 text-gray-400 hover:text-red-300 text-sm rounded-md transition" title="Đăng xuất">⏻</a>
            </div>
        </div>
    </div>
</nav>
<main class="max-w-7xl mx-auto px-4 py-6">{content}</main>
<script>
    const _currentServerId = parseInt(new URLSearchParams(location.search).get('server_id') || '1');

    async function triggerAnalysis() {{
        const btn = document.getElementById('trigger-btn');
        btn.disabled = true; btn.textContent = '⏳ Đang phân tích...';
        try {{
            await fetch('/api/analyses/trigger?server_id=' + _currentServerId, {{method:'POST'}});
            btn.textContent = '✅ Xong! Tải lại sau 4s...';
            setTimeout(() => location.reload(), 4000);
        }} catch(e) {{
            btn.textContent = '❌ Lỗi'; btn.disabled = false;
            setTimeout(() => {{ btn.textContent='▶ Phân tích ngay'; btn.disabled=false; }}, 2000);
        }}
    }}

    // Auto refresh 30s
    setTimeout(() => location.reload(), 30000);
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────────────────────

def render_login(error: str = "", next_url: str = "/") -> str:
    err_html = (
        f'<div class="bg-red-900/50 border border-red-600 text-red-300 text-sm px-4 py-2.5 rounded-lg mb-4">❌ {error}</div>'
        if error else ""
    )
    return f"""<!DOCTYPE html>
<html lang="vi" class="h-full">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Đăng nhập — AI Monitor</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="h-full bg-gray-900 text-gray-100 flex items-center justify-center min-h-screen">
    <div class="w-full max-w-sm">
        <div class="text-center mb-8">
            <div class="text-5xl mb-3">🤖</div>
            <h1 class="text-2xl font-bold text-white">AI Monitor</h1>
            <p class="text-gray-500 text-sm mt-1">AI System Intelligence Platform</p>
        </div>
        <div class="bg-gray-800 border border-gray-700 rounded-xl px-8 py-8 shadow-2xl">
            <h2 class="text-lg font-semibold text-gray-200 mb-6">Đăng nhập</h2>
            {err_html}
            <form method="POST" action="/login">
                <input type="hidden" name="next" value="{next_url}">
                <div class="mb-4">
                    <label class="block text-sm text-gray-400 mb-1.5">Tên đăng nhập</label>
                    <input name="username" type="text" autofocus autocomplete="username"
                        class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3.5 py-2.5 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm"
                        placeholder="admin">
                </div>
                <div class="mb-6">
                    <label class="block text-sm text-gray-400 mb-1.5">Mật khẩu</label>
                    <input name="password" type="password" autocomplete="current-password"
                        class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3.5 py-2.5 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm"
                        placeholder="••••••••">
                </div>
                <button type="submit"
                    class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2.5 rounded-lg transition text-sm">
                    Đăng nhập
                </button>
            </form>
        </div>
        <p class="text-center text-gray-600 text-xs mt-6">AI System Intelligence Platform v2.0</p>
    </div>
</body></html>"""


# ─────────────────────────────────────────────────────────────
# Servers management page
# ─────────────────────────────────────────────────────────────

def render_servers() -> str:
    servers = db.get_all_servers()

    rows = ""
    for s in servers:
        sid = s["id"]
        enabled_badge = (
            '<span class="px-2 py-0.5 rounded text-xs bg-green-900 text-green-300">✅ Active</span>'
            if s.get("enabled") else
            '<span class="px-2 py-0.5 rounded text-xs bg-gray-700 text-gray-400">⏸ Disabled</span>'
        )
        rows += f"""
        <tr class="border-b border-gray-700 hover:bg-gray-800/40">
            <td class="py-3 px-3 text-gray-400 text-sm">{sid}</td>
            <td class="py-3 px-3">
                <div class="font-medium text-gray-200">{s['name']}</div>
                <div class="text-gray-500 text-xs">{s.get('description','')}</div>
            </td>
            <td class="py-3 px-3 text-gray-400 text-xs font-mono">{s['prometheus_url']}</td>
            <td class="py-3 px-3 text-gray-400 text-xs font-mono">{s['loki_url']}</td>
            <td class="py-3 px-3">{enabled_badge}</td>
            <td class="py-3 px-3">
                <div class="flex items-center space-x-2">
                    <button onclick="pingServer({sid})" id="ping-{sid}"
                        class="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 text-xs rounded transition">
                        🔍 Ping
                    </button>
                    <a href="/?server_id={sid}"
                        class="px-2 py-1 bg-indigo-700 hover:bg-indigo-600 text-white text-xs rounded transition">
                        📊 Xem
                    </a>
                    <button onclick="editServer({sid}, {json.dumps(s['name'])}, {json.dumps(s['prometheus_url'])}, {json.dumps(s['loki_url'])}, {json.dumps(s.get('description',''))}, {1 if s.get('enabled') else 0})"
                        class="px-2 py-1 bg-gray-700 hover:bg-yellow-800 text-gray-300 hover:text-yellow-300 text-xs rounded transition">
                        ✏️ Sửa
                    </button>
                    <button onclick="deleteServer({sid}, {json.dumps(s['name'])})"
                        class="px-2 py-1 bg-gray-700 hover:bg-red-900 text-gray-300 hover:text-red-300 text-xs rounded transition">
                        🗑
                    </button>
                </div>
                <div id="ping-result-{sid}" class="text-xs mt-1"></div>
            </td>
        </tr>"""

    content = f"""
    <div class="flex items-center justify-between mb-6">
        <div>
            <h1 class="text-xl font-bold text-gray-100">🖥️ Quản lý Servers</h1>
            <p class="text-gray-500 text-sm mt-0.5">Thêm, sửa, xóa các server cần monitor</p>
        </div>
        <button onclick="openAddModal()"
            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg font-medium transition">
            + Thêm server
        </button>
    </div>

    <!-- Table -->
    <div class="bg-gray-800 rounded-lg overflow-hidden">
        <div class="overflow-x-auto">
            <table class="w-full text-left">
                <thead class="bg-gray-900/60">
                    <tr>
                        <th class="py-2.5 px-3 text-gray-500 text-xs uppercase">#</th>
                        <th class="py-2.5 px-3 text-gray-500 text-xs uppercase">Tên</th>
                        <th class="py-2.5 px-3 text-gray-500 text-xs uppercase">Prometheus URL</th>
                        <th class="py-2.5 px-3 text-gray-500 text-xs uppercase">Loki URL</th>
                        <th class="py-2.5 px-3 text-gray-500 text-xs uppercase">Trạng thái</th>
                        <th class="py-2.5 px-3 text-gray-500 text-xs uppercase">Thao tác</th>
                    </tr>
                </thead>
                <tbody>
                    {rows if rows else '<tr><td colspan="6" class="py-10 text-center text-gray-500">Chưa có server nào. Nhấn "+ Thêm server" để bắt đầu.</td></tr>'}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Add/Edit Modal -->
    <div id="server-modal" class="hidden fixed inset-0 bg-black/60 flex items-center justify-center z-50">
        <div class="bg-gray-800 border border-gray-700 rounded-xl w-full max-w-lg mx-4 p-6 shadow-2xl">
            <h2 id="modal-title" class="text-lg font-semibold text-gray-200 mb-5">Thêm server</h2>
            <form id="server-form" onsubmit="submitServer(event)">
                <input type="hidden" id="modal-server-id" value="">

                <div class="mb-4">
                    <label class="block text-sm text-gray-400 mb-1.5">Tên hiển thị <span class="text-red-400">*</span></label>
                    <input id="f-name" type="text" required placeholder="Production VPS"
                        class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3.5 py-2.5 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm">
                </div>

                <div class="mb-4">
                    <label class="block text-sm text-gray-400 mb-1.5">Prometheus URL <span class="text-red-400">*</span></label>
                    <input id="f-prom" type="url" required placeholder="http://192.168.1.10:9090"
                        class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3.5 py-2.5 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm font-mono">
                    <p class="text-gray-600 text-xs mt-1">Prometheus phải accessible từ AI Engine</p>
                </div>

                <div class="mb-4">
                    <label class="block text-sm text-gray-400 mb-1.5">Loki URL <span class="text-red-400">*</span></label>
                    <input id="f-loki" type="url" required placeholder="http://192.168.1.10:3100"
                        class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3.5 py-2.5 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm font-mono">
                </div>

                <div class="mb-4">
                    <label class="block text-sm text-gray-400 mb-1.5">Ghi chú</label>
                    <input id="f-desc" type="text" placeholder="Mô tả về server này"
                        class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3.5 py-2.5 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm">
                </div>

                <div id="f-enabled-row" class="mb-5 hidden">
                    <label class="flex items-center space-x-2 cursor-pointer">
                        <input id="f-enabled" type="checkbox" checked class="w-4 h-4 accent-indigo-500">
                        <span class="text-sm text-gray-300">Kích hoạt monitoring</span>
                    </label>
                </div>

                <div id="modal-error" class="hidden bg-red-900/50 border border-red-600 text-red-300 text-sm px-3 py-2 rounded mb-4"></div>

                <div class="flex justify-end space-x-3">
                    <button type="button" onclick="closeModal()"
                        class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm rounded-lg transition">
                        Hủy
                    </button>
                    <button type="submit" id="modal-submit"
                        class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg font-medium transition">
                        Lưu
                    </button>
                </div>
            </form>
        </div>
    </div>

    <script>
        function openAddModal() {{
            document.getElementById('modal-title').textContent = 'Thêm server mới';
            document.getElementById('modal-server-id').value = '';
            document.getElementById('f-name').value = '';
            document.getElementById('f-prom').value = '';
            document.getElementById('f-loki').value = '';
            document.getElementById('f-desc').value = '';
            document.getElementById('f-enabled-row').classList.add('hidden');
            document.getElementById('modal-error').classList.add('hidden');
            document.getElementById('server-modal').classList.remove('hidden');
            document.getElementById('f-name').focus();
        }}

        function editServer(id, name, prom, loki, desc, enabled) {{
            document.getElementById('modal-title').textContent = 'Chỉnh sửa server';
            document.getElementById('modal-server-id').value = id;
            document.getElementById('f-name').value = name;
            document.getElementById('f-prom').value = prom;
            document.getElementById('f-loki').value = loki;
            document.getElementById('f-desc').value = desc;
            document.getElementById('f-enabled').checked = enabled === 1;
            document.getElementById('f-enabled-row').classList.remove('hidden');
            document.getElementById('modal-error').classList.add('hidden');
            document.getElementById('server-modal').classList.remove('hidden');
        }}

        function closeModal() {{
            document.getElementById('server-modal').classList.add('hidden');
        }}

        async function submitServer(e) {{
            e.preventDefault();
            const serverId = document.getElementById('modal-server-id').value;
            const body = {{
                name: document.getElementById('f-name').value,
                prometheus_url: document.getElementById('f-prom').value,
                loki_url: document.getElementById('f-loki').value,
                description: document.getElementById('f-desc').value,
            }};
            if (serverId) {{
                body.enabled = document.getElementById('f-enabled').checked;
            }}
            const btn = document.getElementById('modal-submit');
            btn.disabled = true; btn.textContent = 'Đang lưu...';
            try {{
                const method = serverId ? 'PATCH' : 'POST';
                const url = serverId ? '/api/servers/' + serverId : '/api/servers';
                const r = await fetch(url, {{
                    method, headers: {{'Content-Type':'application/json'}},
                    body: JSON.stringify(body),
                }});
                if (!r.ok) {{
                    const d = await r.json();
                    throw new Error(d.detail || 'Lỗi server');
                }}
                location.reload();
            }} catch(err) {{
                const el = document.getElementById('modal-error');
                el.textContent = '❌ ' + err.message;
                el.classList.remove('hidden');
                btn.disabled = false; btn.textContent = 'Lưu';
            }}
        }}

        async function deleteServer(id, name) {{
            if (!confirm('Xóa server "' + name + '"?\\nLịch sử phân tích sẽ không bị xóa.')) return;
            await fetch('/api/servers/' + id, {{method:'DELETE'}});
            location.reload();
        }}

        async function pingServer(id) {{
            const btn = document.getElementById('ping-' + id);
            const result = document.getElementById('ping-result-' + id);
            btn.disabled = true; btn.textContent = '⏳...';
            try {{
                const r = await fetch('/api/servers/' + id + '/ping');
                const d = await r.json();
                const pOk = d.prometheus ? '✅' : '❌';
                const lOk = d.loki ? '✅' : '❌';
                result.innerHTML = pOk + ' Prometheus &nbsp; ' + lOk + ' Loki';
                result.className = 'text-xs mt-1 ' + ((d.prometheus && d.loki) ? 'text-green-400' : 'text-red-400');
            }} catch(e) {{
                result.textContent = '❌ Lỗi kết nối';
                result.className = 'text-xs mt-1 text-red-400';
            }} finally {{
                btn.disabled = false; btn.textContent = '🔍 Ping';
            }}
        }}

        // Đóng modal khi click ngoài
        document.getElementById('server-modal').addEventListener('click', function(e) {{
            if (e.target === this) closeModal();
        }});
    </script>
    """

    return _base_layout("Quản lý Servers", content, active_nav="servers")


# ─────────────────────────────────────────────────────────────
# Dashboard (multi-server)
# ─────────────────────────────────────────────────────────────

def render_index(server_id: int = 0) -> str:
    servers = db.get_all_servers()
    if not servers:
        content = """
        <div class="text-center py-24">
            <div class="text-6xl mb-4">🖥️</div>
            <h2 class="text-xl font-semibold text-gray-300 mb-2">Chưa có server nào</h2>
            <p class="text-gray-500 mb-6">Thêm server để bắt đầu monitoring</p>
            <a href="/servers" class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium text-sm transition">
                + Thêm server
            </a>
        </div>"""
        return _base_layout("Dashboard", content, "dashboard")

    # Chọn server hiện tại
    server_ids = [s["id"] for s in servers]
    if server_id not in server_ids:
        server_id = servers[0]["id"]

    current_server = next(s for s in servers if s["id"] == server_id)

    # Server selector tabs
    tabs = ""
    for s in servers:
        recent = db.get_analyses(limit=1, server_id=s["id"])
        st = recent[0]["status"] if recent else None
        dot = {"ok": "🟢", "warning": "🟡", "critical": "🔴"}.get(st, "⚫")
        active_cls = "bg-indigo-700 text-white" if s["id"] == server_id else "bg-gray-800 text-gray-400 hover:bg-gray-700"
        tabs += f'<a href="/?server_id={s["id"]}" class="px-3 py-1.5 rounded-lg text-sm font-medium {active_cls} transition">{dot} {s["name"]}</a>'

    # Analyses for current server
    analyses = db.get_analyses(limit=30, server_id=server_id)
    total = len(analyses)
    oks = sum(1 for a in analyses if a.get("status") == "ok")
    warns = sum(1 for a in analyses if a.get("status") == "warning")
    crits = sum(1 for a in analyses if a.get("status") == "critical")

    latest = analyses[0] if analyses else None
    latest_status = latest.get("status", "error") if latest else "error"
    latest_summary = latest.get("summary", "Chưa có phân tích") if latest else "Chưa có phân tích"
    latest_time = str(latest.get("created_at", ""))[:19].replace("T", " ") if latest else "—"

    hero_border = {
        "ok": "border-green-700 bg-green-950/40",
        "warning": "border-yellow-600 bg-yellow-950/40",
        "critical": "border-red-600 bg-red-950/40",
        "error": "border-gray-700 bg-gray-800",
    }.get(latest_status, "border-gray-700 bg-gray-800")

    hero_label = {
        "ok": "✅ HỆ THỐNG BÌNH THƯỜNG",
        "warning": "⚠️ CẦN CHÚ Ý",
        "critical": "🚨 CÓ SỰ CỐ NGHIÊM TRỌNG",
        "error": "⚫ CHƯA CÓ DỮ LIỆU",
    }.get(latest_status, latest_status.upper())

    rows = ""
    for a in analyses:
        s = a.get("status", "error")
        atype = {"periodic": "🕐 Định kỳ", "alert": "🚨 Alert", "chat": "💬 Chat"}.get(a.get("analysis_type", ""), "")
        badge_label = {"ok": "✅ OK", "warning": "⚠️ WARN", "critical": "🚨 CRIT"}.get(s, s.upper())
        rows += f"""<tr class="border-b border-gray-700 hover:bg-gray-800/50 cursor-pointer" onclick="location.href='/analyses/{a.get('id')}'">
            <td class="py-2 px-3 text-gray-500 text-sm">{a.get('id')}</td>
            <td class="py-2 px-3"><span class="px-2 py-0.5 rounded text-xs font-semibold s-{s}">{badge_label}</span></td>
            <td class="py-2 px-3 text-gray-300 text-sm max-w-md truncate">{str(a.get('summary',''))[:80]}</td>
            <td class="py-2 px-3 text-gray-500 text-sm">{atype}</td>
            <td class="py-2 px-3 text-gray-500 text-sm">{str(a.get('created_at',''))[:19].replace('T',' ')}</td>
            <td class="py-2 px-3 text-gray-600 text-sm">{a.get('tokens_used',0):,}</td>
        </tr>"""

    content = f"""
    <!-- Server tabs -->
    <div class="flex flex-wrap gap-2 mb-5">
        {tabs}
        <a href="/servers" class="px-3 py-1.5 rounded-lg text-sm bg-gray-700 text-gray-400 hover:bg-gray-600 transition">⚙️ Quản lý</a>
    </div>

    <!-- Hero -->
    <div class="border rounded-xl p-5 mb-5 {hero_border}">
        <div class="flex items-start justify-between">
            <div>
                <div class="text-xs text-gray-500 uppercase tracking-wide mb-1">{current_server['name']}</div>
                <div class="text-xl font-bold s-{latest_status} inline-block px-3 py-1 rounded mb-2">{hero_label}</div>
                <div class="text-gray-300">{latest_summary}</div>
                <div class="text-gray-600 text-sm mt-1">{latest_time} UTC</div>
            </div>
            <a href="/chat?server_id={server_id}" class="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition">
                💬 Hỏi AI
            </a>
        </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-4 gap-3 mb-5">
        <div class="bg-gray-800 rounded-lg p-3 text-center">
            <div class="text-xl font-bold text-gray-100">{total}</div>
            <div class="text-gray-500 text-xs">Tổng</div>
        </div>
        <div class="bg-gray-800 rounded-lg p-3 text-center">
            <div class="text-xl font-bold text-green-400">{oks}</div>
            <div class="text-gray-500 text-xs">OK</div>
        </div>
        <div class="bg-gray-800 rounded-lg p-3 text-center">
            <div class="text-xl font-bold text-yellow-400">{warns}</div>
            <div class="text-gray-500 text-xs">Warning</div>
        </div>
        <div class="bg-gray-800 rounded-lg p-3 text-center">
            <div class="text-xl font-bold text-red-400">{crits}</div>
            <div class="text-gray-500 text-xs">Critical</div>
        </div>
    </div>

    <!-- History table -->
    <div class="bg-gray-800 rounded-lg overflow-hidden">
        <div class="flex items-center justify-between px-4 py-3 border-b border-gray-700">
            <h2 class="font-semibold text-gray-200 text-sm">Lịch sử phân tích — {current_server['name']}</h2>
            <span class="text-gray-600 text-xs">Auto refresh 30s</span>
        </div>
        <div class="overflow-x-auto">
            <table class="w-full text-left">
                <thead class="bg-gray-900/50">
                    <tr>
                        <th class="py-2 px-3 text-gray-500 text-xs uppercase">#</th>
                        <th class="py-2 px-3 text-gray-500 text-xs uppercase">Status</th>
                        <th class="py-2 px-3 text-gray-500 text-xs uppercase">Summary</th>
                        <th class="py-2 px-3 text-gray-500 text-xs uppercase">Loại</th>
                        <th class="py-2 px-3 text-gray-500 text-xs uppercase">Thời gian</th>
                        <th class="py-2 px-3 text-gray-500 text-xs uppercase">Tokens</th>
                    </tr>
                </thead>
                <tbody>
                    {rows if rows else '<tr><td colspan="6" class="py-10 text-center text-gray-500">Chưa có phân tích. Nhấn "▶ Phân tích ngay".</td></tr>'}
                </tbody>
            </table>
        </div>
    </div>"""

    return _base_layout(f"Dashboard — {current_server['name']}", content, "dashboard")


# ─────────────────────────────────────────────────────────────
# Analysis detail
# ─────────────────────────────────────────────────────────────

def render_analysis_detail(analysis_id: int) -> str:
    row = db.get_analysis_by_id(analysis_id)
    if not row:
        return _base_layout("Not Found", f"<div class='text-center py-20 text-gray-500'>Không tìm thấy phân tích #{analysis_id}</div>")

    status = row.get("status", "error")
    server = db.get_server(row.get("server_id", 1)) or {}
    server_name = server.get("name", "Unknown")
    report_md = row.get("full_report", "")
    try:
        metrics_pretty = json.dumps(json.loads(row.get("raw_metrics", "{}")), indent=2, ensure_ascii=False)
    except Exception:
        metrics_pretty = row.get("raw_metrics", "")

    badge_label = {"ok": "✅ OK", "warning": "⚠️ WARNING", "critical": "🚨 CRITICAL"}.get(status, status.upper())
    report_json = json.dumps(report_md)

    content = f"""
    <div class="mb-4 flex items-center justify-between">
        <div class="flex items-center space-x-2 text-sm">
            <a href="/?server_id={row.get('server_id',1)}" class="text-gray-500 hover:text-gray-300">← Dashboard</a>
            <span class="text-gray-700">/</span>
            <span class="text-gray-400">Phân tích #{analysis_id}</span>
            <span class="text-gray-600">— {server_name}</span>
        </div>
        <span class="px-3 py-1 rounded font-semibold text-sm s-{status}">{badge_label}</span>
    </div>

    <div class="grid grid-cols-4 gap-3 mb-4 text-sm">
        <div class="bg-gray-800 rounded p-3"><div class="text-gray-500 text-xs">Server</div><div class="text-gray-200 font-medium">{server_name}</div></div>
        <div class="bg-gray-800 rounded p-3"><div class="text-gray-500 text-xs">Loại</div><div class="text-gray-200 font-medium">{row.get('analysis_type','')}</div></div>
        <div class="bg-gray-800 rounded p-3"><div class="text-gray-500 text-xs">Thời gian</div><div class="text-gray-200 font-medium">{str(row.get('created_at',''))[:19].replace('T',' ')} UTC</div></div>
        <div class="bg-gray-800 rounded p-3"><div class="text-gray-500 text-xs">Tokens</div><div class="text-gray-200 font-medium">{row.get('tokens_used',0):,}</div></div>
    </div>

    <div x-data="{{ tab: 'report' }}" class="bg-gray-800 rounded-lg overflow-hidden">
        <div class="flex border-b border-gray-700">
            <button @click="tab='report'" :class="tab==='report'?'border-b-2 border-indigo-500 text-indigo-400':'text-gray-500'"
                class="px-4 py-3 text-sm font-medium">📋 Báo cáo AI</button>
            <button @click="tab='metrics'" :class="tab==='metrics'?'border-b-2 border-indigo-500 text-indigo-400':'text-gray-500'"
                class="px-4 py-3 text-sm font-medium">📊 Raw Metrics</button>
        </div>
        <div x-show="tab==='report'" class="p-5">
            <div id="report-content" class="prose"></div>
        </div>
        <div x-show="tab==='metrics'" class="p-5">
            <pre class="text-xs text-gray-400 overflow-auto max-h-96 bg-gray-900 rounded p-4">{metrics_pretty[:10000]}</pre>
        </div>
    </div>

    <script>
        document.getElementById('report-content').innerHTML = marked.parse({report_json});
    </script>"""

    return _base_layout(f"Phân tích #{analysis_id}", content)


# ─────────────────────────────────────────────────────────────
# Chat
# ─────────────────────────────────────────────────────────────

def render_chat(server_id: int = 1) -> str:
    servers = db.get_all_servers()
    server = db.get_server(server_id) or (servers[0] if servers else {"id": 1, "name": "Server"})
    session_id = uuid.uuid4().hex

    server_options = "".join(
        f'<option value="{s["id"]}" {"selected" if s["id"] == server_id else ""}>{s["name"]}</option>'
        for s in servers
    )

    content = f"""
    <div x-data="chatApp()" x-init="init()" class="flex flex-col" style="height: calc(100vh - 7rem)">
        <div class="flex items-center justify-between mb-3">
            <div class="flex items-center space-x-3">
                <h1 class="text-base font-semibold text-gray-200">💬 Chat với AI Monitor</h1>
                <select id="server-select" onchange="location.href='/chat?server_id='+this.value"
                    class="bg-gray-700 border border-gray-600 text-gray-300 text-sm rounded px-2 py-1 focus:outline-none focus:border-indigo-500">
                    {server_options}
                </select>
            </div>
            <button @click="clearChat()" class="text-gray-500 hover:text-gray-300 text-xs">🗑 Xóa chat</button>
        </div>

        <div id="messages" class="flex-1 overflow-y-auto bg-gray-800 rounded-lg p-4 space-y-3 mb-3" x-ref="msgContainer">
            <template x-for="msg in messages" :key="msg.id">
                <div :class="msg.role==='user' ? 'flex justify-end' : 'flex justify-start'">
                    <div :class="msg.role==='user'
                        ? 'bg-indigo-600 text-white max-w-lg px-4 py-2 rounded-2xl rounded-tr-sm text-sm'
                        : 'bg-gray-700 text-gray-100 max-w-2xl px-4 py-3 rounded-2xl rounded-tl-sm text-sm prose'">
                        <div x-html="msg.role==='user' ? msg.content : renderMd(msg.content)"></div>
                        <div class="text-xs opacity-40 mt-1" x-text="msg.time"></div>
                    </div>
                </div>
            </template>
            <template x-if="loading">
                <div class="flex justify-start">
                    <div class="bg-gray-700 px-4 py-3 rounded-2xl rounded-tl-sm">
                        <div class="flex space-x-1">
                            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay:.1s"></div>
                            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay:.2s"></div>
                        </div>
                    </div>
                </div>
            </template>
        </div>

        <div class="flex flex-wrap gap-1.5 mb-2">
            <template x-for="q in quickQ" :key="q">
                <button @click="send(q)"
                    class="px-2.5 py-1 bg-gray-700 hover:bg-gray-600 text-gray-400 text-xs rounded-full transition"
                    x-text="q"></button>
            </template>
        </div>

        <div class="flex space-x-2">
            <input x-model="input" @keydown.enter.prevent="if(!loading) send()"
                type="text" placeholder="Hỏi về server... (Enter để gửi)"
                class="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-2.5 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm">
            <button @click="send()" :disabled="loading || !input.trim()"
                class="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition">
                Gửi
            </button>
        </div>
    </div>

    <script>
        function chatApp() {{
            return {{
                sessionId: '{session_id}',
                serverId: {server_id},
                messages: [],
                input: '',
                loading: false,
                quickQ: [
                    'Tóm tắt trạng thái server',
                    'CPU và memory như thế nào?',
                    'Có alert nào đang active không?',
                    'Có lỗi gì trong logs gần đây?',
                    'Chi phí AI 1 giờ qua?',
                    'Queue backlog bao nhiêu?',
                ],
                init() {{
                    this.addMsg('assistant', '👋 Xin chào! Tôi đang monitor **{server.get("name", "server")}**. Hỏi tôi bất kỳ điều gì về server này!');
                }},
                addMsg(role, content) {{
                    this.messages.push({{ id: Date.now(), role, content, time: new Date().toLocaleTimeString('vi-VN') }});
                    this.$nextTick(() => {{ const el = this.$refs.msgContainer; if(el) el.scrollTop = el.scrollHeight; }});
                }},
                async send(text) {{
                    const msg = (text || this.input).trim();
                    if (!msg || this.loading) return;
                    this.input = '';
                    this.addMsg('user', msg);
                    this.loading = true;
                    try {{
                        const r = await fetch('/api/chat', {{
                            method: 'POST',
                            headers: {{'Content-Type':'application/json'}},
                            body: JSON.stringify({{ message: msg, session_id: this.sessionId, server_id: this.serverId }}),
                        }});
                        const d = await r.json();
                        this.addMsg('assistant', d.response);
                    }} catch(e) {{
                        this.addMsg('assistant', '❌ Lỗi kết nối: ' + e.message);
                    }} finally {{ this.loading = false; }}
                }},
                clearChat() {{
                    this.messages = [];
                    this.sessionId = Math.random().toString(36).slice(2);
                    this.init();
                }},
                renderMd(t) {{ return marked.parse(t); }},
            }};
        }}
    </script>"""

    return _base_layout(f"Chat — {server.get('name','')}", content, "chat")
