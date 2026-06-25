"""Frame recording and replay utilities."""

from __future__ import annotations

import gzip
import json
import re
from typing import List, TextIO

from cmd_audio.utils import strip_ansi


def open_record_writer(path: str, mode: str) -> TextIO:
    if mode == "jsonl":
        return open(path, "w", encoding="utf-8")
    if mode in ("txt", "txt-clean"):
        return open(path, "w", encoding="utf-8")
    if mode in ("jsonl.gz", "txt.gz", "txt-clean.gz"):
        return gzip.open(path, "wt", encoding="utf-8")
    raise ValueError(f"Unsupported record mode: {mode}")


def write_record_frame(rec: TextIO, mode: str, t: float, speed: float, frame: str) -> None:
    if mode.startswith("jsonl"):
        rec.write(json.dumps({"t": t, "speed": speed, "frame": frame}) + "\n")
        return
    if mode.startswith("txt-clean"):
        rec.write(f"--- frame t={t:.3f} speed={speed:.3f} ---\n")
        rec.write(strip_ansi(frame))
        rec.write("\n")
        return
    rec.write(f"--- frame t={t:.3f} speed={speed:.3f} ---\n")
    rec.write(frame)
    rec.write("\n")


def load_replay_frames(path: str) -> List[str]:
    opener = gzip.open if path.lower().endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        text = f.read()

    frames: List[str] = []
    if '"frame"' in text:
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            frame = row.get("frame")
            if isinstance(frame, str):
                frames.append(frame)
    else:
        parts = text.split("--- frame ")
        for part in parts:
            if "---\n" not in part:
                continue
            frames.append(part.split("---\n", 1)[1].rstrip("\n"))

    if not frames:
        raise ValueError("Replay file has no readable frames")
    return frames