# Reports: актуальная логика

## Назначение

Reports — слой практических рекомендаций поверх Dashboard, Derived Signals и Opportunity Scoring.

Текущий тип отчёта — **Budget Strategy**.

Frontend route:

    /reports/budget-strategy

Budget Strategy не изменяет исходные данные, сигналы или scoring. Он читает доступную аналитику, формирует рекомендацию и сохраняет отдельный report.

## Предварительные условия

Для генерации необходимы:

- Alembic migration 202606210006;
- работающий PostgreSQL и backend;
- работающий frontend;
- загруженные traffic_countries за выбранный период;
- одна выбранная страна;
- бюджет больше 0;
- валюта USD или EUR.

Channels и Devices улучшают качество рекомендации. Derived Signals и Opportunity Score необязательны: при их отсутствии работает fallback.

## Форма

Обязательные поля:

- Country;
- Date from;
- Date to;
- Budget amount;
- Currency.

Дополнительные поля:

- Company;
- Company Domain;
- Competitors;
- Competitors Domain;
- TLD.

Country является одиночным выбором, поскольку один report относится к одной стране.

Остальные справочные фильтры поддерживают:

- All;
- None для Company и Competitors;
- одиночный и множественный выбор;
- поиск по label и value;
- снятие отдельных значений;
- очистку через кнопку X.

Если поиск не находит значений, отображается **No matching values**.

## Доступность значений

Справочные варианты загружаются через:

    GET /analytics/filter-options

Варианты формируются по фактическому наличию данных за выбранный период.

После выбора Country доступны только компании, домены и TLD, присутствующие в данных выбранной страны.

Company Domain зависит от Country, Company и TLD. Competitors Domain зависит от Country, Competitors и TLD.

Country list зависит от периода, TLD и выбранных company/competitor scopes. Для стран используется объединение доступности Company и Competitors.

Текущая модель является data-backed: компания без данных в выбранной стране не предлагается для company-specific стратегии.

## Scope стратегии

### Overall

Условия:

    Company = All
    Company Domain = All
    Competitors = All
    Competitors Domain = All

Стратегия строится по всему доступному рынку страны.

### Company

Company scope используется, если выбрана Company или Company Domain. Для company-only анализа рекомендуется:

    Company = selected values
    Competitors = None

Если выбрано несколько компаний, их показатели агрегируются.

### Competitor

Competitor scope используется, если Company равна None и выбраны Competitors.

### Company и Competitors

Если одновременно выбраны Company и Competitors, основным scope становится company. Company используется как основной рыночный сигнал, а Competitors — для competitor gap.

## Источники аналитики

| Источник | Использование |
| --- | --- |
| Country Intelligence | traffic, growth, bounce rate, duration, pages per visit |
| Competitor Intelligence | competitor traffic, growth, active competitors |
| Channel Intelligence | channel mix, dominant channel, competitor shares |
| Device Intelligence | dominant device и quality indexes |
| Derived Signals | volatility, concentration, channel shifts, quality risks |
| Opportunity Score | modifier, strengths и risks |

Фактические таблицы:

- fact_traffic_countries_daily;
- fact_traffic_sources_daily;
- fact_journey_sources_daily;
- fact_device_trends_daily;
- derived_signal;
- opportunity_score.

## Opportunity Score и Signals

Opportunity Score ищется по точной комбинации project, country, period, scope и calculation version.

Derived Signals выбираются по точному period, scope и calculation version.

Чтобы report использовал рассчитанные Signals и Scoring:

1. На Dashboard установить тот же период и фильтры.
2. На вкладке Signals выполнить Recalculate.
3. На вкладке Scoring выполнить Recalculate scores.
4. В Reports повторить тот же scope и период.
5. Сгенерировать Budget Strategy.

Opportunity Score хранит scope, но пока не хранит идентичность конкретного набора Company и Domains. Последний пересчёт за период заменяет предыдущие scoring records этого периода и calculation version.

Derived Signals работают аналогично: пересчёт заменяет signals для project, периода и calculation version.

## Fallback

Если Opportunity Score отсутствует, используется нейтральный modifier 50 и сохраняется предупреждение:

    Opportunity score is unavailable; a neutral modifier is used.

Если Derived Signals отсутствуют:

    Derived signals are unavailable; direct analytics fallback is used.

Если Channel data отсутствуют:

    Channel data is unavailable; allocation confidence is low.

Fallback не обещает ROI, CPA, revenue, conversions или количество клиентов.

## Каналы стратегии

| Internal value | Значение |
| --- | --- |
| search | SEO / Search |
| paid | Paid |
| referral | Referral / Partnerships |
| social | Social |
| direct | Brand / Direct |

Direct интерпретируется как budget на brand awareness, retention, owned media и поддержку прямого спроса.

## Channel opportunity score

Формула:

    channel score =
      market signal * 0.30
    + competitor gap * 0.20
    + traffic quality * 0.20
    + stability * 0.15
    + opportunity modifier * 0.15

Компоненты нормализуются в диапазон 0–100. Высокий channel-specific risk уменьшает score на 20.

## Роли каналов

Активные каналы получают роли priority, test, supporting или risky.

Два сильнейших безопасных канала становятся priority. Канал с высоким channel-specific risk или score ниже 35 становится risky. Остальные каналы со score от 50 становятся supporting, остальные — test.

Глобальный риск стратегии не обязательно делает все каналы risky.

## Guardrails

| Role | Minimum | Maximum |
| --- | ---: | ---: |
| Priority | 25% | 45% |
| Test | 5% | 15% |
| Supporting | 5% | 20% |
| Risky | 0% | 10% |

После применения guardrails сумма share равна 100%, а сумма amount равна budget amount.

## Количество активных каналов

    budget < 10 000       → максимум 3 канала
    budget 10 000–49 999  → максимум 4 канала
    budget >= 50 000      → максимум 5 каналов

## Результат

Report содержит:

- country и country code;
- period;
- budget и currency;
- scope;
- Opportunity Score или fallback;
- recommended approach;
- channel allocation;
- channel roles;
- explanation;
- expected directional effect;
- strategy risks и mitigation hints;
- source analytics snapshot;
- warnings;
- calculation version;
- created timestamp.

Expected effect является качественной направленной оценкой, а не финансовым прогнозом.

## Сохранение

Reports сохраняются в таблицу budget_strategy_report.

Strategy key:

    project_id : scope : country_id : date_from : date_to : budget_amount : currency : calculation_version

Если report с таким key уже существует, его содержимое обновляется. Новый дубликат не создаётся.

Strategy key пока не содержит Company, Domains, Competitors и TLD. Разные фильтры с одинаковыми project, scope, country, period, budget, currency и version могут обновить один report.

## API

Генерация:

    POST /reports/budget-strategy/generate

Список:

    GET /reports/budget-strategy

Получение одного report:

    GET /reports/budget-strategy/{id}

Список поддерживает dateFrom, dateTo, country, scope и limit.

## Пользовательские сценарии

### Market-level strategy

1. Выбрать Country и период.
2. Указать бюджет и валюту.
3. Оставить Company и Competitors равными All.
4. Нажать Generate budget strategy.

### Company strategy

1. Выбрать Country.
2. Выбрать Company и при необходимости Company Domain.
3. Установить Competitors в None.
4. Указать период и бюджет.
5. При необходимости пересчитать Signals и Scoring.
6. Сгенерировать report.

### Company versus competitors

1. Выбрать Country.
2. Выбрать Company.
3. Выбрать одного или нескольких Competitors.
4. При необходимости ограничить Domains и TLD.
5. Указать период и бюджет.
6. Сгенерировать report.

## Ошибки

Генерация блокируется на frontend, если Country не выбран.

Backend отклоняет запрос, если:

- Country равен All;
- передано несколько стран;
- Country отсутствует в справочнике;
- Date from больше Date to;
- Budget amount меньше или равен 0;
- Currency не равна USD или EUR.

Frontend отображает фактическое сообщение backend.

## Текущие ограничения

1. Один report относится только к одной стране.
2. Компания без данных в стране недоступна.
3. Нет expansion-сценария для компании с нулевым присутствием.
4. Несколько компаний агрегируются в один scope.
5. Opportunity Score не хранит company/domain filter snapshot.
6. Strategy key не учитывает Company, Domains, Competitors и TLD.
7. Пересчёт Signals и Scoring заменяет прежние записи периода и version.
8. Нет ROI, CPA, CAC, conversion или revenue forecast.
9. Currency conversion не выполняется.
10. Report не запускает кампании и не изменяет внешние бюджеты.

## Возможное развитие

Для полноценного expansion use case потребуется:

- глобальный выбор target company;
- выбор страны без текущего company presence;
- сохранение filter snapshot;
- добавление filter identity в scoring и strategy key;
- разделение market-entry и existing-presence стратегий;
- versioned recalculation без удаления других scopes;
- spend, conversion, CPA и ROI данные для финансового моделирования.
