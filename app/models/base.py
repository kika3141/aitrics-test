import re
from datetime import datetime

from sqlalchemy import event, text
from sqlalchemy.orm import declared_attr
from sqlmodel import Field, SQLModel

from app.core.utils import utcnow

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uix_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}

SQLModel.metadata.naming_convention = naming_convention


def _underscore(name: str) -> str:
    """PascalCase → snake_case"""
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return s.lower()


class BaseSQLModel(SQLModel):
    @declared_attr
    def __tablename__(cls) -> str:
        return _underscore(cls.__name__)


class BaseIntIDModel(BaseSQLModel):
    """Auto-increment 정수 PK + optimistic lock"""

    id: int | None = Field(default=None, primary_key=True)
    version: int = Field(default=1)


class BaseCreatedUpdatedModel(SQLModel):
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "nullable": False,
        },
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "nullable": False,
        },
    )

    @classmethod
    def __declare_last__(cls):
        @event.listens_for(cls, "before_update")
        def receive_before_update(mapper, connection, target):
            target.updated_at = utcnow()


