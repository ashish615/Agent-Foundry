from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ModelCreate(BaseModel):
    slug: str
    display_name: str
    provider: str
    endpoint_url: str | None = None
    context_window: int | None = None
    max_output_tokens: int | None = None
    input_cost_per_1m: Decimal | None = None
    output_cost_per_1m: Decimal | None = None
    capabilities: list[str] = []
    is_active: bool = True
    meta_json: dict = {}


class ModelUpdate(BaseModel):
    display_name: str | None = None
    endpoint_url: str | None = None
    context_window: int | None = None
    max_output_tokens: int | None = None
    input_cost_per_1m: Decimal | None = None
    output_cost_per_1m: Decimal | None = None
    capabilities: list[str] | None = None
    is_active: bool | None = None
    meta_json: dict | None = None


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    display_name: str
    provider: str
    endpoint_url: str | None
    context_window: int | None
    max_output_tokens: int | None
    input_cost_per_1m: Decimal | None
    output_cost_per_1m: Decimal | None
    capabilities: list[str]
    is_active: bool
    meta_json: dict
    created_at: datetime
    updated_at: datetime
