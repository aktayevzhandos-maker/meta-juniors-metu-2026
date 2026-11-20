# API v1 — контракт fullstack-интеграции

Base URL: `http://127.0.0.1:8000/api/v1`. Все пути заканчиваются `/`. JSON UTF-8. Стабильная первая версия: существующие поля не переименовывать при добавлении Qwen/embeddings.

## Поиск

`POST /search/`, `Content-Type: application/json`

```json
{"query":"Нужен специалист по GMP и клиническим исследованиям из Алматы","limit":3,"industry":null}
```

- `query`: 3–1000 символов, непустой, содержит буквы; обязательно.
- `limit`: целое 3–20; по умолчанию 3.
- `industry`: null/отсутствует или точная строка из `/industries/`; дополнительный жёсткий фильтр, не замена текстовому запросу.

Структура ответа (TypeScript, значения времени и баллов не зашиты):

```typescript
type Expert = {
  id: string; full_name: string; title: string;
  industry: string; city: string; skills: string[]; languages: string[];
  years_experience: number;
  availability: 'available' | 'limited' | 'busy';
  availability_label: string; bio: string; is_synthetic: true;
};
type Candidate = {
  expert: Expert;
  score: number; // ranking score, НЕ вероятность
  match_percent: number | null; // покрытие распознанных критериев, НЕ уверенность AI
  match_status: 'full' | 'partial'; // только по распознанным требованиям
  matched_skills: string[];
  matched_industries: string[]; // явное отраслевое условие, если совпало
  profile_industry: string; // отображать и при отрасли, не указанной в запросе
  missing_requirements: string[];
  explanation: string[]; warnings: string[];
  score_components: {bm25: number; skill_coverage: number; availability_penalty: number};
  matched_terms: string[]; // диагностические стемы; НЕ показывать как навыки
};
type SearchResponse = {
  query: string; status: 'ok' | 'partial' | 'no_matches';
  parsed_query: {
    skills: string[]; industries: string[]; cities: string[];
    min_years_experience: number | null; excluded_skills: string[];
    max_years_experience?: number | null; excluded_cities?: string[];
    excluded_industries?: string[]; errors?: string[];
    unrecognized_terms: string[]; // часть условий не распознана — показать предупреждение
  };
  results: Candidate[]; warnings: string[];
  candidate_count: number; total_experts: number; elapsed_ms: number;
  method: string; semantic_embeddings_used: boolean;
  score_description: string; is_synthetic: true;
};
```

```typescript
const API = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1';
const response = await fetch(`${API}/search/`, {
  method: 'POST', headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({query, limit: 3, industry: selectedIndustry || null}),
  signal: AbortSignal.timeout(30000),
});
if (!response.ok) throw new Error(`Поиск недоступен: HTTP ${response.status}`);
const data: SearchResponse = await response.json();
```

UI: видимая пометка «Синтетические данные, не содержат реальных персональных данных». Показывать отрасль, компетенции, доступность, объяснение, недостающие условия. `no_matches` — честное пустое состояние. `partial` — предупреждение, а не «идеальный кандидат». Даже при `ok` отдельные кандидаты могут быть частичными. `match_percent: null` скрывает процент: нет распознанных критериев для его расчёта. `full/100%` относится только к распознанным критериям; предупреждения при неизвестных словах не скрывать. Escape HTML как обычно в React; не использовать dangerouslySetInnerHTML для профилей.

## Остальные endpoints

| Метод и путь | Ответ |
|---|---|
| `GET /health/` | `status, expert_count, offline, is_synthetic, version`; 503, если база не готова или меньше 100 записей |
| `GET /industries/` | `{industries: string[], is_synthetic: true}` |
| `GET /experts/?offset=0&limit=20&industry=IT` | `{count, offset, limit, results: Expert[], is_synthetic}`; limit 1–100 |
| `GET /experts/EXP-001/` | `Expert`; 404 при неизвестном ID |

CSV загружается командой `docker compose exec -T backend python manage.py import_experts /app/data/experts.csv`, HTTP-upload в первой версии не реализован. Колонки: `id,full_name,title,industry,city,skills,languages,years_experience,availability,bio,is_synthetic`. Skills/languages разделены `|`; is_synthetic=true. Весь файл валидируется перед транзакцией, повтор ID внутри файла запрещён, допустимые ID: ASCII буквы/цифры/`_`/`-`. Нет реальных контактов. Изменения CSV нужно включить в образ пересборкой или скопировать через `docker compose cp`, затем повторно импортировать; на следующем запросе индекс строится по текущей базе.

## Ошибки и локальная интеграция

- 400: ошибка DRF по полям, например `{"query":["..."]}` или `{"limit":["..."]}`.
- 503: `registry_empty`/`registry_not_ready`/`database_not_ready`; выполните миграции и импорт.
- 405: неправильный HTTP-метод. GET-поиск не предусмотрен.
- CORS разрешён для `http://localhost:5173` и `http://127.0.0.1:5173`. Другие origins задаются `CORS_ALLOWED_ORIGINS`, через запятую, перед запуском.
- Для разных ноутбуков проще каждому запустить backend из репозитория. LAN: явно задать `DJANGO_ALLOWED_HOSTS` и `CORS_ALLOWED_ORIGINS`, явно изменить публикацию порта Compose с `127.0.0.1:8000:8000` на нужный LAN-адрес, открыть доступ в firewall только в доверенной сети. Это ручная настройка, автоматически не выполнялась.
- Runtime не требует сети. Не подключать CDN, внешние шрифты и платные API на frontend.

## Точка расширения Local AI

`experts/search/engine.py`: `SearchEngine` выдаёт кандидатов и фактические доказательства. Будущий локальный encoder может добавить semantic score перед сортировкой, сохраняя ограничения и существующие поля. Его отсутствие/ошибка должны оставлять BM25 работоспособным. Qwen — только после проверки версии Алмасом; генеративные объяснения не должны подменять факты профиля. В первой итерации нет сетевого вызова даже на localhost к модели.

Основной запуск — Docker Compose с PostgreSQL 16; SQLite не используется. API-контракт при смене БД не изменился. Данные хранятся в volume `postgres-data`, пароль и Django secret — в игнорируемой `.env`. `/health/` возвращает `database: postgresql`.

## Текущий frontend

React-приложение использует относительный `/api/v1/` через same-origin proxy frontend-контейнера (localhost:5173). Vite dev server проксирует туда же через localhost:8000. Пример выше с VITE_API_BASE_URL предназначен для отдельного клиента; текущая реализация не требует этой переменной. Backend API не изменён.

## Условия и отрицания (v2)

Добавлены совместимые поля parsed_query: max_years_experience, excluded_cities, excluded_industries и errors. Старые поля сохранены. «Не из Алматы» исключает город, «без PLC» — навык; список после отрицания ограничен ближайшими распознанными названиями. «Без PLC нужен SCADA» сохраняет SCADA как положительное условие.

Опыт: «не более/до/максимум N» — включительно до N; «менее N» — до N-1; «не менее/от N» — от N; «более/свыше N» — от N+1; «от N до M лет» задаёт обе границы. Исключения работают как фильтры до ранжирования. Верхняя и нижняя границы входят в проверку покрытия и объяснения. Если минимум больше максимума, HTTP API возвращает 400 с объяснением в experience. Внутренний SearchEngine сохраняет диагностическое поле errors. Незнакомый явно указанный город с заглавной буквы после «в/из» сохраняется как условие, поэтому кандидаты из других городов не помечаются full. Это ограниченный парсер, не универсальное понимание географии или русского языка.

## Аналитика и синтетический CSV (интеграционная сборка)

GET `/analytics/` возвращает `{total_requests, period_start, period_end, skills: [{skill, requests, available_experts}], is_synthetic}`. skills — до пяти компетенций по убыванию числа запросов, при равенстве по имени. Период — с первого учтённого запроса до текущего времени, ISO 8601. Учёт только успешных вызовов POST search, включая пустую выдачу. Каждая компетенция из parsed_query.skills учитывается один раз. Пустой parsed_query.skills увеличивает только total_requests. GET и compare не меняют агрегаты. Тексты запросов в БД не сохраняются. available_experts — число профилей со статусом available и каноническим навыком, каждый человек учитывается один раз на навык.

GET `/import/template/` скачивает синтетический шаблон CSV UTF-8. POST `/import/` принимает JSON `{mode: "preview" | "apply", content: "CSV UTF-8", token?: string}`. Для HTTP-интерфейса лимит 1 МБ. Preview полностью валидирует файл действующим parse_csv и возвращает created, updated, token. Apply требует token того же файла (срок 10 минут), повторно валидирует его и вызывает import_csv с replace=False. Обновление по ID, остальные профили сохраняются. Ошибки возвращаются как 400 `{errors: string[]}`. Предпросмотр сообщает первую ошибку валидатора. Финальные счётчики apply отражают состояние в момент применения. Это расширение доступно в локальном деморежиме без аутентификации.

## Каталог и расширенная выдача

Frontend выполняет один POST search с limit=20. Первые три — лучшие совпадения, «Показать ещё» раскрывает следующие три из того же ответа в исходном порядке, без увеличения аналитики. POST compare по-прежнему использует limit=3 с тем же query и industry. GET experts с offset/limit/industry обслуживает каталог. Профиль открывается по /dashboard/catalog?expert=ID через GET experts/{id}/. Каталог и GET профиля не меняют счётчики спроса.

## Фильтр города и раздел реестра

Search и compare принимают дополнительное поле city: null либо непустая строка до 80 символов. Это жёсткий фильтр по точному городу реестра. Город добавляется в parsed_query.cities. При противоречии с исключением города или другим городом в тексте оба endpoint возвращают 400 с объяснением в city. GET /cities/ возвращает {cities: string[], is_synthetic: true} из актуального реестра. Служебное слово «найди» не участвует в лексическом поиске. Поиск только по распознанному городу возвращает профили этого города, незнакомая специальность по-прежнему не заменяется совпадением города.

Общая навигация содержит «Подбор», «Реестр» и отдельную «Аналитику». Реестр использует /dashboard/catalog, BI-страница — /dashboard/analytics. Импорт в каталоге переиспользует текущий preview/apply API. После применения каталог запрашивается заново, аналитика получает текущую доступность из БД при открытии или обновлении. Подсветка сравнения вычисляется из matched_skills, parsed_query и полей expert, без обращения к Qwen. Парные бары аналитики имеют независимые шкалы запросов и людей.

## RU / KK / EN, явные границы и BI

Поиск и compare принимают min_years_experience и max_years_experience (null либо целое 0–60). Явные фильтры стажа ограничивают кандидатов на сервере. Текстовые границы объединяются с фильтрами пересечением; пустой диапазон, конфликт города/отрасли и их исключений возвращают 400 с объяснением. Без явных фильтров текстовые условия сохраняют существующий режим частичных совпадений с missing_requirements. «Специалист» без условий возвращает 400 с просьбой уточнить запрос. С фильтрами выполняется подбор. RU/KK/EN поддерживаются ограниченным локальным словарём городов, компетенций, отрицаний и стажа. parsed_query.language сообщает ru/kk/en; это не универсальный переводчик.

Compare использует тот же запрос и все фильтры с limit=3. Модель получает только подготовленные сравнительные факты, без исходных инструкций пользователя; constrained JSON проверяется по точным фактам и допустимым ID. Ответ содержит language, model и elapsed_ms. Пустая выдача завершает запрос до обращения к Ollama.

GET analytics/?industry=...&skill=... дополнительно возвращает table (весь глобальный спрос по компетенциям), competencies, industries, filtered_requests, expert_count, available_expert_count, availability_by_industry (industry/available/limited/busy/total), filters и demand_scope=global. industry влияет только на предложение реестра, поскольку исторической разбивки спроса по отраслям не было. skill фильтрует связанные показатели и текущую доступность. total_requests остаётся глобальным числом. Истории по дням в текущих агрегатах нет.
