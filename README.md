# CMD-AUDIO

Music-reactive terminal "hacker" visualization with a browser-based live control panel.

Run it with the bundled launcher (uses the project virtualenv):

```bash
./start.sh /path/to/song.mp3
```

## Features

- Audio-synced animated terminal scenes
- Multiple themes and presets
- Scene packs and adaptive scene sync
- ASCII skull in the hacknet array that lips-syncs to timed lyrics
- Browser live-controls panel (see `live_controls.html`)
- Frame recording and replay support
- Optional plugin hook support
- Optional diagnostics output
- The header shows the **song name** (ID3 tag or the YouTube video title), never
  the URL or a temporary file path

## Requirements

- Python 3.9+
- `ffmpeg` for non-WAV audio input conversion and some capture flows
- Optional: `yt-dlp` for YouTube audio downloads
- Optional: `ffplay` or `aplay` for audio playback
- Optional: `tkinter` for setup/control popup UI

No third-party Python packages are required by default, but YouTube support requires `yt-dlp`.

## Installation

### YouTube Support (Optional - Not Required)

YouTube downloading is **completely optional**. The script works perfectly fine without it.

If you want to try YouTube support:
- **Debian/Ubuntu:** `sudo apt-get install yt-dlp`
- **Arch/CachyOS:** May have compatibility issues with Python 3.14+
- **macOS:** `brew install yt-dlp`

**If installation fails or you skip it:** Use these alternatives:
- Local audio files: `python3 music_sync_hacker_effect.py /path/to/song.mp3`
- Microphone input: `python3 music_sync_hacker_effect.py --source mic --capture-seconds 60`
- System audio: `python3 music_sync_hacker_effect.py --source system --capture-seconds 60`

The `--youtube` option will gracefully inform you if yt-dlp is not installed.

## Quick Start

Run with an audio file:

```bash
./start.sh /path/to/song.mp3
```

Run with a YouTube video (downloads audio; the header shows the video title):

```bash
./start.sh --youtube "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Run with a preset and diagnostics:

```bash
./start.sh /path/to/song.mp3 --preset chaos --diagnostics
```

Run using microphone/system capture:

```bash
./start.sh --source mic --capture-seconds 30
./start.sh --source system --capture-seconds 30
```

## Browser controls

The controls panel is served by default when you use the launcher:

```bash
./start.sh /path/to/song.mp3            # renders + serves controls on :8080
./start.sh /path/to/song.mp3 --no-web   # terminal only
./start.sh /path/to/song.mp3 --web-port 9000
```

The app prints the URL it is serving and the panel is at `/` (so
`http://localhost:8080/`). The panel drives the running render: sliders, theme,
banner, UI style and the feature toggles apply on the next frame, and the page
polls `/api/live-state` every 2s so keyboard changes made in the terminal show
up in the browser too. The accent colour of the page follows the active theme,
and the panel previews the render output (levels, banner) as you change it.

The panel only exposes controls the backend can apply live. Anything that is
read once at startup (capture source, sample rate, web port, plugins, scene
packs, presets) stays on the command line — see `./start.sh --help`.

`Stop console` posts to `/api/stop`, which asks the render loop to quit — the
same thing `q` does in the terminal.

`--setup-ui` serves the setup form at `/` and the panel at `/live-controls`.
`--setup-ui --web` together reuse the same port instead of failing to bind.

If the panel cannot reach the backend it shows a red banner instead of silently
doing nothing.

## Common Options

```text
--config PATH                 Load JSON config
--save-config PATH            Save current config and exit
--youtube URL                 YouTube URL to download and play (requires yt-dlp)
--playlist PATH               Text file, one audio path per line
--source {file,mic,system}    Input source
--fps INT                     Frames per second
--sensitivity FLOAT           Visual intensity multiplier
--speed-min FLOAT             Minimum visual speed
--speed-max FLOAT             Maximum visual speed
--theme {matrix,red-alert,ice,amber}
--preset NAME                 Apply visual preset
--lyrics / --no-lyrics        Look up timed lyrics and draw the lyric skull (default on)
--lyrics-file PATH            Use this .lrc instead of auto-detection
--scene-sync {adaptive,bpm,hybrid}
--quality-mode {off,auto}
--ui-style {full,minimal}
--record-file PATH            Save rendered frames
--record-mode FORMAT          jsonl/txt variants (including .gz)
--replay-file PATH            Replay previously recorded frames
--plugin PATH                 Python plugin file with hooks
--video-hook CMD              Run shell command after recording
--diagnostics                 Print startup diagnostics
--setup-ui                    Open setup popup before running
--ui / --no-ui                Enable/disable control popup window
```

Get complete CLI help:

```bash
./start.sh --help
```

## Lyrics and the skull

When CMD-AUDIO knows *timed* lyrics it draws an ASCII skull in the middle of the
hacknet array: the jaw drops on each new line and follows the level while the
line is being sung, with the current line bright underneath and the next one
dim. A track with no timed lyrics is left exactly as it was — no skull, no
placeholder.

Timed lyrics come from, in order:

1. a `.lrc` file next to the audio file (`song.mp3` -> `song.lrc`),
2. a lyrics tag embedded in the container (`ffprobe` reads it),
3. [lrclib.net](https://lrclib.net) — one lookup per track, cached under
   `~/.cache/cmd-audio/lyrics/`.

Plain (untimed) lyrics are detected but never drawn, because there is no way to
know which line is being sung.

```bash
./start.sh song.mp3                  # auto: sidecar, tag, then lrclib
./start.sh song.mp3 --no-lyrics      # never look up or draw lyrics
./start.sh song.mp3 --lyrics-file x.lrc
```

The skull only appears in the three-column layout (terminal at least 150
columns wide) where the array panel has room for it; narrower layouts keep the
array.

## Live Controls

While running in terminal:

- `q`: quit
- `p`: pause
- `+` / `-`: increase/decrease sensitivity
- `]` / `[`: increase/decrease max speed
- `t`: cycle theme
- `b`: toggle banner
- `e`: edit banner text
- `c`: cycle banner alignment
- `v`: cycle banner animation
- `x`: cycle banner size
- `m`: switch terminal profile
- `r`: randomize scene
- `z`: reset music/session
- `0`: reset sensitivity/speed defaults
- `n` / `u`: next/previous track
- `1` / `2` / `3`: toggle mission timeline / defender AI / audio FX
- `a`: toggle alert tones
- `y`: scene sync mode
- `k`: quality mode
- `j`: UI style
- `g`: Unicode bars
- `h`: lock scene
- `o`: operation mode
- `l`: target lock

## Notes

- If your input is not WAV, the script uses `ffmpeg` to convert it.
- The song name in the header comes from the file's tags (`ffprobe`) and falls
  back to a cleaned-up filename; YouTube links are resolved to the video title.
- If `tkinter` is unavailable, UI flags are ignored with a warning and terminal mode continues.
- For troubleshooting startup environment and tools, run with `--diagnostics`.
