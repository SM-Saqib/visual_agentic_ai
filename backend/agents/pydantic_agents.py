from pydantic_ai import Agent
from pydantic import BaseModel
from typing import Optional
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai import RunContext  # Import RunContext

from backend.vector_search import PineconeSearch

# TODO try to resolve issue with Fallback model, and make it work to use multiple models if one fails
# gpt_4o_mini_model = OpenAIModel("openai:gpt-4o-mini-2024-07-18")
# gpt_4o_model = OpenAIModel("openai:gpt-4o")
# fallback_model = FallbackModel(gpt_4o_mini_model, gpt_4o_model)

basic_communication_agent = Agent(
    "openai:gpt-4o",
    system_prompt="You are a sales person , and you are talking to a customer.",
    result_tool_name="final_answer",
    result_type=str,
)


def create_basic_communication_agent(system_prompt: str) -> Agent:
    """Create a basic agent for communication."""
    return Agent(
        "openai:gpt-4o",
        system_prompt=system_prompt,
        result_tool_name="final_answer",
        result_type=str,
    )


# example usage to test the agent

if __name__ == "__main__":
    import asyncio

    async def main():
        answer = await basic_communication_agent.run("tell me about yourself?")
        print(answer)

    asyncio.run(main())
