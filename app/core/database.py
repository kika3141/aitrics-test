import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

logger = logging.getLogger("sqlmodel.engine")

engine = create_async_engine(
    settings.database_url,
    echo=True,
    pool_pre_ping=True,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        txn = session.sync_session.get_transaction()
        txn_id = id(txn) if txn else "none"
        logger.debug(f"[SESSION] opened — transaction_id={txn_id}")
        try:
            yield session
            await session.commit()
            logger.debug(f"[SESSION] committed — transaction_id={txn_id}")
        except Exception:
            await session.rollback()
            logger.debug(f"[SESSION] rolled back — transaction_id={txn_id}")
            raise
