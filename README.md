# UDS CRM Backend (Telegram Mini App)

Готовый backend для CRM-панели в стиле скриншотов UDS: клиенты, операции, товары/услуги, рассылки, сертификаты, обратная связь, источники трафика и дашборд.

## Стек
- Python 3.12
- FastAPI + Pydantic v2
- SQLAlchemy 2.x
- SQLite (файл БД в `./data`)
- Docker

## Структура
- `backend/app/main.py` — точка входа FastAPI
- `backend/app/api/v1/` — роуты API
- `backend/app/models/` — модели БД
- `backend/app/schemas/` — pydantic-схемы
- `backend/app/services/` — бизнес-логика
- `data/` — SQLite база и файлы данных

## Основные API-разделы
- `POST /api/v1/auth/telegram/verify` — Telegram WebApp авторизация (`initData` hash verification)
- `GET /api/v1/admin/dashboard/summary` — статистика блока "Сегодня"
- `GET /api/v1/admin/dashboard/full` — полный payload дашборда (алерты, промо-карточки, ссылки секций, включая `promotion` с вариантами (`certificate_types`, `certificates`, `referral_programs`, `promotion_forecast`))
- `GET/POST /api/v1/admin/operations` — операции
- `GET/POST/PUT /api/v1/admin/clients` — клиентская база
- `GET/POST/PUT /api/v1/admin/products` — товары и услуги (тип карточки: товар/услуга)
- `GET/POST /api/v1/admin/products/locations` — склады/торговые точки
- `GET /api/v1/admin/products/{product_id}/stock` — остатки по складам/точкам
- `GET /api/v1/admin/products/movements`, `POST /api/v1/admin/products/{product_id}/movements` — движение товаров
- `GET/POST/PUT /api/v1/admin/campaigns` — рассылки
- `GET/POST/PUT /api/v1/admin/news` — новости компании (лента публикаций)
- `POST /api/v1/admin/news/track` — трекинг событий по новости (view/transition/click/add_to_cart/booking/purchase)
- `GET /api/v1/admin/news/{news_post_id}/stats` — статистика по конкретной новости
- `GET/POST /api/v1/admin/communications` — раздел рассылок (активные/архив, создание кампаний)
- `POST /api/v1/admin/communications/{campaign_id}/launch` — запуск рассылки по базе с согласиями
- `GET /api/v1/admin/communications/{campaign_id}/stats` — open/click/conversion статистика кампании
- `POST /api/v1/admin/communications/track` — трекинг событий (open/click/conversion)
- `GET/PUT /api/v1/admin/communications/reminders/rules` — автонапоминания о записи (1ч/4ч/1д/1нед)
- `POST /api/v1/admin/communications/appointments` — создание записи клиента
- `GET/POST /api/v1/admin/appointments` — раздел записи для администратора (список с фильтрами и ручное создание)
- `PATCH /api/v1/admin/appointments/{appointment_id}/status` — смена статуса записи (scheduled/cancelled/completed)
- `POST /api/v1/app/appointments/book` — онлайн-запись клиента из приложения (Telegram WebApp initData)
- `POST /api/v1/admin/communications/reminders/run` — обработчик автоматических напоминаний
- `POST /api/v1/feedback/app/rating` — клиент из Telegram Mini App ставит оценку товару/услуге
- `POST /api/v1/feedback/app/message` — клиент пишет администратору, диалог сохраняется по клиенту
- `POST /api/v1/admin/communications/workflows` — старт мастера рассылки (Шаг 1)
- `PUT /api/v1/admin/communications/workflows/{campaign_id}/step-1-audience` — Шаг 1: аудитория
- `PUT /api/v1/admin/communications/workflows/{campaign_id}/step-2-content` — Шаг 2: контент/цепочка
- `PUT /api/v1/admin/communications/workflows/{campaign_id}/step-3-schedule` — Шаг 3: расписание
- `GET /api/v1/admin/communications/workflows/{campaign_id}/step-4-confirmation` — Шаг 4: подтверждение
- `POST /api/v1/admin/communications/workflows/{campaign_id}/step-4-confirm` — Шаг 4: запуск
- `GET /api/v1/admin/communications/workflows/{campaign_id}/step-5-stats` — Шаг 5: статистика
- `GET/POST /api/v1/admin/feedback` — обратная связь (оценки/жалобы/предложения по товару или услуге)
- `GET/POST /api/v1/admin/certificates` — сертификаты
- `GET /api/v1/admin/referral-programs` — варианты раздела реферальных программ (вложенный пункт «Продвижение»)
- `GET /api/v1/admin/referral-programs/config` — текущая конфигурация реферальной программы (до 6 поколений)
- `PUT /api/v1/admin/referral-programs/config` — обновление глубины поколений, % начислений и типа награды (баллы/деньги)
- `GET /api/v1/admin/referral-programs/client-info` — клиентское представление начислений по очередям рекомендаций
- `GET/POST /api/v1/admin/traffic-channels` — источники трафика
- `GET/PUT /api/v1/admin/system-settings` — системные настройки (экран "Системные настройки")
- `GET/POST/PUT/DELETE /api/v1/admin/employees` — сотрудники: карточки, категории, архивация
- `GET/POST/DELETE /api/v1/admin/employees/categories` — категории сотрудников
- `GET/POST /api/v1/admin/employees/{employee_id}/timesheet` — табель (часы/сделка)
- `GET/POST /api/v1/admin/employees/{employee_id}/schedule` — планирование рабочего времени
- `POST /api/v1/admin/employees/payroll/run` — расчёт начислений по системе оплаты (повременная/сдельная)
- `GET /api/v1/admin/employees/{employee_id}/history` — история изменений по сотруднику
- `GET /api/v1/admin/employees/export`, `GET /api/v1/admin/employees/export.csv` — выгрузка начислений с фильтрами по ФИО и периоду
- `GET /api/v1/admin/analytics/customers` — вкладка "Клиенты" в статистике
- `GET /api/v1/admin/analytics/operations` — вкладка "Операции" в статистике
- `GET /api/v1/admin/analytics/finance` — блок финансовой отчётности (доходы/расходы, кэшфлоу по периодам)
- `GET /api/v1/admin/analytics/ratings` — вкладка "Рейтинг" (по оплатам / рекомендациям)
- `GET /api/v1/admin/analytics/levels` — вкладка "Клиенты по уровням"
- `GET /api/v1/admin/analytics/page-go` — вкладка "Посещения UDS APP" (просмотры / посетители)
- `GET /api/v1/admin/analytics/marketing` — маркетинговая аналитика: каналы, воронка, сегменты, CRM-маркетинг, прогноз
- `GET /api/v1/admin/analytics/control-tower` — единый русскоязычный центр управления (продажи + запись + склад + приоритетные действия).
- `GET /api/v1/admin/analytics/control-tower/processes` — 5–7 эталонных процессов с KPI/SLA, baseline/target и триггерами автооркестрации.
- `PUT /api/v1/admin/analytics/control-tower/processes/{process_code}` — управление baseline/target и включением процесса.
- `GET/PUT /api/v1/admin/analytics/control-tower/policy` — policy-слой: частота касаний, приоритет каналов, контроль качества базы.
- `GET/PUT /api/v1/admin/analytics/control-tower/onboarding-goal` — обязательный мастер цели на 90 дней при первом запуске.
- `GET /api/v1/admin/analytics/control-tower/outcomes` — каталог user outcomes + event-storming шаги по ключевым процессам.
- `GET /api/v1/admin/analytics/control-tower/presets/{vertical}` — готовые наборы KPI и настроек (salon/clinic/retail/fitness).
- `GET /api/v1/admin/analytics/control-tower/endpoint-specs` — спецификации крупных endpoint (бизнес-правила, исключения, примеры данных).
- `POST /api/v1/admin/analytics/promotion-forecast` — прогноз притока клиентов и расчет безубыточности акций

## Локальный запуск (PyCharm / terminal)
1. Скопируйте окружение:
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Установите зависимости:
   ```bash
   cd backend
   python -m pip install -e .
   ```
3. Запустите сервер:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Документация:
   - Swagger: `http://localhost:8000/docs`
   - OpenAPI: `http://localhost:8000/openapi.json`

## Docker
Сборка:
```bash
docker build -t uds-crm-backend .
```

Запуск:
```bash
docker run --rm -p 8000:8000 --env-file backend/.env -v $(pwd)/data:/app/data uds-crm-backend
```

Или через Compose:
```bash
docker compose up --build
```

## Amvera / любой generic Docker hosting
Задайте переменные окружения:
- `TELEGRAM_BOT_TOKEN`
- `JWT_SECRET`
- `DATABASE_URL` (по умолчанию `sqlite:///../data/app.db`)
- `CORS_ALLOW_ORIGINS`

Важно смонтировать persistent volume для `/app/data`, чтобы БД не терялась.


## Согласия клиентов для рассылок
- `consent_personal_data` — согласие на обработку ПДн.
- `consent_marketing` — согласие на маркетинговые рассылки.
- Канальные согласия: `consent_sms`, `consent_app_push`, `consent_email`.
- Рассылка отправляется только клиентам, у которых есть `consent_personal_data` + нужные маркетинговые/канальные согласия.


## Диалоги и обратная связь
- Входящие сообщения клиента и ответы админа сохраняются в `messages` на всю историю клиента.
- Привязка клиента выполняется по `tg_id` (Telegram ID).
- При первом сообщении/оценке из Mini App клиент автоматически создаётся в базе и дальше переиспользуется.
- Для исходящих сообщений админа поддержаны каналы: `telegram`, `sms`, `email`, `vk`, `instagram`, `facebook`, `max`.
- В карточке клиента добавлены контактные поля для VK/Instagram/Facebook/MAX.
- `GET /api/v1/admin/dialogues/messages` — реестр сообщений с фильтрами по дате/периоду, ФИО, статусу доставки и каналу.
- `POST /api/v1/admin/dialogues/send-group` — групповая отправка сообщений по списку клиентов (например, VIP или постоянные клиенты).
