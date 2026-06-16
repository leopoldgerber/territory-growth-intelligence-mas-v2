from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

COLUMN_ALIASES = {
    'avg duration': 'avg_visit_duration',
    'avg visit duration': 'avg_visit_duration',
    'bounce desktop': 'bounce_desktop',
    'bounce devices': 'bounce_devices',
    'bounce mobile': 'bounce_mobile',
    'bounce rate': 'bounce_rate',
    'company name': 'company',
    'country code': 'country_iso3',
    'country iso2': 'country_iso2',
    'country iso3': 'country_iso3',
    'country name': 'country',
    'country name en': 'country',
    'domain name': 'domain',
    'avg. visit duration': 'avg_visit_duration',
    'english': 'country_name_en',
    'iso2': 'country_iso2',
    'iso3': 'country_iso3',
    'location': 'country_region',
    'month year': 'month_year',
    'name': 'country_name_ru',
    'pages visit': 'pages_per_visit',
    'search source': 'search_source',
    'search/source': 'search_source',
    'source type': 'source_type',
    'traffic type': 'traffic_type',
    'unique visitors': 'unique_visitors',
    'website': 'domain',
}

EMPTY_VALUES = {'', 'nan', 'none', 'null', 'nat'}


def normalize_column(column_name: str) -> str:
    """Normalize dataframe column name.
    Args:
        column_name (str): Raw column name."""
    normalized_name = column_name.strip().lower().replace('\ufeff', '')
    normalized_name = normalized_name.replace('/', ' ')
    normalized_name = normalized_name.replace('-', ' ')
    normalized_name = '_'.join(normalized_name.split())
    normalized_name = COLUMN_ALIASES.get(normalized_name.replace('_', ' '), normalized_name)
    return normalized_name


def normalize_text(value: Any) -> str | None:
    """Normalize text value.
    Args:
        value (Any): Raw cell value."""
    text_value = str(value).strip()
    if text_value.lower() in EMPTY_VALUES:
        return None
    return text_value


def normalize_source(value: Any) -> str:
    """Normalize source value.
    Args:
        value (Any): Raw source value."""
    text_value = normalize_text(value)
    if text_value is None or text_value == '0':
        return '__empty__'
    return text_value


def normalize_date(value: Any) -> date | None:
    """Normalize date value.
    Args:
        value (Any): Raw date value."""
    import pandas as pd

    parsed_value = pd.to_datetime(value, errors='coerce')
    if pd.isna(parsed_value):
        return None
    date_value = parsed_value.date()
    return date_value


def normalize_number(value: Any) -> Decimal | None:
    """Normalize numeric value.
    Args:
        value (Any): Raw numeric value."""
    text_value = normalize_text(value)
    if text_value is None:
        return None
    if ':' in text_value:
        return normalize_duration(text_value)
    cleaned_value = text_value.replace('%', '').replace(' ', '')
    if ',' in cleaned_value and '.' not in cleaned_value:
        cleaned_value = cleaned_value.replace(',', '.')
    else:
        cleaned_value = cleaned_value.replace(',', '')
    try:
        numeric_value = Decimal(cleaned_value)
    except InvalidOperation:
        return None
    return numeric_value


def normalize_duration(value: str) -> Decimal | None:
    """Normalize duration value.
    Args:
        value (str): Raw duration value."""
    time_parts = value.split(':')
    if len(time_parts) == 2:
        minutes, seconds = time_parts
        duration_value = Decimal(int(minutes) * 60 + int(seconds))
    elif len(time_parts) == 3:
        hours, minutes, seconds = time_parts
        duration_value = Decimal(int(hours) * 3600 + int(minutes) * 60 + int(seconds))
    else:
        return None
    return duration_value


def normalize_integer(value: Any) -> int | None:
    """Normalize integer value.
    Args:
        value (Any): Raw integer value."""
    numeric_value = normalize_number(value)
    if numeric_value is None:
        return None
    integer_value = int(numeric_value)
    return integer_value


def normalize_boolean(value: Any) -> bool | None:
    """Normalize boolean value.
    Args:
        value (Any): Raw boolean value."""
    text_value = normalize_text(value)
    if text_value is None:
        return None
    lowered_value = text_value.lower()
    true_values = {'true', '1', 'yes', 'y'}
    false_values = {'false', '0', 'no', 'n'}
    if lowered_value in true_values:
        return True
    if lowered_value in false_values:
        return False
    return None


def normalize_domain(value: Any) -> str | None:
    """Normalize domain value.
    Args:
        value (Any): Raw domain value."""
    text_value = normalize_text(value)
    if text_value is None:
        return None
    domain_value = text_value.lower().replace('https://', '').replace('http://', '').split('/')[0]
    return domain_value


def normalize_company(value: Any) -> str | None:
    """Normalize company value.
    Args:
        value (Any): Raw company value."""
    text_value = normalize_text(value)
    if text_value is None:
        return None
    company_value = ' '.join(text_value.split())
    return company_value
