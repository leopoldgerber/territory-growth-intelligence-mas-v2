from datetime import date
from hashlib import md5
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tables import (
    DimCalendar,
    DimCompany,
    DimCountry,
    DimDomain,
    FactDeviceTrendsDaily,
    FactJourneySourcesDaily,
    FactTrafficCountriesDaily,
    FactTrafficSourcesDaily,
)

FACT_MODELS = {
    'traffic_countries': FactTrafficCountriesDaily,
    'traffic_sources': FactTrafficSourcesDaily,
    'journey_sources': FactJourneySourcesDaily,
    'trend_by_devices': FactDeviceTrendsDaily,
}


def normalize_name(company_name: str) -> str:
    """Normalize company name.
    Args:
        company_name (str): Company display name."""
    normalized_name = ' '.join(company_name.lower().split())
    return normalized_name


def get_company(session: Session, company_name: str) -> DimCompany:
    """Get or create company dimension.
    Args:
        session (Session): Active database session.
        company_name (str): Company display name."""
    normalized_name = normalize_name(company_name)
    statement = select(DimCompany).where(DimCompany.normalized_name == normalized_name)
    company = session.scalars(statement).first()
    if company is not None:
        return company

    company = DimCompany(name=company_name, normalized_name=normalized_name, is_target_company=False)
    session.add(company)
    session.flush()
    return company


def get_domain(session: Session, company: DimCompany, domain_name: str) -> DimDomain:
    """Get or create domain dimension.
    Args:
        session (Session): Active database session.
        company (DimCompany): Company dimension model.
        domain_name (str): Normalized domain value."""
    statement = select(DimDomain).where(DimDomain.domain == domain_name)
    domain = session.scalars(statement).first()
    if domain is not None:
        return domain

    tld = domain_name.split('.')[-1] if '.' in domain_name else None
    root_domain = '.'.join(domain_name.split('.')[-2:]) if '.' in domain_name else domain_name
    domain = DimDomain(company_id=company.id, domain=domain_name, root_domain=root_domain, tld=tld, is_active=True)
    session.add(domain)
    session.flush()
    return domain


def make_iso(country_name: str, length: int) -> str:
    """Make stable fallback country code.
    Args:
        country_name (str): Country display name.
        length (int): Fallback code length."""
    code_hash = md5(country_name.lower().encode('utf-8')).hexdigest().upper()
    country_code = code_hash[:length]
    return country_code


def get_country(session: Session, row: dict[str, Any]) -> DimCountry:
    """Get or create country dimension.
    Args:
        session (Session): Active database session.
        row (dict[str, Any]): Normalized ingestion row."""
    country_name = row.get('country_name_en') or row.get('country') or 'Unknown'
    country_name_ru = row.get('country_name_ru')
    country_region = row.get('country_region')
    iso2 = normalize_country_code(row.get('country_iso2'), 2)
    iso3 = normalize_country_code(row.get('country_iso3'), 3)
    if iso3 is None and iso2 is not None:
        iso3 = f'{iso2}X'
    if iso2 is None:
        iso2 = make_iso(country_name, 2)
    if iso3 is None:
        iso3 = make_iso(country_name, 3)
    statement = select(DimCountry).where((DimCountry.iso3 == iso3) | (DimCountry.iso2 == iso2))
    country = session.scalars(statement).first()
    if country is not None:
        country.country_name_en = country_name or country.country_name_en
        country.country_name_ru = country_name_ru or country.country_name_ru
        country.region = country_region or country.region
        session.add(country)
        session.flush()
        return country

    country = DimCountry(
        country_name_en=country_name,
        country_name_ru=country_name_ru,
        iso2=iso2,
        iso3=iso3,
        region=country_region,
    )
    session.add(country)
    session.flush()
    return country


def normalize_country_code(country_code: Any, length: int) -> str | None:
    """Normalize country code.
    Args:
        country_code (Any): Raw country code value.
        length (int): Expected code length."""
    if country_code is None:
        return None
    code_value = str(country_code).strip()
    if len(code_value) != length:
        return None
    normalized_code = code_value.upper()
    return normalized_code


def get_calendar(session: Session, row_date: date) -> DimCalendar:
    """Get or create calendar dimension.
    Args:
        session (Session): Active database session.
        row_date (date): Calendar date."""
    calendar = session.get(DimCalendar, row_date)
    if calendar is not None:
        return calendar

    calendar = DimCalendar(
        date=row_date,
        year=row_date.year,
        month=row_date.month,
        month_name=row_date.strftime('%B'),
        day=row_date.day,
        day_of_week=row_date.strftime('%A'),
        week_of_year=int(row_date.strftime('%V')),
        quarter=((row_date.month - 1) // 3) + 1,
        is_weekend=row_date.weekday() >= 5,
        month_year=row_date.replace(day=1),
    )
    session.add(calendar)
    session.flush()
    return calendar


def calendar_values(row: dict[str, Any]) -> dict[str, Any]:
    """Build calendar values.
    Args:
        row (dict[str, Any]): Normalized ingestion row."""
    row_date = row['date']
    values = {
        'day': row.get('day') or row_date.day,
        'day_of_week': row.get('day_of_week') or row_date.strftime('%A'),
        'week_of_year': row.get('week_of_year') or int(row_date.strftime('%V')),
        'is_weekend': row.get('is_weekend') if row.get('is_weekend') is not None else row_date.weekday() >= 5,
        'month': row.get('month') or row_date.strftime('%b'),
        'year': row.get('year') or row_date.year,
        'month_number': row.get('month_number') or row_date.month,
        'month_year': row.get('month_year') or row_date.replace(day=1),
    }
    return values


def check_existing(
    session: Session,
    file_type: str,
    project_id: UUID,
    row: dict[str, Any],
    company_id: int,
    domain_id: int,
    country_id: int | None,
) -> bool:
    """Check existing fact row.
    Args:
        session (Session): Active database session.
        file_type (str): Ingestion file type.
        project_id (UUID): Project identifier.
        row (dict[str, Any]): Normalized ingestion row.
        company_id (int): Company dimension identifier.
        domain_id (int): Domain dimension identifier.
        country_id (int | None): Country dimension identifier."""
    fact_model = FACT_MODELS[file_type]
    statement = select(fact_model.id).where(
        fact_model.project_id == project_id,
        fact_model.date == row['date'],
        fact_model.company_id == company_id,
        fact_model.domain_id == domain_id,
    )
    if file_type == 'traffic_countries':
        statement = statement.where(fact_model.country_id == country_id)
    if file_type == 'journey_sources':
        statement = statement.where(
            fact_model.source_type == row.get('source_type'),
            fact_model.traffic_type == row.get('traffic_type'),
            fact_model.search_source == row.get('search_source'),
        )
    exists = session.scalars(statement).first() is not None
    return exists


def build_fact(
    file_type: str,
    project_id: UUID,
    ingestion_run_id: UUID,
    row: dict[str, Any],
    company_id: int,
    domain_id: int,
    country_id: int | None,
) -> Any:
    """Build fact model.
    Args:
        file_type (str): Ingestion file type.
        project_id (UUID): Project identifier.
        ingestion_run_id (UUID): Ingestion run identifier.
        row (dict[str, Any]): Normalized ingestion row.
        company_id (int): Company dimension identifier.
        domain_id (int): Domain dimension identifier.
        country_id (int | None): Country dimension identifier."""
    shared_values = {
        'project_id': project_id,
        'ingestion_run_id': ingestion_run_id,
        'date': row['date'],
        'company_id': company_id,
        'domain_id': domain_id,
        'calculation_version': row.get('calculation_version'),
        'source_file_name': row.get('source_file_name'),
    } | calendar_values(row)
    fact_values = build_values(file_type, row, shared_values, country_id)
    fact_model = FACT_MODELS[file_type](**fact_values)
    return fact_model


def build_values(
    file_type: str,
    row: dict[str, Any],
    shared_values: dict[str, Any],
    country_id: int | None,
) -> dict[str, Any]:
    """Build fact values.
    Args:
        file_type (str): Ingestion file type.
        row (dict[str, Any]): Normalized ingestion row.
        shared_values (dict[str, Any]): Shared fact values.
        country_id (int | None): Country dimension identifier."""
    if file_type == 'traffic_countries':
        values = shared_values | {
            'country_id': country_id,
            'traffic_share': row.get('traffic_share'),
            'traffic': row.get('traffic'),
            'desktop_share_traffic': row.get('desktop_share_traffic'),
            'mobile_share_traffic': row.get('mobile_share_traffic'),
            'unique_visitors': row.get('unique_visitors'),
            'desktop_share': row.get('desktop_share'),
            'mobile_share': row.get('mobile_share'),
            'pages_per_visit': row.get('pages_per_visit'),
            'avg_visit_duration': row.get('avg_visit_duration'),
            'bounce_rate': row.get('bounce_rate'),
            'traffic_no_bounce': row.get('traffic_no_bounce'),
            'traffic_bounce': row.get('traffic_bounce'),
            'desktop': row.get('desktop'),
            'mobile': row.get('mobile'),
        }
    elif file_type == 'traffic_sources':
        values = shared_values | {
            'direct': row.get('direct'),
            'referral': row.get('referral'),
            'paid': row.get('paid'),
            'social': row.get('social'),
            'search': row.get('search'),
        }
    elif file_type == 'journey_sources':
        values = shared_values | {
            'source_type': row.get('source_type'),
            'traffic_type': row.get('traffic_type'),
            'search_source': row.get('search_source'),
            'traffic_share': row.get('traffic_share'),
            'traffic': row.get('traffic'),
            'changes': row.get('changes'),
        }
    else:
        values = shared_values | {
            'visits_devices': row.get('visits_devices'),
            'visits_desktop': row.get('visits_desktop'),
            'visits_mobile': row.get('visits_mobile'),
            'bounce_desktop_sum': row.get('bounce_desktop_sum'),
            'bounce_mobile_sum': row.get('bounce_mobile_sum'),
            'bounce_devices': row.get('bounce_devices'),
            'bounce_desktop': row.get('bounce_desktop'),
            'bounce_mobile': row.get('bounce_mobile'),
            'unique_devices': row.get('unique_devices'),
            'unique_desktop': row.get('unique_desktop'),
            'unique_mobile': row.get('unique_mobile'),
            'duration_devices': row.get('duration_devices'),
            'duration_desktop': row.get('duration_desktop'),
            'duration_mobile': row.get('duration_mobile'),
            'all_no_bounce': row.get('all_no_bounce'),
            'all_bounce': row.get('all_bounce'),
            'desktop_no_bounce': row.get('desktop_no_bounce'),
            'desktop_bounce': row.get('desktop_bounce'),
            'mobile_no_bounce': row.get('mobile_no_bounce'),
            'mobile_bounce': row.get('mobile_bounce'),
        }
    return values


def load_rows(
    session: Session,
    file_type: str,
    project_id: UUID,
    ingestion_run_id: UUID,
    rows: list[dict[str, Any]],
    source_file_name: str,
) -> dict[str, int | date | None]:
    """Load normalized rows.
    Args:
        session (Session): Active database session.
        file_type (str): Ingestion file type.
        project_id (UUID): Project identifier.
        ingestion_run_id (UUID): Ingestion run identifier.
        rows (list[dict[str, Any]]): Valid normalized rows.
        source_file_name (str): Uploaded source file name."""
    inserted_count = 0
    duplicate_count = 0
    company_ids = set()
    domain_ids = set()
    country_ids = set()
    dates = []

    for row in rows:
        row['source_file_name'] = source_file_name
        company = get_company(session, row['company'])
        domain = get_domain(session, company, row['domain'])
        country = get_country(session, row) if file_type == 'traffic_countries' else None
        get_calendar(session, row['date'])
        country_id = country.id if country is not None else None

        company_ids.add(company.id)
        domain_ids.add(domain.id)
        if country_id is not None:
            country_ids.add(country_id)
        dates.append(row['date'])

        if check_existing(session, file_type, project_id, row, company.id, domain.id, country_id):
            duplicate_count += 1
            continue

        fact_model = build_fact(file_type, project_id, ingestion_run_id, row, company.id, domain.id, country_id)
        session.add(fact_model)
        inserted_count += 1

    summary = {
        'inserted_row_count': inserted_count,
        'skipped_duplicate_count': duplicate_count,
        'company_count': len(company_ids),
        'domain_count': len(domain_ids),
        'country_count': len(country_ids),
        'period_start': min(dates) if dates else None,
        'period_end': max(dates) if dates else None,
    }
    session.flush()
    return summary
