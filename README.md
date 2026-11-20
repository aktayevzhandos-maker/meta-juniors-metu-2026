# AIID — интеллектуальный подбор экспертов

Meta Juniors · AI in Engineering 2026. Локальное fullstack-приложение: React/TypeScript/Vite/Tailwind, Django и PostgreSQL в Docker Compose.

**Задача:** вместо поиска через личные контакты пользователь вводит запрос и получает топ-3 экспертов с проверяемыми причинами выбора. Пользователь — координатор Альянса. Сейчас подбор занимает дни; целевой сценарий — один текстовый запрос и объяснимый результат до 30 секунд.

## Запуск

Docker Compose: Django/Python 3.12 + PostgreSQL 16 (`postgres:16-alpine`). Из корня репозитория:

```powershell
Copy-Item .env.example .env # только на новом ноутбуке; задайте свои локальные пароли
# На подготовленном ноутбуке .env уже создана, не перезаписывайте её.
npm.cmd ci --prefix frontend
npm.cmd run build --prefix frontend
docker compose up -d --build --wait
```

Первый запуск автоматически применяет миграции и загружает CSV, если реестр пуст. Данные сохраняются в именованном PostgreSQL volume. Интерфейс: `http://127.0.0.1:5173`. Проверка API: `GET http://127.0.0.1:8000/api/v1/health/` должен показать `database: postgresql` и 120 профилей. Для офлайн-запуска после первой сборки: `docker compose up -d --no-build --pull never --wait`. На новом ноутбуке заранее подготовьте образы `python:3.12-slim`, `postgres:16-alpine` и соберите backend; runtime не требует интернета. PostgreSQL находится во внутренней сети и не публикует порт на хост; API публикуется только на localhost через отдельную bridge-сеть.

Повторный импорт: `docker compose exec -T backend python manage.py import_experts /app/data/experts.csv`. Существующие ID обновляются; `--replace` явно заменяет реестр после валидации. После изменения CSV на хосте пересоберите backend или скопируйте файл внутрь через `docker compose cp`. `docker compose stop` останавливает сервисы с сохранением данных; не используйте `down -v`, если нужно сохранить реестр.

## Данные и метод

`data/experts.csv`: 120 явно вымышленных профилей, 8 отраслей, 6 городов; без реальных имён и контактов. Генератор: `backend/manage.py generate_experts --output data/experts.csv`. CSV — UTF-8, списки через `|`.

Docker Compose + Django + DRF + PostgreSQL 16, единое приложение. Retrieval: BM25, русско-английский стемминг Snowball, открытый словарь терминов и синонимов. Затем покрытие распознанных компетенций, город, отрасль, минимальный опыт и штраф за занятость. Полные соответствия распознанным требованиям идут раньше частичных. Объяснения используют только поля профиля; при отсутствии соответствия выводятся ограничения. `match_percent` — взвешенное покрытие распознанных требований, **не вероятность пригодности**.

## Проверка

```powershell
docker compose exec -T backend python manage.py test experts
docker compose exec -T backend python manage.py evaluate_search --queries /app/data/reference_queries.json
docker compose exec -T backend python manage.py evaluate_search --queries /app/data/holdout_queries.json
```

Команда оценки выводит фактические Hit@3 и задержки и запрещает внешние Python-соединения на время проверки (локальное подключение PostgreSQL сохраняется). Эталонные и перефразированные запросы составлены командой; их результат не гарантирует качество на неизвестных запросах жюри. Поиск не читает файлы эталонов. Без ML-эксперимента нет оснований заявлять преимущество embeddings.

## Интеграция и ограничения

[API-контракт](docs/API_CONTRACT.md) · [ручная проверка для Жандоса](docs/QA.md). Runtime полностью локальный, без API-ключей и скачивания весов. Зависимости нужно установить до отключения сети; База PostgreSQL работает в отдельном контейнере. Русский — основной язык; поддерживаются перечисленные английские термины, казахский пока не реализован. Qwen и embeddings не обязательны и сейчас не подключены. Словарь ограничен; неизвестные условия требуют ручной проверки. Авторизации и production-развёртывания в этой итерации нет; сервер по умолчанию доступен только на localhost. Данные не отправляются внешним сервисам. Исходные требования: https://hackathon.metu.kz/, раздел AIID; зависимости — open-source, сведения об их лицензиях доступны в metadata установленных пакетов.

## Frontend

Для разработки: `npm.cmd run dev --prefix frontend`; Vite проксирует `/api` в localhost:8000. Для Docker сначала выполните npm ci/build выше (Node.js 24); готовые dist-файлы не хранятся в Git. Frontend-контейнер раздаёт собранные локальные ресурсы и проксирует API в Django на том же origin, без CORS и внешних CDN. Это сервер для локальной демонстрации, не production gateway. После изменения UI: повторить npm build, `docker compose build frontend` и `docker compose up -d --no-deps frontend`.

Доступны текстовый поиск, отраслевой фильтр, доказательства и недостающие условия, профиль и сравнение 2–3 кандидатов. Qwen не обязательна. Синтетическая пометка и пояснение процента видны в UI. Физическое отключение интернета в браузерной проверке ещё не выполнялось; все необходимые ресурсы включены в сборку.

## Интеграционная копия RAG

Worktree от origin/main 476e846, ветка integration/aiid-rag. Существующий проект на 8080 работает отдельно. Из корня исходного репозитория:

```powershell
docker compose -p aiid-integration --project-directory tmp/aiid-integration up -d --no-build --pull never
```

Сайт http://localhost:8081, API http://localhost:8011. Образы aiid-integration-backend:dev и aiid-integration-frontend:dev, отдельный том aiid-integration_postgres-data. Настройки в игнорируемой .env worktree. Используется скачанная qwen2.5:1.5b через host.docker.internal:11434. Сборка изменений UI: npm ci и npm run build в frontend, затем docker compose -p aiid-integration up -d --build из worktree.

POST /api/v1/compare/ принимает query, industry, limit, использует BM25 main с limit=3. Ответ status, comparison/detail, expert_ids, model, elapsed_ms. Карточки и исходные объяснения сохраняются при ошибке модели. Генеративный текст необходимо сверять с фактами анкет.

Qwen 1.5B в свободном тексте путала опыт между профилями. Поэтому сравнение использует constrained JSON: сервер вычисляет общие навыки и фактические отличия, модель возвращает только допустимые формулировки. Это проверяемое изложение анкет с ограниченной свободой генерации.
