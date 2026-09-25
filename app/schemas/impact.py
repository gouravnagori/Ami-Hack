from pydantic import Field, model_validator

from app.schemas.common import SchemaBase


class ImpactSeriesPoint(SchemaBase):
    date: str
    meals: int


class ImpactSummary(SchemaBase):
    meals_rescued: int
    weight_kg: float
    co2e_kg_avoided: float
    co2e_kg: float = 0.0
    on_time_rate: float
    median_time_to_match_s: float
    donations_total: int
    series: list[ImpactSeriesPoint] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def sync_co2e(cls, data):
        if isinstance(data, dict):
            if "co2e_kg" not in data or data["co2e_kg"] is None:
                data["co2e_kg"] = data.get("co2e_kg_avoided", 0.0)
            if "co2e_kg_avoided" not in data or data["co2e_kg_avoided"] is None:
                data["co2e_kg_avoided"] = data.get("co2e_kg", 0.0)
        return data
