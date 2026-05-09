import asyncio
import logging
import signal
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger('groot')


async def main():
    from config import load_config
    from core.wake_word import WakeWordDetector
    from core.listener import Listener
    from core.brain import Brain
    from core.speaker import Speaker
    from core.memory import Memory

    config = load_config()
    memory = Memory()
    speaker = Speaker(config)
    listener = Listener(config)
    brain = Brain(config, memory)
    wake = WakeWordDetector(config)

    logger.info('Groot online')
    speaker.say('Groot online. At your service.')

    def handle_shutdown(sig, frame):
        speaker.say('Shutting down. Goodbye.')
        wake.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    while True:
        logger.info('Waiting for wake word...')
        await wake.wait_for_wake()
        speaker.say('Yes?')

        session_silence = 0
        while True:
            audio = await listener.record_utterance()
            if audio is None:
                session_silence += 1
                if session_silence >= 2:
                    speaker.say("I'll be listening.")
                    memory.end_session()
                    break
                continue

            session_silence = 0
            text = listener.transcribe(audio)
            if not text.strip():
                continue

            logger.info(f'User: {text}')

            if any(kw in text.lower() for kw in ['goodbye', "that's all", 'go to sleep', 'goodnight', 'dismiss']):
                speaker.say('Of course. I will be here.')
                memory.end_session()
                break

            response = await brain.process(text)
            logger.info(f'Groot: {response}')
            speaker.say(response)


if __name__ == '__main__':
    asyncio.run(main())
