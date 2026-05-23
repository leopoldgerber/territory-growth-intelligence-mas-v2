from fastapi import APIRouter

from app.core.config import get_settings


router = APIRouter(tags=['health'])


@router.get('/health')
def read_health() -> dict[str, str]:
    """Read service health.
    Args:
        None (None): No arguments are required."""
    settings = get_settings()
    health_data = {
        'status': 'ok',
        'service': settings.app_name,
        'environment': settings.app_env,
        'version': settings.app_version,
    }
    return health_data
