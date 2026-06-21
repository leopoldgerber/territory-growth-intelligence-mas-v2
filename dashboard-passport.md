# Паспорт страницы Dashboard

## 1. Общая информация

**Страница:** `Dashboard`

**Маршрут:** `/dashboard`

**Назначение:** ручное исследование рыночного присутствия компаний и конкурентов по странам, каналам, устройствам и производным аналитическим сигналам.

**Состояние документа:** актуально на 2026-06-21.

**Текущая Alembic revision:** `202606210006`.

Dashboard является аналитическим рабочим пространством. Он показывает вычисляемые показатели и объяснимые rule-based сигналы, но не создаёт итоговые рекомендации, автоматические стратегии или MAS-решения.

Проект в интерфейсе не выбирается. Backend использует внутренний `DEFAULT_PROJECT_ID` как технический scope данных.

## 2. Состав страницы

Страница содержит:

1. Заголовок `Market exploration dashboard`.
2. Единую панель общих фильтров.
3. Внутреннюю панель из шести аналитических вкладок:
   - `Market Overview`;
   - `Countries`;
   - `Channels`;
   - `Devices`;
   - `Signals`.
   - `Scoring`.

Общие фильтры сохраняются при переключении вкладок. Активная вкладка хранится в URL-параметре `intelligence`.

## 3. Технологический стек

### Frontend

- Next.js 15;
- React 19;
- TypeScript 5;
- TanStack Query 5;
- Tailwind CSS 3;
- Lucide React;
- Next Themes;
- локальные UI-компоненты проекта.

Основные файлы:

```text
frontend/app/dashboard/page.tsx
frontend/components/dashboard/dashboard-filters.tsx
frontend/components/dashboard/dashboard-intelligence-tabs.tsx
frontend/lib/dashboard/query-params.ts
frontend/lib/api/analytics.ts
frontend/lib/api/analytics-queries.ts
frontend/lib/types/analytics.ts
```

### Backend

- Python 3.11+;
- FastAPI;
- SQLAlchemy 2;
- Pydantic;
- PostgreSQL;
- Alembic.

Основные файлы:

```text
backend/app/api/routes/analytics.py
backend/app/schemas/analytics.py
backend/app/analytics/country_intelligence.py
backend/app/analytics/competitor_intelligence.py
backend/app/analytics/channel_intelligence.py
backend/app/analytics/device_intelligence.py
backend/app/analytics/signals/
```

## 4. Источники данных

### Market Overview и Countries

```text
fact_traffic_countries_daily
```

Основная гранулярность:

```text
date + project_id + company_id + domain_id + country_id
```

### Channels

```text
fact_traffic_sources_daily
fact_journey_sources_daily
```

`fact_traffic_sources_daily` содержит агрегаты direct, search, paid, referral и social.

`fact_journey_sources_daily` содержит source type, traffic type, search source и traffic.

### Devices

```text
fact_device_trends_daily
```

Таблица содержит desktop/mobile visits, unique users, bounce/no-bounce и duration.

### Signals

```text
derived_signal
```

Сигналы сохраняются в БД после явного пересчёта. Поле `scope` принимает значения:

```text
overall
company
competitor
```

### Scoring

```text
opportunity_score
```

Содержит сохранённый country-level ranking, восемь факторных scores, category, strengths, weaknesses, risks и explainable breakdown.

## 5. Общие фильтры

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

### Множественный выбор

Несколько значений сохраняются через запятую:

```text
country=USA,DEU,FRA
company=10,12
competitors=1,2
```

### Специальные значения

- `all` — не ограничивать соответствующий scope.
- `none` — не выбирать scope. Поддерживается для Company и Competitors.
- одно значение — применить точный фильтр;
- несколько значений — применить фильтр по перечисленному набору.

Если Company и Competitors равны `None`, сравнительные показатели не отображаются.

### Фильтр TLD

Фильтр ограничивает домены по домену верхнего уровня, например:

```text
com
ru
de
eu
```

При изменении TLD списки Company Domain и Competitor Domain пересчитываются.

### Связь company и domain

- Company Domain показывает только домены выбранных Company.
- Competitor Domain показывает только домены выбранных Competitors.
- При `Company = All` доступны домены всех компаний.
- При `Competitors = All` доступны домены всех конкурентов.
- Недоступные после изменения родительского фильтра значения удаляются из выбора.

### Связь стран с компаниями и конкурентами

Доступные страны формируются по объединению присутствия обеих сторон:

```text
Countries(company scope) UNION Countries(competitor scope)
```

Следствия:

- страна доступна, если данные есть хотя бы у Company или хотя бы у Competitors;
- общая страна не обязана присутствовать у обеих сторон;
- если в выбранной стране у одной стороны нет данных, её показатели равны `0`;
- выбор страны ограничивает доступные компании и домены данными, присутствующими в этой стране;
- выбор компаний или доменов ограничивает список стран их фактическим присутствием.

Опции загружаются через:

```text
GET /analytics/filter-options
```

### Поведение элементов фильтра

- даты сохраняются в URL в формате `YYYY-MM-DD`;
- выпадающие списки закрываются повторным нажатием, кликом вне компонента или `Escape`;
- кнопка очистки возвращает общие фильтры к значениям по умолчанию;
- фильтры автоматически запускают повторные GET-запросы TanStack Query;
- пересчёт Signals является отдельной POST-операцией.

## 6. Общая логика scopes

Сравнительные вкладки используют два независимых scope:

```text
company + companyDomain
competitors + competitorDomain
```

Общие ограничения для обоих scope:

```text
project_id
dateFrom/dateTo
country
tld
```

### Режим All/All

Если Company, Company Domain, Competitors и Competitor Domain одновременно равны `all`, backend возвращает один `overall_scope`. Интерфейс показывает одно нейтральное значение без искусственного дублирования Company/Competitors.

### Раздельный режим

При любом явном выборе используются отдельные `company_scope` и `competitor_scope`.

- Company отображается зелёным: `emerald-500`.
- Competitors отображаются синим: `sky-500`.
- Два значения выводятся через `|`.
- Scope со значением `None` не отображается.
- Выбранный scope без данных отображает нулевые показатели.

Пример:

```text
125 000 | 98 000
company   competitors
```

## 7. Вкладка Market Overview

### Назначение

Общий сравнительный обзор трафика Company и Competitors в выбранных странах и периоде.

### API

```text
GET /analytics/country-intelligence
```

### Основные блоки

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

### Summary

```text
total_traffic = SUM(traffic)
active_companies = COUNT(DISTINCT company_id WHERE traffic > 0)
active_domains = COUNT(DISTINCT domain_id WHERE traffic > 0)
selected_country_count = COUNT(DISTINCT country_id across company and competitor scopes)
```

`Selected Countries` показывает количество выбранных или фактически попавших в scope стран, а не их сокращённые названия.

### Traffic Trend

Трафик суммируется по дате. Company и Competitors используют общую шкалу, поэтому значения визуально сопоставимы.

### Device Split

```text
desktop_share = desktop_traffic / (desktop_traffic + mobile_traffic)
mobile_share = mobile_traffic / (desktop_traffic + mobile_traffic)
```

### Bounce

```text
bounce_rate = bounce / (bounce + no_bounce)
```

### Engagement

- Unique Visitors — сумма доступных unique visitor показателей;
- Pages per Visit — средневзвешенное по traffic;
- Average Visit Duration — средневзвешенное по traffic.

### Market Signal

Период делится на первую и вторую половины:

```text
growth_rate = (second_half_traffic - first_half_traffic) / first_half_traffic
```

Статусы:

- `no_data` — трафик отсутствует;
- `insufficient_data` — недостаточно дат для сравнения;
- `new_activity` — трафик появился только во второй половине;
- `falling` — снижение не менее 10%;
- `stable` — изменение находится примерно в диапазоне от -5% до 5%;
- `promising` — рост не менее 10%, умеренная концентрация и приемлемый bounce rate;
- `overheated` — рост сочетается с высокой концентрацией лидера;
- `growing` — рост не менее 10% без условий promising/overheated;
- `mixed` — остальные комбинации.

Информационное окно Market Signal содержит расшифровку всех статусов.

## 8. Вкладка Countries

### Назначение

Анализ географического присутствия выбранного competitor scope. Фильтр основной Company не участвует в расчёте этой вкладки.

### API

```text
GET /analytics/competitor-intelligence
```

### Основные блоки

- summary competitor presence;
- Top Countries;
- Growing Countries;
- Declining Countries;
- Anchor Markets;
- Peripheral Markets;
- Country Dependency;
- Presence Stability;
- Market Windows.

### Growth Rate

Выбранный период делится на две половины:

```text
growth_rate = (second_half_traffic - first_half_traffic) / first_half_traffic
```

Growth statuses:

- `no_data` — данных нет;
- `new_activity` — активность появилась во второй половине;
- `growing` — рост не менее 10%;
- `declining` — снижение не менее 10%;
- `stable` — изменение не достигло порога 10%.

### Market role

- `anchor` — страна входит в top 3 или даёт не менее 15% трафика;
- `established` — доля от 5% до 15% вне top 3;
- `peripheral` — доля ниже 5% вне top 3.

### Country Dependency

- `low` — top 1 ниже 30% и top 3 ниже 60%;
- `medium` — top 1 не менее 30% или top 3 не менее 60%;
- `high` — top 1 не менее 50% или top 3 не менее 80%.

### Presence Stability

```text
stability_rate = active_days / period_days
```

- `stable` — активность не менее чем в 80% дней;
- `irregular` — от 40% до 79.9%;
- `weak` — менее 40%.

### Market Windows

- `declining_presence` — снижение трафика страны;
- `small_but_growing` — доля ниже 5%, рост не менее 20%;
- `low_stability` — активность менее чем в 40% дней;
- `high_dependency` — высокая концентрация в ведущих странах.

## 9. Вкладка Channels

### Назначение

Сравнение состава каналов Company и Competitors без разделения интерфейса на отдельные блоки.

### API

```text
GET /analytics/channel-intelligence
```

### Структура ответа

```text
combined_scopes
overall_scope
company_scope
competitor_scope
```

Каждый scope содержит:

- summary;
- channel mix;
- company channel dependency;
- channel skews;
- paid/organic summary;
- source type breakdown;
- traffic type breakdown;
- top journey sources;
- opportunity signals.

### Channel Mix

Каналы:

```text
direct
search
paid
referral
social
```

```text
total_channel_traffic = direct + search + paid + referral + social
channel_share = channel_traffic / total_channel_traffic
```

### Dependency

- `low` — dominant share ниже 40%;
- `medium` — от 40% до 59.9%;
- `high` — не менее 60%.

### Channel Skews

- `brand_dependency` — direct не менее 60%;
- `seo_dependency` — search не менее 60%;
- `paid_dependency` — paid не менее 35%;
- `referral_dependency` — referral не менее 30%;
- `social_dependency` — social не менее 25%;
- `balanced_mix` — ни один канал не достигает 40%.

### Paid / Organic

Journey traffic классифицируется как paid, organic или unknown. Если traffic type не определён и source type не указывает paid, значение попадает в unknown.

### Opportunity Signals

- `high_search_share` — search не менее 40%;
- `meaningful_paid_share` — paid не менее 20%;
- `visible_referral_share` — referral не менее 15%;
- `visible_social_share` — social не менее 15%;
- `high_direct_share` — direct не менее 50%;
- `low_*_share` — соответствующий канал не превышает 3%.

Карточки, полосы и таблицы используют единое зелёно-синее разделение scope.

## 10. Вкладка Devices

### Назначение

Сравнение desktop/mobile трафика и качества аудитории между Company и Competitors.

### API

```text
GET /analytics/device-intelligence
```

### Структура ответа

```text
combined_scopes
overall_scope
company_scope
competitor_scope
```

Каждый scope содержит:

- summary;
- quality;
- bounce split;
- daily device trend;
- company device quality;
- device signals.

### Цветовая семантика

Scope:

- Company — зелёный;
- Competitors — синий;
- Overall — нейтральный.

Тип устройства:

- Desktop — `#FB7185`;
- Mobile — `#FDBA74`.

Цвет устройства используется в легендах, названиях столбцов и split-полосах. Цвет числового значения используется для определения company/competitor scope.

### Summary

- Total Visits;
- Desktop Visits;
- Mobile Visits;
- Desktop Share;
- Mobile Share;
- Dominant Device.

`Dominant Device`:

- Desktop — desktop visits больше или равны mobile visits;
- Mobile — mobile visits больше desktop visits;
- None — visits отсутствуют.

### Device Quality Index

```text
duration_score = MIN(MAX(duration, 0) / 180, 1)
no_bounce_rate = MIN(MAX(1 - bounce_rate, 0), 1)
quality_index = duration_score * 0.5 + no_bounce_rate * 0.5
quality_gap = desktop_quality_index - mobile_quality_index
```

Индекс является сравнительным аналитическим показателем, а не итоговым score или рекомендацией.

### Company Device Quality statuses

- `mobile_quality_gap`;
- `desktop_quality_advantage`;
- `mobile_strength`;
- `balanced_device_quality`;
- `mixed_device_quality`.

### Device Signals

- `mobile_new_activity`;
- `mobile_growth_low_quality`;
- `desktop_quality_advantage`;
- `mobile_strength`;
- `balanced_device_quality`.

Информационные окна содержат правила интерпретации этих значений.

## 11. Вкладка Signals

### Назначение

Хранение и просмотр объяснимых rule-based аналитических наблюдений. Сигналы не являются рекомендациями и не заменяют исходные показатели вкладок.

### API

```text
POST /analytics/signals/recalculate
GET  /analytics/signals
GET  /analytics/signals/summary
POST /analytics/scoring/recalculate
GET  /analytics/scoring/opportunities
GET  /analytics/scoring/summary
```

### Жизненный цикл

1. Пользователь задаёт общие Dashboard-фильтры.
2. Нажимает `Recalculate signals`.
3. Backend рассчитывает сигналы отдельно по overall либо по company/competitor scopes.
4. Предыдущие записи для того же project, периода и calculation version удаляются.
5. Новые записи сохраняются в `derived_signal`.
6. GET endpoints возвращают сохранённые записи по периоду, scope, group и severity.

После изменения общих фильтров необходимо повторно нажать `Recalculate signals`. До пересчёта сохранённые записи представляют последний выполненный расчёт соответствующего периода.

### Scope

- `overall` — используется при полном `All/All`;
- `company` — сигналы company scope;
- `competitor` — сигналы competitor scope.

Scope входит в детерминированный `signal_key`, поэтому одинаковый тип сигнала может независимо существовать для Company и Competitors.

### Внутренние фильтры

Внутренние фильтры не относятся к общей панели:

```text
signalGroup
severity
```

Они фильтруют уже сохранённые сигналы и хранятся в URL.

### Signal Groups

- `all` — все группы;
- `growth` — рост, падение и новая активность;
- `volatility` — стабильность и волатильность;
- `competition` — концентрация, фрагментация и расширение;
- `territory` — новое или утраченное присутствие;
- `channel` — изменение долей каналов;
- `quality` — ухудшение engagement quality;
- `device` — различия desktop/mobile.

### Severity

- `low` — информационное или раннее условие;
- `medium` — существенное условие для наблюдения;
- `high` — сильное отклонение или повышенный риск;
- `critical` — зарезервированный максимальный уровень. Текущие calculators его не создают.

Общее правило severity для относительных изменений:

```text
abs(change_rate) >= 50% -> high
abs(change_rate) >= 25% -> medium
иначе -> low
```

Некоторые сигналы задают severity собственным правилом.

### Основные правила Signals

Growth:

- new activity — первая половина равна нулю, во второй есть трафик;
- growth acceleration — рост не менее 25%;
- traffic decline — снижение не менее 20%.

Volatility:

- high volatility — коэффициент дневной волатильности не менее 35%;
- stable market — волатильность не выше 10%.

Competition и Territory:

- high concentration — top 1 не менее 50% или top 3 не менее 80%;
- low competitive noise — не более трёх активных компаний при достаточном трафике;
- fragmented market — top 1 ниже 25% при восьми и более активных компаниях;
- overheated market — рост не менее 20% при top 1 не менее 50%;
- competitor expansion — минимум две новые страны и рост выше 20%;
- new territory — значимая активность появилась во второй половине;
- forgotten territory — трафик снизился почти до неактивного состояния.

Channel:

- channel shift — абсолютное изменение доли канала не менее 20 процентных пунктов.

Quality:

- traffic quality degradation — bounce rate вырос минимум на 10 п.п. или duration снизился минимум на 20%.

Device:

- используются Device Signals из вкладки Devices.

### Таблица Derived Signals

Столбцы:

- Severity;
- Group;
- Type;
- Entity;
- Period;
- Value / Delta;
- Message.

Логика `Value / Delta`:

```text
delta_percent -> delta_value -> value -> None
```

Используется первое доступное значение. Если правило не сработало, отдельная строка сигнала не создаётся.

Все поля таблицы, внутренние фильтры и summary-карточки имеют информационные окна.

## 12. Информационные окна

Компонент:

```text
frontend/components/dashboard/information-popover.tsx
```

Поведение:

- открывается кнопкой с вопросительным знаком;
- рендерится через portal в `document.body`;
- позиционируется относительно viewport;
- открывается сверху, если снизу недостаточно места;
- не сдвигает содержимое страницы;
- закрывается повторным нажатием, кликом вне окна или `Escape`;
- пересчитывает позицию при scroll и resize.

Справки добавлены для расчётных показателей и всех классификаций с несколькими статусами.

## 13. API endpoints

```text
GET  /analytics/filter-options
GET  /analytics/country-intelligence
GET  /analytics/competitor-intelligence
GET  /analytics/channel-intelligence
GET  /analytics/device-intelligence
POST /analytics/signals/recalculate
GET  /analytics/signals
GET  /analytics/signals/summary
```

GET-запросы используют TanStack Query. Query keys включают влияющие Dashboard-фильтры, поэтому смена фильтра создаёт отдельный cache key и инициирует загрузку актуального ответа.

## 14. Состояния интерфейса

Каждая аналитическая вкладка обрабатывает:

- loading — skeleton;
- API error — destructive alert;
- отсутствующий response — unavailable state;
- отсутствие данных — информационный alert или пустое состояние блока;
- выбранный scope без данных — нулевые показатели;
- оба scope равны None — предложение выбрать Company или Competitors.

Таблицы используют горизонтальный scroll при недостаточной ширине. Навигация по вкладкам поддерживает мышь и клавиши `ArrowLeft`, `ArrowRight`, `Home`, `End`.

## 15. Кэширование и обновление

- TanStack Query кэширует GET-ответы по query key.
- Изменение URL-фильтра приводит к новому query key.
- Успешный Signals recalculation инвалидирует списки и summary Signals.
- Redis не участвует в расчётах Dashboard; он требуется для ingestion worker.
- Dashboard читает уже загруженные данные из PostgreSQL.

## 16. Производительность

- основные метрики вычисляются SQL-агрегациями;
- аналитические таблицы имеют индексы по project, date, company, domain и связанным измерениям;
- Channel, Device и Derived Signals получили дополнительные индексы в миграциях этапов 8–10;
- derived signals сохраняются, а не пересчитываются при каждом GET;
- materialized views для Dashboard не используются.

## 17. Миграции

Актуальный head:

```text
202606210006
```

Последние аналитические миграции:

```text
202606210001 - channel intelligence indexes
202606210002 - device intelligence indexes
202606210003 - derived_signal table
202606210004 - derived_signal scope
202606210005 - opportunity_score table and indexes
202606210006 - budget_strategy_report table and indexes
```

После получения изменений необходимо выполнить:

```bash
make alembic-upgrade
```

После миграции `202606210004` необходимо повторно пересчитать Signals, чтобы записи получили актуальное scope-разделение.

## 18. Локальный запуск и проверка

Из корня проекта:

```bash
make db-up
make redis-up
make backend-sync
make frontend-sync
make alembic-upgrade
```

Затем открыть три терминала.

Backend:

```bash
make backend-run
```

Worker:

```bash
make worker-run
```

Frontend:

```bash
make frontend-dev
```

Dashboard:

```text
http://localhost:3000/dashboard
```

Worker не требуется для чтения Dashboard, но должен быть запущен при загрузке новых файлов.

## 19. Проверки качества

Frontend:

```bash
cd frontend
pnpm typecheck
pnpm lint
pnpm build
```

Backend:

```bash
cd backend
uv run ruff check app
uv run python -m compileall -q app
uv run alembic heads
```

Runtime-проверка должна включать:

1. `All/All` — один нейтральный scope.
2. Company + Competitor — два значения с правильными цветами.
3. Company или Competitor = None — скрытие только отсутствующего scope.
4. Страна только одной стороны — `0` у отсутствующей стороны.
5. Множественный выбор стран, компаний и доменов.
6. TLD cascade.
7. Закрытие dropdown по outside click и Escape.
8. Открытие информационных окон вверх при недостатке места.
9. Signals recalculation и последующая фильтрация group/severity.

## 20. Известные особенности и ограничения

- Signals являются snapshot последнего явного пересчёта для периода; после изменения общих фильтров нужен новый recalculation.
- Scoring также является snapshot; после изменения общих фильтров нужен `Recalculate scores`.
- `critical` поддерживается контрактом Signals, но текущие правила его не формируют.
- Dashboard не выполняет прогнозирование и не создаёт рекомендации.
- Значение `0` означает отсутствие агрегированного значения в выбранном scope, а не ошибку запроса.
- Hydration mismatch, возникающий только в обычном Chrome и отсутствующий в Edge/Incognito, связан с расширением, изменяющим DOM до React hydration. Это не является ошибкой расчётов Dashboard.
- Для корректного frontend runtime backend и PostgreSQL должны быть доступны.

## 21. Правила дальнейшего развития

- Не добавлять фильтр Project: используется один проект через backend default scope.
- Сохранять общую панель фильтров для всех вкладок.
- Новые сравнительные показатели должны поддерживать overall/company/competitor scopes.
- Company должен оставаться зелёным, Competitors — синим.
- Новые измерения не должны переиспользовать scope-цвета для другого смысла.
- Выбранный scope без данных должен показывать `0`, а не исчезать.
- Новые статусы и классификации должны сопровождаться информационным окном со всеми возможными значениями.
- Rule-based сигналы должны оставаться объяснимыми и хранить calculation version.
- Изменения схемы `derived_signal` и fact-таблиц должны сопровождаться Alembic migration.
- Opportunity Score должен оставаться объяснимым аналитическим показателем, а не рекомендацией.

## 22. Вкладка Scoring

### Назначение

Формирует explainable country-level Opportunity Score в диапазоне 0–100. Вкладка отвечает на вопрос, насколько страна выглядит привлекательной по выбранным данным, но не рекомендует выход, бюджет или стратегию.

### API

```text
POST /analytics/scoring/recalculate
GET  /analytics/scoring/opportunities
GET  /analytics/scoring/summary
```

### Scope

Используются стандартные значения:

```text
overall
company
competitor
```

При All/All рассчитывается overall ranking. При явном выборе Company/Competitors каждый scope рассчитывается и ранжируется независимо. Если оба scope равны None, пересчёт недоступен.

### Факторы

Opportunity Score включает:

1. Market Size;
2. Growth;
3. Traffic Quality;
4. Competition Level;
5. Competitor Concentration;
6. Channel Stability;
7. Entry Risk;
8. Position Potential.

Указанные планом веса пропорционально нормализуются до суммы `1.00`, поскольку исходный перечень арифметически даёт `1.10`. Относительный приоритет факторов сохранён.

Каждый фактор содержит:

```text
raw_value
score
weight
weighted_score
status
explanation
```

### Categories

- `very_high` — 80–100;
- `high` — 65–79.9999;
- `medium` — 50–64.9999;
- `low` — 35–49.9999;
- `very_low` — 0–34.9999.

### Ranking

Ranking строится отдельно внутри scope по Opportunity Score descending. Tie-breakers:

1. Market Size;
2. Growth;
3. Traffic Quality;
4. Country name ascending.

### Signals и fallback

Scoring использует derived signals той же даты, scope и calculation version. Если signals отсутствуют, расчёт не ломается: Channel Stability получает нейтральный fallback `50` со статусом `not_available`, а UI показывает note.

### UI

Вкладка содержит:

- кнопку `Recalculate scores`;
- summary cards;
- горизонтально прокручиваемую ranking table;
- выбор country row;
- factor breakdown;
- Strengths;
- Weaknesses;
- Risks;
- Signals Used;
- Fallbacks Used.

Scoring сохраняется в БД и после обновления страницы читается через GET endpoints.
