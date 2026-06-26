# Dashboard Tab: Channels

## Назначение

Channels показывает структуру acquisition traffic, journey sources, paid/organic split, channel dependency и rule-based channel signals.

Вкладка отвечает на вопрос:

```text
Через какие каналы выбранная company, competitors или весь рынок получают traffic, и где есть зависимость или возможность роста?
```

## Источник данных

Frontend получает данные через:

```text
GET /analytics/channel-intelligence
```

Основная frontend-обертка:

```text
useChannelIntelligenceQuery()
```

## Scope логика

Channels поддерживает ту же логику разделения company и competitors, что Market Overview.

| Фильтры | Отображение |
|---|---|
| Company = All и Competitors = All | Один overall scope |
| Company выбрана, Competitors = None | Company scope |
| Company = None, Competitors выбраны | Competitor scope |
| Company выбрана, Competitors выбраны | Company green + competitors blue |

Если оба scope `All`, вкладка не дублирует значения. Она показывает один neutral/overall показатель.

## Country scope note

Если country-фильтр ограничивает channel analysis, backend может вернуть `scope_note`.

UI показывает alert:

```text
Country-scoped channel analysis
```

Это означает, что channel metrics рассчитаны в контексте доступных country-domain связок.

## Legend

Вкладка показывает legend:

- default/neutral: overall scope;
- green: company scope;
- blue: competitor scope.

## Карточки Summary

Верхний блок содержит 5 карточек.

### Total Channel Traffic

Сумма traffic по каналам:

- direct;
- search;
- paid;
- referral;
- social.

Дополнительно может отображаться detail:

```text
N companies / N domains
```

### Dominant Channel

Канал с максимальным traffic share.

Если данных нет, отображается `None`.

### Dominant Channel Share

Доля dominant channel от total channel traffic.

### Paid Share

Доля paid journey traffic от всего classified journey traffic.

### Organic Share

Доля organic journey traffic от всего classified journey traffic.

## Карточка Channel Mix

Channel Mix показывает распределение total traffic по каналам.

Каналы:

- direct;
- search;
- paid;
- referral;
- social.

Для каждого канала отображаются:

- traffic;
- share;
- bar visualization.

Если company и competitors выбраны одновременно, для каждого канала могут отображаться две полосы:

- company green;
- competitors blue.

Если overall scope, отображается одна primary/default полоса.

## Таблица Company Channel Dependency

Таблица показывает channel dependency по каждой компании.

Поля:

| Поле | Значение |
|---|---|
| Company | Название компании |
| Total Traffic | Суммарный channel traffic |
| Dominant Channel | Канал с максимальной долей |
| Dominant Share | Доля dominant channel |
| Direct | Direct share |
| Search | Search share |
| Paid | Paid share |
| Referral | Referral share |
| Social | Social share |
| Dependency | Уровень зависимости |

Dependency levels:

| Level | Значение |
|---|---|
| `low` | Dominant channel share ниже 40% |
| `medium` | Dominant channel share от 40% до 59.9% |
| `high` | Dominant channel share минимум 60% |

Если строк нет, таблица не отображается.

## Карточка Channel Skews

Channel Skews показывает rule-based сигналы перекоса в channel mix.

Возможные signals:

| Signal | Значение |
|---|---|
| `brand_dependency` | Direct traffic минимум 60% |
| `seo_dependency` | Search traffic минимум 60% |
| `paid_dependency` | Paid traffic минимум 35% |
| `referral_dependency` | Referral traffic минимум 30% |
| `social_dependency` | Social traffic минимум 25% |
| `balanced_mix` | Ни один канал не достигает 40% |

Каждый item показывает:

- company;
- signal;
- share;
- message.

Если сигналов нет:

```text
No channel skews detected.
```

## Карточка Opportunity Signals

Opportunity Signals показывает rule-based условия, которые могут быть полезны для анализа каналов.

Каждый item содержит:

- type badge;
- signal value;
- message.

Types:

| Type | Значение |
|---|---|
| `seo` | Search является значимым acquisition-направлением |
| `paid` | Paid acquisition имеет заметное присутствие |
| `partnerships` | Referral traffic может указывать на partnership-driven acquisition |
| `social` | Social traffic имеет заметное присутствие |
| `brand` | Direct traffic является крупным acquisition channel |
| `channel_gap` | Канал почти отсутствует и может быть gap/unused route |

Возможные signals:

| Signal | Значение |
|---|---|
| `high_search_share` | Search минимум 40% |
| `meaningful_paid_share` | Paid минимум 20% |
| `visible_referral_share` | Referral минимум 15% |
| `visible_social_share` | Social минимум 15% |
| `high_direct_share` | Direct минимум 50% |
| `low_*_share` | Названный канал имеет долю 3% или ниже |

Каждый item показывает:

- type;
- signal;
- message.

Если сигналов нет:

```text
No channel signals detected.
```

## Карточка Paid / Organic

Показывает journey traffic split:

- Paid;
- Organic;
- Unknown.

Для каждого типа отображаются:

- traffic;
- share;
- bar visualization.

Shares считаются от total classified journey traffic.

## Карточка Source Type Breakdown

Показывает journey traffic по source type.

Для каждого source type:

- traffic;
- share;
- bar.

Если данных нет:

```text
No journey data available.
```

## Карточка Traffic Type Breakdown

Показывает journey traffic по traffic type:

- paid;
- organic;
- unknown;
- другие доступные значения из данных.

Для каждого traffic type:

- traffic;
- share;
- bar.

## Таблица Top Journey Sources

Таблица показывает highest-traffic combinations:

- source type;
- traffic type;
- named source;
- traffic;
- share.

Поля:

| Поле | Значение |
|---|---|
| Source Type | Тип источника |
| Traffic Type | Paid/organic/unknown classification |
| Source | Конкретный source |
| Traffic | Traffic source |
| Share | Доля source внутри scope |

Если строк нет, таблица не отображается.

## Empty и Error состояния

Если идет загрузка, отображается skeleton state.

Если endpoint недоступен:

```text
Failed to load channel intelligence.
```

Если нет данных:

```text
No channel data found for selected filters.
```

## Ключевые файлы

Frontend:

- `frontend/components/dashboard/channel-intelligence/channel-intelligence-section.tsx`
- `frontend/components/dashboard/channel-intelligence/channel-summary-cards.tsx`
- `frontend/components/dashboard/channel-intelligence/channel-mix-card.tsx`
- `frontend/components/dashboard/channel-intelligence/channel-analysis-cards.tsx`
- `frontend/components/dashboard/channel-intelligence/channel-tables.tsx`
- `frontend/components/dashboard/channel-intelligence/channel-comparison.tsx`
- `frontend/lib/api/analytics-queries.ts`
- `frontend/lib/types/analytics.ts`

Backend:

- `backend/app/api/routes/analytics.py`
- `backend/app/analytics/channel_intelligence.py`
