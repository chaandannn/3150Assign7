import logging
from anthropic import AsyncAnthropic
from core.memory import Memory
from tools.registry import get_tools, execute_tool

logger = logging.getLogger('groot.brain')

SYSTEM_PROMPT = (
    'You are Groot, a highly intelligent personal AI assistant — think Jarvis from Iron Man. '
    'You are helpful, efficient, and slightly witty. You control the user\'s Tesla Model 3 '
    'and manage their Google and Apple calendars. '
    'Keep responses concise and conversational — no markdown, no bullet points, just natural speech. '
    'Occasionally address the user as "boss" but not every message. '
    'If the user says "you there?" or a similar greeting, respond warmly and ask how you can help.'
)


class Brain:
    def __init__(self, config: dict, memory: Memory):
        self.memory = memory
        self.client = AsyncAnthropic(api_key=config['anthropic_api_key'])
        self.tools = get_tools(config)
        self.config = config

    async def process(self, user_input: str) -> str:
        self.memory.add_user(user_input)
        messages = self.memory.get_messages()
        response_text = await self._run(messages)
        self.memory.add_assistant(response_text)
        return response_text

    async def _run(self, messages: list) -> str:
        response = await self.client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=512,
            system=SYSTEM_PROMPT,
            tools=self.tools,
            messages=messages,
        )

        while response.stop_reason == 'tool_use':
            tool_results = []
            for block in response.content:
                if block.type == 'tool_use':
                    logger.info(f'Tool call: {block.name}({block.input})')
                    result = await execute_tool(block.name, block.input, self.config)
                    logger.info(f'Tool result: {result}')
                    tool_results.append({
                        'type': 'tool_result',
                        'tool_use_id': block.id,
                        'content': str(result),
                    })

            messages = messages + [
                {'role': 'assistant', 'content': response.content},
                {'role': 'user', 'content': tool_results},
            ]
            response = await self.client.messages.create(
                model='claude-sonnet-4-6',
                max_tokens=512,
                system=SYSTEM_PROMPT,
                tools=self.tools,
                messages=messages,
            )

        return ''.join(
            block.text for block in response.content if hasattr(block, 'text')
        )
