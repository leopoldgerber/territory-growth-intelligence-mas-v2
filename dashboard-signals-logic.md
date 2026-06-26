# Dashboard Signals Logic

## Назначение

Signals на Dashboard отображает derived signals — сохраненные аналитические факты, рассчитанные из загруженных данных.

Signals не является финальной рекомендацией, стратегией или budget decision. Это слой объяснимых наблюдений, который помогает понять, что произошло в данных:

- где есть рост;
- где есть падение;
- где высокая волатильность;
- где есть конкурентная концентрация;
- где изменился channel mix;
- где ухудшилось качество трафика;
- где есть device-specific проблемы.

## Главное правило

Signals работает с сохраненными результатами пересчета.

Это значит:

- вкладка читает данные из таблицы `derived_signal`;
- если для выбранного периода и scope сигналов нет, таблица будет пустой;
- чтобы создать или заменить сигналы, нужно нажать `Recalculate signals`.

## Scope логика

Signals использует общий фильтр Dashboard.

Scope определяется по значениям:

- `company`
- `companyDomain`
- `competitors`
- `competitorDomain`

Логика:

| Состояние фильтров | Scope |
|---|---|
| Company = All и Competitors = All | `overall` |
| Company выбрана, Competitors = None | `company` |
| Company = None, Competitors выбраны | `competitor` |
| Company выбрана, Competitors выбраны | `company` + `competitor` |
| Company = None и Competitors = None | Signals не рассчитываются и не отображаются |

Если Company и Competitors оба `All`, Signals отображаются как общий market-level scope.

Если выбран company scope, строки отображаются green.

Если выбран competitor scope, строки отображаются blue.

## Recalculate signals

Кнопка `Recalculate signals` запускает backend endpoint:

```text
POST /analytics/signals/recalculate
```

В request передаются:

- `date_from`
- `date_to`
- `country`
- `tld`
- `company`
- `company_domain`
- `competitors`
- `competitor_domain`
- `calculation_version`

Текущая версия расчета:

```text
v1
```

## Что происходит при пересчете

При пересчете backend:

1. Проверяет корректность периода.
2. Определяет project через `DEFAULT_PROJECT_ID`.
3. Определяет scopes, которые нужно посчитать.
4. Строит кандидаты сигналов по каждому scope.
5. Удаляет предыдущие persisted signals для этого проекта, периода и `calculation_version`.
6. Вставляет новые signals.
7. Возвращает количество удаленных и вставленных записей.

Пример сообщения:

```text
18 signals saved; 18 previous records replaced.
```

Это означает:

- 18 старых записей были удалены;
- 18 новых записей были сохранены;
- данные в `derived_signal` заменены для выбранного project + period + calculation version.

## Важная особенность замены

Удаление старых signals выполняется по:

- project;
- date from;
- date to;
- calculation version.

Это значит, что пересчет для того же периода и той же версии заменяет предыдущие сигналы этого периода.

Если поменять фильтр и не нажать `Recalculate signals`, интерфейс будет читать уже существующие persisted signals, а не автоматически создавать новые.

## Источники данных для Signals

Signals строятся из нескольких аналитических источников:

| Signal source | Fact data |
|---|---|
| Growth signals | `fact_traffic_countries_daily` |
| Country market signals | `fact_traffic_countries_daily` |
| Channel signals | `fact_traffic_sources_daily` |
| Expansion signals | `fact_traffic_countries_daily` |
| Quality signals | `fact_device_trends_daily` |
| Device signals | Device Intelligence calculations |

## Группы сигналов

Текущие signal groups:

| Group | Что означает |
|---|---|
| `growth` | Рост, падение или появление новой активности |
| `volatility` | Стабильность или высокая изменчивость ежедневного трафика |
| `competition` | Концентрация, фрагментация, активность конкурентов |
| `territory` | Новые, забытые или низкошумные рынки |
| `channel` | Существенные изменения долей acquisition channels |
| `quality` | Ухудшение engagement-метрик |
| `device` | Различия качества между desktop и mobile |

В интерфейсе есть фильтр `Signal group`:

- `All`
- `Growth`
- `Volatility`
- `Competition`
- `Territory`
- `Channel`
- `Quality`
- `Device`

## Severity

Signals имеют severity:

| Severity | Значение |
|---|---|
| `low` | Информационный или ранний сигнал |
| `medium` | Значимый сигнал, который стоит мониторить |
| `high` | Сильное отклонение или повышенный аналитический риск |
| `critical` | Максимальный уровень при наличии соответствующего правила |

В текущих правилах чаще всего используются `low`, `medium` и `high`. `critical` поддерживается схемой и UI, но появляется только если backend rule его выставит.

## Signal types

Текущие типы сигналов формируются правилами backend.

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

- device-specific signals produced through Device Intelligence quality calculations.

## Growth signal logic

Период делится на две половины.

Для выбранного scope сравнивается traffic первой и второй половины.

Правила:

- если первая половина = 0, а во второй есть traffic, создается `new_activity`;
- если growth rate >= 25%, создается `growth_acceleration`;
- если growth rate <= -20%, создается `traffic_decline`.

Severity зависит от силы изменения:

- absolute change >= 50% -> `high`;
- absolute change >= 25% -> `medium`;
- иначе -> `low`.

## Country market signal logic

Для country-level сигналов рассчитываются:

- total traffic;
- first half traffic;
- second half traffic;
- growth rate;
- daily volatility;
- top1 share;
- top3 share;
- active competitors.

Примеры правил:

- высокая daily volatility -> `high_volatility`;
- низкая volatility -> `stable_market`;
- высокая top1 или top3 концентрация -> `high_concentration`;
- мало активных конкурентов при достаточном traffic -> `low_competitive_noise`;
- много конкурентов и низкая top1 доля -> `fragmented_market`;
- высокий рост и высокая концентрация -> `overheated_market`.

## Channel signal logic

Channel signals сравнивают долю канала в первой и второй половине периода.

Если абсолютное изменение доли канала >= 20 percentage points, создается:

```text
channel_shift
```

Пример:

- first half direct share = 30%;
- second half direct share = 55%;
- delta = +25 percentage points;
- создается channel shift signal.

## Expansion signal logic

Expansion signals отслеживают компании, которые расширились в несколько новых стран и одновременно имеют рост traffic.

Правило:

- количество новых стран >= 2;
- growth rate > 20%.

Если условие выполнено, создается:

```text
competitor_expansion
```

## Quality signal logic

Quality signals сравнивают engagement первой и второй половины периода.

Сигнал создается, если:

- bounce rate вырос минимум на 10 percentage points;
- или visit duration упал сильнее чем на 20%.

Тип:

```text
traffic_quality_degradation
```

Severity:

- `high`, если bounce rate вырос минимум на 20 percentage points или duration упал минимум на 40%;
- иначе `medium`.

## Device signal logic

Device signals строятся через Device Intelligence.

Для выбранного scope рассчитываются:

- desktop share;
- mobile share;
- desktop quality index;
- mobile quality index;
- quality gap.

Если Device Intelligence возвращает device-level signals, они сохраняются в `derived_signal` с group:

```text
device
```

## Фильтры внутри Signals

Вкладка Signals имеет дополнительные локальные фильтры:

- Signal group
- Severity

Они не меняют общий Dashboard filter. Они только ограничивают уже сохраненные persisted signals.

## Таблица Derived Signals

Таблица отображает:

| Поле | Значение |
|---|---|
| Severity | Уровень важности сигнала |
| Group | Группа сигнала |
| Type | Конкретное backend rule condition |
| Entity | Тип и идентификатор сущности |
| Period | Период расчета |
| Value / Delta | Основное значение сигнала, delta или delta percent |
| Message | Человекочитаемое объяснение |

Если есть `delta_percent`, таблица показывает его.

Если `delta_percent` нет, но есть `delta_value`, показывается `delta_value`.

Если нет delta, показывается `value`.

Если значения нет, отображается `None`.

## Summary cards

Summary cards показывают агрегированное количество сигналов:

- total signals;
- распределение по группам;
- распределение по severity.

Если выбраны company и competitor scopes, summary отображает их раздельно с общей цветовой логикой:

- company green;
- competitor blue.

Если выбран overall scope, отображается один общий набор summary cards.

## Когда Signals пустые

Signals могут быть пустыми по нескольким причинам:

1. Для выбранного периода еще не нажимали `Recalculate signals`.
2. Сигналы были рассчитаны для другого периода.
3. Сигналы были рассчитаны для другого scope.
4. В данных нет условий, которые активируют правила signals.
5. Выбран локальный фильтр group/severity, под который нет записей.

Пустая таблица не всегда означает ошибку. Иногда это значит, что backend rules не нашли значимых отклонений.

## Как правильно пользоваться Signals

Рекомендуемый flow:

1. Выбрать период.
2. Выбрать country/TLD/company/competitors/domain filters.
3. Перейти на вкладку Signals.
4. Нажать `Recalculate signals`.
5. Проверить summary cards и таблицу.
6. При необходимости ограничить список через Signal group или Severity.
7. После изменения общего фильтра снова нажать `Recalculate signals`.

## Связь со Scoring

Scoring использует Derived Signals как один из источников.

Signals влияют на:

- channel stability;
- entry risk;
- position potential;
- risks;
- strengths;
- weaknesses;
- explanation;
- fallback state.

Если signals отсутствуют, Scoring может использовать fallback для части факторов.

## Ключевые файлы реализации

Frontend:

- `frontend/components/dashboard/derived-signals/derived-signals-section.tsx`
- `frontend/components/dashboard/derived-signals/derived-signal-summary.tsx`
- `frontend/components/dashboard/derived-signals/derived-signal-table.tsx`
- `frontend/lib/api/analytics-queries.ts`
- `frontend/lib/api/analytics.ts`

Backend:

- `backend/app/api/routes/analytics.py`
- `backend/app/analytics/signals/service.py`
- `backend/app/analytics/signals/calculators.py`
- `backend/app/analytics/signals/repository.py`
- `backend/app/analytics/signals/schemas.py`
- `backend/alembic/versions/202606210003_add_derived_signals.py`

