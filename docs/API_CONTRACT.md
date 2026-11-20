# API v1 — контракт для Алмаса

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
