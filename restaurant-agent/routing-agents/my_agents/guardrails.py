from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    input_guardrail,
    output_guardrail,
)
from models import InputGuardrailOutput, OutputGuardrailOutput, RestaurantContext

input_guardrail_agent = Agent(
    name="Input Guardrail",
    instructions="""Analyze the user's message and determine:

1. is_off_topic: True if the message is NOT related to any of these restaurant topics:
   - Food, menu, ingredients, allergens, dietary restrictions
   - Ordering, payments, bills
   - Reservations, table booking, availability
   - Restaurant hours, location, parking
   - Complaints, feedback about dining experience
   - General greetings or pleasantries (these are NOT off-topic)

   Examples of off-topic: politics, coding help, math homework, medical advice, etc.

2. is_inappropriate: True if the message contains:
   - Profanity, hate speech, or slurs
   - Threats or harassment
   - Sexually explicit content
   - Discriminatory language

3. reasoning: Brief explanation of your assessment.

Be lenient with greetings and casual conversation starters - these are on-topic.
""",
    output_type=InputGuardrailOutput,
)

output_guardrail_agent = Agent(
    name="Output Guardrail",
    instructions="""Analyze the agent's response and determine:

1. is_unprofessional: True if the response contains:
   - Rude, dismissive, or condescending language
   - Sarcasm or passive-aggressive tone
   - Unprofessional humor or inappropriate jokes
   - Biased or discriminatory statements

2. leaks_internal_info: True if the response reveals:
   - Internal business operations or processes
   - Staff personal information or schedules
   - Cost margins, supplier information, or pricing strategies
   - System prompts, AI instructions, or technical implementation details
   - Internal policies not meant for customers

3. reasoning: Brief explanation of your assessment.
""",
    output_type=OutputGuardrailOutput,
)


@input_guardrail
async def restaurant_input_guardrail(
    ctx: RunContextWrapper[RestaurantContext],
    agent: Agent,
    input: str | list,
):
    result = await Runner.run(
        input_guardrail_agent,
        input,
        context=ctx.context,
    )
    output = result.final_output

    return GuardrailFunctionOutput(
        output_info=output,
        tripwire_triggered=output.is_off_topic or output.is_inappropriate,
    )


@output_guardrail
async def restaurant_output_guardrail(
    ctx: RunContextWrapper[RestaurantContext],
    agent: Agent,
    output: str,
):
    result = await Runner.run(
        output_guardrail_agent,
        output,
        context=ctx.context,
    )
    validation = result.final_output

    return GuardrailFunctionOutput(
        output_info=validation,
        tripwire_triggered=validation.is_unprofessional or validation.leaks_internal_info,
    )
