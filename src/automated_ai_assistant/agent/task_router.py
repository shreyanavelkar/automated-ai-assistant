import asyncio
import json

from autogen_core import RoutedAgent, MessageContext, default_subscription, SingleThreadedAgentRuntime, \
    AgentType, DefaultTopicId, DefaultSubscription, message_handler
from autogen_core.models import UserMessage, SystemMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from automated_ai_assistant.agent.schedule_meeting import ScheduleMeetingAgent
from automated_ai_assistant.agent.send_email import SendEmailAgent
from automated_ai_assistant.agent.set_reminder import SetReminderAgent
from automated_ai_assistant.agent.utils import load_api_key
from automated_ai_assistant.model.data_types import EndUserMessage
from automated_ai_assistant.utils.registry_utils import AgentRegistry


@default_subscription
class TaskRoutingAgent(RoutedAgent):
    def __init__(self):
        self.registry = AgentRegistry()
        self.api_key = load_api_key()
        self.model_client = OpenAIChatCompletionClient(
            model='gpt-3.5-turbo',
            api_key=self.api_key
        )
        self.system_message = """You are a task routing assistant. Your task is to:
            1. Parse task requests to extract: intent, based on the user's message and given examples
            2. Use the registry to route the task to the appropriate specialized agent
            3. Respond in a friendly, concise manner
            
            For each request, you should:
            - Identify the intent of the task
            - Use the registry below to find the appropriate specialized agent
        """ + json.dumps(self.registry.agents, indent=4)
        super().__init__(
            description='Agent that routes tasks to specialized agents'
        )

    @message_handler
    async def route_task(self, message: EndUserMessage, ctx: MessageContext) -> str:
        """
        Route a task to the appropriate specialized agent.

        Args:
            message (EndUserMessage): user message with task details
            ctx (MessageContext): Message context

        Returns:
            str: Response from the specialized agent
        """
        print(f"Routing task: {message.content}")
        user_message = UserMessage(
            content=message.content,
            source=ctx.topic_id.type,
            type="UserMessage",
        )
        system_message = SystemMessage(
            content=self.system_message,
            source=ctx.topic_id.type,
            type="SystemMessage",
        )
        tools = [{
            "name": "determine_agent",
            "description": "Determine which specialized agent should handle the task",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_type": {
                        "type": "string",
                        "enum": list(self.registry.agents.keys())
                    }
                },
                "required": ["agent_type"]
            }
        }]
        intent = await self.model_client.create(messages=[user_message, system_message],
                                                tools=tools)
        if intent.content[0]:
            agent_type = json.loads(intent.content[0].arguments)["agent_type"]
            await self.runtime.publish_message(
                user_message,
                DefaultTopicId(type=agent_type)
            )
            return f"Routed to {agent_type} agent"

        return "Sorry, I couldn't determine which agent should handle this task."


async def test_router():
    self.model_client = OpenAIChatCompletionClient(
        model='gpt-3.5-turbo',
        api_key=self.api_key
    )


    # router = await agent_runtime.get(AgentType("task_router"))
    test_messages = []

    for msg in test_messages:
        print(f"\nTesting message: {msg}")
        try:
            response = await agent_runtime.publish_message(
                EndUserMessage(content=msg),
                DefaultTopicId(type="task_router")
            )
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {str(e)}")

    await agent_runtime.stop_when_idle()


if __name__ == "__main__":
    asyncio.run(test_router())
