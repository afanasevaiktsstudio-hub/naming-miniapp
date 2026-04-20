# Deploy: Telegram Mini App + Bot

Два независимых деплоя:

1. Frontend (Mini App) — Cloudflare Pages (бесплатно, HTTPS).
2. Backend (FastAPI + aiogram polling) — Railway (Docker, ~$5/мес).

После деплоев связываем их переменными `VITE_API_BASE_URL`, `MINIAPP_URL`, `API_CORS_ORIGINS`.

## 1. Backend на Railway

1. Зайти на [railway.com](https://railway.com), создать проект → `Deploy from GitHub` (или Railway CLI: `railway up`).
2. В настройках сервиса убедиться, что обнаружен Dockerfile (`railway.json` уже лежит в репе).
3. Во вкладке `Variables` добавить переменные из `.env` (все поля из `.env.example`):
   - `BOT_TOKEN`
   - `GIGACHAT_CLIENT_ID`, `GIGACHAT_AUTHORIZATION_KEY`, `GIGACHAT_SCOPE`
   - `GIGACHAT_BASE_URL`, `GIGACHAT_AUTH_URL`, `GIGACHAT_VERIFY_SSL=true`
   - `TEXT_MODEL=GigaChat-2-Pro`, `TEXT_PROVIDER=gigachat`
   - `SQLITE_PATH=/data/bot.db` (см. ниже про persistent volume)
   - `MAX_INPUT_LENGTH=120`, `DAILY_TEXT_LIMIT=20`
   - `API_HOST=0.0.0.0`
   - `MINIAPP_URL=https://<pages-subdomain>.pages.dev` — заполнить после деплоя фронта
   - `API_CORS_ORIGINS=https://<pages-subdomain>.pages.dev`
4. В `Settings → Volumes` примонтировать том к `/data` → SQLite переживёт деплои.
5. В `Settings → Networking` включить публичный URL. Railway назначит домен вида `https://<service>.up.railway.app`.
6. Проверить healthcheck: `GET https://<service>.up.railway.app/api/health` → `{"status":"ok"}`.

## 2. Frontend на Cloudflare Pages

1. Создать проект на [Cloudflare Pages](https://pages.cloudflare.com), подключить репозиторий.
2. Настройки сборки:
   - Framework preset: `None (custom)`.
   - Root directory: `web`.
   - Build command: `npm install && npm run build`.
   - Output dir: `dist`.
   - Node version: `20` (env `NODE_VERSION=20`).
3. Environment variables:
   - `VITE_API_BASE_URL=https://<railway-service>.up.railway.app`
4. После первого билда получишь URL вида `https://<project>.pages.dev`.
5. (Опционально) привязать собственный домен.

### Альтернатива: Vercel
- Root `web`, build `npm run build`, output `dist`, env `VITE_API_BASE_URL=…`.

## 3. Связать Mini App с ботом

1. В Railway-переменных у backend обновить:
   - `MINIAPP_URL=https://<project>.pages.dev`
   - `API_CORS_ORIGINS=https://<project>.pages.dev`
   - Перезапустить сервис.
2. `/start` теперь отдаёт кнопку «Открыть мини-приложение» и меню-кнопку.
3. В BotFather:
   - `/setmenubutton` → выбрать бота → задать URL `https://<project>.pages.dev`, заголовок «Открыть».
   - `/setdomain` → указать домен фронта (нужно для корректной работы WebApp у некоторых клиентов).

## 4. Проверка подписи initData

Сервер жёстко проверяет `X-Telegram-Init-Data` по HMAC `BOT_TOKEN`. Поэтому **одним и тем же `BOT_TOKEN`** должен пользоваться и бот, и API. Не разводить.

## 5. Локальный запуск

Backend:

```bash
source .venv/bin/activate
# .env с DEBUG_USER_ID=<твой tg id>, API_CORS_ORIGINS=http://localhost:5173
python -m app.main
```

Frontend:

```bash
cd web
cp .env.example .env.local   # при необходимости
npm install
npm run dev  # http://localhost:5173, /api проксируется на :8080
```

В dev без Telegram фронт шлёт `X-Debug-User: 1`, backend пускает `DEBUG_USER_ID` как «фейк-пользователя».
