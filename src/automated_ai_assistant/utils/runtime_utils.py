from autogen_core import SingleThreadedAgentRuntime, AgentType, DefaultSubscription

from automated_ai_assistant.agent.schedule_meeting import ScheduleMeetingAgent
from automated_ai_assistant.agent.send_email import SendEmailAgent
from automated_ai_assistant.agent.set_reminder import SetReminderAgent
from automated_ai_assistant.agent.task_router import TaskRoutingAgent


async def initialize_agent_runtime(model_client) -> SingleThreadedAgentRuntime:
    """
    Initializes the agent runtime with the required agents and tools.

    Returns:
        SingleThreadedAgentRuntime: The initialized runtime for managing agents.
    """
    agent_runtime = SingleThreadedAgentRuntime()

    await agent_runtime.add_subscription(
        DefaultSubscription(topic_type="task_router", agent_type="task_router")
    )

    agent_runtime = SingleThreadedAgentRuntime()
    agent_type = AgentType("task_router")
    schedule_meeting_type = AgentType("schedule_meeting")
    set_reminder_type = AgentType("set_reminder")
    send_email_type = AgentType("send_email")

    await agent_runtime.register_factory(type=agent_type,
                                         agent_factory=lambda: TaskRoutingAgent(),
                                         expected_class=TaskRoutingAgent)

    await agent_runtime.register_factory(type=schedule_meeting_type,
                                         agent_factory=lambda: ScheduleMeetingAgent(model_client=model_client),
                                         expected_class=ScheduleMeetingAgent)

    await agent_runtime.register_factory(type=set_reminder_type,
                                         agent_factory=lambda: SetReminderAgent(model_client=model_client),
                                         expected_class=SetReminderAgent)

    await agent_runtime.register_factory(type=send_email_type,
                                         agent_factory=lambda: SendEmailAgent(model_client=model_client),
                                         expected_class=SendEmailAgent)

    await agent_runtime.add_subscription(
        DefaultSubscription(
            topic_type="task_router",
            agent_type="task_router"
        )
    )

    for agent_type in ["schedule_meeting", "send_email", "set_reminder"]:
        await agent_runtime.add_subscription(
            DefaultSubscription(
                topic_type=agent_type,
                agent_type=agent_type
            )
        )
    agent_runtime.start()

    print("Agent runtime initialized successfully.")

    return agent_runtime
