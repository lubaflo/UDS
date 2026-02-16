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
      --bg: #eef0f4;
      --panel: #f6f8fb;
      --card: #ffffff;
      --text: #0d2245;
      --muted: #66728a;
      --line: #d7ddea;
      --sidebar-1: #18326f;
      --sidebar-2: #081739;
      --sidebar-pill: #29458d;
      --accent: #1f3f94;
      --accent-2: #e88700;
      --radius: 16px;
    }}

    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background: var(--bg); color: var(--text); }}

    .layout {{ display: grid; grid-template-columns: 320px 1fr; min-height: 100vh; }}
    .sidebar {{
      background: linear-gradient(180deg, var(--sidebar-1), var(--sidebar-2));
      color: #fff;
      padding: 26px 16px;
    }}

    .brand {{ display:flex; align-items:center; gap:14px; margin-bottom: 22px; }}
    .logo {{
      width: 48px;
      height: 48px;
      border-radius: 14px;
      display:flex;
      align-items:center;
      justify-content:center;
      font-size: 28px;
      font-weight: 800;
      background: rgba(255,255,255,.1);
      border: 1px solid rgba(255,255,255,.15);
    }}
    .brand-title {{ font-size: 31px; line-height: 1; font-weight: 700; letter-spacing: .2px; }}
    .brand-sub {{ margin-top: 4px; font-size: 17px; color: #d6def2; }}

    .menu-item {{
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap: 12px;
      color: #ecf1ff;
      text-decoration: none;
      padding: 12px 14px;
      border-radius: 16px;
      margin-bottom: 10px;
      background: rgba(255,255,255,.06);
      border: 1px solid rgba(255,255,255,.06);
      font-size: 30px;
      letter-spacing: .1px;
    }}
    .menu-item .left {{ display:flex; align-items:center; gap: 12px; }}
    .menu-item .icon {{ width: 28px; text-align: center; opacity: .92; }}
    .menu-item .count {{
      min-width: 34px;
      text-align:center;
      font-size: 22px;
      border-radius: 999px;
      padding: 2px 10px;
      color: #ffd5a0;
      border: 1px solid rgba(255, 170, 86, .7);
    }}
    .menu-item.active, .menu-item:hover {{ background: var(--sidebar-pill); }}

    .note {{
      margin-top: 20px;
      color: #e5ecff;
      background: rgba(7, 17, 43, .34);
      border: 1px solid rgba(220, 231, 255, .2);
      border-radius: 16px;
      padding: 14px;
      font-size: 24px;
      line-height: 1.28;
    }}

    .content {{ padding: 16px 20px 22px; }}
    .top-tabs {{ display:flex; align-items:center; justify-content:space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }}
    .tabs-left, .tabs-right {{ display:flex; align-items:center; gap: 8px; flex-wrap: wrap; }}
    .chip {{
      padding: 9px 14px;
      border-radius: 14px;
      background: var(--card);
      border: 1px solid var(--line);
      font-size: 24px;
      color: #304159;
      text-decoration:none;
    }}
    .chip.active {{ font-weight: 700; color: #0f213f; }}

    .search-row {{ display:flex; gap: 10px; align-items:center; margin-bottom: 14px; flex-wrap: wrap; }}
    .search {{
      min-width: 420px;
      flex: 1;
      display:flex;
      align-items:center;
      gap: 8px;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 10px 14px;
      color: #71829e;
      font-size: 24px;
    }}
    .search .kbd {{
      margin-left: auto;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 1px 10px;
      font-size: 18px;
      color: #8290a8;
      background: #f8faff;
    }}

    .header {{ margin: 8px 0 8px; }}
    .header h1 {{ margin: 0; font-size: 56px; letter-spacing: .2px; }}
    .hint {{ color: #4c6288; font-size: 30px; }}

    .cards {{ display:grid; gap: 12px; grid-template-columns: repeat(4, minmax(200px, 1fr)); margin-top: 8px; }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      overflow: hidden;
    }}
    .card-head {{ display:flex; justify-content:space-between; padding: 14px 16px; font-size: 40px; font-weight: 700; border-bottom: 1px solid var(--line); }}
    .card-body {{ padding: 14px 16px; font-size: 35px; }}
    .metric {{ font-size: 54px; font-weight: 700; margin-bottom: 8px; line-height: 1; }}
    .metric-meta {{ color: #405474; border-left: 4px solid var(--accent-2); padding-left: 10px; }}

    .double {{ display:grid; gap: 12px; grid-template-columns: 1fr 1fr; margin-top: 14px; }}
    .panel {{ background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); overflow:hidden; }}
    .panel-head {{ display:flex; justify-content:space-between; align-items:center; padding: 14px 16px; border-bottom: 1px solid var(--line); font-size: 40px; font-weight: 700; }}
    .panel-body {{ padding: 14px 16px 16px; }}

    .actions {{ display:flex; gap: 10px; flex-wrap: wrap; }}
    .btn {{
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
      color: #1f2d49;
      text-decoration:none;
      padding: 11px 16px;
      font-size: 32px;
      font-weight: 500;
    }}
    .btn.primary {{
      background: var(--accent-2);
      border-color: #bd6300;
      color: #111c30;
      font-weight: 700;
    }}

    pre {{ margin: 0; white-space: pre-wrap; font-size: 31px; color: #0f2347; }}
    table {{ width:100%; border-collapse: collapse; }}
    th, td {{ text-align:left; padding: 12px; border-bottom:1px solid var(--line); font-size: 27px; }}
    th {{ color:#3a4d69; font-size: 24px; letter-spacing: .2px; }}
    .state-draft {{ color: #c05a00; font-weight: 700; }}
    .state-active {{ color: #0f874d; font-weight: 700; }}

    @media (max-width: 1600px) {{
      .layout {{ grid-template-columns: 280px 1fr; }}
      .menu-item {{ font-size: 20px; }}
      .brand-title {{ font-size: 22px; }}
      .brand-sub {{ font-size: 15px; }}
      .hint, .search, .chip, .card-head, .panel-head, .btn, td, pre {{ font-size: 18px; }}
      .header h1 {{ font-size: 42px; }}
      .metric {{ font-size: 46px; }}
      .cards {{ grid-template-columns: repeat(2, minmax(200px,1fr)); }}
      .double {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class=\"layout\">
    <aside class=\"sidebar\">
      <div class=\"brand\">
        <div class=\"logo\">CM</div>
        <div>
          <div class=\"brand-title\">СервисМаркет Бизнес</div>
          <div class=\"brand-sub\">admin · dev</div>
        </div>
      </div>

      <nav>
        <a class=\"menu-item {dashboard_active}\" href=\"/admin/dashboard\"><span class=\"left\"><span class=\"icon\">▦</span>Дашборд</span></a>
        <a class=\"menu-item\" href=\"/docs#/admin.auth\"><span class=\"left\"><span class=\"icon\">🔒</span>Аутентификация</span><span class=\"count\">1</span></a>
        <a class=\"menu-item\" href=\"/docs#/admin.clients\"><span class=\"left\"><span class=\"icon\">👥</span>Клиенты</span><span class=\"count\">4</span></a>
        <a class=\"menu-item {mailings_active}\" href=\"/admin/mailings\"><span class=\"left\"><span class=\"icon\">💬</span>Сообщения</span><span class=\"count\">3</span></a>
        <a class=\"menu-item\" href=\"/docs#/admin.security\"><span class=\"left\"><span class=\"icon\">🛡</span>Безопасность</span><span class=\"count\">1</span></a>
        <a class=\"menu-item\" href=\"/docs#/admin.operations\"><span class=\"left\"><span class=\"icon\">▣</span>Other</span><span class=\"count\">1</span></a>
        <a class=\"menu-item\" href=\"/docs\"><span class=\"left\"><span class=\"icon\">≡</span>API / OpenAPI</span></a>
      </nav>

      <div class=\"note\">Подсказка: если ответы 401/422 — вставь токен сверху (Bearer ...). Получить токен можно в разделе <b>Аутентификация</b>.</div>
    </aside>

    <main class=\"content\">
      <div class=\"top-tabs\">
        <div class=\"tabs-left\">
          <span class=\"chip active\">СервисМаркет</span>
          <span class=\"chip\">пространство</span>
          <span class=\"chip active\">Основное</span>
          <span class=\"chip\">профиль</span>
        </div>
        <div class=\"tabs-right\">
          <span class=\"chip\">+ Сообщения</span>
          <span class=\"chip\">+ Аудит</span>
          <span class=\"chip\">+ OpenAPI</span>
          <span class=\"chip\">http://127.0.0.1:8000</span>
        </div>
      </div>
      {body}
    </main>
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
    <div class=\"search-row\">
      <div class=\"search\">🔎 Поиск (Ctrl+K)... <span class=\"kbd\">Ctrl+K</span></div>
      <span class=\"chip\">Bearer token (если нужен)</span>
      <span class=\"chip\">Save</span>
      <a class=\"chip\" href=\"/docs\">/docs</a>
      <span class=\"chip active\">Обновить</span>
      <span class=\"chip\">Тема</span>
    </div>

    <div class=\"header\">
      <h1>Дашборд</h1>
      <div class=\"hint\">Сводка и быстрые действия</div>
    </div>

    <section class=\"cards\" id=\"dashboard-cards\"></section>

    <section class=\"double\">
      <div class=\"panel\">
        <div class=\"panel-head\"><span>Быстрые действия</span><span class=\"hint\">drawer</span></div>
        <div class=\"panel-body\">
          <div class=\"actions\">
            <a class=\"btn primary\" href=\"/docs#/admin.auth\">+ Получить токен</a>
            <a class=\"btn\" href=\"/docs#/admin.clients\">+ Открыть клиентов</a>
            <a class=\"btn\" href=\"/admin/mailings\">+ Открыть сообщения</a>
            <a class=\"btn\" href=\"/docs#/admin.audit\">+ Открыть аудит</a>
          </div>
        </div>
      </div>
      <div class=\"panel\">
        <div class=\"panel-head\"><span>Проверка</span><span class=\"hint\">/</span></div>
        <div class=\"panel-body\"><pre id=\"health\">{{\n  \"status\": \"ok\"\n}}</pre></div>
      </div>
    </section>

    <script>
      const labels = {
        customers_count: ['Клиенты', 'всего', 'Всего в базе'],
        today_operations: ['Диалоги', 'всего', 'Всего диалогов'],
        appointments_today: ['Аудит', 'лог', 'Записей журнала'],
      }

      async function loadDashboard() {
        const [summaryRes, stateRes] = await Promise.all([
          fetch('/api/v1/admin/dashboard/summary'),
          fetch('/admin/state')
        ])

        const summary = await summaryRes.json()
        const state = await stateRes.json()

        const cardsData = [
          { key: 'customers_count', value: summary.customers_count ?? '—' },
          { key: 'today_operations', value: summary.today_operations ?? '—' },
          { key: 'appointments_today', value: summary.appointments_today ?? '—' },
          { key: 'status', value: state.ui || 'ok', right: '/' , foot: 'GET /'}
        ]

        document.getElementById('dashboard-cards').innerHTML = cardsData.map((item) => {
          if (item.key === 'status') {
            return `
            <article class=\"card\">
              <div class=\"card-head\"><span>Статус API</span><span class=\"hint\">${item.right}</span></div>
              <div class=\"card-body\">
                <div class=\"metric\">${item.value}</div>
                <div class=\"metric-meta\">${item.foot}</div>
              </div>
            </article>`
          }
          const [title, right, foot] = labels[item.key] || [item.key, '', '']
          return `
            <article class=\"card\">
              <div class=\"card-head\"><span>${title}</span><span class=\"hint\">${right}</span></div>
              <div class=\"card-body\">
                <div class=\"metric\">${item.value}</div>
                <div class=\"metric-meta\">${foot}</div>
              </div>
            </article>`
        }).join('')

        document.getElementById('health').textContent = JSON.stringify({ status: state.ui || 'ok' }, null, 2)
      }

      loadDashboard().catch((e) => {
        document.getElementById('health').textContent = JSON.stringify({ status: 'error', detail: String(e) }, null, 2)
      })
    </script>
    """
    return _render_page("UDS CRM — Дашборд", body, "dashboard")


@router.get("/admin/mailings", response_class=HTMLResponse, include_in_schema=False)
def admin_mailings() -> HTMLResponse:
    body = """
    <div class=\"search-row\">
      <div class=\"search\">🔎 Поиск (Ctrl+K)... <span class=\"kbd\">Ctrl+K</span></div>
      <span class=\"chip\">Bearer token (если нужен)</span>
      <span class=\"chip\">Save</span>
      <a class=\"chip\" href=\"/docs\">/docs</a>
      <span class=\"chip active\">Обновить</span>
      <span class=\"chip\">Тема</span>
    </div>

    <div class=\"header\">
      <h1>Сообщения / Рассылки</h1>
      <div class=\"hint\">Кампании из /api/v1/admin/campaigns и /api/v1/admin/communications</div>
    </div>

    <section class=\"panel\" style=\"margin-bottom:12px\">
      <div class=\"panel-head\"><span>Кампании</span><span class=\"hint\">последние</span></div>
      <div class=\"panel-body\">
        <table>
          <thead><tr><th>Название</th><th>Канал</th><th>Статус</th><th>Дата запуска</th></tr></thead>
          <tbody id=\"campaign-rows\"><tr><td colspan=\"4\">Загрузка...</td></tr></tbody>
        </table>
      </div>
    </section>

    <section class=\"cards\" id=\"campaign-metrics\"></section>

    <script>
      const statusClass = (s) => s === 'active' ? 'state-active' : 'state-draft'

      async function loadMailings() {
        const [campaignsRes, commRes] = await Promise.all([
          fetch('/api/v1/admin/campaigns'),
          fetch('/api/v1/admin/communications')
        ])
        const campaigns = await campaignsRes.json()
        const communications = await commRes.json()

        const list = campaigns.items || campaigns || []
        const rows = list.slice(0, 12).map((item) => {
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
          ['Активные кампании', activeCount, 'В работе'],
          ['Архив кампаний', archivedCount, 'Завершенные'],
          ['Всего записей', list.length, 'Суммарно']
        ]
        document.getElementById('campaign-metrics').innerHTML = cards.map(([title, value, foot]) => `
          <article class=\"card\">
            <div class=\"card-head\"><span>${title}</span><span class=\"hint\">всего</span></div>
            <div class=\"card-body\">
              <div class=\"metric\">${value}</div>
              <div class=\"metric-meta\">${foot}</div>
            </div>
          </article>
        `).join('')
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
