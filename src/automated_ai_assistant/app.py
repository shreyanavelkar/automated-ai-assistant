import asyncio

from autogen_core import DefaultTopicId
from autogen_ext.models.openai import OpenAIChatCompletionClient

from automated_ai_assistant.agent.utils import load_api_key
from automated_ai_assistant.model.data_types import EndUserMessage
from automated_ai_assistant.utils.runtime_utils import initialize_agent_runtime


async def main():
    api_key = load_api_key()
    model_client = OpenAIChatCompletionClient(
        api_key=api_key,
        model="gpt-3.5-turbo",
        temperature=0.2
    )
    runtime = await initialize_agent_runtime(model_client=model_client)

    test_messages = [
        # "I need to schedule a meeting with my boss",
        # "I need to set a reminder for tomorrow",
        # "I need to send an email to my boss"
    ]

    for msg in test_messages:
        print(f"\nProcessing request: {msg}")
        try:
            result = await runtime.publish_message(
                message=EndUserMessage(content=msg),
                topic_id=DefaultTopicId(type="task_router")
            )
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {str(e)}")

    await runtime.stop()


if __name__ == "__main__":
    asyncio.run(main())
