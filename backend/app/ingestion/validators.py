from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.ingestion.normalizers import (
    normalize_boolean,
    normalize_company,
    normalize_date,
    normalize_domain,
    normalize_integer,
    normalize_number,
    normalize_source,
    normalize_text,
)
from app.ingestion.schemas import FileSchema


@dataclass
class ValidationError:
    row_number: int
    column_name: str
    error_code: str
    error_message: str
    raw_value: str | None


@dataclass
class ValidationResult:
    valid_rows: list[dict[str, Any]]
    errors: list[ValidationError]
    row_count: int


def check_columns(data: Any, schema: FileSchema) -> list[ValidationError]:
    """Check required dataframe columns.
    Args:
        data (pd.DataFrame): Uploaded dataframe.
        schema (FileSchema): File validation schema."""
    errors = []
    missing_columns = [column_name for column_name in schema.required_columns if column_name not in data.columns]
    for column_name in missing_columns:
        errors.append(
            ValidationError(
                row_number=0,
                column_name=column_name,
                error_code='missing_required_column',
                error_message=f'Missing required column: {column_name}',
                raw_value=None,
            ),
        )
    return errors


def format_value(value: Any) -> str | None:
    """Format raw validation value.
    Args:
        value (Any): Raw cell value."""
    import pandas as pd

    if pd.isna(value):
        return None
    text_value = str(value)
    return text_value


def normalize_row(raw_row: dict[str, Any], schema: FileSchema) -> tuple[dict[str, Any], list[ValidationError]]:
    """Normalize dataframe row.
    Args:
        raw_row (dict[str, Any]): Raw dataframe row.
        schema (FileSchema): File validation schema."""
    row_number = int(raw_row.get('__row_number__', 0))
    normalized_row: dict[str, Any] = {}
    errors: list[ValidationError] = []

    for column_name in schema.date_columns:
        value = raw_row.get(column_name)
        date_value = normalize_date(value)
        if date_value is None:
            errors.append(
                build_error(row_number, column_name, 'invalid_date', 'Value cannot be converted to date', value),
            )
        normalized_row[column_name] = date_value

    for column_name in schema.text_columns:
        value = raw_row.get(column_name)
        if column_name == 'company':
            text_value = normalize_company(value)
        elif column_name == 'domain':
            text_value = normalize_domain(value)
        elif column_name == 'search_source':
            text_value = normalize_source(value)
        else:
            text_value = normalize_text(value)
        normalized_row[column_name] = text_value

    for column_name in schema.boolean_columns:
        value = raw_row.get(column_name)
        boolean_value = normalize_boolean(value)
        if boolean_value is None and normalize_text(value) is not None:
            errors.append(
                build_error(row_number, column_name, 'invalid_boolean', 'Value cannot be converted to boolean', value),
            )
        normalized_row[column_name] = boolean_value

    if schema.file_type == 'traffic_countries':
        normalized_row = normalize_country_fields(raw_row, normalized_row)

    for column_name in schema.integer_columns:
        if column_name not in raw_row:
            normalized_row[column_name] = None
            continue
        value = raw_row.get(column_name)
        integer_value = normalize_integer(value)
        if integer_value is None and normalize_text(value) is not None:
            errors.append(
                build_error(row_number, column_name, 'invalid_integer', 'Value cannot be converted to integer', value),
            )
        if integer_value is not None and integer_value < 0 and not allows_negative(column_name):
            errors.append(build_error(row_number, column_name, 'negative_value', 'Value cannot be negative', value))
        normalized_row[column_name] = integer_value

    numeric_columns = schema.numeric_columns + schema.ratio_columns
    for column_name in numeric_columns:
        if column_name not in raw_row:
            normalized_row[column_name] = None
            continue
        value = raw_row.get(column_name)
        numeric_value = normalize_number(value)
        if numeric_value is None and normalize_text(value) is not None:
            errors.append(
                build_error(row_number, column_name, 'invalid_numeric', 'Value cannot be converted to numeric', value),
            )
        if numeric_value is not None and numeric_value < 0 and not allows_negative(column_name):
            errors.append(build_error(row_number, column_name, 'negative_value', 'Value cannot be negative', value))
        if column_name in schema.ratio_columns:
            errors.extend(check_ratio(row_number, column_name, numeric_value, value))
        normalized_row[column_name] = numeric_value

    for column_name in schema.required_columns:
        if normalized_row.get(column_name) is None:
            errors.append(build_error(row_number, column_name, 'empty_required_value', 'Required value is empty', None))

    normalized_row['__row_number__'] = row_number
    return normalized_row, errors


def normalize_country_fields(raw_row: dict[str, Any], normalized_row: dict[str, Any]) -> dict[str, Any]:
    """Normalize traffic countries country fields.
    Args:
        raw_row (dict[str, Any]): Raw dataframe row.
        normalized_row (dict[str, Any]): Normalized dataframe row."""
    country_code = normalize_text(raw_row.get('country'))
    country_name = normalize_text(raw_row.get('country_name_en'))
    if country_code is not None and len(country_code) <= 3:
        normalized_row['country_iso2'] = country_code.lower() if len(country_code) == 2 else None
        normalized_row['country_iso3'] = country_code.upper() if len(country_code) == 3 else None
    if country_name is not None:
        normalized_row['country'] = country_name
    return normalized_row


def check_ratio(
    row_number: int,
    column_name: str,
    numeric_value: Decimal | None,
    raw_value: Any,
) -> list[ValidationError]:
    """Check ratio value range.
    Args:
        row_number (int): Source row number.
        column_name (str): Source column name.
        numeric_value (Decimal | None): Normalized numeric value.
        raw_value (Any): Raw cell value."""
    errors = []
    if numeric_value is not None and numeric_value > 100:
        errors.append(build_error(row_number, column_name, 'ratio_out_of_range', 'Ratio value exceeds 100', raw_value))
    return errors


def allows_negative(column_name: str) -> bool:
    """Check whether negative values are allowed.
    Args:
        column_name (str): Normalized column name."""
    allowed_columns = {'changes'}
    is_allowed = column_name in allowed_columns
    return is_allowed


def build_error(
    row_number: int,
    column_name: str,
    error_code: str,
    error_message: str,
    raw_value: Any,
) -> ValidationError:
    """Build validation error.
    Args:
        row_number (int): Source row number.
        column_name (str): Source column name.
        error_code (str): Validation error code.
        error_message (str): Validation error message.
        raw_value (Any): Raw cell value."""
    validation_error = ValidationError(
        row_number=row_number,
        column_name=column_name,
        error_code=error_code,
        error_message=error_message,
        raw_value=format_value(raw_value),
    )
    return validation_error


def validate_data(data: Any, schema: FileSchema) -> ValidationResult:
    """Validate uploaded dataframe.
    Args:
        data (pd.DataFrame): Uploaded dataframe.
        schema (FileSchema): File validation schema."""
    column_errors = check_columns(data, schema)
    if column_errors:
        result = ValidationResult(valid_rows=[], errors=column_errors, row_count=len(data))
        return result

    valid_rows = []
    validation_errors = []
    data = data.copy()
    data['__row_number__'] = range(2, len(data) + 2)

    for raw_row in data.to_dict(orient='records'):
        normalized_row, row_errors = normalize_row(raw_row, schema)
        if row_errors:
            validation_errors.extend(row_errors)
        else:
            valid_rows.append(normalized_row)

    duplicate_errors = check_duplicates(valid_rows, schema)
    if duplicate_errors:
        validation_errors.extend(duplicate_errors)
        duplicate_rows = {error.row_number for error in duplicate_errors}
        valid_rows = [row for row in valid_rows if row['__row_number__'] not in duplicate_rows]

    result = ValidationResult(valid_rows=valid_rows, errors=validation_errors, row_count=len(data))
    return result


def check_duplicates(valid_rows: list[dict[str, Any]], schema: FileSchema) -> list[ValidationError]:
    """Check file-level duplicate keys.
    Args:
        valid_rows (list[dict[str, Any]]): Valid normalized rows.
        schema (FileSchema): File validation schema."""
    errors = []
    seen_keys = set()
    for row in valid_rows:
        unique_key = tuple(row.get(column_name) for column_name in schema.key_columns)
        if unique_key in seen_keys:
            errors.append(
                build_error(
                    int(row['__row_number__']),
                    ','.join(schema.key_columns),
                    'duplicate_file_key',
                    'Duplicate key inside uploaded file',
                    str(unique_key),
                ),
            )
        seen_keys.add(unique_key)
    return errors
