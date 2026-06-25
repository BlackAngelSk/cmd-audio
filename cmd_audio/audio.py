"""Audio feature extraction: RMS, Goertzel bands, beat detection, BPM."""

from __future__ import annotations

import math
import struct
import wave
from dataclasses import dataclass
from typing import List, Tuple

from cmd_audio.config import FREQ_CENTERS
from cmd_audio.utils import clamp, normalize, smooth


@dataclass
class AudioFeatures:
    fps: int
    duration: float
    levels: List[float]
    bands: List[List[float]]
    beats: List[bool]
    fluxes: List[float]
    beat_times: List[float]
    bpm_estimate: float


# ---------------------------------------------------------------------------
# PCM helpers
# ---------------------------------------------------------------------------

def decode_pcm_to_mono_samples(data: bytes, sample_width: int, channels: int) -> List[int]:
    """Decode raw PCM *data* into mono integer samples."""
    if sample_width not in (1, 2, 3, 4):
        raise ValueError(f"Unsupported sample width: {sample_width} bytes")

    frame_size = sample_width * channels
    if frame_size <= 0 or len(data) % frame_size != 0:
        return []

    frame_count = len(data) // frame_size
    out: List[int] = []

    if sample_width == 1:
        for i in range(frame_count):
            offset = i * frame_size
            total = 0
            for c in range(channels):
                total += data[offset + c] - 128
            out.append(int(total / channels))
        return out

    if sample_width == 2:
        for i in range(frame_count):
            offset = i * frame_size
            total = 0
            for c in range(channels):
                ch_off = offset + (c * sample_width)
                total += struct.unpack_from("<h", data, ch_off)[0]
            out.append(int(total / channels))
        return out

    if sample_width == 3:
        for i in range(frame_count):
            offset = i * frame_size
            total = 0
            for c in range(channels):
                ch_off = offset + (c * sample_width)
                b0 = data[ch_off]
                b1 = data[ch_off + 1]
                b2 = data[ch_off + 2]
                unsigned = b0 | (b1 << 8) | (b2 << 16)
                signed = unsigned - 0x1000000 if unsigned & 0x800000 else unsigned
                total += signed
            out.append(int(total / channels))
        return out

    for i in range(frame_count):
        offset = i * frame_size
        total = 0
        for c in range(channels):
            ch_off = offset + (c * sample_width)
            total += struct.unpack_from("<i", data, ch_off)[0]
        out.append(int(total / channels))
    return out


def rms_from_samples(samples: List[int]) -> float:
    if not samples:
        return 0.0
    energy = 0.0
    for s in samples:
        energy += float(s * s)
    return math.sqrt(energy / len(samples))


def goertzel_power(samples: List[int], sample_rate: int, freq: float) -> float:
    if not samples:
        return 0.0
    omega = 2.0 * math.pi * (freq / float(sample_rate))
    coeff = 2.0 * math.cos(omega)
    s_prev = 0.0
    s_prev2 = 0.0
    for x in samples:
        s = float(x) + coeff * s_prev - s_prev2
        s_prev2 = s_prev
        s_prev = s
    power = s_prev2 * s_prev2 + s_prev * s_prev - coeff * s_prev * s_prev2
    return max(0.0, power)


# ---------------------------------------------------------------------------
# Beat / flux detection
# ---------------------------------------------------------------------------

def detect_beats(levels: List[float]) -> List[bool]:
    beats: List[bool] = []
    deltas = [0.0]
    for i in range(1, len(levels)):
        deltas.append(max(0.0, levels[i] - levels[i - 1]))

    for i in range(len(levels)):
        a = max(0, i - 12)
        b = max(1, i)
        baseline = sum(deltas[a:b]) / max(1, b - a)
        strong = deltas[i] > (baseline * 1.65 + 0.03)
        beats.append(strong and levels[i] > 0.35)
    return beats


def detect_fluxes(levels: List[float], bands: List[List[float]]) -> List[float]:
    if not levels:
        return []

    fluxes: List[float] = [0.0]
    for i in range(1, len(levels)):
        level_flux = max(0.0, levels[i] - levels[i - 1])
        if i < len(bands) and (i - 1) < len(bands):
            band_flux = sum(max(0.0, bands[i][j] - bands[i - 1][j]) for j in range(len(bands[i])))
            band_flux /= max(1, len(bands[i]))
        else:
            band_flux = 0.0
        fluxes.append(level_flux + band_flux)

    return normalize(smooth(fluxes, radius=2))


def normalize_band_matrix(bands: List[List[float]]) -> List[List[float]]:
    if not bands:
        return []
    band_count = len(bands[0])
    cols: List[List[float]] = [[row[i] for row in bands] for i in range(band_count)]
    norm_cols = [normalize(col) for col in cols]

    out: List[List[float]] = []
    for r in range(len(bands)):
        out.append([norm_cols[c][r] for c in range(band_count)])
    return out


# ---------------------------------------------------------------------------
# BPM estimation
# ---------------------------------------------------------------------------

def estimate_bpm(beat_times: List[float]) -> float:
    if len(beat_times) < 4:
        return 0.0
    intervals: List[float] = []
    for i in range(1, len(beat_times)):
        dt = beat_times[i] - beat_times[i - 1]
        if 0.2 <= dt <= 2.0:
            intervals.append(dt)
    if not intervals:
        return 0.0
    avg = sum(intervals) / len(intervals)
    if avg <= 1e-6:
        return 0.0
    bpm = 60.0 / avg
    while bpm < 70.0:
        bpm *= 2.0
    while bpm > 180.0:
        bpm *= 0.5
    return bpm


# ---------------------------------------------------------------------------
# Main reader
# ---------------------------------------------------------------------------

def read_audio_features(wav_path: str, fps: int) -> AudioFeatures:
    """Read a WAV file and extract per-frame audio features."""
    with wave.open(wav_path, "rb") as wf:
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        sample_rate = wf.getframerate()
        total_frames = wf.getnframes()

        frames_per_bucket = max(1, sample_rate // fps)
        levels_raw: List[float] = []
        bands_raw: List[List[float]] = []

        while True:
            data = wf.readframes(frames_per_bucket)
            if not data:
                break

            samples = decode_pcm_to_mono_samples(data, sample_width, channels)
            rms = rms_from_samples(samples)
            levels_raw.append(rms)

            band_row: List[float] = []
            for f in FREQ_CENTERS:
                if f >= (sample_rate / 2.0):
                    band_row.append(0.0)
                else:
                    band_row.append(goertzel_power(samples, sample_rate, f))
            bands_raw.append(band_row)

    if not levels_raw:
        raise ValueError("No audio data found")

    levels_smooth = smooth(levels_raw, radius=2)
    levels = normalize(levels_smooth)
    bands = normalize_band_matrix(bands_raw)
    beats = detect_beats(levels)
    fluxes = detect_fluxes(levels, bands)
    beat_times = [i / float(fps) for i, is_beat in enumerate(beats) if is_beat]
    bpm_estimate = estimate_bpm(beat_times)
    duration = total_frames / float(sample_rate)
    return AudioFeatures(
        fps=fps,
        duration=duration,
        levels=levels,
        bands=bands,
        beats=beats,
        fluxes=fluxes,
        beat_times=beat_times,
        bpm_estimate=bpm_estimate,
    )


# ---------------------------------------------------------------------------
# Demo / synthetic audio
# ---------------------------------------------------------------------------

def make_demo_audio_features(fps: int, seconds: int = 180) -> AudioFeatures:
    """Generate synthetic audio features for demo mode."""
    frame_count = max(fps * max(10, seconds), fps)
    levels: List[float] = []
    bands: List[List[float]] = []
    beats: List[bool] = []
    fluxes: List[float] = []
    beat_times: List[float] = []

    bpm = 124.0
    beat_interval = 60.0 / bpm
    last_level = 0.0

    for i in range(frame_count):
        t = i / float(fps)
        is_beat = (t % beat_interval) < (1.0 / float(fps))

        groove = 0.45 + 0.28 * math.sin(2.0 * math.pi * 0.55 * t)
        wobble = 0.17 * math.sin(2.0 * math.pi * 0.11 * t + 1.2)
        sparkle = 0.08 * math.sin(2.0 * math.pi * 2.4 * t)
        beat_kick = 0.32 if is_beat else 0.0
        level = clamp(groove + wobble + sparkle + beat_kick, 0.0, 1.0)
        levels.append(level)

        band_row = [
            clamp(level * 0.90 + 0.10 * math.sin(2.0 * math.pi * 0.30 * t), 0.0, 1.0),
            clamp(level * 0.85 + 0.12 * math.sin(2.0 * math.pi * 0.38 * t + 0.8), 0.0, 1.0),
            clamp(level * 0.78 + 0.13 * math.sin(2.0 * math.pi * 0.72 * t + 1.1), 0.0, 1.0),
            clamp(level * 0.72 + 0.16 * math.sin(2.0 * math.pi * 1.10 * t + 0.2), 0.0, 1.0),
            clamp(level * 0.68 + 0.18 * math.sin(2.0 * math.pi * 1.45 * t + 1.7), 0.0, 1.0),
            clamp(level * 0.62 + 0.20 * math.sin(2.0 * math.pi * 2.10 * t + 0.4), 0.0, 1.0),
            clamp(level * 0.56 + 0.22 * math.sin(2.0 * math.pi * 2.90 * t + 2.0), 0.0, 1.0),
            clamp(level * 0.50 + 0.25 * math.sin(2.0 * math.pi * 3.40 * t + 2.4), 0.0, 1.0),
        ]
        bands.append(band_row)
        beats.append(is_beat)
        fluxes.append(max(0.0, level - last_level))
        if is_beat:
            beat_times.append(t)
        last_level = level

    return AudioFeatures(
        fps=fps,
        duration=frame_count / float(fps),
        levels=levels,
        bands=bands,
        beats=beats,
        fluxes=smooth(fluxes, radius=2),
        beat_times=beat_times,
        bpm_estimate=bpm,
    )