import json
import logging
from typing import List

from autogen_core import type_subscription, RoutedAgent, message_handler, MessageContext
from autogen_core.models import UserMessage, LLMMessage, SystemMessage
from autogen_core.tools import Tool, FunctionTool
from autogen_ext.models import OpenAIChatCompletionClient

from automated_ai_assistant.agent.utils import load_api_key
from automated_ai_assistant.model.data_types import EmailDetails
from automated_ai_assistant.utils.google_utils import GoogleAPIInterface

google_api = GoogleAPIInterface()


def send_email(email_details: EmailDetails) -> str:
    """
    :param email_details:
    :return:
    """
    try:
        email = google_api.send_email(
            email_details=email_details
        )
        return f"Email sent successfully: {email.get('id')}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


def get_send_email_tool() -> List[Tool]:
    return [
        FunctionTool(
            name="send_email",
            func=send_email,
            description="Send email with the details provided.",
        )
    ]


@type_subscription(topic_type='send_email')
class SendEmailAgent(RoutedAgent):

    def __init__(self):
        self.api_key = load_api_key()
        self.model_client = OpenAIChatCompletionClient(
            model='gpt-3.5-turbo',
            api_key=self.api_key
        )
        self.system_message = """You are an email sending assistant. Your task is to:
            1. Parse email requests to extract: subject, body, and recipients
            2. Use the send_email tool to send the email
            3. Respond in a friendly, concise manner
            
            For each request, you should:
            - Create clear email subjects
            - Format the email details correctly for the tool
        """
        super().__init__(
            description='Specialized agent for sending emails'
        )

    @message_handler
    async def handle_message(self, message: UserMessage, ctx: MessageContext) -> str:
        try:
            session: List[LLMMessage] = [message, SystemMessage(content=self.system_message, type="SystemMessage")]
            response = await self.model_client.create(messages=session,
                                                      tools=get_send_email_tool())
            if response.finish_reason == 'function_calls':
                function_call = response.content[0]
                raw_args = json.loads(function_call.arguments)
                email_details = EmailDetails(**raw_args['email_details'])
                result = send_email(email_details)
                return result
        except Exception as e:
            logging.error(f"Error handling message: {str(e)}")
            return "Failed to schedule the meeting."
