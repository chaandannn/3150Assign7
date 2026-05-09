import logging
from collections import deque

logger = logging.getLogger('groot.memory')

MAX_TURNS = 20


class Memory:
    def __init__(self):
        self._messages: deque = deque(maxlen=MAX_TURNS * 2)

    def add_user(self, text: str):
        self._messages.append({'role': 'user', 'content': text})

    def add_assistant(self, text: str):
        self._messages.append({'role': 'assistant', 'content': text})

    def get_messages(self) -> list:
        return list(self._messages)

    def end_session(self):
        self._messages.clear()
        logger.info('Session memory cleared')
