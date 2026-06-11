"""Shared schema base: camelCase JSON (matches the React frontend's
TypeScript interfaces) + a generic pagination envelope."""

from datetime import datetime, timezone
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class APIModel(BaseModel):
    """All responses serialize snake_case fields as camelCase."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    @field_serializer("*", when_used="json")
    def _tag_naive_datetimes_as_utc(self, value):
        """The DB stores naive UTC (`datetime.utcnow`). Serialized without an
        offset, browsers parse it as *local* time — shifting every timestamp
        by -5:30 for IST users. Tag naive datetimes as UTC so JSON carries
        `+00:00` and the frontend converts correctly."""
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class Paginated(APIModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
