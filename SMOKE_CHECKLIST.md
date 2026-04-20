# Smoke Checklist — Mini App flow

## Локальный dev

- [ ] `.env` заполнен: `BOT_TOKEN`, `GIGACHAT_*`, `MINIAPP_URL`, `API_CORS_ORIGINS`, `DEBUG_USER_ID`
- [ ] `python -m app.main` поднимает backend (`/api/health` → 200) и бота (polling)
- [ ] `cd web && npm run dev` стартует Mini App на :5173 с проксированием `/api`
- [ ] В браузере (dev) все 5 экранов проходятся, анимации работают
- [ ] `pytest -q` зелёный (17 тестов)

## Прод (после deploy)

- [ ] `/start` отвечает сообщением с кнопкой «Открыть мини-приложение»
- [ ] Меню-кнопка в боте открывает Mini App
- [ ] Welcome → Input → Loading → Variants → Selected проходятся
- [ ] Генерация 5 вариантов занимает ≤ 15 сек
- [ ] Клик по карточке сохраняет выбор (виден `selected_index` в session)
- [ ] «Хочу ещё варианты» возвращает на Input и повторно генерирует
- [ ] После `DAILY_TEXT_LIMIT` → 429 / «Лимит на сегодня исчерпан»
- [ ] Рестарт сервиса в Railway — сессия и лимит восстанавливаются из SQLite
- [ ] Запрос к API без `X-Telegram-Init-Data` → 401
- [ ] CORS: запрос с чужого домена отклоняется браузером
