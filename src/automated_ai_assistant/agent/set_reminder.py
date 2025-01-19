import json
from typing import List

from autogen_core import type_subscription, RoutedAgent, message_handler, MessageContext
from autogen_core.models import UserMessage, LLMMessage, SystemMessage
from autogen_core.tools import Tool, FunctionTool
from autogen_ext.models import OpenAIChatCompletionClient
from automated_ai_assistant.model.data_types import ReminderDetails, EndUserMessage
from automated_ai_assistant.oltp_tracing import logger
from automated_ai_assistant.utils.google_utils import GoogleAPIInterface

google_api = GoogleAPIInterface()


def set_reminder(reminder_details: ReminderDetails) -> str:
    """
    Set a reminder using Google Calendar API.

    Args:
        reminder_details (object): Details of the reminder to set. with fields:
            title: Reminder title
            description: Reminder description
            reminder_time: Reminder time in ISO format

    Returns:
        str: Confirmation message with reminder link
    """
    try:
        logger.info(f"Setting reminder: {reminder_details}")
        reminder = google_api.set_reminder(
            reminder_details=reminder_details
        )
        return f"Reminder set successfully: {reminder.get('htmlLink')}"
    except Exception as e:
        return f"Error setting reminder: {str(e)}"


def get_set_reminder_tool() -> List[Tool]:
    return [
        FunctionTool(
            name="set_reminder",
            func=set_reminder,
            description="Set a reminder with the details provided.",
        )
    ]


@type_subscription(topic_type="set_reminder")
class SetReminderAgent(RoutedAgent):

    def __init__(self, model_client: OpenAIChatCompletionClient):
        self.model_client = model_client
        self.system_message = """You are a reminder setting assistant. Your task is to:
            1. Parse reminder requests to extract: title, description, and time
            2. Use the set_reminder tool to create the reminder
            3. Respond in a friendly, concise manner
            
            For each request, you should:
            - Convert provided times to UTC
            - Create clear reminder titles
            - Format the reminder details correctly for the tool
        """
        super().__init__(
            description='Specialized agent for setting reminders'
        )

    @message_handler
    async def handle_message(self, message: EndUserMessage, ctx: MessageContext) -> str:
        try:
            logger.info(f"Received message: {message.content} from source: {message.source}")
            session: List[LLMMessage] = [UserMessage(content=message.content, type="UserMessage"),
                                         SystemMessage(content=self.system_message, type="SystemMessage")]
            response = await self.model_client.create(messages=session,
                                                      tools=get_set_reminder_tool())
            logger.info(f"Received response: {response}")
            if response.finish_reason == 'function_calls':
                function_call = response.content[0]
                raw_args = json.loads(function_call.arguments)
                reminder_details = ReminderDetails(**raw_args['reminder_details'])
                result = set_reminder(reminder_details)
                return result
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            return "Failed to schedule the meeting."
