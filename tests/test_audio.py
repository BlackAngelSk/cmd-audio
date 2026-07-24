"""Tests for audio feature extraction, beat detection, and BPM estimation."""

from __future__ import annotations

import math
import struct
import wave
import tempfile
import os

import pytest

from cmd_audio.audio import (
    AudioFeatures,
    decode_pcm_to_mono_samples,
    detect_beats,
    detect_fluxes,
    estimate_bpm,
    goertzel_power,
    make_demo_audio_features,
    normalize_band_matrix,
    read_audio_features,
    rms_from_samples,
)


# ---------------------------------------------------------------------------
# PCM decoding tests
# ---------------------------------------------------------------------------

class TestDecodePcmToMonoSamples:
    def test_8bit_mono(self) -> None:
        data = bytes([128, 200, 50, 128])
        samples = decode_pcm_to_mono_samples(data, sample_width=1, channels=1)
        assert samples == [0, 72, -78, 0]

    def test_16bit_mono(self) -> None:
        data = struct.pack("<hhh", 1000, -1000, 0)
        samples = decode_pcm_to_mono_samples(data, sample_width=2, channels=1)
        assert samples == [1000, -1000, 0]

    def test_16bit_stereo(self) -> None:
        data = struct.pack("<hhhh", 1000, -1000, 2000, -2000)
        samples = decode_pcm_to_mono_samples(data, sample_width=2, channels=2)
        assert samples == [0, 0]  # averaged

    def test_32bit_mono(self) -> None:
        data = struct.pack("<iii", 500000, -500000, 0)
        samples = decode_pcm_to_mono_samples(data, sample_width=4, channels=1)
        assert samples == [500000, -500000, 0]

    def test_empty_data(self) -> None:
        samples = decode_pcm_to_mono_samples(b"", sample_width=1, channels=1)
        assert samples == []

    def test_invalid_sample_width(self) -> None:
        with pytest.raises(ValueError):
            decode_pcm_to_mono_samples(b"\x00" * 5, sample_width=5, channels=1)

    def test_invalid_frame_size(self) -> None:
        samples = decode_pcm_to_mono_samples(b"\x00\x01", sample_width=1, channels=3)
        assert samples == []


# ---------------------------------------------------------------------------
# RMS tests
# ---------------------------------------------------------------------------

class TestRmsFromSamples:
    def test_silence(self) -> None:
        assert rms_from_samples([0, 0, 0]) == 0.0

    def test_single_sample(self) -> None:
        assert abs(rms_from_samples([100]) - 100.0) < 1e-9

    def test_empty(self) -> None:
        assert rms_from_samples([]) == 0.0

    def test_known_value(self) -> None:
        val = rms_from_samples([1, -1])
        assert abs(val - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# Goertzel tests
# ---------------------------------------------------------------------------

class TestGoertzelPower:
    def test_silence(self) -> None:
        power = goertzel_power([0] * 100, 44100, 1000.0)
        assert abs(power) < 1e-9

    def test_sine_wave(self) -> None:
        freq = 440.0
        sr = 44100
        n = 1024
        samples = [int(32767 * math.sin(2 * math.pi * freq * i / sr)) for i in range(n)]
        power = goertzel_power(samples, sr, freq)
        assert power > 0


# ---------------------------------------------------------------------------
# Beat detection tests
# ---------------------------------------------------------------------------

class TestDetectBeats:
    def test_silence(self) -> None:
        beats = detect_beats([0.0] * 100)
        assert not any(beats)

    def test_wide(self) -> None:
        levels = [0.0] * 100
        for i in range(0, 100, 20):
            levels[i] = 1.0
        beats = detect_beats(levels)
        assert len(beats) == 100


# ---------------------------------------------------------------------------
# Flux detection tests
# ---------------------------------------------------------------------------

class TestDetectFluxes:
    def test_empty(self) -> None:
        assert detect_fluxes([], []) == []

    def test_constant(self) -> None:
        levels = [0.5, 0.5, 0.5, 0.5, 0.5]
        bands = [[0.5, 0.5]] * 5
        fluxes = detect_fluxes(levels, bands)
        assert len(fluxes) == 5
        for f in fluxes:
            assert f >= 0.0


# ---------------------------------------------------------------------------
# BPM estimation tests
# ---------------------------------------------------------------------------

class TestEstimateBpm:
    def test_empty(self) -> None:
        assert estimate_bpm([]) == 0.0

    def test_few_beats(self) -> None:
        assert estimate_bpm([0.0, 0.5, 1.0]) == 0.0

    def test_known_bpm(self) -> None:
        beat_times = [i * 0.5 for i in range(20)]
        bpm = estimate_bpm(beat_times)
        assert abs(bpm - 120.0) < 1.0


# ---------------------------------------------------------------------------
# Band matrix normalization tests
# ---------------------------------------------------------------------------

class TestNormalizeBandMatrix:
    def test_empty(self) -> None:
        assert normalize_band_matrix([]) == []

    def test_single_row(self) -> None:
        result = normalize_band_matrix([[1.0, 2.0]])
        assert len(result) == 1


# ---------------------------------------------------------------------------
# AudioFeatures dataclass tests
# ---------------------------------------------------------------------------

class TestAudioFeatures:
    def test_create(self) -> None:
        af = AudioFeatures(
            fps=30,
            duration=10.0,
            levels=[],
            bands=[],
            beats=[],
            fluxes=[],
            beat_times=[],
            bpm_estimate=120.0,
        )
        assert af.fps == 30
        assert af.bpm_estimate == 120.0


# ---------------------------------------------------------------------------
# Make demo audio tests
# ---------------------------------------------------------------------------

class TestMakeDemoAudioFeatures:
    def test_default(self) -> None:
        af = make_demo_audio_features(30)
        assert af.fps == 30
        assert len(af.levels) > 0
        assert len(af.beats) > 0
        assert af.bpm_estimate > 0

    def test_sufficient_frames(self) -> None:
        af = make_demo_audio_features(10, seconds=10)
        assert af.fps == 10
        assert len(af.levels) > 0


# ---------------------------------------------------------------------------
# WAV file reading tests
# ---------------------------------------------------------------------------

class TestReadAudioFeatures:
    def _write_wav(self, path: str, samples: list[int], sr: int = 44100) -> None:
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            data = b"".join(struct.pack("<h", max(-32768, min(32767, s))) for s in samples)
            wf.writeframes(data)

    def test_reads_wav(self, tmp_path: str) -> None:
        path = str(tmp_path) + "/test.wav"
        sr = 44100
        duration = 1.0
        n = int(sr * duration)
        samples = [int(32767 * math.sin(2 * math.pi * 440 * i / sr)) for i in range(n)]
        self._write_wav(path, samples, sr)
        af = read_audio_features(path, 30)
        assert af.fps == 30
        assert af.duration > 0
        assert len(af.levels) > 0