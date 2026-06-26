# Dashboard Tab: Devices

## Назначение

Devices показывает desktop/mobile traffic, audience quality, engagement differences и device-level signals.

Вкладка отвечает на вопрос:

```text
Как распределяется traffic между desktop и mobile, и где качество одного устройства заметно отличается от другого?
```

## Источник данных

Frontend получает данные через:

```text
GET /analytics/device-intelligence
```

Основная frontend-обертка:

```text
useDeviceIntelligenceQuery()
```

## Scope логика

Devices использует ту же scope-логику, что Market Overview и Channels:

| Фильтры | Отображение |
|---|---|
| Company = All и Competitors = All | Один overall scope |
| Company выбрана, Competitors = None | Company scope |
| Company = None, Competitors выбраны | Competitor scope |
| Company выбрана, Competitors выбраны | Company green + competitors blue |

Если оба scope `All`, вкладка показывает один neutral/overall показатель.

## Цвета устройств

Для desktop/mobile используется отдельная палитра, не совпадающая со scope-палитрой:

| Device | Цвет |
|---|---|
| Desktop | `#FB7185` |
| Mobile | `#FDBA74` |

Scope цвета сохраняются отдельно:

- company: green;
- competitors: blue;
- overall: default.

## Country scope note

Если backend возвращает `scope_note`, UI показывает alert:

```text
Country-scoped device analysis
```

Это означает, что device metrics рассчитаны с учетом выбранных стран и доступных country-domain связок.

## Карточки Summary

Верхний блок содержит 6 карточек.

### Total Visits

Общее количество visits по выбранному scope.

### Desktop Visits

Количество desktop visits.

Карточка маркируется desktop color:

```text
#FB7185
```

### Mobile Visits

Количество mobile visits.

Карточка маркируется mobile color:

```text
#FDBA74
```

### Desktop Share

Доля desktop visits.

### Mobile Share

Доля mobile visits.

### Dominant Device

Устройство с большей долей visits.

Statuses:

| Status | Значение |
|---|---|
| `Desktop` | Desktop visits больше или равны mobile visits |
| `Mobile` | Mobile visits больше desktop visits |
| `None` | Visits отсутствуют |

## Карточка Device Split

Показывает desktop/mobile share внутри каждого scope.

Для каждого scope отображается stacked bar:

- desktop segment: `#FB7185`;
- mobile segment: `#FDBA74`.

Если есть company и competitor scopes, показываются две строки:

- Company;
- Competitors.

Если overall scope, показывается строка Overall.

## Карточка Unique Users

Показывает:

- All devices unique users;
- Desktop unique users;
- Mobile unique users.

Значения разделяются по scope:

- overall/default;
- company green;
- competitors blue.

## Карточка Bounce / No-Bounce

Показывает:

- Desktop bounce rate;
- Mobile bounce rate;
- Desktop no-bounce;
- Mobile no-bounce.

Desktop и mobile дополнительно маркируются device colors.

## Карточка Duration Comparison

Показывает:

- All devices duration;
- Desktop duration;
- Mobile duration;
- Desktop - mobile duration gap.

Duration форматируется как:

```text
minutes:seconds
```

Duration gap может быть положительным или отрицательным.

## Карточка Device Quality Comparison

Показывает comparative quality index.

Поля:

- Desktop quality;
- Mobile quality;
- Quality gap.

Device Quality Index объединяет:

- normalized visit duration;
- no-bounce rate.

Это не финальный score и не рекомендация. Это сравнительный диагностический сигнал.

## Карточка Device Signals

Device Signals показывает rule-based device conditions.

Возможные signals:

| Signal | Значение |
|---|---|
| `mobile_new_activity` | Mobile traffic появляется во второй половине периода |
| `mobile_growth_low_quality` | Mobile растет, но quality ниже desktop |
| `desktop_quality_advantage` | Desktop имеет значимое преимущество качества |
| `mobile_strength` | Mobile лидирует по traffic и имеет сопоставимое или лучшее качество |
| `balanced_device_quality` | Desktop и mobile quality отличаются менее чем на 10% |

Severity:

| Severity | Значение |
|---|---|
| `low` | Информационное условие |
| `medium` | Существенное условие, которое стоит мониторить |

Если сигналов нет:

```text
No device signals detected.
```

## Таблица Daily Device Trend

Таблица показывает daily device metrics.

Поля:

| Поле | Значение |
|---|---|
| Date | Дата |
| Desktop Visits | Desktop visits |
| Mobile Visits | Mobile visits |
| Desktop Share | Desktop share |
| Mobile Share | Mobile share |

Если для одной стороны нет строки по дате, значение показывается как `0`.

Таблица отображается только если есть хотя бы одна дата.

## Таблица Company Device Quality

Таблица показывает device quality по компаниям.

Поля:

| Поле | Значение |
|---|---|
| Company | Название компании |
| Desktop Share | Доля desktop |
| Mobile Share | Доля mobile |
| Desktop Bounce | Desktop bounce rate |
| Mobile Bounce | Mobile bounce rate |
| Desktop Duration | Desktop avg duration |
| Mobile Duration | Mobile avg duration |
| Quality Gap | Разница quality index |
| Signal | Device quality classification |

Возможные table signals:

| Signal | Значение |
|---|---|
| `mobile_quality_gap` | Mobile share значимая, но desktop quality выше |
| `desktop_quality_advantage` | Desktop quality выше минимум на 15% |
| `mobile_strength` | Mobile лидирует по traffic с равным или лучшим quality |
| `balanced_device_quality` | Quality gap ниже 10% |
| `mixed_device_quality` | Более сильная классификация не применима |

## Empty и Error состояния

Если идет загрузка, отображается skeleton state.

Если endpoint недоступен:

```text
Failed to load device intelligence.
```

Если нет данных:

```text
No device data found for selected filters.
```

## Ключевые файлы

Frontend:

- `frontend/components/dashboard/device-intelligence/device-intelligence-section.tsx`
- `frontend/components/dashboard/device-intelligence/device-summary-cards.tsx`
- `frontend/components/dashboard/device-intelligence/device-metric-cards.tsx`
- `frontend/components/dashboard/device-intelligence/device-signals-card.tsx`
- `frontend/components/dashboard/device-intelligence/device-tables.tsx`
- `frontend/components/dashboard/device-intelligence/device-comparison.tsx`
- `frontend/lib/api/analytics-queries.ts`
- `frontend/lib/types/analytics.ts`

Backend:

- `backend/app/api/routes/analytics.py`
- `backend/app/analytics/device_intelligence.py`

