import asyncio
import json

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Handoff
from autogen_core import DefaultTopicId
from autogen_ext.models.openai import OpenAIChatCompletionClient
from fastapi import FastAPI

from automated_ai_assistant.agent.utils import load_api_key
from automated_ai_assistant.model.data_types import EndUserMessage
from automated_ai_assistant.oltp_tracing import logger
from automated_ai_assistant.utils.runtime_utils import initialize_agent_runtime

app = FastAPI()


@app.get("/")
def check_health():
    return "Alive"


def map_of_intent_to_required_fields():
    required_fields_map = {
        "schedule_meeting": ["start time", "duration", "attendees", "summary", "description"],
        "send_email": ["subject", "body", "recipients"],
        "set_reminder": ["title", "description", "time"]
    }
    return required_fields_map


def intent():
    return ["schedule_meeting", "send_email", "set_reminder"]


def return_response_to_user(message: str) -> str:
    return f"{message}"


def handoff_to() -> Handoff:
    return Handoff(
        target="task_router",
        description="Handoff to task router",
        name="transfer_to_task_router",
        message="Transferred to task router, adopting the role of task router immediately."
    )


class ChatAgent(AssistantAgent):
    def __init__(self, model_client: OpenAIChatCompletionClient):
        self.model_client = model_client
        self.system_messages = """You are a helpful personal AI assistant. Helping users with the following tasks:
            1. Schedule meetings
            2. Send emails
            3. Set reminders
            
            For each task, you should:
            - From the input message, identify the intent """ + json.dumps(intent(), indent=4) + """
            - Required fields should be one of the following: """ + json.dumps(map_of_intent_to_required_fields(),
                                                                               indent=4) + """
            - Respond to user greetings
            - based on the user's message identify the task type and engage with the user to gather all required information
            - Once all the information is gathered, use the appropriate specialized agent to handle the task
            """

        super().__init__(
            name="ChatAgent",
            model_client=model_client,
            tools=[return_response_to_user],
            handoffs=[handoff_to()],
            reflect_on_tool_use=True,
            tool_call_summary_format="{result}"
        )


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
                message=EndUserMessage(content=msg, source="user"),
                topic_id=DefaultTopicId(type="task_router")
            )
            logger.info(f"Result: {result}")
        except Exception as e:
            print(f"Error: {str(e)}")

    await runtime.stop_when_idle()


if __name__ == "__main__":
    asyncio.run(process())
