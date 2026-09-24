from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class GeoPoint(SchemaBase):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    address: str | None = None


class CursorPage(SchemaBase, Generic[T]):
    items: list[T]
    next_cursor: str | None = None


class ErrorDetail(SchemaBase):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str = ""


class ErrorResponse(SchemaBase):
    error: ErrorDetail
