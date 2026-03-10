from dataclasses import dataclass


@dataclass
class RestaurantContext:
    customer_id: int
    name: str
    restaurant_name: str = "Nomad Kitchen"
