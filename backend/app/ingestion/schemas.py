from dataclasses import dataclass


@dataclass(frozen=True)
class FileSchema:
    file_type: str
    table_name: str
    required_columns: tuple[str, ...]
    key_columns: tuple[str, ...]
    date_columns: tuple[str, ...]
    boolean_columns: tuple[str, ...]
    text_columns: tuple[str, ...]
    integer_columns: tuple[str, ...]
    numeric_columns: tuple[str, ...]
    ratio_columns: tuple[str, ...]


FILE_SCHEMAS: dict[str, FileSchema] = {
    'traffic_countries': FileSchema(
        file_type='traffic_countries',
        table_name='fact_traffic_countries_daily',
        required_columns=('date', 'company', 'domain', 'country'),
        key_columns=('date', 'company', 'domain', 'country'),
        date_columns=('date', 'month_year'),
        boolean_columns=('is_weekend',),
        text_columns=(
            'company',
            'domain',
            'country',
            'country_name_ru',
            'country_name_en',
            'country_region',
            'country_iso2',
            'country_iso3',
            'day_of_week',
            'month',
            'calculation_version',
        ),
        integer_columns=(
            'day',
            'week_of_year',
            'year',
            'month_number',
            'traffic',
            'desktop_share_traffic',
            'mobile_share_traffic',
            'unique_visitors',
            'traffic_no_bounce',
            'traffic_bounce',
            'desktop',
            'mobile',
        ),
        numeric_columns=('pages_per_visit', 'avg_visit_duration'),
        ratio_columns=('traffic_share', 'desktop_share', 'mobile_share', 'bounce_rate'),
    ),
    'traffic_sources': FileSchema(
        file_type='traffic_sources',
        table_name='fact_traffic_sources_daily',
        required_columns=('date', 'company', 'domain'),
        key_columns=('date', 'company', 'domain'),
        date_columns=('date', 'month_year'),
        boolean_columns=('is_weekend',),
        text_columns=('company', 'domain', 'day_of_week', 'month', 'calculation_version'),
        integer_columns=(
            'day',
            'week_of_year',
            'year',
            'month_number',
            'direct',
            'referral',
            'paid',
            'social',
            'search',
        ),
        numeric_columns=(),
        ratio_columns=(),
    ),
    'journey_sources': FileSchema(
        file_type='journey_sources',
        table_name='fact_journey_sources_daily',
        required_columns=('date', 'company', 'domain', 'source_type'),
        key_columns=('date', 'company', 'domain', 'source_type', 'traffic_type', 'search_source'),
        date_columns=('date', 'month_year'),
        boolean_columns=('is_weekend',),
        text_columns=(
            'company',
            'domain',
            'source_type',
            'traffic_type',
            'search_source',
            'day_of_week',
            'month',
            'calculation_version',
        ),
        integer_columns=('day', 'week_of_year', 'year', 'month_number', 'traffic'),
        numeric_columns=('changes',),
        ratio_columns=('traffic_share',),
    ),
    'trend_by_devices': FileSchema(
        file_type='trend_by_devices',
        table_name='fact_device_trends_daily',
        required_columns=('date', 'company', 'domain'),
        key_columns=('date', 'company', 'domain'),
        date_columns=('date', 'month_year'),
        boolean_columns=('is_weekend',),
        text_columns=('company', 'domain', 'day_of_week', 'month', 'calculation_version'),
        integer_columns=(
            'day',
            'week_of_year',
            'year',
            'month_number',
            'visits_devices',
            'visits_desktop',
            'visits_mobile',
            'bounce_desktop_sum',
            'bounce_mobile_sum',
            'unique_devices',
            'unique_desktop',
            'unique_mobile',
            'all_no_bounce',
            'all_bounce',
            'desktop_no_bounce',
            'desktop_bounce',
            'mobile_no_bounce',
            'mobile_bounce',
        ),
        numeric_columns=('duration_devices', 'duration_desktop', 'duration_mobile'),
        ratio_columns=('bounce_devices', 'bounce_desktop', 'bounce_mobile'),
    ),
}

ALLOWED_EXTENSIONS = {'.csv', '.xlsx'}


def get_schema(file_type: str) -> FileSchema:
    """Get ingestion file schema.
    Args:
        file_type (str): Ingestion file type."""
    schema = FILE_SCHEMAS[file_type]
    return schema


def list_types() -> list[str]:
    """List supported file types.
    Args:
        None (None): No arguments are required."""
    file_types = list(FILE_SCHEMAS.keys())
    return file_types
