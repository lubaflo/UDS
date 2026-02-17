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
    {"key": "products", "title": "Товары и услуги", "endpoint": "/api/v1/admin/products", "icon": "🧾", "module": "products"},
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

      const optsRes = await fetch('/api/v1/app/appointments/booking-options', {{ headers: заголовки() }});
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
        const res = await fetch(url, {{ headers: заголовки() }});
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
            headers: заголовки(),
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
          const init = {{ method, headers: заголовки() }};
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
        items.append(
            f"""
            <a class=\"menu-item {css}\" href=\"/admin/{section['key']}\" data-module=\"{section['module']}\">
              <span class=\"left\"><span class=\"icon\">{section['icon']}</span>{section['title']}</span>
            </a>
            """
        )
    return "\n".join(items)


def _section_body(section: dict[str, str]) -> str:
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
                const res = await fetch(action.value, {{ headers: заголовки() }});
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
              const response = await fetch(section.endpoint, {{ headers: заголовки() }});
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
