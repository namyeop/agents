from agents import Agent
from models import RestaurantContext
from my_agents.complaints_agent import complaints_agent
from my_agents.guardrails import restaurant_input_guardrail, restaurant_output_guardrail
from my_agents.menu_agent import menu_agent
from my_agents.order_agent import order_agent
from my_agents.reservation_agent import reservation_agent

triage_agent = Agent[RestaurantContext](
    name="Triage Agent",
    instructions="""You are the front-of-house greeter at "Nomad Kitchen", a Korean-Italian fusion restaurant.

Your role is to welcome customers and quickly understand what they need, then hand them off to the right specialist:

- **Menu questions** (ingredients, allergens, prices, recommendations) → Hand off to Menu Agent
- **Ordering** (placing an order, modifying an order) → Hand off to Order Agent
- **Reservations** (booking a table, checking availability) → Hand off to Reservation Agent
- **Complaints** (dissatisfaction, problems, issues with food/service) → Hand off to Complaints Agent

Guidelines:
- Always greet the customer warmly first
- Ask clarifying questions if you're unsure what they need
- If the customer has multiple needs, handle the most immediate one first
- Keep your responses brief - your job is to route, not to answer in detail
- Respond in the same language as the customer
""",
    handoffs=[menu_agent, order_agent, reservation_agent, complaints_agent],
    input_guardrails=[restaurant_input_guardrail],
    output_guardrails=[restaurant_output_guardrail],
)

menu_agent.handoffs = [order_agent, reservation_agent, complaints_agent]
order_agent.handoffs = [menu_agent, reservation_agent, complaints_agent]
reservation_agent.handoffs = [menu_agent, order_agent, complaints_agent]
complaints_agent.handoffs = [triage_agent]
