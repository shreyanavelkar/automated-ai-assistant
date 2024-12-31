import json
from typing import Optional

from autogen_agentchat.messages import TextMessage
from autogen_core import RoutedAgent, message_handler, MessageContext, default_subscription
from autogen_core.models import UserMessage, SystemMessage
from autogen_ext.models import OpenAIChatCompletionClient

from automated_ai_assistant.agent.utils import load_api_key
from automated_ai_assistant.registry import AgentRegistry


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

    @message_handler()
    async def route_task(self, message: TextMessage, ctx: MessageContext) -> str:
        """
        Route a task to the appropriate specialized agent.

        Args:
            message (TextMessage): user message with task details
            ctx (MessageContext): Message context

        Returns:
            str: Response from the specialized agent
        """
        user_message = UserMessage(
            text=message.text,
            type='UserMessage',
        )
        system_message = SystemMessage(
            text=self.system_message,
            type='SystemMessage',
        )
        intent = await self.model_client.create(messages=[user_message, system_message])
        agent = await self.get_agent_from_intent(intent)
        if agent:
            return f"Routing task to {agent['agent_type']} agent..."
        else:
            return "Sorry, I don't understand that task."

    async def get_agent_from_intent(self, intent: str) -> Optional[dict]:
        return self.registry.get_agent(intent)
