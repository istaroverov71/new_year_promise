# Генератор обещаний 🎄

Telegram-бот [@newyear_generator_bot](https://t.me/newyear_generator_bot): крутит два барабана —
«Я обещаю (кому), что в 2027 я (что)» — и делает из результата мем с выбранной фоткой.

## Что где лежит

- `data/who.txt`, `data/what.txt` — фразы, по одной на строку. Можно править прямо на GitHub.
- `photos/` — фото для мемов (jpg/png). Порядок в боте — по алфавиту имён файлов, так что удобно называть `01.jpg`, `02.jpg`…
- `fonts/Rubik.ttf` — шрифт надписи (свободная лицензия OFL).
- `bot/` — код бота: `handlers.py` — что бот отвечает, `meme.py` — рисование мема, `promises.py` — сборка фразы.
- `api/` — точки входа для хостинга Vercel.

## Запуск на Vercel (бесплатно)

1. Зайди на [vercel.com](https://vercel.com) → Sign up → Continue with GitHub.
2. Add New → Project → выбери репозиторий `new_year_promise` → Import.
3. Перед нажатием Deploy раскрой Environment Variables и добавь:
   - `BOT_TOKEN` — токен от BotFather;
   - `WEBHOOK_SECRET` — придумай любую длинную строку из латинских букв и цифр (например `snegovik2027tralala`).
4. Нажми Deploy и дождись зелёного статуса. Vercel покажет адрес вида `https://new-year-promise.vercel.app`.
5. Открой в браузере `https://<твой-адрес>/api/setup`.
   Должно появиться `"ok": true`.
6. Напиши боту `/start`.

После этого каждое изменение в репозитории (новые фразы, фотки) Vercel выкатывает сам за минуту.

## Статистика

Владелец (Telegram ID в переменной `ADMIN_ID`) может написать боту `/stats` и увидеть,
сколько людей пользуется ботом, сколько прокруток и мемов, какие фото популярнее.
Для этого в Vercel нужна база: проект → Storage → Create Database → Upstash for Redis (Free)
→ подключить к проекту. Без базы бот работает как обычно, просто без статистики.

## Проверка на своём компьютере

```
pip install -r requirements.txt
BOT_TOKEN=... python run_local.py
```
