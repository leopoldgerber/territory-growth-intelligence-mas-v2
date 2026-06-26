# Dashboard Tab: Scoring

## Назначение

Scoring отображает Opportunity Scoring — explainable country-level ranking привлекательности рынков.

Вкладка отвечает на вопрос:

```text
Какие страны выглядят наиболее перспективными по выбранным данным, scope и периоду?
```

Scoring не является финальным решением о бюджете или автоматической стратегией. Это аналитический score, который может использоваться в Reports и ручном анализе.

## Источник данных

Чтение:

```text
GET /analytics/scoring/opportunities
GET /analytics/scoring/summary
```

Пересчет:

```text
POST /analytics/scoring/recalculate
```

Frontend hooks:

- `useOpportunityScoresQuery()`
- `useOpportunityScoringSummaryQuery()`
- `useRecalculateOpportunityScoresMutation()`

## Persisted logic

Scoring читает persisted records из таблицы `opportunity_score`.

Если выбран новый scope или период, но пересчет еще не был выполнен, таблица может быть пустой.

Чтобы создать или заменить scores, нужно нажать:

```text
Recalculate scores
```

## Scope логика

| Фильтры | Scope |
|---|---|
| Company = All и Competitors = All | `overall` |
| Company выбрана, Competitors = None | `company` |
| Company = None, Competitors выбраны | `competitor` |
| Company выбрана, Competitors выбраны | `company` + `competitor` |
| Company = None и Competitors = None | Scoring не отображается |

Цвета:

- overall: default;
- company: green;
- competitor: blue.

## Header

Header содержит:

- заголовок `Opportunity Scoring`;
- информационное окно;
- описание;
- legend для company/competitor scopes;
- кнопку `Recalculate scores`.

Кнопка disabled, если:

- идет пересчет;
- нет выбранных scopes.

## Recalculate result alerts

После успешного пересчета отображается:

```text
Opportunity scores recalculated.
N scores saved; N previous records replaced.
```

Если пересчет завершился ошибкой:

```text
Failed to recalculate opportunity scores.
```

## Fallback alert

Если Derived Signals отсутствуют и часть факторов использует fallback, UI показывает:

```text
Scoring fallback is active.
```

Это не ошибка. Это значит, что score рассчитан, но часть факторов использует нейтральную fallback-логику.

## Карточки Summary

Scoring Summary содержит 4 карточки.

### Total Countries

Количество distinct countries с persisted scores в выбранных scopes.

### Average Score

Среднее значение Opportunity Score по отображаемым scores.

### Top Country

Страна с максимальным score.

Tie-breaking выполняется ranking rules на backend.

### Very High / High

Количество стран в категориях:

- `very_high`;
- `high`.

## Таблица Scoring Ranking

Главная таблица показывает country ranking.

Поля:

| Поле | Значение |
|---|---|
| Rank | Позиция внутри scope |
| Country | Страна и country code |
| Scope | Overall / Company / Competitor |
| Score | Итоговый Opportunity Score |
| Category | Score category |
| Market Size | Factor score |
| Growth | Factor score |
| Quality | Factor score |
| Competition | Factor score |
| Concentration | Factor score |
| Channel Stability | Factor score |
| Entry Risk | Factor score |
| Position Potential | Factor score |

При клике на страну выбирается active row и ниже отображается detail-блок.

## Score factors

Opportunity Score состоит из 8 факторов.

| Factor | Вес | Что означает |
|---|---:|---|
| Market Size | 18% | Traffic percentile или single-country fallback |
| Growth | 18% | Движение traffic между половинами периода |
| Quality | 16% | Visit duration, no-bounce rate, pages per visit |
| Competition | 14% | Активная конкурентная плотность |
| Concentration | 12% | Top1 и Top3 share |
| Channel Stability | 10% | Channel-shift signals или fallback |
| Entry Risk | 10% | Инвертированный риск на основе risk signals |
| Position Potential | 12% | Positive signal bonus |

## Score category

| Category | Range |
|---|---:|
| `very_high` | 80-100 |
| `high` | 65-79.9999 |
| `medium` | 50-64.9999 |
| `low` | 35-49.9999 |
| `very_low` | 0-34.9999 |

## Detail-блок

После выбора строки отображается detail для выбранной country/scope.

Верхняя часть:

- country score detail;
- summary explanation;
- final score;
- score category.

## Таблица Factor Breakdown

Detail-блок содержит таблицу факторов.

Поля:

| Поле | Значение |
|---|---|
| Factor | Название фактора |
| Raw Value | Исходное значение или набор метрик |
| Score | Нормализованный score фактора |
| Weight | Вес фактора |
| Weighted Score | Вклад фактора в итоговый score |
| Status | Статус фактора |
| Explanation | Объяснение расчета |

### Factor Status

| Status | Значение |
|---|---|
| `strong` | Factor score минимум 75 |
| `moderate` | Factor score выше 40 и ниже 75 |
| `weak` | Factor score 40 или ниже |
| `not_available` | Источник отсутствует, используется fallback |

## Блоки Strengths, Weaknesses, Risks

Detail-блок содержит 3 карточки:

### Strengths

Список факторов, где score минимум 75.

### Weaknesses

Список факторов, где score 40 или ниже.

### Risks

Список risk signals, которые повлияли на scoring.

Если список пустой, отображается:

```text
None detected.
```

## Signals Used и Fallbacks Used

Нижняя часть detail-блока показывает:

### Signals Used

Список signal types, которые использовались в score.

Если signals отсутствуют:

```text
None
```

### Fallbacks Used

Список факторов, где использовался fallback.

Если fallback не использовался:

```text
None
```

## Ranking logic

Страны ранжируются отдельно внутри каждого scope.

Сортировка:

1. Opportunity Score по убыванию.
2. Market Size factor по убыванию.
3. Growth factor по убыванию.
4. Quality factor по убыванию.
5. Country name по возрастанию.

## Empty и Error состояния

Если Company и Competitors одновременно `None`:

```text
Company and competitors are not selected.
```

Если scores не найдены:

```text
No opportunity scores found for selected filters.
```

Если endpoint недоступен:

```text
Failed to load opportunity scores.
```

## Рекомендуемый flow

1. Выбрать общий Dashboard filter.
2. Перейти на Signals.
3. Нажать `Recalculate signals`.
4. Перейти на Scoring.
5. Нажать `Recalculate scores`.
6. Проверить summary cards.
7. Проверить ranking table.
8. Открыть detail по нужной стране.

Если изменить общий фильтр, Scoring желательно пересчитать заново.

## Ключевые файлы

Frontend:

- `frontend/components/dashboard/opportunity-scoring/opportunity-scoring-section.tsx`
- `frontend/components/dashboard/opportunity-scoring/scoring-summary-cards.tsx`
- `frontend/components/dashboard/opportunity-scoring/scoring-ranking.tsx`
- `frontend/lib/api/analytics-queries.ts`
- `frontend/lib/types/analytics.ts`

Backend:

- `backend/app/api/routes/analytics.py`
- `backend/app/analytics/scoring/service.py`
- `backend/app/analytics/scoring/calculators.py`
- `backend/app/analytics/scoring/repository.py`
- `backend/alembic/versions/202606210005_add_opportunity_scores.py`

