from typing import Any, List, Optional

from automated_ai_assistant.agent.schedule_meeting import get_schedule_meeting_tool
from automated_ai_assistant.agent.send_email import get_send_email_tool
from automated_ai_assistant.agent.set_reminder import get_set_reminder_tool


class AgentRegistry:
    def __init__(self):
        self.agents = {
            "router": {
                'agent_type': 'task_router',
                'description': 'Agent that routes tasks to specialized agents',
                'examples': 'Schedule a meeting with john@example.com at 3PM on 3rd January 2025, Set a reminder to shop for groceries at 2PM on 2nd January 2025,Send a Christmas greetings email to Jane@example.com'
            },
            "send_email": {
                'agent_type': 'send_email',
                'description': 'Specialized agent for sending emails',
                'examples': 'Send an email to abc@gmail.com asking for project update, Send a reminder email to john@exampl.com asking for updates on weekly report'
            },
            "set_reminder": {
                'agent_type': 'set_reminder',
                'description': 'Specialized agent for setting reminders',
                'examples': 'Remind me to buy groceries at 2PM on 2nd January 2025, Remind me to call John at 3PM on 3rd January 2025'
            },
            "schedule_meeting": {
                'agent_type': 'schedule_meeting',
                'description': 'Specialized agent for scheduling meetings',
                'examples': 'Schedule a meeting with john@example.com to discuss weekly updates at 3PM on 3rd January 2025, Schedule a meeting with jane@eample.com asking for help on a project'
            }
        }

    def retrieve_all_agent_tools(self) -> List[dict[str, Any]]:
        tools = []
        agent_tools = {
            'schedule_meeting': get_schedule_meeting_tool(),
            'send_email': get_send_email_tool(),
            'set_reminder': get_set_reminder_tool()
        }

        for agent, tool_list in agent_tools.items():
            for tool in tool_list:
                tools.append({
                    'agent': agent,
                    'function': tool.name,
                    'description': tool.description,
                    'arguments': list(tool.schema["parameters"]["properties"])
                })

        return tools