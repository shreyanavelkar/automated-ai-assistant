import asyncio

from autogen_core import DefaultTopicId
from autogen_ext.models.openai import OpenAIChatCompletionClient
from automated_ai_assistant.oltp_tracing import logger
from fastapi import FastAPI

from automated_ai_assistant.agent.utils import load_api_key
from automated_ai_assistant.model.data_types import EndUserMessage
from automated_ai_assistant.utils.runtime_utils import initialize_agent_runtime

app = FastAPI()


@app.get("/")
def check_health():
    return "Alive"


async def process():
    api_key = load_api_key()
    model_client = OpenAIChatCompletionClient(
        api_key=api_key,
        model="gpt-3.5-turbo",
        temperature=0.2
    )
    runtime = await initialize_agent_runtime(model_client=model_client)

    test_messages = [
    ]

    for msg in test_messages:
        logger.info(f"\nProcessing request: {msg}")
        try:
            result = await runtime.publish_message(
                message=EndUserMessage(content=msg),
                topic_id=DefaultTopicId(type="task_router")
            )
            logger.info(f"Result: {result}")
        except Exception as e:
            print(f"Error: {str(e)}")

    await runtime.stop_when_idle()


if __name__ == "__main__":
    asyncio.run(process())