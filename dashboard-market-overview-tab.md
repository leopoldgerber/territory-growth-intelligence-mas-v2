# Dashboard Tab: Market Overview

## Назначение

Market Overview показывает общий срез рынка по выбранным фильтрам Dashboard. Вкладка отвечает на вопрос:

```text
Что происходит с выбранной компанией, конкурентами или всем рынком в выбранных странах и периоде?
```

Вкладка использует общий Dashboard filter:

- Date from / Date to
- Country
- Top-Level Domain
- Company
- Company Domain
- Competitors
- Competitors Domain

## Scope логика

Market Overview поддерживает общую логику разделения показателей:

| Фильтры | Отображение |
|---|---|
| Company = All и Competitors = All | Один общий market-level показатель |
| Company выбрана, Competitors = None | Только company-показатели |
| Company = None, Competitors выбраны | Только competitor-показатели |
| Company выбрана, Competitors выбраны | Company green и competitors blue через разделитель `|` |

Если Company и Competitors оба `All`, два отдельных значения не показываются. Отображается один общий показатель цветом по умолчанию.

## Источник данных

Frontend получает данные через:

```text
GET /analytics/country-intelligence
```

Основная frontend-обертка:

```text
useCountryIntelligenceQuery()
```

Backend возвращает:

- company/overall summary;
- competitor summary;
- top competitors;
- daily traffic trend;
- device split;
- bounce / no-bounce metrics;
- engagement metrics;
- market signal для company/overall scope;
- market signal для competitor scope.

## Карточки Summary

В верхнем блоке отображаются 5 карточек.

### Total Traffic

Суммарный traffic за выбранный период и фильтры.

Логика отображения:

- overall: одно значение;
- company scope: green;
- competitor scope: blue;
- company + competitor: `company | competitor`.

### Active Companies

Количество активных компаний в выбранной выборке.

Для company scope значение фактически показывает активные компании/конкуренты внутри выбранного company/domain контекста.

### Active Domains

Количество активных доменов в выбранной выборке.

Значение зависит от фильтров:

- Company;
- Company Domain;
- Competitors;
- Competitors Domain;
- TLD.

### Selected Countries

Количество выбранных стран.

Важно: отображается именно количество стран, а не список country codes.

Если Country = All, значение равно количеству доступных стран в текущем data-backed контексте.

### Selected Period

Период анализа:

```text
date_from - date_to
```

Если период не задан, отображается `All`, но в текущей UI-логике даты имеют значения по умолчанию.

## Таблица Top Competitors

Таблица показывает крупнейших конкурентов по traffic в выбранном контексте.

Поля:

| Поле | Значение |
|---|---|
| Rank | Позиция конкурента по traffic |
| Company | Название компании |
| Traffic | Суммарный traffic |
| Traffic Share | Доля traffic конкурента |
| Domains Count | Количество активных доменов компании |

Если competitor scope не выбран, вместо таблицы отображается сообщение:

```text
Competitors are not selected.
```

Если competitors выбраны, но данных нет, отображается alert `No competitors`.

## Блок Traffic Trend

Traffic Trend показывает daily trend за выбранный период.

Логика:

- строится по датам из company/overall trend и competitor trend;
- для каждой даты отображается значение company/overall и competitor;
- если выбраны обе стороны, значения показываются разными цветами;
- bars нормализуются относительно максимального traffic в отображаемом наборе;
- если точек больше 14, отображаются последние 14 точек.

Если trend пустой, отображается:

```text
No daily trend points for selected filters.
```

## Блок Desktop / Mobile Split

Карточка показывает распределение traffic по устройствам.

Строки:

- Desktop
- Mobile

Для каждой строки показываются:

- traffic;
- share от общего traffic;
- bar визуализация доли.

При раздельном отображении:

- company/overall bar: green или primary;
- competitor bar: blue.

## Блок Bounce / No-Bounce

Карточка показывает engagement split:

- No-bounce;
- Bounce;
- Bounce rate.

Значения разделяются по scope так же, как и остальные показатели:

- default для overall;
- green для company;
- blue для competitors.

## Блок Engagement

Карточка показывает:

- Unique visitors;
- Pages per visit;
- Avg visit duration.

Avg visit duration форматируется как:

```text
minutes:seconds
```

## Блок Market Signal

Market Signal показывает rule-based статус рынка за выбранный период.

Период делится на две половины. Traffic второй половины сравнивается с первой.

Для каждого активного scope отображаются:

- scope label;
- status badge;
- growth rate;
- текстовое объяснение.

### Статусы Market Signal

| Status | Значение |
|---|---|
| `no_data` | Нет traffic в выбранном периоде |
| `insufficient_data` | Недостаточно dated traffic points для сравнения |
| `new_activity` | Traffic отсутствовал в первой половине и появился во второй |
| `falling` | Traffic во второй половине снизился минимум на 10% |
| `stable` | Изменение между половинами находится между -5% и 5% |
| `promising` | Traffic вырос минимум на 10%, leader share ниже 40%, bounce rate ниже 55% |
| `overheated` | Traffic вырос минимум на 10%, но лидер держит минимум 50% traffic |
| `growing` | Traffic вырос минимум на 10%, но не попал в promising/overheated |
| `mixed` | Ситуация не соответствует остальным правилам |

Для описания статусов есть информационное окно в заголовке `Market Signal`.

## Empty и Error состояния

Если данные загружаются, отображается skeleton state.

Если backend endpoint недоступен, отображается destructive alert:

```text
Failed to load country intelligence.
```

Если данных нет:

```text
No country data found for selected filters.
```

Если Company и Competitors одновременно `None`:

```text
Company and competitors are not selected.
```

## Ключевые файлы

Frontend:

- `frontend/components/dashboard/country-intelligence/country-intelligence-section.tsx`
- `frontend/lib/api/analytics-queries.ts`
- `frontend/lib/types/analytics.ts`

Backend:

- `backend/app/api/routes/analytics.py`
- `backend/app/analytics/country_intelligence.py`

