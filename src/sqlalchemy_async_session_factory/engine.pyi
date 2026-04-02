# pylint: disable=too-many-arguments

from sqlalchemy.ext.asyncio import AsyncEngine

def create_async_engine_with_pool(
    database_url: str,
    echo: bool = ...,
    pool_size: int = ...,
    max_overflow: int = ...,
    pool_timeout: int = ...,
    pool_pre_ping: bool = ...,
    pool_recycle: int = ...,
    **kwargs: object,
) -> AsyncEngine: ...
