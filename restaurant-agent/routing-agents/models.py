from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class RestaurantContext:
    customer_id: int
    name: str
    restaurant_name: str = "Nomad Kitchen"


class InputGuardrailOutput(BaseModel):
    is_off_topic: bool
    is_inappropriate: bool
    reasoning: str


class OutputGuardrailOutput(BaseModel):
    is_unprofessional: bool
    leaks_internal_info: bool
    reasoning: str
