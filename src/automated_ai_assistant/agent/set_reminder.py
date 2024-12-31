from typing import List, ClassVar

from autogen_agentchat.agents import AssistantAgent
from autogen_core import type_subscription, Subscription
from autogen_core.tools import Tool, FunctionTool
from autogen_ext.models import OpenAIChatCompletionClient

from automated_ai_assistant.agent.utils import load_api_key
from automated_ai_assistant.data_types import ReminderDetails
from automated_ai_assistant.google_utils import GoogleAPIInterface

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


@type_subscription(topic_type='set_reminder')
class SetReminderAgent(AssistantAgent):

    internal_unbound_subscriptions_list: ClassVar[List[Subscription]] = []

    def __init__(self):
        self.api_key = load_api_key()
        self.model_client = OpenAIChatCompletionClient(
            model='gpt-3.5-turbo',
            api_key=self.api_key
        )
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
            name='SetReminderAgent',
            model_client=self.model_client,
            system_message=self.system_message,
            description='Specialized agent for setting reminders',
            tools=[set_reminder]
        )
