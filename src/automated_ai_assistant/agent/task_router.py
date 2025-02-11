import json

from autogen_core import RoutedAgent, MessageContext, DefaultTopicId, message_handler, \
    type_subscription
from autogen_core.models import UserMessage, SystemMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from automated_ai_assistant.agent.utils import load_api_key
from automated_ai_assistant.model.data_types import EndUserMessage
from automated_ai_assistant.oltp_tracing import logger
from automated_ai_assistant.utils.registry_utils import AgentRegistry


@type_subscription(topic_type="task_router")
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
        logger.info(f"Routing task: {message.content} from source: {message.source}")
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
        logger.info(f"Extracted intent: {intent}")
        if intent.content[0]:
            agent_type = json.loads(intent.content[0].arguments)["agent_type"]
            await self.runtime.publish_message(
                message,
                DefaultTopicId(type=agent_type)
            )
            return f"Routed to {agent_type} agent"

        return "Sorry, I couldn't determine which agent should handle this task."
