# CMD-AUDIO Feature Roadmap

> A multi-phase development plan for expanding the cmd-audio terminal music visualization.

---

## Current Project Summary

**What it is:** A Python-based music-reactive terminal "hacker" visualization with ~30+ visual modules, 10 themes, mission system, defender AI, plugin system, Tkinter control UI, frame recording/replay.

**Tech stack:** Pure Python 3.9+, ANSI escape codes, optional ffmpeg/yt-dlp/tkinter.

---

## 🔹 Phase 1 — Code Quality, Stability & Polish *(Foundation)*

These are low-risk improvements that make the codebase more maintainable and robust.

| # | Feature / Task | Description |
|---|----------------|-------------|
| 1.1 | **Unit test suite** | Add `pytest` tests for audio features, visual rendering, config parsing, mission timeline, and scene pack loading. Currently there are zero tests. |
| 1.2 | **Type hints & mypy strictness** | The codebase uses `from __future__ import annotations` but many functions lack full type annotations. Add strict typing throughout. |
| 1.3 | **Refactor `main.py` monolith** | `main.py` is 1374 lines with the entire render loop, key handling, audio switching, and UI management in one function. Split into `render_loop.py`, `input_handler.py`, `audio_manager.py`. |
| 1.4 | **Logging system** | Replace `print(..., file=sys.stderr)` and ad-hoc log lists with a proper `logging` module integration with configurable verbosity levels. ✅ **Done** (see `logging_config.py`) |
| 1.5 | **Error handling improvements** | Many bare `except Exception: pass` blocks. Add structured error handling with meaningful messages and optional crash reports. |
| 1.6 | **Config validation** | Add schema validation for JSON configs using a `dataclass` or `pydantic` model to catch malformed configs early. |
| 1.7 | **CLI help documentation** | Improve `--help` output with examples, group arguments into sections, and generate man-page output. |
| 1.8 | **Package distribution** | Add `pyproject.toml` with `pip install -e .` support, entry points (`cmd-audio` command), and PyPI readiness. |
| 1.9 | **Performance profiling** | Add `--profile` CLI flag to measure frame render time, audio analysis time, and identify bottlenecks. |
| 1.10 | **Frame drop monitoring** | Improve the existing `dropped_frames` counter with a sliding window average and auto-adjustment that is more aggressive. |

---

## 🔸 Phase 2 — Audio & Rendering Enhancements *(Core Experience)*

These improve the core audio-reactive rendering experience.

| # | Feature / Task | Description |
|---|----------------|-------------|
| 2.1 | **Real-time audio analysis (streaming)** | Currently audio is pre-analyzed from a WAV file. Add live FFT streaming for mic/system input to enable more responsive visuals. |
| 2.2 | **Spectral frequency heatmap** | Add a visual module that renders a 2D heatmap showing frequency bands over time (like a spectrogram). |
| 2.3 | **Volume/gain normalization** | Auto-normalize audio levels across different tracks so visuals are consistent. Add `--normalize` flag. |
| 2.4 | **Custom color themes** | Allow users to define custom themes via JSON (RGB values or ANSI codes) instead of being limited to 10 preset themes. |
| 2.5 | **Transition effects between themes** | Instead of instant theme switches, add a crossfade/blend transition over 2-3 frames. |
| 2.6 | **More visual modules** | Add new modules like: ASCII waveforms, 3D wireframe cube rotation, matrix rain variant, fractal patterns, or bar chart equalizer. |
| 2.7 | **Adaptive frame rate scaling** | Auto-adjust FPS based on terminal size and system load — smaller terminals get higher FPS, larger ones get lower. |
| 2.8 | **Audio waveform/spectrogram overlay** | Display a small waveform strip at the bottom or top of the terminal alongside the main visualization. |
| 2.9 | **Beat detection improvement** | Upgrade from the current beat detection to include onset detection, tempo estimation (BPM), and beat strength analysis. |
| 2.10 | **Layered rendering system** | Allow multiple visual modules to be displayed simultaneously in different terminal regions (e.g., left half = waveform, right half = hacker scenes). |

---

## 🔶 Phase 3 — User Experience & Interaction *(Usability)*

These improve how users interact with and control the tool.

| # | Feature / Task | Description |
|---|----------------|-------------|
| 3.1 | **TUI menu system** | Replace the basic Tkinter popup with a full `curses`-based TUI for config selection, preset browsing, and playlist management — no X11 required. |
| 3.2 | **Playlist management** | Add shuffle, repeat (single/all), random order, and auto-advance with crossfade. Store playlists as JSON. |
| 3.3 | **Keyboard shortcuts help overlay** | Press `?` to show a hittable key reference overlay without leaving the visualization. |
| 3.4 | **State persistence** | Save all runtime settings (theme, sensitivity, banner text, etc.) to a session file and auto-restore on next launch. |
| 3.5 | **Favorites / presets library** | Let users create, name, and save custom presets beyond the 3 built-in ones, stored in `~/.config/cmd-audio/presets/`. |
| 3.6 | **Scene pack browser** | Interactive command to browse and preview scene packs before applying them. |
| 3.7 | **Notification system** | Optional toast-style notifications for events (track change, mission phase, defender action) at the bottom of screen. |
| 3.8 | **Remote control via socket/IPC** | Allow external programs to send commands (e.g., change theme, trigger effect) via a Unix socket or TCP port. Enables integration with music players, etc. |
| 3.9 | **Mouse support** | If the terminal supports it, add mouse click handling for UI elements (slider-like sensitivity control). |
| 3.10 | **Multiple terminal support** | Allow the visualization to span across multiple terminal windows or tmux panes. |

---

## 🔴 Phase 4 — Networking & Integration *(Advanced)*

These add capabilities that extend cmd-audio beyond the local terminal.

| # | Feature / Task | Description |
|---|----------------|-------------|
| 4.1 | **Web server mode** | Run a small `http.server` that serves a browser-based visualization (using WebSockets for real-time audio data). |
| 4.2 | **MQTT / OSC integration** | Publish audio features (BPM, level, beat) via MQTT or OSC for use in live performance setups. |
| 4.3 | **Music player integration** | Auto-detect running music players (VLC, mpv, Spotify via D-Bus) and sync visuals automatically. |
| 4.4 | **Screen capture integration** | Integrate with `ffmpeg` or `wf-recorder` to record the terminal output as a video file (not just frame snapshots). |
| 4.5 | **Server/client mode** | Allow multiple terminals to connect to a "server" that does audio analysis, with clients rendering different visual modules. |
| 4.6 | **API for external plugins** | Create a formal plugin API with event system, so external Python packages can define new visual modules, themes, or mission phases. |
| 4.7 | **REST API** | Expose a JSON API for controlling the visualization (change theme, get current audio features, etc.). |
| 4.8 | **Chat overlay** | Integrate a chat-like overlay (IRC, Discord) where messages can be displayed visually in the terminal alongside the visualization. |
| 4.9 | **Network trigger mode** | Visuals can be triggered by network events (e.g., a webhook or network packet capture). |
| 4.10 | **Plugin marketplace** | Support loading plugins from a remote registry or local directory with versioning. |

---

## 🟣 Phase 5 — Platform & Ecosystem *(Long-term / Experimental)*

These are ambitious features that would make cmd-audio a full platform.

| # | Feature / Task | Description |
|---|----------------|-------------|
| 5.1 | **Rust/C extension for audio processing** | Rewrite the audio analysis (FFT, Goertzel) in Rust as a Python extension for 10x performance. |
| 5.2 | **GPU-accelerated rendering** | For terminals that support it (e.g., in a browser via WebGL), use GPU acceleration for complex visual effects. |
| 5.3 | **Multiple audio source mixing** | Allow mixing multiple audio sources (e.g., microphone + file) and blend their visual responses. |
| 5.4 | **Scene graph / storyboard system** | Define scenes with transitions, duration, and effects in a JSON storyboard format, similar to video editing. |
| 5.5 | **Live performance mode** | A dedicated mode for live DJ/performer use with triggers, beat sync, MIDI integration, and real-time control via external hardware. |
| 5.6 | **Accessibility modes** | High contrast themes, screen reader descriptions of visuals for visually impaired users. |
| 5.7 | **WebAssembly build** | Package the core visualization logic in WASM to run in any terminal emulator that supports it. |
| 5.8 | **Desktop app** | Wrap in a native desktop app (Electron/Tauri) with a GUI for non-terminal users. |
| 5.9 | **Collaborative mode** | Multiple users can connect to a shared visualization session and control different aspects. |
| 5.10 | **AI-driven scene generation** | Use a simple ML model to analyze audio features and generate custom visual patterns that adapt to music genres. |

---

## 📊 Recommended Phase Execution Order

```
Phase 1 (1-2 weeks) ──► Phase 2 (2-3 weeks) ──► Phase 3 (3-4 weeks) ──► Phase 4 (4-6 weeks) ──► Phase 5 (Ongoing)
```

- **Phase 1** is the foundation — it addresses technical debt and makes everything you add later cleaner and more maintainable.
- **Phase 2** directly improves the core experience that users interact with.
- **Phase 3** makes the tool more usable and accessible.
- **Phase 4** extends cmd-audio beyond the local terminal.
- **Phase 5** is the long-term vision for making cmd-audio a full platform.