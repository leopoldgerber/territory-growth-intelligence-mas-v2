# Dashboard Scoring Logic

## Назначение

Scoring на Dashboard рассчитывает Opportunity Score — объяснимый country-level показатель привлекательности рынка в выбранном аналитическом scope.

Scoring отвечает на вопрос:

```text
Какие страны выглядят наиболее перспективными по текущим данным и выбранному scope?
```

Opportunity Score не является финальной стратегией, budget decision или автоматической рекомендацией. Это аналитический ranking, который используется как один из входов для дальнейших решений и Reports.

## Главное правило

Scoring работает с сохраненными результатами пересчета.

Это значит:

- вкладка читает данные из таблицы `opportunity_score`;
- если для выбранного периода и scope score не был рассчитан, таблица будет пустой;
- чтобы создать или заменить scores, нужно нажать `Recalculate scores`.

## Scope логика

Scoring использует общий фильтр Dashboard.

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
| Company = None и Competitors = None | Scoring не рассчитывается и не отображается |

Если Company и Competitors оба `All`, отображается общий market-level score.

Если выбран company scope, значения отображаются green.

Если выбран competitor scope, значения отображаются blue.

## Почему при выборе company может быть пусто

Если пользователь выбрал company после того, как scores были рассчитаны только для `overall`, таблица может стать пустой.

Причина:

- `overall`, `company` и `competitor` являются разными persisted scopes;
- Scoring не пересчитывает новый scope автоматически;
- после смены фильтра нужно нажать `Recalculate scores`.

Пример:

1. Было `company=all`, `competitors=all`.
2. Пользователь нажал `Recalculate scores`.
3. Backend сохранил только `overall` scores.
4. Пользователь выбрал `company=company_10`.
5. UI начинает читать `scope=company`.
6. Company scores еще не сохранены.
7. Таблица пустая до нового пересчета.

Это ожидаемая логика.

## Recalculate scores

Кнопка `Recalculate scores` запускает backend endpoint:

```text
POST /analytics/scoring/recalculate
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
3. Определяет scoring scopes.
4. Для каждого scope рассчитывает country metrics.
5. Подтягивает persisted derived signals для этого scope и country.
6. Строит explainable score candidates.
7. Ранжирует страны внутри каждого scope.
8. Удаляет предыдущие persisted scores для проекта, периода и `calculation_version`.
9. Вставляет новые scores.
10. Возвращает количество созданных и замененных записей.

Пример сообщения:

```text
18 scores saved; 18 previous records replaced.
```

Это означает:

- старые scores для выбранного project + period + calculation version были удалены;
- новые scores были сохранены;
- данные в `opportunity_score` заменены для этого периода и версии расчета.

## Важная особенность замены

Удаление старых scores выполняется по:

- project;
- date from;
- date to;
- calculation version.

Поэтому повторный пересчет того же периода заменяет предыдущие scoring records.

## Источники данных

Opportunity Scoring использует:

- country-level traffic metrics;
- traffic growth between period halves;
- traffic quality metrics;
- competitive density;
- concentration metrics;
- persisted Derived Signals;
- fallback calculations, если signals отсутствуют.

Основная fact-база для country-level metrics:

```text
fact_traffic_countries_daily
```

Дополнительный signal input:

```text
derived_signal
```

## Факторы Opportunity Score

Итоговый score строится из восьми факторов.

| Factor | Вес | Что оценивает |
|---|---:|---|
| `market_size` | 18% | Размер рынка по traffic |
| `growth` | 18% | Динамика traffic между половинами периода |
| `traffic_quality` | 16% | Bounce rate, visit duration, pages per visit |
| `competition_level` | 14% | Плотность активных компаний и доменов |
| `concentration` | 12% | Top1 и Top3 traffic share |
| `channel_stability` | 10% | Стабильность каналов на основе channel signals |
| `entry_risk` | 10% | Инвертированный риск на основе risk signals |
| `position_potential` | 12% | Потенциал позиции на основе positive signals |

Веса нормализуются так, чтобы итоговая сумма равнялась 100%.

## Market Size

Market Size показывает относительный размер страны внутри выбранного scope.

Если стран несколько:

- используется traffic percentile среди стран scope.

Если страна одна:

- используется logarithmic fallback относительно reference traffic.

Это нужно, чтобы single-country сценарий не давал искусственно максимальный score без контекста сравнения.

## Growth

Growth сравнивает traffic первой и второй половины периода.

Примеры score:

- новая активность во второй половине -> 75;
- рост >= 50% -> 100;
- рост >= 25% -> 80;
- рост >= 10% -> 65;
- около нуля -> 50;
- умеренное падение -> 35 или 20;
- сильное падение -> 0.

## Traffic Quality

Traffic Quality собирается из:

- average visit duration;
- inverse bounce rate;
- pages per visit.

Текущая внутренняя формула:

- duration score: 35%;
- no-bounce score: 45%;
- pages score: 20%.

## Competition Level

Competition Level оценивает активную конкурентную плотность.

Используются:

- active companies;
- active domains;
- market size score.

Малое количество конкурентов может быть положительным, если рынок не слишком маленький.

Слишком высокая конкурентная плотность снижает score.

## Concentration

Concentration оценивает структуру рынка:

- top1 share;
- top3 share.

Высокая концентрация снижает opportunity score.

Более фрагментированный рынок повышает score, потому что вход или рост позиции потенциально проще.

## Channel Stability

Channel Stability зависит от Derived Signals.

Используются channel shift signals:

- если есть несколько high/critical shifts, score низкий;
- если есть medium shifts, score средний;
- если channel shifts отсутствуют и signals доступны, score выше;
- если derived signals отсутствуют вообще, используется neutral fallback.

Fallback:

```text
score = 50
status = not_available
```

## Entry Risk

Entry Risk является инвертированным score.

Чем меньше риск-сигналов, тем выше score.

Risk signals:

- `high_concentration`
- `overheated_market`
- `traffic_quality_degradation`
- `high_volatility`
- `forgotten_territory`
- `mobile_growth_low_quality`

Severity превращается в penalty:

- critical/high -> 25 points;
- medium -> 15 points;
- low -> 5 points.

Итог:

```text
entry_risk = 100 - penalty
```

## Position Potential

Position Potential начинается с neutral baseline:

```text
50
```

Positive signals добавляют bonus.

Positive signals:

- `growth_acceleration`
- `low_competitive_noise`
- `fragmented_market`
- `new_territory`
- `stable_market`
- `small_but_growing`

Bonus:

- critical/high -> 20 points;
- medium -> 12 points;
- low -> 5 points.

Итог:

```text
position_potential = 50 + bonus
```

## Score category

Final Opportunity Score классифицируется так:

| Category | Range |
|---|---:|
| `very_high` | 80-100 |
| `high` | 65-79.9999 |
| `medium` | 50-64.9999 |
| `low` | 35-49.9999 |
| `very_low` | 0-34.9999 |

## Factor status

Каждый factor имеет status:

| Status | Значение |
|---|---|
| `strong` | factor score >= 75 |
| `moderate` | factor score > 40 и < 75 |
| `weak` | factor score <= 40 |
| `not_available` | исходных данных нет, используется fallback |

## Ranking

Страны ранжируются отдельно внутри каждого scope.

Порядок сортировки:

1. Opportunity Score по убыванию.
2. Market Size score по убыванию.
3. Growth score по убыванию.
4. Traffic Quality score по убыванию.
5. Country name по возрастанию.

Если выбраны company и competitors одновременно, company и competitor получают отдельные ranking внутри своих scopes.

## Таблица Scoring

Таблица показывает:

- Rank;
- Country;
- Scope;
- Score;
- Category;
- Market Size;
- Growth;
- Quality;
- Competition;
- Concentration;
- Channel Stability;
- Entry Risk;
- Position Potential.

При выборе строки отображается detail-блок.

## Detail-блок

Detail-блок показывает:

- summary explanation;
- final score;
- category;
- factor breakdown;
- raw values;
- score по каждому фактору;
- factor weight;
- weighted score;
- factor status;
- explanation;
- strengths;
- weaknesses;
- risks;
- signals used;
- fallbacks used.

## Fallback logic

Если Derived Signals не найдены, Scoring не падает.

Он использует fallback для факторов, которым нужны signals.

Основной fallback сейчас:

```text
channel_stability = 50
status = not_available
```

Когда fallback активен, UI показывает alert:

```text
Scoring fallback is active.
Derived signals were not found for this period. Some scoring factors use fallback calculations.
```

Это не ошибка, но качество объяснения ниже, потому что часть score рассчитана без persisted signals.

## Связь со Signals

Рекомендуемый порядок:

1. Выбрать общий Dashboard filter.
2. Перейти на Signals.
3. Нажать `Recalculate signals`.
4. Перейти на Scoring.
5. Нажать `Recalculate scores`.

Так Scoring сможет использовать свежие derived signals.

Если сначала пересчитать Scoring без Signals, score будет создан, но часть факторов может работать через fallback.

## Как правильно пользоваться Scoring

Market-level сценарий:

1. Company = All.
2. Competitors = All.
3. Выбрать period/country/TLD при необходимости.
4. Нажать `Recalculate scores`.
5. Смотреть общий country ranking.

Company-specific сценарий:

1. Выбрать одну или несколько Company.
2. Competitors можно оставить `None` или выбрать отдельно.
3. При необходимости выбрать Company Domain.
4. Нажать `Recalculate scores`.
5. Смотреть company scope в green.

Competitor scenario:

1. Company = None.
2. Выбрать одного или нескольких Competitors.
3. При необходимости выбрать Competitors Domain.
4. Нажать `Recalculate scores`.
5. Смотреть competitor scope в blue.

Comparison scenario:

1. Выбрать Company.
2. Выбрать Competitors.
3. Нажать `Recalculate scores`.
4. Смотреть две группы строк:
   - company scope green;
   - competitor scope blue.

## Когда Scoring пустой

Scoring может быть пустым по нескольким причинам:

1. Scores еще не пересчитывались для выбранного period/scope.
2. Выбран scope, для которого нет persisted records.
3. Для выбранного scope нет country-level fact data.
4. Company или competitors установлены в `None` одновременно.
5. Выбран country/TLD/domain, где нет данных по этому scope.

Пустая таблица не всегда означает ошибку. Чаще всего это значит, что нужно нажать `Recalculate scores` после изменения фильтра.

## Связь с Reports

Reports Budget Strategy использует Opportunity Score как один из входов.

Если score для выбранной страны или scope отсутствует, Reports может:

- использовать fallback;
- показать warning;
- или не сгенерировать стратегию, если входных данных недостаточно.

Поэтому перед генерацией Reports желательно:

1. Проверить Dashboard filters.
2. Пересчитать Signals.
3. Пересчитать Scoring.
4. Убедиться, что нужная страна и scope отображаются в Scoring.

## Ключевые файлы реализации

Frontend:

- `frontend/components/dashboard/opportunity-scoring/opportunity-scoring-section.tsx`
- `frontend/components/dashboard/opportunity-scoring/scoring-summary-cards.tsx`
- `frontend/components/dashboard/opportunity-scoring/scoring-ranking.tsx`
- `frontend/lib/api/analytics-queries.ts`
- `frontend/lib/api/analytics.ts`

Backend:

- `backend/app/api/routes/analytics.py`
- `backend/app/analytics/scoring/service.py`
- `backend/app/analytics/scoring/calculators.py`
- `backend/app/analytics/scoring/repository.py`
- `backend/app/analytics/scoring/schemas.py`
- `backend/alembic/versions/202606210005_add_opportunity_scores.py`

