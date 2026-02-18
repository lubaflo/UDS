from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(tags=["admin.ui"])


SECTIONS: list[dict[str, str]] = [
    {"key": "dashboard", "title": "Дашборд", "endpoint": "/api/v1/admin/dashboard/full", "icon": "▦", "module": "core"},
    {"key": "appointments", "title": "Записи", "endpoint": "/api/v1/admin/appointments", "icon": "🗓", "module": "services"},
    {"key": "operations", "title": "Операции", "endpoint": "/api/v1/admin/operations", "icon": "💳", "module": "core"},
    {"key": "clients", "title": "Клиенты", "endpoint": "/api/v1/admin/clients", "icon": "👥", "module": "core"},
    {"key": "products", "title": "Товары", "endpoint": "/api/v1/admin/products", "icon": "🧾", "module": "products"},
    {"key": "employees", "title": "Сотрудники", "endpoint": "/api/v1/admin/employees", "icon": "🧑‍💼", "module": "core"},
    {"key": "messages", "title": "Сообщения и диалоги", "endpoint": "/api/v1/admin/dialogues", "icon": "💬", "module": "messaging"},
    {"key": "communications", "title": "Коммуникации и рассылки", "endpoint": "/api/v1/admin/communications", "icon": "📨", "module": "marketing"},
    {"key": "campaigns", "title": "Кампании", "endpoint": "/api/v1/admin/campaigns", "icon": "🚀", "module": "marketing"},
    {"key": "analytics", "title": "Аналитика", "endpoint": "/api/v1/admin/analytics/control-tower", "icon": "📊", "module": "analytics"},
    {"key": "traffic", "title": "Источники трафика", "endpoint": "/api/v1/admin/traffic-channels", "icon": "📈", "module": "marketing"},
    {"key": "referral_programs", "title": "Реферальные программы", "endpoint": "/api/v1/admin/referral-programs", "icon": "🤝", "module": "referrals"},
    {"key": "certificates", "title": "Сертификаты", "endpoint": "/api/v1/admin/certificates", "icon": "🎟", "module": "certificates"},
    {"key": "feedback", "title": "Обратная связь", "endpoint": "/api/v1/admin/feedback", "icon": "⭐", "module": "core"},
    {"key": "news", "title": "Новости", "endpoint": "/api/v1/admin/news", "icon": "📰", "module": "core"},
    {"key": "security", "title": "Безопасность", "endpoint": "/api/v1/admin/audit-log", "icon": "🛡", "module": "security"},
    {"key": "system_settings", "title": "Системные настройки", "endpoint": "/api/v1/admin/system-settings", "icon": "⚙", "module": "core"},
]


QUICK_ACTIONS: list[dict[str, str | dict]] = [
    {"label": "+ Запись", "method": "POST", "url": "/api/v1/admin/appointments", "body": {"client_id": 1, "title": "Новая запись", "starts_at": 1735689600}},
    {"label": "+ Продажа", "method": "POST", "url": "/api/v1/admin/operations", "body": {"client_id": 1, "op_type": "purchase", "amount_rub": 1000, "comment": "Продажа из панели"}},
    {"label": "+ Клиент", "method": "POST", "url": "/api/v1/admin/clients", "body": {"full_name": "Новый клиент", "phone": "+79990000000"}},
    {"label": "+ Товар/Услуга", "method": "POST", "url": "/api/v1/admin/products", "body": {"name": "Новая позиция", "item_type": "service", "price_rub": 1000}},
    {"label": "Отправить сообщение", "method": "POST", "url": "/api/v1/admin/dialogues/send-group", "body": {"channel": "telegram", "subject": "Уведомление", "text": "Сообщение из админки"}},
    {"label": "Создать рассылку", "method": "POST", "url": "/api/v1/admin/communications", "body": {"name": "Новая рассылка", "channel": "sms", "message_template": "Добрый день!"}},
    {"label": "Возврат", "method": "POST", "url": "/api/v1/admin/operations", "body": {"client_id": 1, "op_type": "refund", "amount_rub": -500, "comment": "Возврат"}},
    {"label": "Экспорт отчёта", "method": "GET", "url": "/api/v1/admin/clients/export.csv", "body": {}},
    {"label": "Задача / заметка", "method": "POST", "url": "/api/v1/admin/news", "body": {"title": "Служебная заметка", "content": "Проверить задачу", "status": "draft"}},
    {"label": "Сканер / штрихкод", "method": "GET", "url": "/api/v1/admin/products", "body": {}},
]


_BASE_HTML = """<!doctype html>
<html lang=\"ru\">
<head>
  <meta charset=\"utf-8\"/>
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"/>
  <title>{title}</title>
  <style>
    :root {{
      --bg: #eef1f7;
      --panel: #f8f9fc;
      --card: #ffffff;
      --text: #14284d;
      --muted: #677692;
      --line: #d5dded;
      --sidebar-1: #17326f;
      --sidebar-2: #0a1739;
      --sidebar-pill: #2d4a96;
      --accent: #ffb65f;
      --accent-2: #f4f8ff;
      --radius: 14px;
    }}

    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background: var(--bg); color: var(--text); font-size: 14px; }}

    .layout {{ display: grid; grid-template-columns: 300px 1fr; min-height: 100vh; }}
    .sidebar {{ background: linear-gradient(180deg, var(--sidebar-1), var(--sidebar-2)); color: #fff; padding: 16px 12px; }}
    .brand {{ display:flex; align-items:center; gap:10px; margin-bottom: 14px; text-decoration:none; color:#fff; }}
    .logo {{ width: 38px; height: 38px; border-radius: 10px; display:flex; align-items:center; justify-content:center; font-size: 16px; font-weight: 800; background: rgba(255,255,255,.13); border: 1px solid rgba(255,255,255,.18); }}
    .brand-title {{ font-size: 16px; line-height: 1; font-weight: 700; }}
    .brand-sub {{ margin-top: 3px; font-size: 12px; color: #d5def7; }}

    .menu {{ max-height: calc(100vh - 140px); overflow:auto; padding-right: 4px; }}
    .menu-item {{
      display:flex; align-items:center; justify-content:space-between; gap: 8px;
      color: #edf2ff; text-decoration: none; padding: 9px 10px; border-radius: 12px;
      margin-bottom: 7px; background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.08); font-size: 13px;
    }}
    .menu-item .left {{ display:flex; align-items:center; gap: 7px; }}
    .menu-item .icon {{ width: 18px; text-align:center; opacity: .95; }}
    .menu-item.active, .menu-item:hover {{ background: var(--sidebar-pill); }}
    .menu-submenu {{ display:none; flex-direction:column; gap:6px; margin:-2px 0 8px 28px; }}
    .menu-submenu.open {{ display:flex; }}
    .menu-subitem {{
      display:block; text-decoration:none; color:#dbe6ff; font-size:12px;
      padding:7px 10px; border-radius:10px; border:1px solid rgba(206, 220, 255, .24);
      background: rgba(8, 24, 63, .36);
    }}
    .menu-subitem.active {{ background: rgba(108, 137, 219, .26); color:#fff; }}

    .content {{ padding: 10px 14px 16px; }}

    .topbar {{ background: var(--panel); border:1px solid var(--line); border-radius: var(--radius); padding: 8px; margin-bottom: 10px; }}
    .topbar-row {{ display:flex; align-items:center; justify-content:space-between; gap:8px; flex-wrap:wrap; }}
    .group {{ display:flex; align-items:center; gap:6px; flex-wrap:wrap; }}
    .chip, .btn {{
      border:1px solid var(--line); background:#fff; color:#1f3052; border-radius:10px;
      padding:7px 10px; text-decoration:none; font-size:12px; cursor:pointer;
    }}
    .chip.active {{ background: var(--accent-2); font-weight: 600; }}
    .btn.primary {{ background: var(--accent); border-color: #d78a2f; color:#1f2a43; font-weight:700; }}
    .search {{ min-width: 320px; flex:1; display:flex; align-items:center; gap:8px; background:#fff; border:1px solid var(--line); border-radius:10px; padding:7px 10px; color:#6b7892; font-size:12px; }}
    .kbd {{ margin-left:auto; border:1px solid var(--line); border-radius:999px; padding:1px 8px; background:#f8faff; font-size:11px; }}

    .header {{ margin: 10px 0; display:flex; align-items:center; justify-content:space-between; gap:8px; flex-wrap:wrap; }}
    .header h1 {{ margin:0; font-size: 24px; }}
    .hint {{ color: var(--muted); font-size: 12px; }}

    .grid {{ display:grid; gap:10px; grid-template-columns: repeat(3,minmax(220px,1fr)); }}
    .panel {{ background: var(--card); border:1px solid var(--line); border-radius:var(--radius); overflow:hidden; }}
    .panel-head {{ padding:10px 12px; border-bottom:1px solid var(--line); display:flex; align-items:center; justify-content:space-between; font-size:13px; font-weight:700; }}
    .panel-body {{ padding:10px 12px; }}

    .actions {{ display:flex; gap:6px; flex-wrap:wrap; }}
    .table-wrap {{ overflow:auto; }}
    table {{ width:100%; border-collapse: collapse; }}
    th, td {{ text-align:left; padding:8px; border-bottom:1px solid var(--line); font-size:12px; vertical-align:top; }}
    th {{ color:#405273; }}

    .drawer {{ position: fixed; top: 0; right: -520px; width: 500px; max-width: calc(100vw - 20px); height: 100vh; background:#fff; border-left:1px solid var(--line); box-shadow: -8px 0 28px rgba(18,36,73,.18); z-index: 100; transition: right .2s ease; display:flex; flex-direction:column; }}
    .drawer.open {{ right: 0; }}
    .drawer-head {{ padding:10px 12px; border-bottom:1px solid var(--line); display:flex; justify-content:space-between; align-items:center; }}
    .drawer-body {{ padding:12px; overflow:auto; }}
    textarea, input, select {{ width:100%; border:1px solid var(--line); border-radius:10px; padding:8px; font:inherit; }}
    .row {{ display:grid; gap:8px; grid-template-columns: 1fr 1fr; margin-bottom:8px; }}
    .product-spec-shell {{ background:#f3f5f9; border:1px solid #dde3ee; border-radius:0; margin:-10px -12px; padding:18px 0 0; min-height:620px; }}
    .product-spec {{ max-width: 1120px; margin: 0 auto; padding: 0 18px 18px; }}
    .product-spec-card {{ background:#fff; border:1px solid #d9e0ec; border-radius:14px; padding:14px 18px 16px; box-shadow:0 1px 2px rgba(18,36,73,.04); }}
    .spec-grid {{ display:grid; grid-template-columns: 200px 1fr; gap:10px 14px; align-items:center; }}
    .spec-label {{ text-align:right; font-weight:500; font-size:14px; line-height:1.2; color:#2c3e61; }}
    .spec-label-with-icon {{ display:flex; align-items:center; justify-content:flex-end; gap:6px; }}
    .spec-label-icon {{ width:16px; height:16px; border-radius:50%; border:1px solid var(--line); color:#7284a7; font-size:11px; line-height:1; display:inline-flex; align-items:center; justify-content:center; background:#f8fbff; }}
    .spec-field {{ width:100%; }}
    .spec-inline {{ display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap:10px; }}
    .spec-inline.two {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .spec-note {{ color:#7f8ea7; font-size:14px; margin-bottom:6px; }}
    .spec-input-group {{ display:grid; grid-template-columns: 44px 1fr; }}
    .spec-input-group .prefix {{ border:1px solid var(--line); border-right:none; border-radius:10px 0 0 10px; display:flex; align-items:center; justify-content:center; background:#f8faff; color:#5b6d8f; }}
    .spec-input-group input {{ border-radius:0 10px 10px 0; }}
    .spec-with-suffix {{ display:grid; grid-template-columns: 1fr 58px; }}
    .spec-with-suffix .suffix {{ border:1px solid var(--line); border-left:none; border-radius:0 10px 10px 0; display:flex; align-items:center; justify-content:center; background:#f6f8fc; color:#2a3f69; }}
    .spec-with-suffix input {{ border-radius:10px 0 0 10px; }}
    .spec-barcode-row {{ display:grid; grid-template-columns: 1fr 52px; }}
    .spec-icon-btn {{ border:1px solid var(--line); border-left:none; border-radius:0 10px 10px 0; background:#fff; color:#2a3f69; cursor:pointer; font-size:22px; line-height:1; }}
    .spec-field-with-help {{ display:grid; grid-template-columns: 1fr 24px; gap:8px; align-items:center; }}
    .spec-help-icon {{ width:18px; height:18px; border-radius:50%; border:1px solid #ccd8ef; color:#7d8eaf; font-size:11px; line-height:1; display:inline-flex; align-items:center; justify-content:center; background:#f8fbff; cursor:default; }}
    .spec-tax-row {{ display:grid; grid-template-columns: minmax(0, 1fr) 90px minmax(0, 1fr); gap:10px; align-items:center; }}
    .spec-tax-title {{ color:#2a3f69; font-size:14px; text-align:center; }}
    .spec-form-error {{ margin-top:10px; border:1px solid #f3b6bf; background:#fff1f4; color:#9c2f42; padding:10px; border-radius:10px; display:none; }}
    .spec-save {{ margin-top:16px; border-top:1px dashed var(--line); padding-top:18px; }}
    .spec-save .btn.primary {{ min-width:130px; background:#f7cb00; border-color:#efbf00; border-radius:12px; color:#22314e; }}
    .spec-grid textarea {{ min-height:56px; resize:vertical; }}
    .product-spec textarea, .product-spec input, .product-spec select {{ border-color:#d5ddeb; background:#fff; height:46px; }}
    .product-spec textarea {{ height:auto; min-height:56px; }}

    @media (max-width: 900px) {{
      .product-spec-shell {{ margin:0; border-radius:12px; min-height:auto; }}
      .spec-grid {{ grid-template-columns: 1fr; }}
      .product-spec-card {{ padding:12px; }}
      .spec-label {{ text-align:left; font-size:14px; }}
      .spec-inline, .spec-inline.two {{ grid-template-columns: 1fr; }}
      .spec-tax-row {{ grid-template-columns: 1fr; }}
      .spec-tax-title {{ text-align:left; }}
    }}

    pre {{ margin:0; background:#f6f8fd; border:1px solid var(--line); border-radius:10px; padding:10px; font-size:12px; white-space:pre-wrap; }}

    .badge {{ border-radius: 999px; background: #f2f6ff; color:#2a3f69; border:1px solid #d6e2fd; font-size:11px; padding:2px 8px; }}

    @media (max-width: 1200px) {{
      .layout {{ grid-template-columns: 1fr; }}
      .sidebar {{ min-height:auto; }}
      .grid {{ grid-template-columns: 1fr; }}
      .search {{ min-width: 220px; }}
    }}
  </style>
</head>
<body>
  <div class=\"layout\">
    <aside class=\"sidebar\">
      <a class=\"brand\" href=\"/admin/dashboard\">
        <div class=\"logo\">УБ</div>
        <div>
          <div class=\"brand-title\">Универсальная админка</div>
          <div class=\"brand-sub\">все разделы на русском</div>
        </div>
      </a>
      <nav class=\"menu\">{menu_html}</nav>
    </aside>

    <main class=\"content\">
      <div class=\"topbar\">
        <div class=\"topbar-row\" style=\"margin-bottom:6px\">
          <div class=\"group\">
            <a class=\"chip active\" href=\"/admin/dashboard\">Лого → Дашборд</a>
            <button class=\"chip\" data-space=\"Выбрать\">Выбрать</button>
            <button class=\"chip\" data-space=\"Создать филиал\">Создать филиал</button>
            <button class=\"chip\" data-space=\"Настроить\">Настроить</button>
          </div>
          <div class=\"search\" id=\"global-search\">🔎 Глобальный поиск: клиенты, записи, чеки, товары, сотрудники, диалоги, сертификаты <span class=\"kbd\">Ctrl+K</span></div>
        </div>

        <div class=\"topbar-row\" style=\"margin-bottom:6px\">
          <div class=\"group\" id=\"quick-actions\"></div>
        </div>

        <div class=\"topbar-row\">
          <div class=\"group\">
            <button class=\"chip\" data-open=\"уведомления\">🔔 Уведомления</button>
            <button class=\"chip\" data-open=\"сообщения\">💬 Сообщения</button>
            <button class=\"chip\" data-open=\"быстрые настройки\">⚙ Быстрые настройки</button>
            <button class=\"chip\" data-open=\"помощь\">❓ Помощь</button>
            <button class=\"chip\" data-open=\"профиль\">Профиль</button>
          </div>
          <div class=\"group\">
            <input id=\"token-input\" placeholder=\"Токен доступа (Bearer)\" style=\"width:300px\" />
            <button class=\"btn\" id=\"save-token\">Сохранить токен</button>
            <a class=\"btn\" href=\"/docs\">Открыть API</a>
          </div>
        </div>
      </div>

      {body}
    </main>
  </div>

  <aside class=\"drawer\" id=\"drawer\">
    <div class=\"drawer-head\">
      <strong id=\"drawer-title\">Действие</strong>
      <button class=\"btn\" id=\"drawer-close\">Закрыть</button>
    </div>
    <div class=\"drawer-body\" id=\"drawer-body\"></div>
  </aside>

  <script>
    const быстрыеКнопки = {quick_actions};
    const текущаяСекция = {section};

    const токенКлюч = 'админка_токен';
    const модульКлюч = 'админка_модули';
    const наборПоУмолчанию = {{services:true, products:true, messaging:true, marketing:true, analytics:true, certificates:true, referrals:true, security:true, core:true}};

    function взятьТокен() {{ return localStorage.getItem(токенКлюч) || ''; }}
    function сохранитьТокен(value) {{ localStorage.setItem(токенКлюч, value); }}
    function заголовки() {{
      const t = взятьТокен();
      return t ? {{'Authorization': `Bearer ${{t}}`, 'Content-Type':'application/json'}} : {{'Content-Type':'application/json'}};
    }}

    function открытьDrawer(заголовок, html) {{
      document.getElementById('drawer-title').textContent = заголовок;
      document.getElementById('drawer-body').innerHTML = html;
      document.getElementById('drawer').classList.add('open');
    }}
    function закрытьDrawer() {{ document.getElementById('drawer').classList.remove('open'); }}

    document.getElementById('drawer-close').addEventListener('click', закрытьDrawer);
    document.getElementById('save-token').addEventListener('click', () => {{
      const value = document.getElementById('token-input').value.trim();
      сохранитьТокен(value);
      alert('Токен сохранен');
    }});

    document.getElementById('token-input').value = взятьТокен();

    const контейнерБыстрыхКнопок = document.getElementById('quick-actions');
    быстрыеКнопки.forEach((a) => {{
      const btn = document.createElement('button');
      btn.className = 'btn primary';
      btn.textContent = a.label;
      btn.addEventListener('click', () => показатьФормуДействия(a));
      контейнерБыстрыхКнопок.appendChild(btn);
    }});


    async function открытьМастерЗаписи() {{
      открытьDrawer('Создание записи', `
        <div class="hint" style="margin-bottom:8px">Порядок: мастер → услуга → дата → время → клиент.</div>
        <div class="row">
          <label>Мастер
            <select id="appt-employee"><option value="">Не выбран</option></select>
          </label>
          <label>Услуга
            <select id="appt-service"><option value="">Не выбрана</option></select>
          </label>
        </div>
        <div class="row">
          <label>Дата
            <input id="appt-date" type="date" />
          </label>
          <label>Время
            <select id="appt-slot"><option value="">Выберите время</option></select>
          </label>
        </div>
        <div class="row">
          <label>ID клиента
            <input id="appt-client-id" type="number" min="1" placeholder="например, 1" />
          </label>
          <label>Источник
            <select id="appt-source">
              <option value="online">Онлайн</option>
              <option value="admin_phone">Звонок клиента</option>
              <option value="admin_manual" selected>Админ вручную</option>
            </select>
          </label>
        </div>
        <div class="actions" style="margin-top:8px">
          <button class="btn primary" id="appt-create">Создать запись</button>
        </div>
        <pre id="appt-result" style="margin-top:8px">Ожидание...</pre>
      `);

      const now = new Date();
      document.getElementById('appt-date').value = now.toISOString().slice(0,10);

      const optsRes = await fetch('/api/v1/app/appointments/booking-options', {{ headers: (window.заголовки ? window.заголовки() : {{ 'Content-Type': 'application/json' }}) }});
      const opts = await optsRes.json();
      (opts.masters || []).forEach((m) => {{
        const op = document.createElement('option');
        op.value = m.id;
        op.textContent = `${{m.full_name}}${{m.position ? ` (${{m.position}})` : ''}}`;
        document.getElementById('appt-employee').appendChild(op);
      }});
      (opts.services || []).forEach((s) => {{
        const op = document.createElement('option');
        op.value = s.id;
        op.textContent = `${{s.name}} · ${{s.price_rub}}₽`;
        document.getElementById('appt-service').appendChild(op);
      }});

      async function loadSlots() {{
        const date = document.getElementById('appt-date').value;
        if (!date) return;
        const employeeId = document.getElementById('appt-employee').value;
        const dayStart = Math.floor(new Date(`${{date}}T00:00:00Z`).getTime()/1000);
        const url = `/api/v1/app/appointments/slots?date_ts=${{dayStart}}${{employeeId ? `&employee_id=${{employeeId}}` : ''}}`;
        const res = await fetch(url, {{ headers: (window.заголовки ? window.заголовки() : {{ 'Content-Type': 'application/json' }}) }});
        const data = await res.json();
        const slotSelect = document.getElementById('appt-slot');
        slotSelect.innerHTML = '<option value="">Выберите время</option>';
        (data.items || []).forEach((slot) => {{
          const op = document.createElement('option');
          op.value = slot.starts_at;
          op.textContent = slot.label;
          slotSelect.appendChild(op);
        }});
      }}

      document.getElementById('appt-date').addEventListener('change', loadSlots);
      document.getElementById('appt-employee').addEventListener('change', loadSlots);
      await loadSlots();

      document.getElementById('appt-create').addEventListener('click', async () => {{
        const result = document.getElementById('appt-result');
        const payload = {{
          client_id: Number(document.getElementById('appt-client-id').value),
          employee_id: document.getElementById('appt-employee').value ? Number(document.getElementById('appt-employee').value) : null,
          service_id: document.getElementById('appt-service').value ? Number(document.getElementById('appt-service').value) : null,
          starts_at: Number(document.getElementById('appt-slot').value),
          source: document.getElementById('appt-source').value,
          title: 'Запись из календаря',
          duration_minutes: 60,
        }};
        try {{
          const res = await fetch('/api/v1/admin/appointments', {{
            method: 'POST',
            headers: (window.заголовки ? window.заголовки() : {{ 'Content-Type': 'application/json' }}),
            body: JSON.stringify(payload),
          }});
          const data = await res.json();
          result.textContent = JSON.stringify({{ статус: res.status, данные: data }}, null, 2);
        }} catch (e) {{
          result.textContent = String(e);
        }}
      }});
    }}

    function показатьФормуДействия(action) {{
      const isGet = action.method === 'GET';
      const json = JSON.stringify(action.body || {{}}, null, 2);
      открытьDrawer(action.label, `
        <div class=\"hint\" style=\"margin-bottom:8px\">Метод: <b>${{action.method}}</b> · Путь: <b>${{action.url}}</b></div>
        <div class=\"row\">
          <label>Путь
            <input id=\"action-url\" value=\"${{action.url}}\" />
          </label>
          <label>Метод
            <input id=\"action-method\" value=\"${{action.method}}\" />
          </label>
        </div>
        <label>${{isGet ? 'Параметры JSON (необязательно)' : 'Тело запроса JSON'}}
          <textarea id=\"action-body\" rows=\"10\">${{json}}</textarea>
        </label>
        <div class=\"actions\" style=\"margin-top:8px\">
          <button class=\"btn primary\" id=\"run-action\">Выполнить</button>
          <button class=\"btn\" id=\"copy-link\">Скопировать ссылку</button>
          <button class=\"btn\" id=\"go-section\">Открыть раздел</button>
        </div>
        <div style=\"margin-top:8px\">
          <div class=\"hint\" style=\"margin-bottom:4px\">Результат</div>
          <pre id=\"action-result\">Ожидание выполнения...</pre>
        </div>
      `);

      document.getElementById('copy-link').addEventListener('click', async () => {{
        await navigator.clipboard.writeText(location.origin + document.getElementById('action-url').value);
        alert('Ссылка скопирована');
      }});

      document.getElementById('go-section').addEventListener('click', () => {{
        location.href = '/admin/' + текущаяСекция.key;
      }});

      document.getElementById('run-action').addEventListener('click', async () => {{
        const resultEl = document.getElementById('action-result');
        const url = document.getElementById('action-url').value.trim();
        const method = document.getElementById('action-method').value.trim().toUpperCase();
        let body = undefined;
        try {{
          const raw = document.getElementById('action-body').value.trim();
          if (raw) body = JSON.parse(raw);
        }} catch (e) {{
          resultEl.textContent = 'Ошибка JSON: ' + e;
          return;
        }}

        try {{
          const init = {{ method, headers: (window.заголовки ? window.заголовки() : {{ 'Content-Type': 'application/json' }}) }};
          if (method !== 'GET' && method !== 'HEAD') init.body = JSON.stringify(body || {{}});
          const res = await fetch(url, init);
          const text = await res.text();
          let parsed = text;
          try {{ parsed = JSON.parse(text); }} catch (_e) {{}}
          resultEl.textContent = JSON.stringify({{ статус: res.status, данные: parsed }}, null, 2);
        }} catch (e) {{
          resultEl.textContent = 'Ошибка запроса: ' + e;
        }}
      }});
    }}

    document.querySelectorAll('[data-open]').forEach((btn) => {{
      btn.addEventListener('click', () => {{
        const label = btn.getAttribute('data-open');
        const общиеПанели = {{
          'уведомления': ['Отметить прочитанным', 'Настроить', 'Открыть'],
          'сообщения': ['Открыть раздел сообщений', 'Назначить ответственного', 'Создать запись'],
          'быстрые настройки': ['Режим кассы', 'Тихие часы', 'Показать подсказки', 'Тема: светлая/темная', 'Плотность интерфейса'],
          'помощь': ['Документация', 'Чат поддержки', 'Статус системы'],
          'профиль': ['Мой профиль', 'Мои уведомления', 'Мои права', 'Выйти'],
        }};
        const actions = (общиеПанели[label] || []).map((x) => `<span class=\"badge\">${{x}}</span>`).join(' ');

        if (label === 'быстрые настройки') {{
          const модули = JSON.parse(localStorage.getItem(модульКлюч) || 'null') || наборПоУмолчанию;
          const чекбоксы = Object.entries(модули).map(([k,v]) => `
            <label style=\"display:flex;align-items:center;gap:8px;margin-bottom:6px\">
              <input type=\"checkbox\" data-module=\"${{k}}\" ${{v ? 'checked' : ''}} style=\"width:auto\" />
              <span>${{k}}</span>
            </label>
          `).join('');

          открытьDrawer('Быстрые настройки', `
            <div class=\"hint\" style=\"margin-bottom:8px\">${{actions}}</div>
            <h4 style=\"margin:4px 0 6px\">Модули (включить/выключить)</h4>
            ${{чекбоксы}}
            <div class=\"actions\"><button class=\"btn primary\" id=\"save-modules\">Сохранить</button></div>
          `);

          document.getElementById('save-modules').addEventListener('click', () => {{
            const next = {{...модули}};
            document.querySelectorAll('[data-module]').forEach((el) => {{ next[el.getAttribute('data-module')] = el.checked; }});
            localStorage.setItem(модульКлюч, JSON.stringify(next));
            location.reload();
          }});
          return;
        }}

        открытьDrawer(label.charAt(0).toUpperCase() + label.slice(1), `<div class=\"hint\" style=\"margin-bottom:8px\">${{actions}}</div><div class=\"actions\"><a class=\"btn primary\" href=\"/admin/messages\">Открыть</a></div>`);
      }});
    }});

    document.querySelectorAll('[data-menu-toggle]').forEach((link) => {{
      link.addEventListener('click', (e) => {{
        const menuKey = link.getAttribute('data-menu-toggle');
        const submenu = document.querySelector(`[data-submenu="${{menuKey}}"]`);
        if (!submenu) return;
        const shouldOpen = !submenu.classList.contains('open');
        document.querySelectorAll('[data-submenu]').forEach((node) => node.classList.remove('open'));
        if (shouldOpen) {{
          e.preventDefault();
          submenu.classList.add('open');
        }}
      }});
    }});

    document.addEventListener('keydown', (e) => {{
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {{
        e.preventDefault();
        открытьDrawer('Глобальный поиск', `
          <input id=\"global-input\" placeholder=\"Введите запрос: клиент, запись, товар, сотрудник...\" />
          <div class=\"actions\" style=\"margin-top:8px\">
            <button class=\"btn primary\" id=\"search-run\">Открыть</button>
            <button class=\"btn\">Создать</button>
            <button class=\"btn\">Скопировать ссылку</button>
            <button class=\"btn\">Позвонить / Написать</button>
            <button class=\"btn\">Создать запись</button>
          </div>
        `);
        document.getElementById('search-run').addEventListener('click', () => location.href = '/admin/clients');
      }}
    }});
  </script>
</body>
</html>
"""


SECTION_ACTIONS: dict[str, list[dict[str, str]]] = {
    "dashboard": [
        {"label": "Настроить дашборд", "type": "drawer", "value": "Настройка виджетов и KPI"},
        {"label": "Добавить виджет", "type": "drawer", "value": "Выручка / Записи / Клиенты / Средний чек"},
        {"label": "Экспорт", "type": "quick", "value": "/api/v1/admin/dashboard/full"},
    ],
    "appointments": [
        {"label": "+ Запись", "type": "quick", "value": "/api/v1/admin/appointments"},
        {"label": "Массовые действия", "type": "drawer", "value": "Подтвердить / Отменить / Переназначить"},
        {"label": "Экспорт", "type": "quick", "value": "/api/v1/admin/appointments"},
    ],
    "operations": [
        {"label": "+ Продажа", "type": "quick", "value": "/api/v1/admin/operations"},
        {"label": "Возврат", "type": "quick", "value": "/api/v1/admin/operations"},
        {"label": "Открыть / закрыть смену", "type": "drawer", "value": "Внутренний журнал операций"},
    ],
}


def _menu(active: str) -> str:
    items: list[str] = []
    for section in SECTIONS:
        css = "active" if active == section["key"] else ""
        submenu_html = ""
        if section["key"] == "products":
            submenu_css = "open" if active == "products" else ""
            submenu_html = """
              <div class=\"menu-submenu {submenu_css}\" data-submenu=\"products\">
                <a class=\"menu-subitem\" href=\"/admin/products#products-add\">Спецификация товара</a>
                <a class=\"menu-subitem\" href=\"/admin/products#products-inventory\">Учет наличия</a>
                <a class=\"menu-subitem\" href=\"/admin/products#products-audit\">Инвентаризация</a>
                <a class=\"menu-subitem\" href=\"/admin/products#products-spec\">Создание товара</a>
                <a class=\"menu-subitem\" href=\"/admin/products#products-service-create\">Создание услуги</a>
                <a class=\"menu-subitem\" href=\"/admin/products#products-service-tech-card\">Технологическая карточка услуги</a>
                <a class=\"menu-subitem\" href=\"/admin/products#products-service-inventory\">Инвентаризация товаров для оказания услуги</a>
                <a class=\"menu-subitem\" href=\"/admin/products#products-service-materials\">Учет наличия материалов для оказания услуги</a>
              </div>
            """.format(submenu_css=submenu_css)
        toggle_attr = f' data-menu-toggle="{section["key"]}"' if section["key"] == "products" else ""
        items.append(
            f"""
            <a class=\"menu-item {css}\" href=\"/admin/{section['key']}\" data-module=\"{section['module']}\"{toggle_attr}>
              <span class=\"left\"><span class=\"icon\">{section['icon']}</span>{section['title']}</span>
            </a>
            {submenu_html}
            """
        )
    return "\n".join(items)


def _products_section_body(section: dict[str, str]) -> str:
    return f"""
      <section class="header">
        <div>
          <h1>{section['title']}</h1>
          <div class="hint">Полный цикл: создание товара → учет наличия → инвентаризация → технологическая карточка услуги.</div>
        </div>
      </section>

      <section class="panel" style="margin-bottom:10px">
        <div class="panel-head"><span>Рабочее подменю</span><span class="hint" id="products-mode-hint">товары</span></div>
        <div class="panel-body">
          <div class="actions" style="margin-bottom:8px">
            <button class="btn primary" data-products-mode="goods">Товары</button>
            <button class="btn" data-products-mode="services">Услуги</button>
          </div>
          <div class="actions">
            <button class="btn primary" data-products-screen="add" data-products-group="goods" id="products-add">Создание товара</button>
            <button class="btn" data-products-screen="inventory" id="products-inventory">Учет наличия</button>
            <button class="btn" data-products-screen="audit" id="products-audit">Инвентаризация</button>
            <button class="btn" data-products-screen="spec" id="products-spec">Создание товара</button>
            <button class="btn" data-products-screen="service-create" data-products-group="services" id="products-service-create" style="display:none">Создание услуги</button>
            <button class="btn" data-products-screen="service-tech-card" data-products-group="services" id="products-service-tech-card" style="display:none">Технологическая карточка услуги</button>
            <button class="btn" data-products-screen="service-inventory" data-products-group="services" id="products-service-inventory" style="display:none">Инвентаризация товаров для оказания услуги</button>
            <button class="btn" data-products-screen="service-materials" data-products-group="services" id="products-service-materials" style="display:none">Учет наличия материалов для оказания услуги</button>
          </div>
        </div>
      </section>

      <section class="panel" id="products-workspace">
        <div class="panel-head"><span id="products-screen-title">Создание товара</span><span class="hint" id="products-status">ожидание</span></div>
        <div class="panel-body" id="products-screen-body">Загрузка...</div>
      </section>

      <script>
        (function() {{
          const tokenKey = 'админка_токен';
          function fallbackHeaders() {{
            const token = localStorage.getItem(tokenKey) || '';
            return token ? {{ Authorization: `Bearer ${{token}}`, 'Content-Type': 'application/json' }} : {{ 'Content-Type': 'application/json' }};
          }}
          const apiHeaders = () => (window.заголовки ? window.заголовки() : fallbackHeaders());

          const state = {{ products: [], services: [], locations: [] }};
          const statusEl = document.getElementById('products-status');
          const modeHintEl = document.getElementById('products-mode-hint');
          const titleEl = document.getElementById('products-screen-title');
          const bodyEl = document.getElementById('products-screen-body');
          let currentMode = 'goods';

          async function readJson(response) {{
            const text = await response.text();
            try {{ return JSON.parse(text); }} catch (_e) {{ return text; }}
          }}

          async function fetchProducts() {{
            const response = await fetch('/api/v1/admin/products?page=1&page_size=200', {{ headers: apiHeaders() }});
            const data = await readJson(response);
            if (!response.ok) throw new Error(typeof data === 'string' ? data : JSON.stringify(data));
            state.products = data.items || [];
            state.services = state.products.filter((x) => x.item_type === 'service');
          }}

          async function fetchLocations() {{
            const response = await fetch('/api/v1/admin/products/locations', {{ headers: apiHeaders() }});
            const data = await readJson(response);
            if (!response.ok) throw new Error(typeof data === 'string' ? data : JSON.stringify(data));
            state.locations = Array.isArray(data) ? data : [];
          }}

          function optionRows(items, valueKey, labelKey) {{
            return items.map((x) => `<option value="${{x[valueKey]}}">${{x[labelKey]}}</option>`).join('');
          }}

          function renderAddProduct() {{
            titleEl.textContent = 'Создание товара';
            bodyEl.innerHTML = `
              <div class="product-spec-shell">
                <div class="product-spec">
                  <div class="product-spec-card">
                    <div class="spec-grid">
                    <div class="spec-label">Название</div>
                    <div class="spec-field"><input id="p-name" maxlength="100" /></div>

                    <div class="spec-label">Название в чеке</div>
                    <div class="spec-field spec-field-with-help"><input id="p-receipt-name" maxlength="100" /><span class="spec-help-icon" title="Название, которое печатается в чеке">i</span></div>

                    <div class="spec-label">Артикул</div>
                    <div class="spec-field"><input id="p-sku" /></div>

                    <div class="spec-label">Штрихкод</div>
                    <div class="spec-field spec-barcode-row">
                      <input id="p-barcode" style="border-radius:10px 0 0 10px" />
                      <button type="button" id="p-barcode-generate" class="spec-icon-btn" title="Сгенерировать штрихкод">↻</button>
                    </div>

                    <div class="spec-label">Категория</div>
                    <div class="spec-field">
                      <select id="p-category">
                        <option value="Основные товары">Основные товары</option>
                        <option value="Расходные материалы">Расходные материалы</option>
                        <option value="Сопутствующие товары">Сопутствующие товары</option>
                      </select>
                    </div>

                    <div class="spec-label">Единицы измерения</div>
                    <div class="spec-field spec-inline">
                    <div>
                      <div class="spec-note">Для продажи</div>
                      <select id="p-unit-sale">
                        <option value="Штука">Штука</option>
                        <option value="Упаковка">Упаковка</option>
                        <option value="мл">мл</option>
                        <option value="г">г</option>
                      </select>
                    </div>
                    <div>
                      <div class="spec-note">Равно</div>
                      <div class="spec-input-group">
                        <span class="prefix">=</span>
                        <input id="p-unit-ratio" type="number" min="1" step="1" value="1" />
                      </div>
                    </div>
                    <div>
                      <div class="spec-note">Для списания</div>
                      <select id="p-unit-stock">
                        <option value="Штука">Штука</option>
                        <option value="Упаковка">Упаковка</option>
                        <option value="мл">мл</option>
                        <option value="г">г</option>
                      </select>
                    </div>
                  </div>

                    <div class="spec-label">Массы</div>
                    <div class="spec-field spec-inline two">
                    <div>
                      <div class="spec-note">Масса нетто</div>
                      <div class="spec-with-suffix">
                        <input id="p-netto" type="number" min="0" step="0.01" value="0" />
                        <span class="suffix">гр.</span>
                      </div>
                    </div>
                    <div>
                      <div class="spec-note">Масса брутто</div>
                      <div class="spec-with-suffix">
                        <input id="p-brutto" type="number" min="0" step="0.01" value="0" />
                        <span class="suffix">гр.</span>
                      </div>
                    </div>
                  </div>

                    <div class="spec-label">Цена продажи</div>
                    <div class="spec-field spec-with-suffix">
                      <input id="p-price" type="number" min="0" step="1" value="0" />
                      <span class="suffix">₽</span>
                    </div>

                    <div class="spec-label"><span class="spec-label-with-icon">Себестоимость <span class="spec-label-icon" title="Нужна для расчета маржинальности">i</span></span></div>
                    <div class="spec-field spec-with-suffix">
                      <input id="p-cost" type="number" min="0" step="1" value="0" />
                      <span class="suffix">₽</span>
                    </div>

                    <div class="spec-label">Система налогообложения</div>
                    <div class="spec-field spec-tax-row">
                    <select id="p-tax-system">
                      <option value="По умолчанию">По умолчанию</option>
                      <option value="ОСН">ОСН</option>
                      <option value="УСН доход">УСН доход</option>
                      <option value="УСН доход-расход">УСН доход-расход</option>
                    </select>
                    <div class="spec-tax-title">НДС</div>
                    <select id="p-vat">
                      <option value="По умолчанию">По умолчанию</option>
                      <option value="Без НДС">Без НДС</option>
                      <option value="20%">20%</option>
                      <option value="10%">10%</option>
                    </select>
                  </div>

                    <div class="spec-label"><span class="spec-label-with-icon">Критичный остаток <span class="spec-label-icon" title="При достижении этого уровня товар помечается как дефицитный">i</span></span></div>
                    <div class="spec-field spec-field-with-help">
                    <div class="spec-with-suffix">
                      <input id="p-critical" type="number" min="0" step="1" value="0" />
                      <span class="suffix">шт.</span>
                    </div>
                    <span class="spec-help-icon" title="Минимальный остаток, при котором товар считается дефицитным">i</span>
                  </div>

                    <div class="spec-label"><span class="spec-label-with-icon">Желаемый остаток <span class="spec-label-icon" title="Целевой остаток для автоматических подсказок закупки">i</span></span></div>
                    <div class="spec-field spec-field-with-help">
                    <div class="spec-with-suffix">
                      <input id="p-desired" type="number" min="0" step="1" value="0" />
                      <span class="suffix">шт.</span>
                    </div>
                    <span class="spec-help-icon" title="Целевой остаток для подсказок закупки">i</span>
                  </div>

                    <div class="spec-label">Комментарий</div>
                    <div class="spec-field"><textarea id="p-comment" rows="3"></textarea></div>
                    </div>
                    <div class="spec-save">
                      <div class="actions">
                        <button class="btn primary" id="p-create">Сохранить</button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div id="p-error" class="spec-form-error"></div>
              <pre id="p-result" style="margin-top:8px; display:none">Ожидание...</pre>
            `;

            const barcodeEl = document.getElementById('p-barcode');
            document.getElementById('p-barcode-generate').addEventListener('click', () => {{
              const randomPart = String(Math.floor(100000000000 + Math.random() * 900000000000));
              const checksum = randomPart.split('').reduce((acc, digit, index) => acc + Number(digit) * (index % 2 ? 3 : 1), 0);
              const control = (10 - (checksum % 10)) % 10;
              barcodeEl.value = `${{randomPart}}${{control}}`;
            }});

            const nameEl = document.getElementById('p-name');
            const receiptNameEl = document.getElementById('p-receipt-name');
            nameEl.addEventListener('input', () => {{
              if (!receiptNameEl.value.trim()) {{
                receiptNameEl.value = nameEl.value;
              }}
            }});

            const errorEl = document.getElementById('p-error');
            const saveButtonEl = document.getElementById('p-create');

            function toInt(value, fallback = 0) {{
              const normalized = Number(value);
              if (!Number.isFinite(normalized)) return fallback;
              return Math.max(0, Math.round(normalized));
            }}

            function vatPercent(value) {{
              if (value === 'Без НДС') return 0;
              if (value === '10%') return 10;
              return 20;
            }}

            function showError(message) {{
              errorEl.style.display = message ? 'block' : 'none';
              errorEl.textContent = message || '';
            }}

            async function createProduct() {{
              const resultEl = document.getElementById('p-result');
              const saleUnit = document.getElementById('p-unit-sale').value;
              const stockUnit = document.getElementById('p-unit-stock').value;
              const ratio = Math.max(1, toInt(document.getElementById('p-unit-ratio').value, 1));
              const netto = toInt(document.getElementById('p-netto').value);
              const brutto = toInt(document.getElementById('p-brutto').value);
              const taxSystem = document.getElementById('p-tax-system').value;
              const vat = document.getElementById('p-vat').value;
              const nameValue = document.getElementById('p-name').value.trim();
              const criticalStock = toInt(document.getElementById('p-critical').value);
              const desiredStock = toInt(document.getElementById('p-desired').value);
              const manualComment = document.getElementById('p-comment').value.trim();

              showError('');
              if (!nameValue) {{
                showError('Заполните поле «Название».');
                return;
              }}
              if (desiredStock < criticalStock) {{
                showError('Желаемый остаток не может быть меньше критичного остатка.');
                return;
              }}

              const payload = {{
                name: nameValue,
                category: document.getElementById('p-category').value,
                full_name: nameValue,
                receipt_name: document.getElementById('p-receipt-name').value.trim() || nameValue,
                description: '',
                item_type: 'product',
                unit: saleUnit,
                unit_for_writeoff: stockUnit,
                unit_ratio: ratio,
                is_promo: false,
                price_rub: toInt(document.getElementById('p-price').value),
                cost_price_rub: toInt(document.getElementById('p-cost').value),
                sku: document.getElementById('p-sku').value.trim(),
                barcode: document.getElementById('p-barcode').value.trim(),
                tax_rate_percent: vatPercent(vat),
                critical_stock: criticalStock,
                desired_stock: desiredStock,
                stock: 0,
                track_inventory: true,
                comment: [
                  manualComment,
                  `Ед. продажи: ${{saleUnit}}`,
                  `Ед. списания: ${{stockUnit}}`,
                  `Соотношение: 1=${{ratio}}`,
                  `Масса нетто: ${{netto}} гр.`,
                  `Масса брутто: ${{brutto}} гр.`,
                  `СНО: ${{taxSystem}}`,
                  `НДС: ${{vat}}`,
                ].filter(Boolean).join(' | '),
                images: [],
              }};

              statusEl.textContent = 'сохранение';
              saveButtonEl.disabled = true;
              saveButtonEl.textContent = 'Сохранение...';
              try {{
                const response = await fetch('/api/v1/admin/products', {{ method: 'POST', headers: apiHeaders(), body: JSON.stringify(payload) }});
                const data = await readJson(response);
                statusEl.textContent = response.ok ? 'сохранено' : 'ошибка';
                resultEl.style.display = response.ok ? 'none' : 'block';
                resultEl.textContent = JSON.stringify({{ status: response.status, data }}, null, 2);
                if (response.ok) {{
                  await fetchProducts();
                  document.getElementById('p-comment').value = '';
                }}
              }} catch (e) {{
                statusEl.textContent = 'ошибка';
                resultEl.style.display = 'block';
                resultEl.textContent = String(e);
              }} finally {{
                saveButtonEl.disabled = false;
                saveButtonEl.textContent = 'Сохранить';
              }}
            }}

            saveButtonEl.addEventListener('click', createProduct);
            bodyEl.addEventListener('keydown', (event) => {{
              if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {{
                event.preventDefault();
                createProduct();
              }}
            }});
          }}

          function renderInventory() {{
            titleEl.textContent = 'Учет наличия товара';
            const goods = state.products.filter((x) => x.item_type === 'product' && x.track_inventory);
            bodyEl.innerHTML = `
              <div class="hint" style="margin-bottom:8px">Операции движения: приход, расход, корректировка остатков.</div>
              <div class="row">
                <label>Товар<select id="i-product">${{optionRows(goods, 'id', 'name')}}</select></label>
                <label>Склад/точка<select id="i-location">${{optionRows(state.locations, 'id', 'name')}}</select></label>
              </div>
              <div class="row">
                <label>Тип движения
                  <select id="i-type">
                    <option value="income">Приход</option>
                    <option value="expense">Расход</option>
                    <option value="adjustment">Корректировка</option>
                  </select>
                </label>
                <label>Количество<input id="i-qty" type="number" min="0" value="1" /></label>
              </div>
              <div class="row">
                <label>Себестоимость за единицу, ₽<input id="i-cost" type="number" min="0" value="0" /></label>
                <label>Контрагент<input id="i-counterparty" placeholder="Поставщик/ответственный" /></label>
              </div>
              <label>Комментарий<textarea id="i-comment" rows="3"></textarea></label>
              <div class="actions" style="margin-top:8px">
                <button class="btn primary" id="i-save">Сохранить операцию</button>
                <button class="btn" id="i-refresh">Обновить движения</button>
              </div>
              <pre id="i-result" style="margin-top:8px">Ожидание...</pre>
            `;

            const resultEl = document.getElementById('i-result');
            if (!goods.length || !state.locations.length) {{
              resultEl.textContent = 'Нужны минимум 1 товар и 1 склад (локация).';
              return;
            }}

            document.getElementById('i-save').addEventListener('click', async () => {{
              statusEl.textContent = 'сохранение';
              const productId = Number(document.getElementById('i-product').value);
              const payload = {{
                location_id: Number(document.getElementById('i-location').value),
                movement_type: document.getElementById('i-type').value,
                quantity: Number(document.getElementById('i-qty').value || 0),
                unit_cost_rub: Number(document.getElementById('i-cost').value || 0),
                counterparty: document.getElementById('i-counterparty').value.trim(),
                comment: document.getElementById('i-comment').value.trim(),
              }};
              try {{
                const response = await fetch(`/api/v1/admin/products/${{productId}}/movements`, {{ method: 'POST', headers: apiHeaders(), body: JSON.stringify(payload) }});
                const data = await readJson(response);
                statusEl.textContent = response.ok ? 'сохранено' : 'ошибка';
                resultEl.textContent = JSON.stringify({{ status: response.status, data }}, null, 2);
                if (response.ok) await fetchProducts();
              }} catch (e) {{
                statusEl.textContent = 'ошибка';
                resultEl.textContent = String(e);
              }}
            }});

            document.getElementById('i-refresh').addEventListener('click', async () => {{
              const productId = Number(document.getElementById('i-product').value);
              const response = await fetch(`/api/v1/admin/products/movements?product_id=${{productId}}&page=1&page_size=10`, {{ headers: apiHeaders() }});
              const data = await readJson(response);
              resultEl.textContent = JSON.stringify({{ status: response.status, data }}, null, 2);
            }});
          }}

          function renderInventoryAudit() {{
            titleEl.textContent = 'Инвентаризация';
            const goods = state.products.filter((x) => x.item_type === 'product' && x.track_inventory);
            bodyEl.innerHTML = `
              <div class="hint" style="margin-bottom:8px">Проведение инвентаризации: сравните факт с текущим остатком и зафиксируйте корректировку.</div>
              <div class="row">
                <label>Товар<select id="a-product">${{optionRows(goods, 'id', 'name')}}</select></label>
                <label>Склад/точка<select id="a-location">${{optionRows(state.locations, 'id', 'name')}}</select></label>
              </div>
              <div class="row">
                <label>Текущий остаток<input id="a-current" type="number" value="0" disabled /></label>
                <label>Фактический остаток<input id="a-counted" type="number" min="0" value="0" /></label>
              </div>
              <label>Комментарий инвентаризации<textarea id="a-comment" rows="3" placeholder="Номер акта, ответственный, причина расхождения"></textarea></label>
              <div class="actions" style="margin-top:8px">
                <button class="btn" id="a-load">Обновить текущий остаток</button>
                <button class="btn primary" id="a-apply">Провести инвентаризацию</button>
                <button class="btn" id="a-history">История корректировок</button>
              </div>
              <pre id="a-result" style="margin-top:8px">Ожидание...</pre>
            `;

            const resultEl = document.getElementById('a-result');
            if (!goods.length || !state.locations.length) {{
              resultEl.textContent = 'Нужны минимум 1 товар и 1 склад (локация).';
              return;
            }}

            async function loadCurrentStock() {{
              const productId = Number(document.getElementById('a-product').value);
              const locationId = Number(document.getElementById('a-location').value);
              const response = await fetch(`/api/v1/admin/products/${{productId}}/stock`, {{ headers: apiHeaders() }});
              const data = await readJson(response);
              const byLocation = response.ok && data.by_location ? data.by_location : [];
              const current = byLocation.find((x) => x.location_id === locationId);
              document.getElementById('a-current').value = current ? current.quantity : 0;
              resultEl.textContent = JSON.stringify({{ status: response.status, data }}, null, 2);
            }}

            document.getElementById('a-load').addEventListener('click', loadCurrentStock);
            document.getElementById('a-product').addEventListener('change', loadCurrentStock);
            document.getElementById('a-location').addEventListener('change', loadCurrentStock);

            document.getElementById('a-apply').addEventListener('click', async () => {{
              statusEl.textContent = 'сохранение';
              const productId = Number(document.getElementById('a-product').value);
              const payload = {{
                location_id: Number(document.getElementById('a-location').value),
                movement_type: 'adjustment',
                quantity: Number(document.getElementById('a-counted').value || 0),
                unit_cost_rub: 0,
                counterparty: 'Инвентаризация',
                comment: document.getElementById('a-comment').value.trim() || 'Инвентаризация',
              }};
              try {{
                const response = await fetch(`/api/v1/admin/products/${{productId}}/movements`, {{ method: 'POST', headers: apiHeaders(), body: JSON.stringify(payload) }});
                const data = await readJson(response);
                statusEl.textContent = response.ok ? 'сохранено' : 'ошибка';
                resultEl.textContent = JSON.stringify({{ status: response.status, data }}, null, 2);
                if (response.ok) {{
                  await fetchProducts();
                  await loadCurrentStock();
                }}
              }} catch (e) {{
                statusEl.textContent = 'ошибка';
                resultEl.textContent = String(e);
              }}
            }});

            document.getElementById('a-history').addEventListener('click', async () => {{
              const productId = Number(document.getElementById('a-product').value);
              const locationId = Number(document.getElementById('a-location').value);
              const response = await fetch(`/api/v1/admin/products/movements?product_id=${{productId}}&location_id=${{locationId}}&movement_type=adjustment&page=1&page_size=20`, {{ headers: apiHeaders() }});
              const data = await readJson(response);
              resultEl.textContent = JSON.stringify({{ status: response.status, data }}, null, 2);
            }});

            loadCurrentStock();
          }}

          function renderSpecification() {{
            titleEl.textContent = 'Создание товара';
            const goods = state.products.filter((x) => x.item_type === 'product');
            bodyEl.innerHTML = `
              <div class="hint" style="margin-bottom:8px">Быстрое создание товарной позиции с базовыми реквизитами.</div>
              <div class="row">
                <label>Название товара<input id="spec-name" maxlength="100" placeholder="Например, Маска для волос" /></label>
                <label>Категория<input id="spec-category" value="Без категории" /></label>
              </div>
              <div class="row">
                <label>Ед. измерения<input id="spec-unit" value="Штуки" /></label>
                <label>Цена, ₽<input id="spec-price" type="number" min="0" value="0" /></label>
              </div>
              <label>Комментарий<textarea id="spec-comment" rows="3"></textarea></label>
              <div class="actions" style="margin-top:8px">
                <button class="btn primary" id="spec-save">Создать товар</button>
                <button class="btn" id="spec-list">Показать товары</button>
              </div>
              <pre id="spec-result" style="margin-top:8px">Ожидание...</pre>
            `;

            const resultEl = document.getElementById('spec-result');
            document.getElementById('spec-save').addEventListener('click', async () => {{
              const payload = {{
                name: document.getElementById('spec-name').value.trim(),
                category: document.getElementById('spec-category').value.trim() || 'Без категории',
                full_name: document.getElementById('spec-name').value.trim(),
                receipt_name: document.getElementById('spec-name').value.trim(),
                description: '',
                item_type: 'product',
                unit: document.getElementById('spec-unit').value.trim() || 'Штуки',
                is_promo: false,
                price_rub: Number(document.getElementById('spec-price').value || 0),
                cost_price_rub: 0,
                sku: '',
                barcode: '',
                critical_stock: 0,
                desired_stock: 0,
                stock: 0,
                track_inventory: true,
                comment: document.getElementById('spec-comment').value.trim(),
                images: [],
              }};
              if (!payload.name) {{
                resultEl.textContent = 'Ошибка: заполните название товара.';
                return;
              }}
              statusEl.textContent = 'сохранение';
              try {{
                const response = await fetch('/api/v1/admin/products', {{ method: 'POST', headers: apiHeaders(), body: JSON.stringify(payload) }});
                const data = await readJson(response);
                statusEl.textContent = response.ok ? 'сохранено' : 'ошибка';
                resultEl.textContent = JSON.stringify({{ status: response.status, data }}, null, 2);
                if (response.ok) await fetchProducts();
              }} catch (e) {{
                statusEl.textContent = 'ошибка';
                resultEl.textContent = String(e);
              }}
            }});

            document.getElementById('spec-list').addEventListener('click', async () => {{
              await fetchProducts();
              const rows = state.products.filter((x) => x.item_type === 'product').slice(0, 20).map((x) => `${{x.id}} — ${{x.name}}`).join('\n');
              resultEl.textContent = rows || 'Список товаров пуст.';
            }});
          }}

          function renderServiceCreate() {{
            titleEl.textContent = 'Создание услуги';
            const goods = state.products.filter((x) => x.item_type === 'product');
            bodyEl.innerHTML = `
              <div class="hint" style="margin-bottom:8px">Создание карточки услуги и привязка базового расходника (опционально).</div>
              <div class="row">
                <label>Название услуги<input id="svc-name" maxlength="100" placeholder="Например, Стрижка" /></label>
                <label>Цена, ₽<input id="svc-price" type="number" min="0" value="0" /></label>
              </div>
              <div class="row">
                <label>Длительность, минут<input id="svc-duration" type="number" min="5" value="60" /></label>
                <label>Базовый материал<select id="svc-material"><option value="">Не выбран</option>${{optionRows(goods, 'id', 'name')}}</select></label>
              </div>
              <label>Комментарий<textarea id="svc-comment" rows="3"></textarea></label>
              <div class="actions" style="margin-top:8px">
                <button class="btn primary" id="svc-save">Создать услугу</button>
              </div>
              <pre id="svc-result" style="margin-top:8px">Ожидание...</pre>
            `;

            const resultEl = document.getElementById('svc-result');
            document.getElementById('svc-save').addEventListener('click', async () => {{
              const name = document.getElementById('svc-name').value.trim();
              if (!name) {{
                resultEl.textContent = 'Ошибка: заполните название услуги.';
                return;
              }}
              statusEl.textContent = 'сохранение';
              const payload = {{
                name,
                category: 'Услуги',
                full_name: name,
                receipt_name: name,
                description: `Длительность: ${{Number(document.getElementById('svc-duration').value || 0)}} минут`,
                item_type: 'service',
                unit: 'Услуга',
                is_promo: false,
                price_rub: Number(document.getElementById('svc-price').value || 0),
                cost_price_rub: 0,
                sku: '',
                barcode: '',
                critical_stock: 0,
                desired_stock: 0,
                stock: 0,
                track_inventory: false,
                comment: document.getElementById('svc-comment').value.trim(),
                images: [],
              }};
              try {{
                const response = await fetch('/api/v1/admin/products', {{ method: 'POST', headers: apiHeaders(), body: JSON.stringify(payload) }});
                const data = await readJson(response);
                statusEl.textContent = response.ok ? 'сохранено' : 'ошибка';
                resultEl.textContent = JSON.stringify({{ status: response.status, data }}, null, 2);
                if (response.ok) await fetchProducts();
              }} catch (e) {{
                statusEl.textContent = 'ошибка';
                resultEl.textContent = String(e);
              }}
            }});
          }}

          function renderServiceTechCard() {{
            titleEl.textContent = 'Технологическая карточка услуги';
            const goods = state.products.filter((x) => x.item_type === 'product');
            bodyEl.innerHTML = `
              <div class="hint" style="margin-bottom:8px">Подтягиваем услуги/товары из блока «Товар» и дополняем нормой списания.</div>
              <div class="row">
                <label>Услуга<select id="s-service">${{optionRows(state.services, 'id', 'name')}}</select></label>
                <label>Расходник<select id="s-material">${{optionRows(goods, 'id', 'name')}}</select></label>
              </div>
              <div class="row">
                <label>Количество на услугу<input id="s-qty" type="number" min="1" value="1" /></label>
                <label>Ед. измерения<input id="s-unit" value="Штуки" /></label>
              </div>
              <label>Комментарий<textarea id="s-comment" rows="3"></textarea></label>
              <div class="actions" style="margin-top:8px">
                <button class="btn primary" id="s-save">Добавить в спецификацию</button>
                <button class="btn" id="s-refresh">Показать спецификацию услуги</button>
              </div>
              <pre id="s-result" style="margin-top:8px">Ожидание...</pre>
            `;

            const resultEl = document.getElementById('s-result');
            if (!state.services.length || !goods.length) {{
              resultEl.textContent = 'Нужны минимум 1 услуга и 1 товар.';
              return;
            }}

            async function showSpec() {{
              const serviceId = Number(document.getElementById('s-service').value);
              const response = await fetch(`/api/v1/admin/products/${{serviceId}}/specification`, {{ headers: apiHeaders() }});
              const data = await readJson(response);
              resultEl.textContent = JSON.stringify({{ status: response.status, data }}, null, 2);
            }}

            document.getElementById('s-save').addEventListener('click', async () => {{
              statusEl.textContent = 'сохранение';
              const serviceId = Number(document.getElementById('s-service').value);
              const payload = {{
                material_product_id: Number(document.getElementById('s-material').value),
                quantity: Number(document.getElementById('s-qty').value || 0),
                unit: document.getElementById('s-unit').value.trim() || 'Штуки',
                comment: document.getElementById('s-comment').value.trim(),
              }};
              try {{
                const response = await fetch(`/api/v1/admin/products/${{serviceId}}/specification`, {{ method: 'POST', headers: apiHeaders(), body: JSON.stringify(payload) }});
                const data = await readJson(response);
                statusEl.textContent = response.ok ? 'сохранено' : 'ошибка';
                resultEl.textContent = JSON.stringify({{ status: response.status, data }}, null, 2);
              }} catch (e) {{
                statusEl.textContent = 'ошибка';
                resultEl.textContent = String(e);
              }}
            }});

            document.getElementById('s-refresh').addEventListener('click', showSpec);
            showSpec();
          }}

          async function renderServiceInventory() {{
            titleEl.textContent = 'Инвентаризация товаров для оказания услуги';
            bodyEl.innerHTML = `
              <div class="hint" style="margin-bottom:8px">Сверка норм списания по техкартам с фактическими остатками материалов.</div>
              <pre id="service-inventory-result">Загрузка...</pre>
            `;
            const resultEl = document.getElementById('service-inventory-result');
            const goods = state.products.filter((x) => x.item_type === 'product');
            const lines = goods.map((g) => `${{g.name}}: остаток ${{g.stock ?? 0}} ${{g.unit || ''}}`).join('\n');
            resultEl.textContent = lines || 'Нет товаров для инвентаризации.';
          }}

          async function renderServiceMaterials() {{
            titleEl.textContent = 'Учет наличия материалов для оказания услуги';
            bodyEl.innerHTML = `
              <div class="hint" style="margin-bottom:8px">Контроль наличия материалов, необходимых для выполнения услуг.</div>
              <pre id="service-materials-result">Загрузка...</pre>
            `;
            const resultEl = document.getElementById('service-materials-result');
            const goods = state.products.filter((x) => x.item_type === 'product');
            const deficit = goods.filter((g) => Number(g.stock || 0) <= Number(g.critical_stock || 0));
            resultEl.textContent = deficit.length
              ? deficit.map((g) => `${{g.name}}: остаток ${{g.stock || 0}}, критический минимум ${{g.critical_stock || 0}}`).join('\n')
              : 'Критических позиций не найдено.';
          }}

          const screenModes = {{
            add: 'goods',
            inventory: 'goods',
            audit: 'goods',
            spec: 'goods',
            'service-create': 'services',
            'service-tech-card': 'services',
            'service-inventory': 'services',
            'service-materials': 'services',
          }};
          const renderers = {{
            add: renderAddProduct,
            inventory: renderInventory,
            audit: renderInventoryAudit,
            spec: renderAddProduct,
            'service-create': renderServiceCreate,
            'service-tech-card': renderServiceTechCard,
            'service-inventory': renderServiceInventory,
            'service-materials': renderServiceMaterials,
          }};

          function setMode(mode) {{
            currentMode = mode;
            modeHintEl.textContent = mode === 'services' ? 'услуги' : 'товары';
            document.querySelectorAll('[data-products-mode]').forEach((b) => {{
              b.classList.toggle('primary', b.getAttribute('data-products-mode') === mode);
            }});
            document.querySelectorAll('[data-products-screen]').forEach((b) => {{
              const screen = b.getAttribute('data-products-screen');
              const btnMode = screenModes[screen] || 'goods';
              b.style.display = btnMode === mode ? '' : 'none';
            }});
          }}

          function activateScreen(screen) {{
            setMode(screenModes[screen] || 'goods');
            document.querySelectorAll('[data-products-screen]').forEach((b) => {{
              b.classList.toggle('primary', b.getAttribute('data-products-screen') === screen);
            }});
            renderers[screen]();
            if (window.location.hash !== `#products-${{screen}}`) {{
              window.history.replaceState(null, '', `#products-${{screen}}`);
            }}
            document.querySelectorAll('.menu-subitem').forEach((item) => {{
              item.classList.toggle('active', item.getAttribute('href').endsWith(`#products-${{screen}}`));
            }});
          }}

          document.querySelectorAll('[data-products-screen]').forEach((b) => {{
            b.addEventListener('click', () => activateScreen(b.getAttribute('data-products-screen')));
          }});

          document.querySelectorAll('[data-products-mode]').forEach((b) => {{
            b.addEventListener('click', () => {{
              const mode = b.getAttribute('data-products-mode') || 'goods';
              setMode(mode);
              const fallbackScreen = mode === 'services' ? 'service-create' : 'add';
              activateScreen(fallbackScreen);
            }});
          }});

          (async () => {{
            statusEl.textContent = 'загрузка';
            try {{
              await Promise.all([fetchProducts(), fetchLocations()]);
              statusEl.textContent = 'готово';
              const hashScreen = (window.location.hash || '').replace('#products-', '');
              const initialScreen = renderers[hashScreen] ? hashScreen : 'add';
              activateScreen(initialScreen);
            }} catch (e) {{
              statusEl.textContent = 'ошибка';
              bodyEl.textContent = `Ошибка загрузки: ${{e}}`;
            }}
          }})();
        }})();
      </script>
    """


def _section_body(section: dict[str, str]) -> str:
    if section["key"] == "products":
        return _products_section_body(section)

    actions = SECTION_ACTIONS.get(section["key"], [
        {"label": "Открыть", "type": "quick", "value": section["endpoint"]},
        {"label": "Обновить", "type": "quick", "value": section["endpoint"]},
        {"label": "Настроить", "type": "drawer", "value": f"Параметры раздела «{section['title']}»"},
    ])

    button_parts: list[str] = []
    for i, action in enumerate(actions):
        css = "primary" if i == 0 else ""
        action_json = json.dumps(action, ensure_ascii=False).replace('\"', '&quot;')
        button_parts.append(
            f"<button class=\"btn {css}\" data-section-action=\"{action_json}\">{action['label']}</button>"
        )
    buttons = "".join(button_parts)

    return f"""
      <section class=\"header\">
        <div>
          <h1>{section['title']}</h1>
          <div class=\"hint\">Данные раздела подключены к API: {section['endpoint']}</div>
        </div>
        <div class=\"actions\">{buttons}</div>
      </section>

      <section class=\"grid\" style=\"margin-bottom:10px\">
        <article class=\"panel\">
          <div class=\"panel-head\"><span>Экраны и вкладки</span><span class=\"hint\">рабочие</span></div>
          <div class=\"panel-body\" id=\"section-tabs\">Загрузка...</div>
        </article>
        <article class=\"panel\">
          <div class=\"panel-head\"><span>Фильтры и массовые действия</span><span class=\"hint\">активно</span></div>
          <div class=\"panel-body\">Статус, период, сотрудник, филиал, теги, источник. Массово: подтвердить, отменить, назначить, экспорт.</div>
        </article>
        <article class=\"panel\">
          <div class=\"panel-head\"><span>Модульность</span><span class=\"hint\">on / off</span></div>
          <div class=\"panel-body\">Управление модулями в «Быстрые настройки»: услуги, товары, склад, сертификаты, рефералы, маркетинг.</div>
        </article>
      </section>

      <section class=\"panel\">
        <div class=\"panel-head\"><span>Текущие данные</span><span class=\"hint\" id=\"section-status\">ожидание</span></div>
        <div class=\"panel-body table-wrap\">
          <table>
            <thead><tr id=\"table-head\"></tr></thead>
            <tbody id=\"table-body\"><tr><td>Загрузка...</td></tr></tbody>
          </table>
        </div>
      </section>

      <script>
        (function() {{
          const section = {json.dumps(section, ensure_ascii=False)};

          const baseTabs = {{
            dashboard: ['Обзор', 'Оперативная лента'],
            appointments: ['Календарь', 'Список записей', 'Карточка записи', 'Настройки записей'],
            operations: ['Продажи', 'Платежи', 'Возвраты', 'Документы', 'Служебные журналы'],
            clients: ['Список клиентов', 'Карточка клиента'],
            products: ['Каталог', 'Карточка товара', 'Карточка услуги'],
            employees: ['Список', 'Карточка сотрудника'],
            messages: ['Входящие', 'Диалог'],
            communications: ['Рассылки', 'Транзакционные уведомления', 'Согласия'],
            campaigns: ['Список кампаний', 'Карточка кампании'],
            analytics: ['Дашборды', 'Конструктор отчетов', 'КПЭ-центр'],
            traffic: ['Каналы', 'Кампании', 'Конверсии', 'Стоимость', 'ROI'],
            referral_programs: ['Правила', 'Коды и ссылки', 'Приглашения', 'Начисления', 'Выплаты', 'Антифрод'],
            certificates: ['Данные', 'Операции', 'Клиент', 'История'],
            feedback: ['Отзывы', 'Оценки NPS/CSAT', 'Причины отмен', 'Баг-репорты'],
            news: ['Лента', 'Черновики', 'Публикации'],
            security: ['Роли и права', 'Журнал аудита', 'Сессии и устройства', '2FA/политики паролей'],
            system_settings: ['Организация', 'Модули и функции', 'Интерфейс и бренд', 'Интеграции', 'Импорт/экспорт/миграции'],
          }};

          const tabs = baseTabs[section.key] || ['Список'];
          document.getElementById('section-tabs').innerHTML = tabs.map((t) => `<span class=\"badge\" style=\"margin-right:4px\">${{t}}</span>`).join('');

          document.querySelectorAll('[data-section-action]').forEach((el) => {{
            const action = JSON.parse(el.getAttribute('data-section-action'));
            el.addEventListener('click', async () => {{
              if (section.key === 'appointments' && action.label === '+ Запись') {{
                await открытьМастерЗаписи();
                return;
              }}
              if (action.type === 'drawer') {{
                открытьDrawer(action.label, `<div class=\"hint\">${{action.value}}</div>`);
                return;
              }}
              try {{
                const res = await fetch(action.value, {{ headers: (window.заголовки ? window.заголовки() : {{ 'Content-Type': 'application/json' }}) }});
                const text = await res.text();
                let parsed = text;
                try {{ parsed = JSON.parse(text); }} catch (_e) {{}}
                открытьDrawer(action.label, `<pre>${{JSON.stringify({{статус: res.status, данные: parsed}}, null, 2)}}</pre>`);
              }} catch (e) {{
                открытьDrawer(action.label, `<pre>Ошибка: ${{e}}</pre>`);
              }}
            }});
          }});

          async function loadData() {{
            const statusEl = document.getElementById('section-status');
            statusEl.textContent = 'загрузка';
            try {{
              const response = await fetch(section.endpoint, {{ headers: (window.заголовки ? window.заголовки() : {{ 'Content-Type': 'application/json' }}) }});
              const text = await response.text();
              let data = text;
              try {{ data = JSON.parse(text); }} catch (_e) {{}}

              if (!response.ok) {{
                statusEl.textContent = `ошибка ${{response.status}}`;
                document.getElementById('table-head').innerHTML = '<th>Статус</th><th>Детали</th>';
                document.getElementById('table-body').innerHTML = `<tr><td>${{response.status}}</td><td><pre>${{JSON.stringify(data, null, 2)}}</pre></td></tr>`;
                return;
              }}

              statusEl.textContent = 'подключено';
              const rows = Array.isArray(data) ? data : (Array.isArray(data.items) ? data.items : [data]);
              if (!rows.length) {{
                document.getElementById('table-head').innerHTML = '<th>Результат</th>';
                document.getElementById('table-body').innerHTML = '<tr><td>Нет данных</td></tr>';
                return;
              }}
              const keys = Object.keys(rows[0]).slice(0, 6);
              document.getElementById('table-head').innerHTML = keys.map((k) => `<th>${{k}}</th>`).join('');
              document.getElementById('table-body').innerHTML = rows.slice(0, 15).map((row) => `<tr>${{keys.map((k) => `<td>${{typeof row[k] === 'object' ? JSON.stringify(row[k]) : row[k] ?? ''}}</td>`).join('')}}</tr>`).join('');
            }} catch (e) {{
              statusEl.textContent = 'ошибка';
              document.getElementById('table-head').innerHTML = '<th>Ошибка</th>';
              document.getElementById('table-body').innerHTML = `<tr><td>${{e}}</td></tr>`;
            }}
          }}

          loadData();
        }})();
      </script>
    """


def _render_page(section: dict[str, str]) -> HTMLResponse:
    return HTMLResponse(
        _BASE_HTML.format(
            title=f"UDS CRM — {section['title']}",
            menu_html=_menu(section["key"]),
            body=_section_body(section),
            quick_actions=json.dumps(QUICK_ACTIONS, ensure_ascii=False),
            section=json.dumps(section, ensure_ascii=False),
        )
    )


@router.get("/admin", include_in_schema=False)
def admin_root() -> RedirectResponse:
    return RedirectResponse(url="/admin/dashboard", status_code=307)


@router.get("/admin/state", include_in_schema=False)
def admin_state() -> dict:
    return {
        "ui": "ok",
        "routes": [f"/admin/{s['key']}" for s in SECTIONS],
        "sections": SECTIONS,
        "quick_actions": QUICK_ACTIONS,
        "meta": json.dumps({"version": 2, "lang": "ru"}),
    }


def _admin_section(section_key: str) -> HTMLResponse:
    section = next((s for s in SECTIONS if s["key"] == section_key), SECTIONS[0])
    return _render_page(section)


for _section in SECTIONS:
    def _build_endpoint(key: str):
        def _endpoint() -> HTMLResponse:
            return _admin_section(key)

        return _endpoint

    router.add_api_route(
        f"/admin/{_section['key']}",
        _build_endpoint(_section["key"]),
        methods=["GET"],
        response_class=HTMLResponse,
        include_in_schema=False,
    )
