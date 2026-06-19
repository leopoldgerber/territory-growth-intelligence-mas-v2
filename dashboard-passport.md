# Паспорт страницы Dashboard

## 1. Назначение

`Dashboard` — рабочая страница ручной аналитики и исследования рынков. Она не формирует MAS-рекомендации и отчёты, а показывает рассчитанные показатели по загруженным данным.

Текущий маршрут:

```text
/dashboard
```

Основной источник данных:

```text
fact_traffic_countries_daily
```

Гранулярность источника:

```text
date + company + domain + country
```

## 2. Текущее содержимое страницы

Страница состоит из следующих блоков:

1. Заголовок `Market exploration dashboard`.
2. Общая панель фильтров.
3. `Market Overview` — placeholder, аналитика ещё не реализована.
4. Внутренняя tab-панель аналитики:
   - `Country Intelligence` — первая вкладка;
   - `Competitor Intelligence` — вторая вкладка.
6. `Channel Intelligence` — future placeholder.
7. `Device Intelligence` — future placeholder.

Обе вкладки находятся внутри Dashboard и используют одну общую панель фильтров. Отдельная top-level страница для конкурентов не используется.

## 3. Технологическое устройство

### Frontend

- Next.js 15, React 19, TypeScript.
- TanStack Query для загрузки аналитики.
- Tailwind CSS и локальные UI-компоненты.
- Состояние фильтров хранится в URL query params.
- API client: `frontend/lib/api/analytics.ts`.
- Query hooks: `frontend/lib/api/analytics-queries.ts`.
- Типы ответов: `frontend/lib/types/analytics.ts`.
- Страница: `frontend/app/dashboard/page.tsx`.

### Backend

- FastAPI.
- SQLAlchemy ORM и SQL-агрегации.
- PostgreSQL.
- Analytics routes: `backend/app/api/routes/analytics.py`.
- Pydantic schemas: `backend/app/schemas/analytics.py`.
- Country service: `backend/app/analytics/country_intelligence.py`.
- Competitor service: `backend/app/analytics/competitor_intelligence.py`.

### Database

Для аналитики используются составные индексы по `project_id`, дате, стране, компании и домену. Актуальная локальная Alembic revision:

```text
202606190001
```

Материализованные представления и фоновые пересчёты для Dashboard не используются.

## 4. Фильтры Dashboard

### URL-параметры

```text
dateFrom
dateTo
country
tld
company
companyDomain
competitors
competitorDomain
intelligence
```

Значения по умолчанию:

```text
dateFrom=2025-01-01
dateTo=2025-02-01
country=all
tld=all
company=all
companyDomain=all
competitors=all
competitorDomain=all
intelligence=country
```

`intelligence` хранит активную внутреннюю вкладку (`country` или `competitor`) и не является аналитическим фильтром.

### Множественный выбор

Несколько значений записываются в один URL-параметр через запятую:

```text
country=USA,DEU,FRA
company=1,2
competitors=3,4
```

### Семантика специальных значений

- `all` — использовать все доступные значения и не добавлять ограничение по этому измерению.
- `none` — область не выбрана. Поддерживается для `company` и `competitors`.
- Одна или несколько записей — ограничить расчёт перечисленными значениями.

### Взаимозависимость фильтров

Опции фильтров рассчитываются endpoint `GET /analytics/filter-options` по данным за выбранный период.

- Выбор стран ограничивает доступные компании, домены и TLD значениями, у которых есть данные в этих странах.
- Выбор компании и/или её домена ограничивает список стран странами присутствия этой области.
- Выбор конкурентов и/или их доменов аналогично ограничивает список стран.
- Если одновременно выбраны компания и конкуренты, страны формируются по пересечению доступности обеих активных областей.
- `Company Domain` зависит от выбранной компании и TLD.
- `Competitors Domain` зависит от выбранных конкурентов и TLD.
- Недоступные после изменения соседнего фильтра значения автоматически удаляются из выбора.
- Выпадающие списки закрываются кликом вне фильтра или клавишей `Escape`.

## 5. Analytics API

### Filter options

```text
GET /analytics/filter-options
```

Возвращает:

- страны;
- TLD;
- компании;
- домены с привязкой к компании и TLD.

### Country Intelligence

```text
GET /analytics/country-intelligence
```

Использует общий фильтр страны, TLD и периода, а также две отдельные области:

- `company + companyDomain`;
- `competitors + competitorDomain`.

### Competitor Intelligence

```text
GET /analytics/competitor-intelligence
```

Использует:

- период;
- множественный фильтр стран;
- TLD;
- `competitors`;
- `competitorDomain`;
- `limit`.

Фильтр основной компании на расчёт Competitor Intelligence не влияет.

## 6. Country Intelligence — актуальное техническое состояние

### Backend

Реализованы отдельные SQL-агрегации для области компании и области конкурентов:

- summary;
- daily traffic trend;
- desktop/mobile split;
- bounce/no-bounce;
- engagement;
- market signal;
- top competitors;
- количество выбранных стран.

Ответ содержит параллельные структуры:

```text
summary / competitor_summary
traffic_trend / competitor_traffic_trend
device_split / competitor_device_split
bounce / competitor_bounce
engagement / competitor_engagement
market_signal / competitor_market_signal
```

### Frontend

Компонент:

```text
frontend/components/dashboard/country-intelligence/country-intelligence-section.tsx
```

Отображаются:

- Total Traffic;
- Active Companies;
- Active Domains;
- Selected Countries;
- Selected Period;
- Top Competitors;
- Traffic Trend;
- Desktop/Mobile Split;
- Bounce/No-Bounce;
- Engagement;
- Market Signal.

Цветовая логика:

- компания — зелёный;
- конкуренты — синий;
- компания и конкуренты одновременно — два значения через `|`;
- отсутствующая область `None` не отображается;
- выбранная область без данных отображает `0`;
- при одинаковых `Company = All` и `Competitors = All` с одинаковыми domain-фильтрами показывается одно нейтральное значение.

Для Market Signal есть кнопка с вопросительным знаком. Она открывает окно с описанием всех типов сигнала и закрывается повторным нажатием, кликом снаружи или `Escape`.

### Состояния интерфейса

- Loading — skeleton.
- API error — destructive alert.
- Нет ответа — empty state.
- `Company = None` и `Competitors = None` — сообщение о необходимости выбрать область.
- Выбранная область без данных не скрывает карточки: показатели выводятся как нулевые.

## 7. Country Intelligence — логика расчётов

### Общий scope

Обе области используют одинаковые ограничения:

```text
project_id
dateFrom/dateTo
country
tld
```

Затем применяются собственные company/domain-фильтры.

### Summary

- `total_traffic` — сумма `traffic`.
- `active_companies` — число уникальных `company_id` со значением `traffic > 0`.
- `active_domains` — число уникальных `domain_id` со значением `traffic > 0`.
- `country_count` — число уникальных стран.
- `date_count` — число уникальных дат.
- `selected_country_count` — число уникальных стран в объединении областей компании и конкурентов.

### Traffic Trend

Трафик суммируется по каждой дате. Во frontend отображаются последние 14 доступных точек. Шкала компании и конкурентов общая, поэтому длины полос сопоставимы.

### Device Split

```text
desktop_traffic = sum(desktop_share_traffic)
mobile_traffic = sum(mobile_share_traffic)
desktop_share = desktop_traffic / (desktop_traffic + mobile_traffic)
mobile_share = mobile_traffic / (desktop_traffic + mobile_traffic)
```

### Bounce

```text
no_bounce = sum(traffic_no_bounce)
bounce = sum(traffic_bounce)
bounce_rate = bounce / (bounce + no_bounce)
```

### Engagement

- `unique_visitors` — сумма уникальных посетителей из fact-строк.
- `pages_per_visit` — средневзвешенное по traffic.
- `avg_visit_duration` — средневзвешенное по traffic.

### Market Signal

Набор дневных точек делится на первую и вторую половины. Сравнивается суммарный трафик двух частей.

- `no_data` — трафик отсутствует.
- `insufficient_data` — меньше двух дат.
- `new_activity` — в первой половине трафика нет, во второй он появился.
- `falling` — growth rate не выше `-10%`.
- `stable` — growth rate от `-5%` до `5%`.
- `promising` — рост не ниже `10%`, доля лидера ниже `40%`, bounce rate ниже `55%`.
- `overheated` — рост не ниже `10%`, доля лидера не ниже `50%`.
- `growing` — рост не ниже `10%`, но условия `promising/overheated` не выполнены.
- `mixed` — остальные случаи.

Формула:

```text
growth_rate = (second_half_traffic - first_half_traffic) / first_half_traffic
```

## 8. Competitor Intelligence — актуальное техническое состояние

### Backend

Реализован отдельный service layer:

```text
backend/app/analytics/competitor_intelligence.py
```

Основная агрегация выполняется по странам одним SQL-запросом. Дополнительно рассчитываются distinct domains и active days.

Ответ содержит:

- summary;
- top countries;
- growing countries;
- declining countries;
- anchor markets;
- peripheral markets;
- country dependency;
- presence stability;
- market windows.

### Frontend

Компоненты:

```text
frontend/components/dashboard/competitor-intelligence/
```

Реализованы:

- пять summary-карточек;
- таблица Top Countries;
- таблицы Growing Countries и Declining Countries;
- списки Anchor Markets и Peripheral Markets;
- Country Dependency;
- Presence Stability;
- Market Windows.

Цветовая логика:

- выбран один или несколько конкурентов — показатели синие;
- `Competitors = All` — единая агрегированная область и нейтральный цвет;
- `Competitors = None` — select-state без расчётных карточек.

### Состояния интерфейса

- Loading — skeleton.
- API error — destructive alert.
- `Competitors = None` — предложение выбрать конкурента или `All`.
- Нет данных по активным фильтрам — отдельный empty state.
- Данные есть — полный аналитический блок.

## 9. Competitor Intelligence — логика расчётов

### Scope

```text
project_id
dateFrom/dateTo
country
tld
competitors
competitorDomain
```

При множественном выборе показатели конкурентов суммируются. Аналитика описывает объединённую выбранную конкурентную область.

### Summary

- `total_traffic` — сумма трафика выбранной области.
- `active_countries` — число стран с `traffic > 0`.
- `active_domains` — число уникальных доменов с `traffic > 0`.
- `top_country` — страна с максимальным трафиком.
- `top_country_share` — доля top country в общем трафике области.
- `growth_rate` — изменение суммарного трафика между половинами периода.

### Деление периода

Competitor Intelligence делит календарный диапазон пополам по дате:

```text
first half: date <= midpoint
second half: date > midpoint
```

### Country metrics

Для каждой страны рассчитываются:

```text
traffic
traffic_share
first_half_traffic
second_half_traffic
growth_rate
growth_status
market status
```

Growth statuses:

- `new_activity` — первая половина равна `0`, вторая больше `0`;
- `growing` — growth rate не ниже `10%`;
- `declining` — growth rate не выше `-10%`;
- `stable` — остальные ненулевые случаи;
- `no_data` — трафик равен `0`.

### Anchor Markets

Страна считается anchor market, если:

```text
traffic_share >= 0.15
or rank <= 3
```

### Peripheral Markets

Страна считается peripheral market, если:

```text
traffic_share < 0.05
and country is not an anchor market
```

### Country Dependency

```text
top1_country_share = доля первой страны
top3_country_share = сумма долей трёх первых стран
```

Уровень зависимости:

- `high` — top 1 не ниже `50%` или top 3 не ниже `80%`;
- `medium` — top 1 не ниже `30%` или top 3 не ниже `60%`;
- `low` — остальные случаи.

### Presence Stability

```text
active_days = count distinct date where traffic > 0
period_days = календарное число дней между dateFrom и dateTo включительно
stability_rate = active_days / period_days
```

Статусы:

- `stable` — не ниже `80%`;
- `irregular` — от `40%` до `80%`;
- `weak` — ниже `40%`.

### Market Windows

Market Windows — rule-based аналитические сигналы, а не рекомендации.

- `declining_presence` — country growth rate не выше `-10%`.
- `small_but_growing` — country share ниже `5%`, growth rate не ниже `20%`.
- `low_stability` — stability rate ниже `40%`.
- `high_dependency` — dependency level равен `high`.

## 10. Производительность

Используются индексы:

```text
(project_id, date)
(project_id, country_id, date)
(project_id, domain_id, date)
(project_id, company_id, date)
(project_id, country_id, domain_id, date)
(project_id, company_id, country_id, date)
(project_id, domain_id, country_id, date)
```

## 11. Актуальный статус проверок

На момент обновления паспорта:

- backend Ruff — успешно;
- backend compileall — успешно;
- FastAPI route smoke-check — успешно;
- Competitor Intelligence runtime-запрос к локальной PostgreSQL — успешно;
- Alembic upgrade до `202606190001` — успешно;
- frontend ESLint — успешно;
- frontend TypeScript typecheck — успешно;
- отдельный набор unit/integration-тестов для Dashboard пока отсутствует;
- визуальная browser-проверка последнего Competitor Intelligence блока не завершена из-за локальной ошибки фонового запуска процессов `Path/PATH` в рабочей сессии.

## 12. Текущие границы Dashboard

На странице пока не реализованы:

- Market Overview analytics;
- Channel Intelligence;
- Device Intelligence;
- MAS-рекомендации;
- генерация Reports;
- opportunity score;
- budget strategy;
- фоновые аналитические пересчёты;
- materialized views.

Country Intelligence и Competitor Intelligence являются ручным аналитическим слоем и могут позднее использоваться MAS как источник структурированных показателей.
