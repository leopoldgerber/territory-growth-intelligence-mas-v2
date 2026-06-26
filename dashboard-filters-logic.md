# Dashboard Filters Logic

## Назначение

Фильтры Dashboard задают общий аналитический контекст для всех внутренних вкладок страницы Dashboard:

- Market Overview
- Countries
- Channels
- Devices
- Signals
- Scoring

Фильтр находится над вкладками и является единым для всей страницы. При переключении вкладок выбранные значения сохраняются, потому что состояние фильтров хранится в URL query params.

## Параметры фильтра

Текущий набор общих фильтров:

| Фильтр | Query param | Значение по умолчанию | Логика |
|---|---|---:|---|
| Date from | `dateFrom` | `2025-01-01` | Начало периода анализа |
| Date to | `dateTo` | `2025-02-01` | Конец периода анализа |
| Country | `country` | `all` | Одна страна, несколько стран, все страны или `None` |
| Top-Level Domain | `tld` | `all` | Один или несколько TLD, все TLD или `None` |
| Company | `company` | `all` | Одна компания, несколько компаний, все компании или `None` |
| Company Domain | `companyDomain` | `all` | Один или несколько доменов выбранных компаний, все домены или `None` |
| Competitors | `competitors` | `all` | Одна компания, несколько компаний, все компании или `None` |
| Competitors Domain | `competitorDomain` | `all` | Один или несколько доменов выбранных конкурентов, все домены или `None` |

Фильтр `project` в интерфейс не добавляется. Проект один, поэтому backend использует `DEFAULT_PROJECT_ID`.

## Значения All и None

`All` означает, что фильтр не ограничивает выборку по этому измерению.

Примеры:

- `country=all` означает все доступные страны.
- `company=all` означает все доступные компании.
- `companyDomain=all` означает все домены, доступные с учетом выбранных company и TLD.

`None` доступен для фильтров Country, Top-Level Domain, Company, Company Domain, Competitors и Competitors Domain.

`None` означает, что соответствующий аналитический scope не выбран:

- `company=none` отключает company scope.
- `competitors=none` отключает competitor scope.
- `country=none` означает, что страны не выбраны и аналитические вкладки получают пустой country context.
- `tld=none` означает, что домены верхнего уровня не выбраны и TLD context пустой.
- `companyDomain=none` означает, что домены company scope не выбраны.
- `competitorDomain=none` означает, что домены competitor scope не выбраны.
- Если одновременно `company=none` и `competitors=none`, вкладки Signals и Scoring не показывают scope-аналитику и предлагают выбрать company или competitors.

## Множественный выбор

Фильтры Country, TLD, Company, Company Domain, Competitors и Competitors Domain поддерживают множественный выбор.

В URL несколько выбранных значений сохраняются через запятую:

```text
country=DEU,FRA,USA
company=1,3,8
companyDomain=example.com,example.de
```

При выборе `All` фильтр переходит в состояние, где выбраны все доступные значения. После снятия одной или нескольких меток `All` перестает считаться активным, а в URL сохраняется конкретный список выбранных значений.

## Поиск в фильтрах

Все dropdown-фильтры поддерживают поиск.

Поиск работает по:

- label значения;
- техническому value значения.

Если подходящих значений нет, отображается сообщение:

```text
No matching values.
```

Поиск не меняет выбранные значения сам по себе. Он только ограничивает видимый список опций внутри dropdown.

## Очистка значений

Для выбранных конкретных значений доступна кнопка очистки.

Логика очистки:

- если фильтр поддерживает `None`, очистка переводит его в `None`;
- если фильтр не поддерживает `None`, очистка возвращает его в `All`.

Кнопка `Clear` в блоке фильтров сбрасывает весь Dashboard к значениям по умолчанию:

```text
dateFrom=2025-01-01
dateTo=2025-02-01
country=all
tld=all
company=all
companyDomain=all
competitors=all
competitorDomain=all
```

## Зависимость фильтров друг от друга

Фильтры не являются статическими справочниками. Доступные значения рассчитываются backend endpoint:

```text
GET /analytics/filter-options
```

Endpoint получает текущие значения:

- period;
- country;
- tld;
- company;
- companyDomain;
- competitors;
- competitorDomain.

И возвращает data-backed варианты, то есть значения, которые реально присутствуют в загруженных fact-таблицах за выбранный контекст.

## Country

Country поддерживает:

- `All`;
- `None`;
- одну страну;
- несколько стран.

`None` нужен для полного сброса выбранных стран без возврата к `All`. В этом состоянии country context пустой, поэтому data-backed аналитические блоки могут показывать отсутствие данных.

Если выбраны company, company domain, competitors или competitors domain, список стран должен отражать все страны, где есть данные хотя бы по выбранной стороне.

То есть логика доступности стран использует объединение выбранных company и competitors, а не только пересечение.

Пример:

- company есть в Germany и France;
- competitor есть в France и Spain;
- доступные страны: Germany, France, Spain.

Если в выбранной стране у одной из сторон нет данных, показатели этой стороны на аналитических вкладках отображаются как `0`, а не скрываются из-за отсутствия данных.

## TLD

Top-Level Domain фильтрует домены по значению TLD:

- `.com`
- `.ru`
- `.de`
- `.eu`
- и другие доступные значения из справочника доменов.

Если выбран `All`, TLD не ограничивает список доменов.

Если выбран `None`, TLD context становится пустым, и data-backed аналитика получает пустую выборку по TLD.

Если выбран конкретный TLD, то Company Domain и Competitors Domain показывают только домены с этим TLD.

## Company и Company Domain

Company поддерживает:

- `All`;
- `None`;
- одну компанию;
- несколько компаний.

Company Domain зависит от выбранных Company и TLD.

Логика:

- если `company=all`, в Company Domain доступны все домены с учетом TLD;
- если выбрана одна company, доступны только домены этой company;
- если выбрано несколько company, доступны домены этих company;
- если `company=none`, Company Domain очищается до доступного нейтрального состояния.
- если `companyDomain=none`, company domain context пустой и выбранные company не получают доменную выборку.

Если ранее выбранный домен стал недоступен после смены Company или TLD, frontend автоматически удаляет его из выбранного списка.

## Competitors и Competitors Domain

Competitors использует тот же справочник компаний, что и Company.

Это сделано намеренно:

- competitor может быть любой компанией из данных;
- выбранная company может также отображаться в competitors;
- это позволяет сравнивать домены внутри одной компании, если у компании несколько доменов.

Competitors Domain зависит от выбранных Competitors и TLD.

Логика:

- если `competitors=all`, доступны все домены с учетом TLD;
- если выбран один competitor, доступны только его домены;
- если выбрано несколько competitors, доступны домены этих competitors;
- если `competitors=none`, competitor scope отключается.
- если `competitorDomain=none`, competitor domain context пустой и выбранные competitors не получают доменную выборку.

## URL как источник состояния

Dashboard не хранит выбранные фильтры в local state как основной источник истины.

Основной источник состояния:

```text
URL query params
```

Frontend читает query params, нормализует их и передает в API hooks.

Плюсы такого подхода:

- можно обновить страницу без потери фильтров;
- можно открыть ссылку с уже выбранным аналитическим контекстом;
- все вкладки Dashboard используют один и тот же фильтр;
- Signals и Scoring используют тот же period и scope, что остальные вкладки.

## Защита от некорректных значений

Frontend нормализует значения фильтров.

Если в URL вручную указать значение, которого нет среди доступных options, оно удаляется из фильтра.

Пример:

```text
company=999999
```

Если такой company нет в доступных options, frontend вернет фильтр к корректному состоянию.

## Даты

Date from и Date to используют HTML date input.

Изменение даты применяется только когда значение соответствует формату:

```text
YYYY-MM-DD
```

Если пользователь начал вводить дату, но значение еще неполное, фильтр не применяется до завершения валидной даты.

Если после blur значение невалидно, оно сбрасывается к дефолтному значению.

## Защита от мерцания интерфейса

React Query использует `placeholderData: keepPreviousData`.

Это означает:

- при смене фильтра предыдущие данные временно остаются на экране;
- UI не прыгает в loading state на каждый клик;
- scroll внутри dropdown сохраняется после выбора значения;
- множественный выбор не должен сбрасывать список наверх.

## Как фильтр влияет на вкладки

Market Overview, Countries, Channels и Devices запрашивают backend analytics endpoints с полным набором фильтров.

Signals и Scoring используют фильтры иначе:

- period, country, tld, company, domains и competitors участвуют в пересчете;
- чтение Signals и Scoring идет из уже сохраненных таблиц;
- если фильтр был изменен, а пересчет не выполнен, сохраненных результатов для нового контекста может не быть.

## Цветовая логика scope

Во всех аналитических вкладках используется единая цветовая логика:

- default color: общий scope, когда Company и Competitors оба `All`;
- green: company scope;
- blue: competitor scope.

Если Company и Competitors оба `All`, не показываются два отдельных значения. Отображается один общий показатель в цвете по умолчанию.

Если выбран только company, отображаются только company-показатели.

Если выбраны только competitors, отображаются только competitor-показатели.

Если выбраны и company, и competitors, показатели отображаются раздельно:

- company green;
- competitors blue.

## Текущие ограничения

Фильтры показывают только значения, которые есть в загруженных данных.

Это значит:

- нельзя выбрать компанию, по которой нет fact-данных в выбранном периоде;
- нельзя выбрать страну, которой нет в загруженном периоде;
- нельзя выбрать домен, если он не связан с выбранной company или TLD;
- сценарии анализа потенциальной экспансии в страну без текущих данных пока не являются частью Dashboard-фильтра.

## Ключевые файлы реализации

Frontend:

- `frontend/components/dashboard/dashboard-filters.tsx`
- `frontend/components/dashboard/multi-select-filter.tsx`
- `frontend/lib/dashboard/query-params.ts`
- `frontend/lib/dashboard/filter-options.ts`
- `frontend/lib/api/analytics-queries.ts`

Backend:

- `backend/app/api/routes/analytics.py`
- `backend/app/analytics/country_intelligence.py`
