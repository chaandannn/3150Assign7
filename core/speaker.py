import logging
import platform
import subprocess
import threading

logger = logging.getLogger('groot.speaker')


class Speaker:
    def __init__(self, config: dict):
        self._cfg = config.get('tts', {})
        self._platform = platform.system()
        self._lock = threading.Lock()

        if self._platform != 'Darwin':
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty('rate', self._cfg.get('rate', 175))
            voice_id = self._cfg.get('voice_id')
            if voice_id:
                self._engine.setProperty('voice', voice_id)
        else:
            self._engine = None

    def say(self, text: str):
        logger.info(f'Speaking: {text}')
        with self._lock:
            if self._platform == 'Darwin':
                voice = self._cfg.get('macos_voice', 'Samantha')
                rate = self._cfg.get('macos_rate', 200)
                subprocess.run(['say', '-v', voice, '-r', str(rate), text], check=False)
            else:
                self._engine.say(text)
                self._engine.runAndWait()
