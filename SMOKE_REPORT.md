# Smoke report — Telegram Mini App

Дата: 2026-04-20

Кодовая база: `main`, коммит-хеш — подставить перед релизом.

## 1. Локальный e2e (закрыт)

Оборудование: macOS, Python 3.13, Node 20.

### 1.1 Backend API (TestClient)

Команда:

```bash
source .venv/bin/activate
python -m pytest -q
```

Результат (снимок):

```
.................                                                        [100%]
17 passed in 1.16s
```

Покрытые сценарии:
- `GET /api/health` → 200.
- Без `X-Telegram-Init-Data` → 401.
- Валидный `initData` → получение пустой сессии, генерация 5 вариантов, выбор индекса 2, проверка `selected_index == 2`.
- Лимит `DAILY_TEXT_LIMIT=3` → 3 успешных запроса, 4-й → `429 Too Many Requests`.
- `X-Debug-User: 1` + `DEBUG_USER_ID>0` → 200.
- `/api/select` без предварительных вариантов → 404.
- HMAC-верификация initData: happy-path, битая подпись, протухший `auth_date`, пустой заголовок.

### 1.2 Frontend build

```bash
cd web && npm run build
```

```
vite v5.4.21 building for production...
✓ 396 modules transformed.
dist/index.html                   0.61 kB │ gzip:  0.40 kB
dist/assets/index-B0dBQXkT.css    5.14 kB │ gzip:  1.61 kB
dist/assets/index-5yaAt3NM.js   267.27 kB │ gzip: 87.20 kB
✓ built in 667ms
```

TypeScript strict-build — без ошибок.

### 1.3 Ручной прогон UI (dev)

- `npm run dev` → `http://localhost:5173`, `/api/*` проксируется на `http://127.0.0.1:8080`.
- В dev-режиме используется `X-Debug-User: 1`, `DEBUG_USER_ID` задан в `.env`.
- Экраны Welcome → Input → Loading → Variants → Selected проходятся без ошибок, анимации на framer-motion работают.

## 2. Прод-e2e (чеклист на выполнение после деплоя)

Выполнить после публикации `MINIAPP_URL` и `API` на Railway (см. [DEPLOY.md](DEPLOY.md)).

Окружение:
- Backend: `https://<railway-service>.up.railway.app`.
- Frontend: `https://<project>.pages.dev`.
- Клиент: Telegram iOS/Android/Desktop, аккаунт тестера.

### Чеклист

- [ ] `GET https://<railway>/api/health` → `{"status":"ok"}`.
- [ ] `/start` в боте → приходит сообщение с двумя кнопками (web_app + канал).
- [ ] Меню-кнопка бота (в поле ввода слева) открывает Mini App.
- [ ] Welcome отображает бренд-заголовок, «Аналитикада · Нейминг», пилюлю ФЗ-53, кнопку «Начать».
- [ ] Input принимает `Riverside`, показывает счётчик символов, MainButton Telegram активен.
- [ ] Loading: `skeleton` + ротирующий спиннер + текст «5–10 сек».
- [ ] Variants: 5 карточек появляются по стаггеру (opacity + translate), tap по карточке даёт haptic.
- [ ] Selected: показывает выбранный вариант крупно, кнопки «Подписаться» и «Сгенерировать ещё».
- [ ] Регенерация возвращает на Input, прошлая сессия сохранена (source_name в pill).
- [ ] Повтор до исчерпания `DAILY_TEXT_LIMIT` → 4-й раз показывает «Лимит на сегодня исчерпан».
- [ ] Рестарт контейнера на Railway: сессия и лимит в `/data/bot.db` сохраняются (volume).
- [ ] Проверка безопасности: запрос без `X-Telegram-Init-Data` → 401; подделанный hash → 401.
- [ ] CORS: `Access-Control-Allow-Origin` = домен Pages; другие домены получают ошибку preflight.

## 3. Артефакты

Собрать и приложить:
- Скриншоты каждого экрана Mini App (Welcome/Input/Loading/Variants/Selected).
- Скриншот `/start` с кнопкой web_app.
- Вывод `curl -i https://<railway>/api/health` (ожидается 200).
- Скриншот страницы Railway: healthcheck `/api/health` — зелёный.
- Скриншот Cloudflare Pages: последний деплой — `Success`.

## 4. Рисковые зоны

- `GIGACHAT_VERIFY_SSL=false` локально (корп. сертификат). В Railway по умолчанию `true`; если не работает — включить `false` и зафиксировать в репорте.
- Персистентность: без volume в Railway SQLite будет обнуляться при редеплое. Перед релизом убедиться, что `/data` смонтирован и `SQLITE_PATH=/data/bot.db`.
- Mini App требует публичного HTTPS. Локальный `localhost` в Telegram WebView не откроется — тестируем только через задеплоенный URL.
