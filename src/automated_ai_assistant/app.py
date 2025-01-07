import asyncio

from autogen_core import SingleThreadedAgentRuntime, DefaultSubscription, DefaultTopicId, AgentType

from automated_ai_assistant.agent.schedule_meeting import ScheduleMeetingAgent
from automated_ai_assistant.agent.send_email import SendEmailAgent
from automated_ai_assistant.agent.set_reminder import SetReminderAgent
from automated_ai_assistant.agent.task_router import TaskRoutingAgent
from automated_ai_assistant.model.data_types import EndUserMessage


async def initialize_agent_runtime() -> SingleThreadedAgentRuntime:
    """
    Initializes the agent runtime with the required agents and tools.

    Returns:
        SingleThreadedAgentRuntime: The initialized runtime for managing agents.
    """
    agent_runtime = SingleThreadedAgentRuntime()

    await agent_runtime.register_factory(
        type=AgentType("task_router"),
        agent_factory=lambda: TaskRoutingAgent(),
        expected_class=TaskRoutingAgent
    )

    await agent_runtime.register_factory(
        type=AgentType("schedule_meeting"),
        agent_factory=lambda: ScheduleMeetingAgent(),
        expected_class=ScheduleMeetingAgent
    )

    await agent_runtime.register_factory(
        type=AgentType("send_email"),
        agent_factory=lambda: SendEmailAgent(),
        expected_class=SendEmailAgent
    )

    await agent_runtime.register_factory(
        type=AgentType("set_reminder"),
        agent_factory=lambda: SetReminderAgent(),
        expected_class=SetReminderAgent
    )

    await agent_runtime.add_subscription(
        DefaultSubscription(topic_type="task_router", agent_type="task_router")
    )

    agent_runtime.start()

    print("Agent runtime initialized successfully.")

    return agent_runtime

async def main():
    runtime = await initialize_agent_runtime()

    test_messages = []

    for msg in test_messages:
        print(f"\nProcessing request: {msg}")
        try:
            result = await runtime.publish_message(
                message=EndUserMessage(content=msg),
                topic_id=DefaultTopicId(type="task_router")
            )
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {str(e)}")

    await runtime.stop()


if __name__ == "__main__":
    asyncio.run(main())
