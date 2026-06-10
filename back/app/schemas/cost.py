from pydantic import BaseModel


class CostEstimate(BaseModel):
    currency: str
    estimated_cost: float
