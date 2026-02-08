"""Backend package for CareConnect"""

from .database import (
    get_database_config,
    get_supabase
)

__all__ = [
    'get_database_config',
    'get_supabase'
]
