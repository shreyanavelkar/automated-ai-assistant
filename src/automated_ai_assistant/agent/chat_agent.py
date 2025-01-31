import json

from autogen_core import default_subscription, RoutedAgent, message_handler, MessageContext, DefaultTopicId
from autogen_core.models import UserMessage, SystemMessage
from autogen_ext.models import OpenAIChatCompletionClient

from automated_ai_assistant.model.data_types import EndUserMessage
from automated_ai_assistant.oltp_tracing import logger


@default_subscription
class ChatAgent(RoutedAgent):

    def map_of_intent_to_required_fields(self):
        required_fields_map = {
            "schedule_meeting": ["start time", "duration", "attendees", "summary", "description"],
            "send_email": ["subject", "body", "recipients"],
            "set_reminder": ["title", "description", "time"]
        }
        return required_fields_map

    def intent(self):
        return ["schedule_meeting", "send_email", "set_reminder"]

    def __init__(self, model_client: OpenAIChatCompletionClient):
        self.model_client = model_client
        self.system_messages = """You are a helpful personal AI assistant. Helping users with the following tasks:
            1. Schedule meetings
            2. Send emails
            3. Set reminders

            For each task, you should:
            - From the input message, identify the intent """ + json.dumps(self.intent(), indent=4) + """
            - Required fields should be one of the following: """ + json.dumps(self.map_of_intent_to_required_fields(),
                                                                               indent=4) + """
            - Respond to user greetings
            - based on the user's message identify the task type and engage with the user to gather all required information
            - Once all the information is gathered, use the tool call_task_router to handoff the task to the task router

             example: 
             user : I want to schedule a meeting with john
             assistant : Sure, I can help with that. Can you please provide me with the start time, duration, attendees, summary, and description of the meeting?
             user : 10:00 AM, 1 hour
             assistant : Who else will be attending the meeting?
             user : john
             assistant : Can you provide me the email Id of john?
             user : john@abc.com
             assistant : Great! What should be the title of the meeting?
             user : Project discussion
             assistant : What should be the description of the meeting?
             user : Discuss the project progress, timelines, and blockers
             assistant : Great! I have all the required information. Let me schedule the meeting for you.
             next you will create a prompt message to handoff the task to the task router, like:
             schedule a meeting with john@abc.com on 23rd January 2026 at 10:00 AM for 1 hour with the title Project discussion and description Discuss the project progress, timelines, and blockers

             example of the task handoff to the task router:
             user : I want to schedule a meeting with john@abc.com on 23rd January 2026 at 10:00 AM for 1 hour with the title Project discussion and description Discuss the project progress, timelines, and blockers
             assistant : Great! I have all the required information. Let me schedule the meeting for you.
            """

        super().__init__("ChatAgent")

    @message_handler
    async def engage_with_user(self, message: EndUserMessage, ctx: MessageContext) -> None:
        """
        Engage with the user until all required information is gathered.

        Args:
            message (str): User message
            ctx (MessageContext): Message context

        Returns:
            str: Response to the user
        """

        try:

            tools = [{
                "name": "determine_next_action",
                "description": "Determine if the response should be a text message returned to user or calling task_router",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt_to_task_router": {
                            "type": "string",
                            "description": "Prompt to handoff the task to the task router"
                        }
                    },
                    "required": ["response_type"]
                }
            }]

            user_message = UserMessage(
                content=message.content,
                source="user",
                type="UserMessage",
            )
            system_message = SystemMessage(
                content=self.system_messages,
                type="SystemMessage",
            )
            response = await self.model_client.create(
                messages=[
                    user_message,
                    system_message
                ],
                tools=tools
            )

            logger.info(f"Received response: {response}")

            if response.finish_reason == "function_call":
                arguments = json.loads(response.content[0].arguments)
                if "prompt_to_task_router" in arguments:
                    await self.publish_message(
                        message=EndUserMessage(content=arguments["prompt_to_task_router"], source="ChatAgent"),
                        topic_id=DefaultTopicId(type="task_router")
                    )

        except Exception as e:
            logger.error(f"Failed to parse response: {str(e)}")
