from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(tags=["admin.ui"])


_BASE_HTML = """<!doctype html>
<html lang=\"ru\">
<head>
  <meta charset=\"utf-8\"/>
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"/>
  <title>{title}</title>
  <style>
    :root {{
      --bg: #f4f7fb;
      --card: #ffffff;
      --text: #1f2a37;
      --muted: #6b7280;
      --brand: #4f46e5;
      --brand-2: #06b6d4;
      --ok: #16a34a;
      --warn: #d97706;
      --border: #e5e7eb;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background: var(--bg); color: var(--text); }}
    .layout {{ display: grid; grid-template-columns: 260px 1fr; min-height: 100vh; }}
    .sidebar {{ background: #0f172a; color: #cbd5e1; padding: 22px 16px; }}
    .logo {{ color: #fff; font-weight: 700; font-size: 20px; margin-bottom: 24px; }}
    .menu a {{ display: block; color: #cbd5e1; text-decoration: none; padding: 10px 12px; border-radius: 10px; margin-bottom: 6px; }}
    .menu a.active, .menu a:hover {{ background: #1e293b; color: #fff; }}
    .content {{ padding: 24px; }}
    .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }}
    .header h1 {{ margin: 0; font-size: 28px; }}
    .hint {{ color: var(--muted); font-size: 14px; }}
    .grid {{ display: grid; gap: 14px; grid-template-columns: repeat(auto-fit,minmax(220px,1fr)); margin-bottom: 18px; }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 14px; box-shadow: 0 3px 16px rgba(15,23,42,.04); }}
    .metric {{ font-size: 28px; font-weight: 700; margin-top: 6px; }}
    .tag {{ display:inline-block; padding:4px 8px; border-radius:999px; font-size:12px; background:#eef2ff; color:#3730a3; }}
    table {{ width:100%; border-collapse: collapse; background: var(--card); border-radius: 14px; overflow: hidden; }}
    th, td {{ text-align:left; padding: 12px; border-bottom:1px solid var(--border); font-size:14px; }}
    th {{ background: #f8fafc; color:#334155; }}
    .state-draft {{ color: var(--warn); font-weight:600; }}
    .state-active {{ color: var(--ok); font-weight:600; }}
    .actions {{ margin-top: 14px; display:flex; gap:10px; flex-wrap:wrap; }}
    .btn {{ text-decoration:none; color:#fff; background:linear-gradient(120deg,var(--brand),var(--brand-2)); padding:10px 14px; border-radius:10px; font-size:14px; }}
  </style>
</head>
<body>
  <div class=\"layout\">
    <aside class=\"sidebar\">
      <div class=\"logo\">UDS CRM</div>
      <nav class=\"menu\">
        <a href=\"/admin/dashboard\" class=\"{dashboard_active}\">Дашборд</a>
        <a href=\"/admin/mailings\" class=\"{mailings_active}\">Рассылки</a>
        <a href=\"/docs\">Swagger API</a>
        <a href=\"/redoc\">ReDoc</a>
      </nav>
    </aside>
    <main class=\"content\">{body}</main>
  </div>
</body>
</html>
"""


def _render_page(title: str, body: str, active: str) -> HTMLResponse:
    return HTMLResponse(
        _BASE_HTML.format(
            title=title,
            body=body,
            dashboard_active="active" if active == "dashboard" else "",
            mailings_active="active" if active == "mailings" else "",
        )
    )


@router.get("/admin", include_in_schema=False)
def admin_root() -> RedirectResponse:
    return RedirectResponse(url="/admin/dashboard", status_code=307)


@router.get("/admin/dashboard", response_class=HTMLResponse, include_in_schema=False)
def admin_dashboard() -> HTMLResponse:
    body = """
    <div class=\"header\">
      <div>
        <h1>Дашборд CRM</h1>
        <div class=\"hint\">Живые данные из backend API /api/v1/admin/dashboard/*</div>
      </div>
      <span class=\"tag\">Админ-панель</span>
    </div>
    <div id=\"metrics\" class=\"grid\"></div>
    <div class=\"card\">
      <h3>Разделы CRM</h3>
      <div id=\"sections\" class=\"hint\">Загрузка...</div>
    </div>
    <script>
      const labels = {
        customers_count: 'Клиенты',
        today_revenue: 'Выручка сегодня',
        today_operations: 'Операции сегодня',
        new_customers_today: 'Новых клиентов',
        appointments_today: 'Записи сегодня'
      }

      async function loadDashboard() {
        const [summaryRes, fullRes] = await Promise.all([
          fetch('/api/v1/admin/dashboard/summary'),
          fetch('/api/v1/admin/dashboard/full')
        ])
        const summary = await summaryRes.json()
        const full = await fullRes.json()

        const metricsNode = document.getElementById('metrics')
        metricsNode.innerHTML = Object.entries(summary)
          .filter(([k, v]) => typeof v === 'number' || typeof v === 'string')
          .slice(0, 6)
          .map(([k, v]) => `<div class=\"card\"><div class=\"hint\">${labels[k] || k}</div><div class=\"metric\">${v}</div></div>`)
          .join('')

        const sections = (full.sections || []).map(s => `<li><b>${s.section}</b> — ${s.route}</li>`).join('')
        document.getElementById('sections').innerHTML = `<ul>${sections}</ul>`
      }

      loadDashboard().catch((e) => {
        document.getElementById('sections').textContent = 'Ошибка загрузки данных: ' + e
      })
    </script>
    """
    return _render_page("UDS CRM — Дашборд", body, "dashboard")


@router.get("/admin/mailings", response_class=HTMLResponse, include_in_schema=False)
def admin_mailings() -> HTMLResponse:
    body = """
    <div class=\"header\">
      <div>
        <h1>Рассылки</h1>
        <div class=\"hint\">Кампании из /api/v1/admin/campaigns и /api/v1/admin/communications</div>
      </div>
      <span class=\"tag\">Маркетинг</span>
    </div>
    <div class=\"grid\" id=\"campaign-metrics\"></div>
    <table>
      <thead><tr><th>Название</th><th>Канал</th><th>Статус</th><th>Дата запуска</th></tr></thead>
      <tbody id=\"campaign-rows\"><tr><td colspan=\"4\">Загрузка...</td></tr></tbody>
    </table>
    <div class=\"actions\">
      <a class=\"btn\" href=\"/docs#/admin.campaigns\">Открыть методы Campaigns</a>
      <a class=\"btn\" href=\"/docs#/admin.communications\">Открыть методы Communications</a>
    </div>
    <script>
      const statusClass = (s) => s === 'active' ? 'state-active' : 'state-draft'

      async function loadMailings() {
        const [campaignsRes, commRes] = await Promise.all([
          fetch('/api/v1/admin/campaigns'),
          fetch('/api/v1/admin/communications')
        ])
        const campaigns = await campaignsRes.json()
        const communications = await commRes.json()

        const rows = (campaigns.items || campaigns || []).slice(0, 12).map((item) => {
          const title = item.title || item.name || 'Без названия'
          const channel = item.channel || item.channel_type || 'app_push'
          const status = item.status || 'draft'
          const launchAt = item.launch_at || item.send_at || '—'
          return `<tr><td>${title}</td><td>${channel}</td><td class=\"${statusClass(status)}\">${status}</td><td>${launchAt}</td></tr>`
        }).join('')

        document.getElementById('campaign-rows').innerHTML = rows || '<tr><td colspan="4">Пока нет кампаний</td></tr>'

        const activeCount = (communications.active || communications.active_items || []).length || 0
        const archivedCount = (communications.archived || communications.archived_items || []).length || 0
        const cards = [
          ['Активные кампании', activeCount],
          ['Архив кампаний', archivedCount],
          ['Всего записей', (campaigns.items || campaigns || []).length]
        ]
        document.getElementById('campaign-metrics').innerHTML = cards.map(([label, value]) =>
          `<div class=\"card\"><div class=\"hint\">${label}</div><div class=\"metric\">${value}</div></div>`
        ).join('')
      }

      loadMailings().catch((e) => {
        document.getElementById('campaign-rows').innerHTML = `<tr><td colspan=\"4\">Ошибка: ${e}</td></tr>`
      })
    </script>
    """
    return _render_page("UDS CRM — Рассылки", body, "mailings")


@router.get("/admin/state", include_in_schema=False)
def admin_state() -> dict:
    return {"ui": "ok", "routes": ["/admin/dashboard", "/admin/mailings"], "meta": json.dumps({"version": 1})}
