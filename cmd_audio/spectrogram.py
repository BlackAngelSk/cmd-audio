"""Spectral frequency heatmap (Phase 2.2)."""

from __future__ import annotations

import math
from typing import List, Optional
from cmd_audio.utils import clamp

CURRENT_STYLE = {
    "bar_on": "#",
    "bar_off": ".",
    "spark": [".", "-", "=", "#", "*"]
}


def render_spectrogram(bands: List[List[float]], width: int, height: int) -> List[str]:
    """Render a 2D heatmap of frequency bands over time."""
    if not bands:
        return ["" for _ in range(height)]

    rows: List[str] = []
    # Scale to fit height
    for y in range(height):
        row = []
        # Each column is a time step (band row)
        time_steps = len(bands)
        for x in range(width):
            if time_steps > 0:
                t = int(x * time_steps / max(1, width))
                t = int(clamp(float(t), 0.0, float(time_steps - 1)))
            else:
                t = 0
            
            if height > 0:
                band_idx = int(y * len(bands[0]) / max(1, height)) if bands[0] else 0
                band_idx = int(clamp(float(band_idx), 0.0, float(len(bands[0]) - 1 if bands[0] else 0)))
            else:
                band_idx = 0
            
            if t < len(bands) and band_idx < len(bands[t]):
                value = bands[t][band_idx]
            else:
                value = 0.0
            
            # Convert to character
            if value < 0.3:
                char = "."
            elif value < 0.5:
                char = ":"
            elif value < 0.7:
                char = "#"
            elif value < 0.9:
                char = "*"
            else:
                char = "@"
            row.append(char)
        rows.append("".join(row))
    return rows


def render_spectrogram_with_colors(bands: List[List[float]], width: int, height: int) -> List[str]:
    """Render a 2D heatmap with ANSI color codes."""
    if not bands:
        return ["" for _ in range(height)]
    if not bands[0]:
        return ["" for _ in range(height)]
    
    rows: List[str] = []
    for y in range(height):
        row = []
        time_steps = len(bands)
        for x in range(width):
            t = int(x * time_steps / max(1, width))
            t = int(clamp(float(t), 0.0, float(time_steps - 1)))
            
            band_idx = int(y * len(bands[0]) / max(1, height))
            band_idx = int(clamp(float(band_idx), 0.0, float(len(bands[0]) - 1)))
            
            # Get the value
            if t < len(bands) and band_idx < len(bands[t]):
                value = bands[t][band_idx]
            else:
                value = 0.0
            
            # Color based on value
            if value < 0.2:
                color = "\033[32m"  # green
            elif value < 0.4:
                color = "\033[33m"  # yellow
            elif value < 0.6:
                color = "\033[93m"  # bright yellow
            elif value < 0.8:
                color = "\033[31m"  # red
            else:
                color = "\033[91m"  # bright red
            char = "█" if value > 0.5 else "▒" if value > 0.3 else "░"
            row.append(f"{color}{char}\033[0m")
        rows.append("".join(row))
    return rows


def freq_band_label(idx: int, total_bands: int, width: int) -> str:
    """Return a frequency band label for spectrogram."""
    labels = ["Bass", "Low", "Mid", "High", "Air"]
    if total_bands <= len(labels):
        return labels[idx] if idx < len(labels) else f"B{idx+1}"
    return f"B{idx+1}"


def render_spectrogram_with_labels(bands: List[List[float]], width: int, height: int) -> List[str]:
    """Render a 2D heatmap with frequency band labels."""
    rows = render_spectrogram(bands, width, height)
    # Add labels at the left
    height_actual = len(rows)
    if height_actual < 2:
        return rows
    band_count = len(bands[0]) if bands and bands[0] else 1
    step = max(1, height_actual // band_count)
    for i in range(band_count):
        row_idx = i * step
        if row_idx < height_actual:
            label = freq_band_label(i, band_count, width)
            rows[row_idx] = f"{label} {rows[row_idx]}"
    return rows