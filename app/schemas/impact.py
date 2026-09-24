from pydantic import Field

from app.schemas.common import SchemaBase


class ImpactSeriesPoint(SchemaBase):
    date: str
    meals: int


class ImpactSummary(SchemaBase):
    meals_rescued: int
    weight_kg: float
    co2e_kg_avoided: float
    on_time_rate: float
    median_time_to_match_s: float
    donations_total: int
    series: list[ImpactSeriesPoint] = Field(default_factory=list)
