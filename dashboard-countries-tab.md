# Dashboard Tab: Countries

## Назначение

Countries показывает country-level аналитику по конкурентному присутствию, распределению traffic между странами, росту, падению, market roles и rule-based market windows.

Вкладка отвечает на вопрос:

```text
В каких странах выбранные competitors или весь конкурентный набор сильнее всего представлены и где есть рыночные сигналы?
```

## Источник данных

Frontend получает данные через:

```text
GET /analytics/competitor-intelligence
```

Основная frontend-обертка:

```text
useCompetitorIntelligenceQuery()
```

Несмотря на историческое имя компонента `CompetitorIntelligenceSection`, UI-вкладка называется `Countries`.

## Scope и цветовая логика

Countries анализирует competitors context.

Если `competitors=all`, значения отображаются цветом по умолчанию.

Если выбран конкретный competitor или несколько competitors, значения подсвечиваются blue.

Если `competitors=none`, вкладка не строит аналитику и показывает сообщение с просьбой выбрать competitor или `All`.

## Карточки Summary

В верхнем блоке отображаются 5 карточек.

### Total Traffic

Суммарный traffic выбранных competitors или всего конкурентного набора.

### Active Countries

Количество стран, где есть traffic в выбранном периоде и фильтрах.

### Active Domains

Количество доменов, участвующих в выбранном competitor context.

### Top Country

Страна с максимальным traffic.

Дополнительно отображается доля top country:

```text
top_country_share
```

### Growth Rate

Общий growth rate между первой и второй половинами выбранного периода.

Для карточки есть информационное окно:

```text
Compares total traffic in the second half of the selected period with the first half.
```

## Таблица Top Countries

Top Countries показывает страны, отсортированные по traffic.

Поля:

| Поле | Значение |
|---|---|
| Rank | Позиция страны по traffic |
| Country | Название страны и country code |
| Traffic | Суммарный traffic |
| Traffic Share | Доля страны в общем selected traffic |
| Growth Rate | Рост между половинами периода |
| Status | Growth status и market role |

### Growth Rate

Growth Rate сравнивает traffic страны во второй половине периода с первой половиной.

### Status

В колонке Status показываются два badge:

- traffic movement status;
- market role status.

Traffic movement:

| Status | Значение |
|---|---|
| `new_activity` | Traffic появляется только во второй половине периода |
| `growing` | Traffic вырос минимум на 10% |
| `declining` | Traffic снизился минимум на 10% |
| `stable` | Traffic есть, но без движения минимум на 10% |
| `no_data` | Нет traffic |

Market role:

| Status | Значение |
|---|---|
| `anchor` | Top-3 страна или минимум 15% traffic |
| `established` | От 5% до 15% traffic вне top-3 |
| `peripheral` | Менее 5% traffic вне top-3 |

## Таблица Growing Countries

Показывает страны с позитивным движением.

В таблицу попадают:

- страны с ростом минимум 10%;
- страны с `new_activity`, где traffic появился во второй половине периода.

Поля:

- Country
- Traffic
- Growth

Если таких стран нет:

```text
No growing countries for selected filters.
```

## Таблица Declining Countries

Показывает страны, где traffic снизился минимум на 10% между половинами периода.

Поля:

- Country
- Traffic
- Growth

Если таких стран нет:

```text
No declining countries for selected filters.
```

## Карточка Anchor Markets

Anchor Markets показывает страны, которые являются ключевыми для выбранного competitor context.

Правило:

- top-3 страны по traffic;
- или любая страна с долей traffic минимум 15%.

Каждая строка показывает:

- country;
- traffic share.

## Карточка Peripheral Markets

Peripheral Markets показывает страны с низкой долей traffic.

Правило:

- country traffic share < 5%;
- страна не входит в top anchor markets.

Каждая строка показывает:

- country;
- traffic share.

## Карточка Country Dependency

Country Dependency оценивает концентрацию traffic в ведущих странах.

Поля:

- Top 1 country share;
- Top 3 countries share;
- dependency level.

Dependency levels:

| Level | Значение |
|---|---|
| `low` | Top 1 ниже 30% и Top 3 ниже 60% |
| `medium` | Top 1 минимум 30% или Top 3 минимум 60% |
| `high` | Top 1 минимум 50% или Top 3 минимум 80% |

## Карточка Presence Stability

Presence Stability показывает, насколько регулярно есть positive traffic в выбранном периоде.

Поля:

- Active days;
- Period days;
- Stability rate;
- status.

Statuses:

| Status | Значение |
|---|---|
| `stable` | Active traffic минимум на 80% дней |
| `irregular` | Active traffic от 40% до 79.9% дней |
| `weak` | Active traffic менее чем на 40% дней |

## Карточка Market Windows

Market Windows показывает rule-based market signals по странам.

Возможные signals:

| Signal | Значение |
|---|---|
| `declining_presence` | Country traffic снизился минимум на 10% |
| `small_but_growing` | Country share ниже 5%, но growth минимум 20% |
| `low_stability` | Traffic активен менее чем на 40% дней |
| `high_dependency` | Traffic сильно сконцентрирован в leading markets |

Каждый market window показывает:

- country;
- signal;
- message.

Эти значения являются статусами market window:

- `declining_presence` фиксирует страну, где competitor traffic снижается минимум на 10%;
- `small_but_growing` фиксирует малую страну с долей ниже 5%, но ростом минимум 20%;
- `low_stability` фиксирует слабую регулярность presence, когда active traffic есть менее чем на 40% дней;
- `high_dependency` фиксирует высокую зависимость от leading markets, когда top country или top-3 countries держат слишком большую долю traffic.

Если сигналов нет:

```text
No rule-based market signals for selected filters.
```

## Empty и Error состояния

Если идет загрузка, отображается skeleton state.

Если endpoint недоступен:

```text
Failed to load competitor intelligence.
```

Если `competitors=none`:

```text
Select a competitor or domain to view competitor intelligence.
```

Если total traffic = 0:

```text
No competitor data found for selected filters.
```

## Ключевые файлы

Frontend:

- `frontend/components/dashboard/competitor-intelligence/competitor-intelligence-section.tsx`
- `frontend/components/dashboard/competitor-intelligence/competitor-summary-cards.tsx`
- `frontend/components/dashboard/competitor-intelligence/competitor-country-tables.tsx`
- `frontend/components/dashboard/competitor-intelligence/competitor-market-analysis.tsx`
- `frontend/lib/api/analytics-queries.ts`
- `frontend/lib/types/analytics.ts`

Backend:

- `backend/app/api/routes/analytics.py`
- `backend/app/analytics/competitor_intelligence.py`
