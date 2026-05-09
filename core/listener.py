import io
import logging
import wave
import asyncio
import webrtcvad
import pyaudio
from faster_whisper import WhisperModel

logger = logging.getLogger('groot.listener')

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_MS = 30
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_MS / 1000)  # 480 samples
SILENCE_TIMEOUT_FRAMES = int(2000 / CHUNK_MS)        # 2s of silence ends utterance
NO_SPEECH_TIMEOUT_FRAMES = int(8000 / CHUNK_MS)      # 8s with no speech -> None
MIN_VOICED_FRAMES = int(300 / CHUNK_MS)              # minimum 300ms of actual speech


class Listener:
    def __init__(self, config: dict):
        model_size = config.get('stt', {}).get('whisper_model', 'base.en')
        logger.info(f'Loading Whisper model: {model_size}')
        self.model = WhisperModel(model_size, device='cpu', compute_type='int8')
        self.vad = webrtcvad.Vad(2)
        self.pa = pyaudio.PyAudio()
        logger.info('Listener ready')

    async def record_utterance(self):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._record_blocking)

    def _record_blocking(self):
        stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SAMPLES,
        )
        frames = []
        silent_frames = 0
        voiced_frames = 0
        pre_speech_timeout = 0

        try:
            while True:
                pcm = stream.read(CHUNK_SAMPLES, exception_on_overflow=False)
                is_speech = self.vad.is_speech(pcm, SAMPLE_RATE)

                if is_speech:
                    voiced_frames += 1
                    silent_frames = 0
                    pre_speech_timeout = 0
                    frames.append(pcm)
                elif voiced_frames > 0:
                    silent_frames += 1
                    frames.append(pcm)
                    if silent_frames >= SILENCE_TIMEOUT_FRAMES:
                        break
                else:
                    pre_speech_timeout += 1
                    if pre_speech_timeout >= NO_SPEECH_TIMEOUT_FRAMES:
                        return None
        finally:
            stream.stop_stream()
            stream.close()

        if voiced_frames < MIN_VOICED_FRAMES:
            return None

        return b''.join(frames)

    def transcribe(self, audio_bytes: bytes) -> str:
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_bytes)
        buf.seek(0)
        segments, _ = self.model.transcribe(buf, language='en', vad_filter=True)
        return ' '.join(seg.text for seg in segments).strip()
