from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models import OpenAIChatCompletionClient

from automated_ai_assistant.agent.utils import load_api_key
from automated_ai_assistant.data_types import EmailDetails
from automated_ai_assistant.google_utils import GoogleAPIInterface


class SendEmailAgent(AssistantAgent):

    def __init__(self):
        self.api_key = load_api_key()
        self.model_client = OpenAIChatCompletionClient(
            model='gpt-3.5-turbo',
            api_key=self.api_key
        )
        self.google_api = GoogleAPIInterface()
        self.system_message = """You are an email sending assistant. Your task is to:
            1. Parse email requests to extract: subject, body, and recipients
            2. Use the send_email tool to send the email
            3. Respond in a friendly, concise manner
            
            For each request, you should:
            - Create clear email subjects
            - Format the email details correctly for the tool
        """
        super().__init__(
            name='SendEmailAgent',
            model_client=self.model_client,
            system_message=self.system_message,
            description='Specialized agent for sending emails',
            tools=[self.send_email]
        )

    def send_email(self, email_details: EmailDetails) -> str:
        """
        :param email_details:
        :return:
        """
        try:
            details = EmailDetails(**email_details)
            email = self.google_api.send_email(
                email_details=details
            )
            return f"Email sent successfully: {email.get('id')}"
        except Exception as e:
            return f"Error sending email: {str(e)}"
