import json
import logging
from typing import List

from autogen_core import type_subscription, message_handler, MessageContext, RoutedAgent
from autogen_core.models import UserMessage, LLMMessage, SystemMessage
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
            description="Schedules meeting with the details provided."
        )
    ]


@type_subscription(topic_type="schedule_meeting")
class ScheduleMeetingAgent(RoutedAgent):

    def __init__(self):
        self.api_key = load_api_key()
        self.model_client = OpenAIChatCompletionClient(
            model='gpt-3.5-turbo',
            api_key=self.api_key
        )
        self.google_api = GoogleAPIInterface()

        self.system_message = """You are a meeting scheduling assistant. Your task is to:
        1. Parse meeting requests to extract: time, duration, attendees, and purpose
        2. Use the schedule_meeting tool to create the meeting
        3. Respond in a friendly, concise manner

        For each request, you should:
        - Convert provided times to UTC
        - Create clear meeting summaries
        - Format the meeting details correctly for the tool
        """
        super().__init__(
            description='Specialized agent for scheduling meetings'
        )

    @message_handler
    async def handle_message(self, message: UserMessage, ctx: MessageContext) -> str:
        try:
            session: List[LLMMessage] = [message, SystemMessage(content=self.system_message, type="SystemMessage")]
            response = await self.model_client.create(messages=session,
                                                      tools=get_schedule_meeting_tool())
            if response.finish_reason == 'function_calls':
                function_call = response.content[0]
                raw_args = json.loads(function_call.arguments)
                meeting_details = MeetingDetails(**raw_args['meeting_details'])
                result = schedule_meeting(meeting_details)
                return result
        except Exception as e:
            logging.error(f"Error handling message: {str(e)}")
            return "Failed to schedule the meeting."
