import logging
from typing import List, ClassVar

from autogen_agentchat.agents import AssistantAgent
from autogen_core import type_subscription, Subscription
from autogen_core.tools import Tool, FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient

from automated_ai_assistant.agent.utils import load_api_key
from automated_ai_assistant.data_types import MeetingDetails
from automated_ai_assistant.google_utils import GoogleAPIInterface

google_api = GoogleAPIInterface()


def schedule_meeting(meeting_details: MeetingDetails) -> str:
    """
    Schedule a meeting using Google Calendar API.

    Args:
        meeting_details (object): Details of the meeting to schedule. with fields:
            start_time: Meeting start time in ISO format
            end_time: Meeting end time in ISO format
            summary: Meeting title
            description: Meeting description
            attendees: List of attendee email addresses

    Returns:
        str: Confirmation message with meeting link
    """
    try:
        logging.info(f"Scheduling meeting: {meeting_details}")
        event = google_api.schedule_meeting(
            meeting_details=meeting_details
        )
        return f"Meeting scheduled successfully: {event.get('htmlLink')}"
    except Exception as e:
        return f"Failed to schedule meeting: {str(e)}"


def get_schedule_meeting_tool() -> List[Tool]:
    return [
        FunctionTool(
            name="schedule_meeting",
            func=schedule_meeting,
            description="Schedules meeting with the details provided.",
        )
    ]


@type_subscription(topic_type='schedule_meeting')
class ScheduleMeetingAgent(AssistantAgent):

    internal_unbound_subscriptions_list: ClassVar[List[Subscription]] = []

    def __init__(self):
        self.api_key = load_api_key()
        self.model_client = OpenAIChatCompletionClient(
            model='gpt-3.5-turbo',
            api_key=self.api_key
        )
        self.google_api = GoogleAPIInterface()

        system_message = """You are a meeting scheduling assistant. Your task is to:
        1. Parse meeting requests to extract: time, duration, attendees, and purpose
        2. Use the schedule_meeting tool to create the meeting
        3. Respond in a friendly, concise manner

        For each request, you should:
        - Convert provided times to UTC
        - Create clear meeting summaries
        - Format the meeting details correctly for the tool
        """

        super().__init__(
            name='ScheduleMeetingAgent',
            model_client=self.model_client,
            system_message=system_message,
            description='Specialized agent for scheduling meetings',
            tools=[schedule_meeting]
        )
