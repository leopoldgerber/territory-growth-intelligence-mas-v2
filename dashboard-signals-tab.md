# Dashboard Tab: Signals

## Назначение

Signals отображает Derived Signals — сохраненные аналитические факты, рассчитанные из traffic, competition, channel, quality и device данных.

Вкладка отвечает на вопрос:

```text
Какие значимые условия и отклонения обнаружены в выбранном периоде и scope?
```

Signals не является финальной рекомендацией или budget strategy. Это объяснимый слой наблюдений.

## Источник данных

Чтение:

```text
GET /analytics/signals
GET /analytics/signals/summary
```

Пересчет:

```text
POST /analytics/signals/recalculate
```

Frontend hooks:

- `useDerivedSignalsQuery()`
- `useDerivedSignalsSummaryQuery()`
- `useRecalculateDerivedSignalsMutation()`

## Persisted logic

Signals читает persisted records из таблицы `derived_signal`.

Если фильтр изменился, новые signals не создаются автоматически.

Чтобы создать или заменить signals для выбранного периода и scope, нужно нажать:

```text
Recalculate signals
```

## Scope логика

| Фильтры | Scope |
|---|---|
| Company = All и Competitors = All | `overall` |
| Company выбрана, Competitors = None | `company` |
| Company = None, Competitors выбраны | `competitor` |
| Company выбрана, Competitors выбраны | `company` + `competitor` |
| Company = None и Competitors = None | Signals не отображаются |

Цвета:

- overall: default;
- company: green;
- competitor: blue.

## Верхний header

Header содержит:

- заголовок `Derived Signals`;
- информационное окно с объяснением;
- текстовое описание;
- legend для company/competitor scopes;
- кнопку `Recalculate signals`.

Кнопка disabled, если:

- идет пересчет;
- нет выбранных scopes.

## Recalculate result alerts

После успешного пересчета отображается:

```text
Signals recalculated.
N signals saved; N previous records replaced.
```

Если пересчет завершился ошибкой:

```text
Failed to recalculate signals.
```

## Локальные фильтры Signals

Signals имеет два локальных фильтра внутри вкладки.

Они не меняют общий Dashboard filter.

### Signal group

Значения:

| Group | Значение |
|---|---|
| `all` | Все группы |
| `growth` | Рост, падение, новая активность |
| `volatility` | Стабильность или высокая изменчивость traffic |
| `competition` | Концентрация, фрагментация, expansion |
| `territory` | Новые, забытые или low-noise markets |
| `channel` | Изменения channel shares |
| `quality` | Engagement quality conditions |
| `device` | Desktop/mobile quality differences |

### Severity

Значения:

| Severity | Значение |
|---|---|
| `all` | Все severity |
| `low` | Информационный или ранний сигнал |
| `medium` | Значимый сигнал для мониторинга |
| `high` | Сильное отклонение или повышенный риск |
| `critical` | Максимальный приоритет, если rule его выставит |

## Карточки Summary

Блок `DerivedSignalSummaryCards` содержит 5 карточек.

### Total Signals

Количество всех triggered analytical conditions в выбранных scopes и локальных filters.

### High Severity

Количество signals с severity `high`.

### Growth Signals

Количество signals группы `growth`.

### Competition Signals

Количество signals группы `competition`.

### Quality Signals

Сумма signals групп:

- `quality`;
- `device`.

Если активны company и competitor scopes, карточки показывают значения раздельно:

```text
company | competitor
```

## Таблица Derived Signals

Таблица показывает persisted signals.

Поля:

| Поле | Значение |
|---|---|
| Severity | Уровень важности |
| Group | Signal group |
| Type | Конкретный backend rule |
| Entity | Entity type и entity id |
| Period | Date from - date to |
| Value / Delta | Основное измерение сигнала |
| Message | Человекочитаемое объяснение |

### Value / Delta

Порядок выбора значения:

1. `delta_percent`, если есть;
2. `delta_value`, если есть;
3. `value`, если есть;
4. `None`, если значения отсутствуют.

## Типы Signals

Основные signal types:

Growth:

- `new_activity`
- `growth_acceleration`
- `traffic_decline`

Volatility:

- `high_volatility`
- `stable_market`

Competition:

- `high_concentration`
- `low_competitive_noise`
- `fragmented_market`
- `overheated_market`
- `competitor_expansion`

Territory:

- `low_noise_market`
- `new_territory`
- `forgotten_territory`

Channel:

- `channel_shift`

Quality:

- `traffic_quality_degradation`

Device:

- `mobile_new_activity`
- `mobile_growth_low_quality`
- `desktop_quality_advantage`
- `mobile_strength`
- `balanced_device_quality`

## Empty и Error состояния

Если нет выбранных scopes:

```text
Company and competitors are not selected.
```

Если signals не найдены:

```text
No derived signals found for selected filters.
```

Если загрузка failed:

```text
Failed to load derived signals.
```

## Рекомендуемый flow

1. Выбрать общий Dashboard filter.
2. Перейти на Signals.
3. Нажать `Recalculate signals`.
4. Проверить summary cards.
5. Проверить таблицу.
6. При необходимости отфильтровать по Signal group и Severity.

После изменения общего фильтра пересчет нужно выполнить снова.

## Ключевые файлы

Frontend:

- `frontend/components/dashboard/derived-signals/derived-signals-section.tsx`
- `frontend/components/dashboard/derived-signals/derived-signal-summary.tsx`
- `frontend/components/dashboard/derived-signals/derived-signal-table.tsx`
- `frontend/lib/api/analytics-queries.ts`
- `frontend/lib/types/analytics.ts`

Backend:

- `backend/app/api/routes/analytics.py`
- `backend/app/analytics/signals/service.py`
- `backend/app/analytics/signals/calculators.py`
- `backend/app/analytics/signals/repository.py`
- `backend/alembic/versions/202606210003_add_derived_signals.py`

