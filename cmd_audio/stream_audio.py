"""Real-time audio streaming for live mic/system input (Phase 2.1)."""

from __future__ import annotations

import math
import threading
import queue
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from cmd_audio.config import FREQ_CENTERS
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)

try:
    import pyaudio  # type: ignore[import-untyped]
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

try:
    import sounddevice as sd  # type: ignore[import-untyped]
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False


@dataclass
class StreamingAudioConfig:
    """Configuration for real-time audio streaming."""
    sample_rate: int = 44100
    channels: int = 1
    sample_width: int = 2  # bytes per sample
    chunk_size: int = 1024
    fps: int = 30
    buffer_seconds: float = 2.0
    source: str = "mic"  # "mic" or "system"


@dataclass
class StreamingAudioFrame:
    """A single frame of streaming audio data."""
    level: float
    bands: List[float]
    is_beat: bool
    flux: float
    time: float


def _rms(samples: List[float]) -> float:
    """Compute RMS of samples."""
    if not samples:
        return 0.0
    return math.sqrt(sum(s * s for s in samples) / len(samples))


def _goertzel(samples: List[float], sample_rate: int, freq: float) -> float:
    """Simple Goertzel filter."""
    k = int(0.5 + len(samples) * freq / sample_rate)
    w = 2.0 * math.pi * k / len(samples)
    coeff = 2.0 * math.cos(w)
    s0, s1, s2 = 0.0, 0.0, 0.0
    n = len(samples)
    if n == 0:
        return 0.0
    for i in range(n):
        s0 = samples[i] + coeff * s1 - s2
        s2 = s1
        s1 = s0
    return math.sqrt(s1 * s1 + s2 * s2 - coeff * s1 * s2) / n


def _detect_beats(levels: List[float], threshold: float = 0.25) -> List[bool]:
    """Simple beat detection."""
    if not levels:
        return []
    beats = []
    for i in range(len(levels)):
        if i == 0:
            beats.append(levels[i] > threshold)
        else:
            beats.append(levels[i] > levels[i - 1] * 1.2 and levels[i] > threshold)
    return beats


class AudioStreamAnalyzer:
    """Real-time audio analyzer that provides streaming audio features."""

    def __init__(self, config: StreamingAudioConfig) -> None:
        self.config = config
        self.running = False
        self.audio_queue: queue.Queue = queue.Queue(maxsize=100)
        self.frame_callback: Optional[Callable[[StreamingAudioFrame], None]] = None
        self.stream: Any = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the audio stream."""
        if not HAS_PYAUDIO and not HAS_SOUNDDEVICE:
            raise RuntimeError("No audio library available. Install pyaudio or sounddevice.")
        self.running = True
        self._thread = threading.Thread(target=self._audio_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the audio stream."""
        self.running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self.stream is not None:
            try:
                self.stream.stop()  # type: ignore[union-attr]
                self.stream.close()  # type: ignore[union-attr]
            except Exception:
                pass

    def _audio_loop(self) -> None:
        """Main audio processing loop."""
        if HAS_SOUNDDEVICE:
            self._sounddevice_loop()
        elif HAS_PYAUDIO:
            self._pyaudio_loop()
        else:
            logger.error("No audio library available")

    def _sounddevice_loop(self) -> None:
        """Audio loop using sounddevice."""
        sd_attr = sd  # type: ignore[possibly-unbound]
        try:
            with sd_attr.InputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype="int16",
                blocksize=self.config.chunk_size,
            ) as stream:
                self.stream = stream
                last_level = 0.0
                while self.running:
                    data, overflowed = stream.read(self.config.chunk_size)
                    if data is None:
                        continue
                    # Convert to mono list
                    samples = [float(x[0]) for x in data]
                    level = _rms(samples)
                    bands = [_goertzel(samples, self.config.sample_rate, f) for f in FREQ_CENTERS]
                    flux = max(0.0, level - last_level)
                    last_level = level

                    # Normalize
                    max_b = max(bands) if bands else 1.0
                    bands_norm = [b / max_b for b in bands] if max_b > 0 else bands
                    beats = _detect_beats([level])

                    frame = StreamingAudioFrame(
                        level=level,
                        bands=bands_norm,
                        is_beat=beats[0] if beats else False,
                        flux=flux,
                        time=0.0,
                    )
                    if self.frame_callback:
                        self.frame_callback(frame)
        except Exception as e:
            logger.error("Audio stream error: %s", e)

    def _pyaudio_loop(self) -> None:
        """Audio loop using pyaudio."""
        pa_pyaudio = pyaudio  # type: ignore[possibly-unbound]
        try:
            pa = pa_pyaudio.PyAudio()
            stream = pa.open(
                format=pa_pyaudio.paInt16,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                frames_per_buffer=self.config.chunk_size,
            )
            self.stream = stream
            last_level = 0.0
            while self.running:
                data = stream.read(self.config.chunk_size, exception_on_overflow=False)
                samples = [float(b / 32768.0) for b in data if isinstance(b, int)]
                level = _rms(samples)
                bands = [_goertzel(samples, self.config.sample_rate, f) for f in FREQ_CENTERS]
                flux = max(0.0, level - last_level)
                last_level = level

                max_b = max(bands) if bands else 1.0
                bands_norm = [b / max_b for b in bands] if max_b > 0 else bands
                beats = _detect_beats([level])

                frame = StreamingAudioFrame(
                    level=level,
                    bands=bands_norm,
                    is_beat=beats[0] if beats else False,
                    flux=flux,
                    time=0.0,
                )
                if self.frame_callback:
                    self.frame_callback(frame)
            stream.stop_stream()
            stream.close()
            pa.terminate()
        except Exception as e:
            logger.error("Audio stream error: %s", e)


def create_streaming_analyzer(config: Optional[StreamingAudioConfig] = None) -> AudioStreamAnalyzer:
    """Factory function to create a streaming audio analyzer."""
    if config is None:
        config = StreamingAudioConfig()
    return AudioStreamAnalyzer(config)


def get_audio_backend() -> str:
    """Get the available audio backend."""
    if HAS_SOUNDDEVICE:
        return "sounddevice"
    if HAS_PYAUDIO:
        return "pyaudio"
    return "none"


def is_streaming_available() -> bool:
    """Check if streaming audio is available."""
    return HAS_PYAUDIO or HAS_SOUNDDEVICE