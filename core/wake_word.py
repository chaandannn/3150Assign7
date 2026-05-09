import asyncio
import logging
import struct
import pyaudio
import pvporcupine

logger = logging.getLogger('groot.wake_word')


class WakeWordDetector:
    def __init__(self, config: dict):
        wake_cfg = config.get('wake_word', {})
        keyword = wake_cfg.get('keyword', 'jarvis')
        custom_model = wake_cfg.get('custom_model_path')

        kwargs = {'access_key': config['picovoice_access_key']}
        if custom_model:
            kwargs['keyword_paths'] = [custom_model]
        else:
            kwargs['keywords'] = [keyword]

        self.porcupine = pvporcupine.create(**kwargs)
        self.pa = pyaudio.PyAudio()

    async def wait_for_wake(self):
        stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length,
        )
        loop = asyncio.get_running_loop()
        try:
            while True:
                result = await loop.run_in_executor(None, self._read_frame, stream)
                if result >= 0:
                    logger.info('Wake word detected')
                    return
        finally:
            stream.stop_stream()
            stream.close()

    def _read_frame(self, stream) -> int:
        pcm = stream.read(self.porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from('h' * self.porcupine.frame_length, pcm)
        return self.porcupine.process(pcm)

    def cleanup(self):
        self.pa.terminate()
        self.porcupine.delete()
