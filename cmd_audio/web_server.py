"""Web server mode for browser-based visualization and HTML settings UI."""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Dict, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from cmd_audio.logging_config import get_logger
from cmd_audio.config import THEMES as _THEMES

logger = get_logger(__name__)

# <repo>/live_controls.html -- the page shipped with the project.
LIVE_CONTROLS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "live_controls.html"
)


def load_live_controls_html() -> str:
    """Read the bundled live-controls page (empty string when missing)."""
    try:
        with open(LIVE_CONTROLS_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as exc:
        logger.warning("live_controls.html not found at %s: %s", LIVE_CONTROLS_PATH, exc)
        return ""


def _current_live_state() -> Any:
    """The live state this server drives.

    Prefers the state handed to the server, but falls back to the process-wide
    one so the controls work no matter which component started the server.
    """
    try:
        from cmd_audio.control import get_browser_live_state

        return get_browser_live_state()
    except Exception:
        return None


class AudioServer:
    """HTTP server that serves a browser-based settings UI and visualization."""

    def __init__(self, host: str = "localhost", port: int = 8080, live_on_root: bool = False):
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.audio_data: Dict[str, Any] = {}
        self.current_config: Dict[str, Any] = {}
        self.config_received: Optional[Dict[str, Any]] = None
        self.config_event = threading.Event()
        self.live_controls_html: str = ""
        self.live_state: Any = None
        # When True, "/" serves the live controls instead of the setup form
        # (used for --web sessions, where setup already happened).
        self.live_on_root: bool = live_on_root
        self.bind_error: Optional[str] = None

    def set_live_state(self, live_state: Any) -> None:
        """Set the live control state for runtime music changes."""
        self.live_state = live_state

    def _state(self) -> Any:
        """Live state for request handling (explicit state first, then global)."""
        return self.live_state if self.live_state is not None else _current_live_state()

    def start(self) -> bool:
        """Start serving. Returns False when the port could not be bound."""
        if not self.live_controls_html:
            self.live_controls_html = load_live_controls_html()
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        # Give the socket a moment so a bind failure is reported, not swallowed.
        for _ in range(150):
            if self.server is not None or self.bind_error is not None:
                break
            time.sleep(0.02)
        if self.server is not None:
            self.port = int(self.server.server_address[1])
        return self.server is not None

    def stop(self) -> None:
        self.running = False
        if self.server:
            self.server.shutdown()

    def _run(self) -> None:
        try:
            handler = self._make_handler()
            self.server = HTTPServer((self.host, self.port), handler)
            self.server.serve_forever()
        except Exception as e:
            self.bind_error = str(e)
            self.running = False
            logger.error("Web server error on %s:%s: %s", self.host, self.port, e)

    def set_current_config(self, config: Dict[str, Any]) -> None:
        self.current_config = config

    def wait_for_config(self, timeout: float = 300.0) -> Optional[Dict[str, Any]]:
        self.config_event.wait(timeout=timeout)
        return self.config_received

    def update_audio_data(self, data: Dict[str, Any]) -> None:
        self.audio_data = data

    def set_live_controls_html(self, html: str) -> None:
        self.live_controls_html = html

    def _make_handler(self) -> type:
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                pass

            def do_GET(self) -> None:
                path = self.path.split("?", 1)[0]
                if path == "/" and server.live_on_root:
                    self._send_live_controls()
                elif path == "/" or path == "/settings":
                    self._send_html(SETTINGS_HTML)
                elif path == "/live-controls" or path == "/live":
                    self._send_live_controls()
                elif path == "/api/config":
                    ls = server._state()
                    if ls is not None and server.live_on_root:
                        # A live session: report the running configuration.
                        self._send_json(ls.to_dict())
                    else:
                        self._send_json(server.current_config)
                elif path == "/api/audio":
                    self._send_json(server.audio_data)
                elif path == "/api/live-state":
                    ls = server._state()
                    if ls is not None:
                        self._send_json(ls.snapshot().__dict__)
                    else:
                        self._send_json({"error": "Live state not available"})
                else:
                    self.send_error(404)

            def _send_live_controls(self) -> None:
                html = server.live_controls_html or load_live_controls_html()
                if not html:
                    self._send_error(404, "Live controls HTML not loaded")
                else:
                    server.live_controls_html = html
                    self._send_html(html)

            def do_POST(self) -> None:
                if self.path == "/api/start":
                    length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(length)
                    try:
                        config = json.loads(body.decode())
                        server.config_received = config
                        server.config_event.set()
                        self._send_json({"status": "ok"})
                    except Exception as e:
                        self._send_json({"status": "error", "message": str(e)})
                elif self.path == "/api/music":
                    length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(length)
                    try:
                        data = json.loads(body.decode())
                        music_url = data.get("url", "").strip()
                        if not music_url:
                            self._send_json({"status": "error", "message": "No URL provided"})
                            return
                        ls = server._state()
                        if ls is not None:
                            ls.request_music_change(music_url)
                            self._send_json({"status": "ok", "message": "Music change requested"})
                        else:
                            self._send_json({"status": "error", "message": "Live state not available"})
                    except Exception as e:
                        self._send_json({"status": "error", "message": str(e)})
                elif self.path == "/api/live":
                    length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(length)
                    try:
                        data = json.loads(body.decode())
                        ls = server._state()
                        if ls is None:
                            self._send_json({"status": "error", "message": "Live state not available"})
                            return
                        # Apply each setting if present. Values arrive as
                        # whatever the DOM control produced, so coerce by kind.
                        applied: List[str] = []
                        rejected: List[str] = []

                        numeric = {
                            "sensitivity": ls.set_sensitivity,
                        }
                        strings = {
                            "theme": ls.set_theme,
                            "theme_mode": ls.set_theme_mode,
                            "banner_text": ls.set_banner_text,
                            "banner_align": ls.set_banner_align,
                            "banner_anim": ls.set_banner_anim,
                            "banner_size": ls.set_banner_size,
                            "ui_style": ls.set_ui_style,
                            "quality_mode": ls.set_quality_mode,
                            "scene_sync": ls.set_scene_sync,
                            "terminal_mode": ls.set_terminal_mode,
                            "operation_mode": ls.set_operation_mode,
                            "target_lock": ls.set_target_lock,
                        }
                        booleans = {
                            "show_banner": ls.set_show_banner,
                            "unicode_bars": ls.set_unicode_bars,
                            "lock_scene": ls.set_lock_scene,
                            "alert_tones": ls.set_alert_tones,
                            "mission_timeline": ls.set_mission_timeline,
                            "defender_ai": ls.set_defender_ai,
                            "audio_fx": ls.set_audio_fx,
                            "paused": ls.set_paused,
                        }

                        for key, setter in numeric.items():
                            if key in data:
                                setter(float(data[key]))
                                applied.append(key)
                        for key, setter in strings.items():
                            if key in data:
                                setter(str(data[key]))
                                applied.append(key)
                        for key, setter in booleans.items():
                            if key in data:
                                setter(bool(data[key]))
                                applied.append(key)

                        # Bounds are pairs: only the changed half is sent, so
                        # merge with the current values instead of resetting the
                        # other one to its default.
                        snap = ls.snapshot()
                        if "speed_min" in data or "speed_max" in data:
                            ls.set_speed_bounds(
                                float(data.get("speed_min", snap.speed_min)),
                                float(data.get("speed_max", snap.speed_max)),
                            )
                            applied.extend(k for k in ("speed_min", "speed_max") if k in data)
                        if "terminal_switch_min" in data or "terminal_switch_max" in data:
                            ls.set_terminal_switch_bounds(
                                float(data.get("terminal_switch_min", snap.terminal_switch_min)),
                                float(data.get("terminal_switch_max", snap.terminal_switch_max)),
                            )
                            applied.extend(
                                k for k in ("terminal_switch_min", "terminal_switch_max") if k in data
                            )

                        rejected = [k for k in data if k not in applied]
                        self._send_json({"status": "ok", "applied": applied, "ignored": rejected})
                    except Exception as e:
                        self._send_json({"status": "error", "message": str(e)})
                elif self.path == "/api/cancel":
                    server.config_received = None
                    server.config_event.set()
                    self._send_json({"status": "cancelled"})
                else:
                    self.send_error(404)

            def _send_json(self, data: Any) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())

            def _send_html(self, html: str) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html.encode())

            def _send_error(self, code: int, message: str = "") -> None:
                self.send_response(code)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(message.encode())

        return Handler


def start_web_server(
    host: str = "localhost",
    port: int = 8080,
    live_on_root: bool = True,
    max_port_tries: int = 10,
) -> AudioServer:
    """Start a web server, walking up to the next free port if one is taken.

    A port clash used to be logged and swallowed, leaving the browser controls
    pointing at a dead socket.
    """
    server: Optional[AudioServer] = None
    candidates = [port] if port == 0 else list(range(port, port + max_port_tries))
    for candidate in candidates:
        server = AudioServer(host, candidate, live_on_root=live_on_root)
        if server.start():
            if candidate != port:
                logger.warning("Port %s busy -- serving live controls on %s instead", port, candidate)
            return server
    if server is not None:
        logger.error("Could not bind any port in %s..%s: %s", port, port + max_port_tries - 1, server.bind_error)
    return server if server is not None else AudioServer(host, port, live_on_root=live_on_root)


def is_web_server_available() -> bool:
    return True


# ---------------------------------------------------------------------------
# HTML Settings Page
# ---------------------------------------------------------------------------

_theme_options_html = "\n".join(
    f"    <option value=\"{name}\">{name}</option>"
    for name in _THEMES
)

SETTINGS_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CMD-AUDIO  //  Setup</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0d1117;--bg2:#161b22;--bg3:#1c2128;--fg:#c9d1d9;--fg2:#8b949e;--accent:#00ff9f;--accent2:#00cc7f;--border:#30363d;--btn:#238636;--btn2:#2ea043;--cancel:#da3633;--cancel2:#f85149}
body{background:var(--bg);color:var(--fg);font-family:'Cascadia Code','Fira Code','JetBrains Mono',monospace;font-size:13px;line-height:1.5;padding:20px 30px;max-width:900px;margin:0 auto}
h1{color:var(--accent);font-size:28px;margin-bottom:2px}
.sub{color:var(--fg2);font-size:12px;margin-bottom:12px}
.accent-line{height:2px;background:var(--accent);margin-bottom:16px;border-radius:1px}
.tabs{display:flex;gap:2px;border-bottom:2px solid var(--border);margin-bottom:0}
.tab{padding:8px 16px;background:var(--bg2);color:var(--fg2);cursor:pointer;border:none;font-family:inherit;font-size:12px;font-weight:700;border-radius:6px 6px 0 0;transition:all .15s}
.tab:hover{background:var(--bg3);color:var(--fg)}
.tab.active{background:var(--bg3);color:var(--accent);border-bottom:2px solid var(--accent)}
.panel{display:none;background:var(--bg3);border:1px solid var(--border);border-radius:0 0 8px 8px;padding:20px;margin-bottom:16px}
.panel.active{display:block}
.field{display:grid;grid-template-columns:160px 1fr;gap:8px;align-items:center;margin-bottom:8px}
.field label{color:var(--fg);font-size:12px;font-weight:600}
.field input,.field select{background:var(--bg);color:var(--fg);border:1px solid var(--border);border-radius:4px;padding:6px 10px;font-family:inherit;font-size:13px;width:100%}
.field input:focus,.field select:focus{border-color:var(--accent);outline:none;box-shadow:0 0 0 1px var(--accent2)}
.field select{cursor:pointer}
.checkbox-row{display:flex;flex-wrap:wrap;gap:16px;margin:8px 0}
.checkbox-row label{display:flex;align-items:center;gap:6px;color:var(--fg);font-size:12px;cursor:pointer}
.checkbox-row input[type=checkbox]{accent-color:var(--accent);width:16px;height:16px}
.btn-row{display:flex;gap:12px;justify-content:flex-end;margin-top:16px;padding-top:12px;border-top:1px solid var(--border)}
.btn{padding:10px 28px;border:none;border-radius:6px;font-family:inherit;font-size:14px;font-weight:700;cursor:pointer;transition:all .15s}
.btn-start{background:var(--btn);color:#fff}
.btn-start:hover{background:var(--btn2)}
.btn-cancel{background:var(--cancel);color:#fff}
.btn-cancel:hover{background:var(--cancel2)}
.error{color:#f85149;font-size:12px;margin-top:4px;display:none}
.field input.error,.field select.error{border-color:#f85149}
</style>
</head>
<body>
<h1>CMD-AUDIO</h1>
<div class="sub">Configure your run parameters below</div>
<div class="accent-line"></div>

<div class="tabs" id="tabs">
  <button class="tab active" data-panel="source">Source & Audio</button>
  <button class="tab" data-panel="playback">Playback</button>
  <button class="tab" data-panel="visual">Visual & Theme</button>
  <button class="tab" data-panel="banner">Banner</button>
  <button class="tab" data-panel="features">Features</button>
  <button class="tab" data-panel="advanced">Advanced</button>
</div>

<form id="settings-form">
<!-- Source & Audio -->
<div class="panel active" id="source">
  <div class="field"><label>Source</label><select id="source"><option value="file">file</option><option value="mic">mic</option><option value="system">system</option></select></div>
  <div class="field"><label>YouTube URL</label><input type="text" id="youtube" placeholder="https://youtube.com/watch?v=..."></div>
  <div class="field"><label>Audio File</label><input type="text" id="audio" placeholder="/path/to/audio.mp3"></div>
  <div class="field"><label>Playlist File</label><input type="text" id="playlist" placeholder="/path/to/playlist.txt"></div>
  <div class="field"><label>Capture Seconds</label><input type="number" id="capture_seconds" value="30" min="1" max="3600"></div>
  <div class="field"><label>FPS</label><input type="number" id="fps" value="30" min="1" max="240"></div>
  <div class="checkbox-row"><label><input type="checkbox" id="play" checked> Play Audio</label></div>
</div>

<!-- Playback -->
<div class="panel" id="playback">
  <div class="field"><label>Sensitivity</label><input type="number" id="sensitivity" value="1.0" min="0.1" max="4.0" step="0.05"></div>
  <div class="field"><label>Speed Min</label><input type="number" id="speed_min" value="0.25" min="0.05" max="6.0" step="0.05"></div>
  <div class="field"><label>Speed Max</label><input type="number" id="speed_max" value="3.0" min="0.05" max="6.0" step="0.1"></div>
  <div class="field"><label>Switch Min (s)</label><input type="number" id="terminal_switch_min" value="4.0" min="0.5" max="60.0" step="0.5"></div>
  <div class="field"><label>Switch Max (s)</label><input type="number" id="terminal_switch_max" value="11.0" min="0.5" max="60.0" step="0.5"></div>
  <div class="field"><label>Seed (optional)</label><input type="number" id="seed" placeholder="random"></div>
</div>

<!-- Visual & Theme -->
<div class="panel" id="visual">
  <div class="field"><label>Theme</label><select id="theme">
{{THEME_OPTIONS}}
  </select></div>
  <div class="field"><label>Preset</label><select id="preset"><option value="">(none)</option><option value="cinematic">cinematic</option><option value="chaos">chaos</option><option value="minimal">minimal</option></select></div>
  <div class="field"><label>Scene Sync</label><select id="scene_sync"><option value="adaptive">adaptive</option><option value="bpm">bpm</option><option value="hybrid">hybrid</option></select></div>
  <div class="field"><label>Quality</label><select id="quality_mode"><option value="auto">auto</option><option value="off">off</option></select></div>
  <div class="field"><label>Theme Mode</label><select id="theme_mode"><option value="manual">manual</option><option value="bass">bass</option></select></div>
  <div class="field"><label>Bass Threshold</label><input type="number" id="bass_threshold" value="0.15" min="0.01" max="1.0" step="0.01"></div>
  <div class="field"><label>UI Style</label><select id="ui_style"><option value="full">full</option><option value="minimal">minimal</option></select></div>
  <div class="field"><label>Scene Pack</label><select id="scene_pack"><option value="">(none)</option></select></div>
  <div class="field"><label>Scene Pack File</label><input type="text" id="scene_pack_file" placeholder="/path/to/packs.json"></div>
</div>

<!-- Banner -->
<div class="panel" id="banner">
  <div class="checkbox-row"><label><input type="checkbox" id="show_banner"> Show Banner Row</label></div>
  <div class="field"><label>Banner Text</label><input type="text" id="banner_text" placeholder="Your text here"></div>
  <div class="field"><label>Banner Align</label><select id="banner_align"><option value="left">left</option><option value="center" selected>center</option><option value="right">right</option></select></div>
  <div class="field"><label>Banner Animation</label><select id="banner_anim"><option value="off">off</option><option value="scroll">scroll</option><option value="pulse">pulse</option></select></div>
  <div class="field"><label>Banner Size</label><select id="banner_size"><option value="normal">normal</option><option value="large">large</option></select></div>
</div>

<!-- Features -->
<div class="panel" id="features">
  <div class="checkbox-row">
    <label><input type="checkbox" id="keep_converted"> Keep Converted WAV</label>
    <label><input type="checkbox" id="alert_tones"> Alert Tones</label>
    <label><input type="checkbox" id="defender_ai" checked> Defender AI</label>
  </div>
  <div class="checkbox-row">
    <label><input type="checkbox" id="diagnostics"> Print Diagnostics</label>
    <label><input type="checkbox" id="mission_timeline" checked> Mission Timeline</label>
    <label><input type="checkbox" id="audio_fx" checked> Audio FX</label>
  </div>
  <div class="checkbox-row">
    <label><input type="checkbox" id="normalize"> Normalize Audio</label>
    <label><input type="checkbox" id="profile"> Performance Profile</label>
    <label><input type="checkbox" id="adaptive_fps"> Adaptive FPS</label>
  </div>
  <div class="checkbox-row">
    <label><input type="checkbox" id="high_contrast"> High Contrast</label>
    <label><input type="checkbox" id="detect_player"> Detect Player</label>
    <label><input type="checkbox" id="theme_transition"> Theme Transition</label>
  </div>
</div>

<!-- Advanced -->
<div class="panel" id="advanced">
  <div class="field"><label>Record File</label><input type="text" id="record_file" placeholder="/path/to/recording.jsonl"></div>
  <div class="field"><label>Record Mode</label><select id="record_mode"><option value="jsonl">jsonl</option><option value="txt">txt</option><option value="txt-clean">txt-clean</option><option value="jsonl.gz">jsonl.gz</option><option value="txt.gz">txt.gz</option><option value="txt-clean.gz">txt-clean.gz</option></select></div>
  <div class="field"><label>Plugin File</label><input type="text" id="plugin" placeholder="/path/to/plugin.py"></div>
  <div class="field"><label>Video Hook</label><input type="text" id="video_hook" placeholder="shell command"></div>
  <div class="field"><label>MQTT Broker</label><input type="text" id="mqtt" placeholder="localhost"></div>
  <div class="field"><label>OSC Address</label><input type="text" id="osc" placeholder="localhost:9000"></div>
  <div class="checkbox-row">
    <label><input type="checkbox" id="web"> Web Server</label>
    <label><input type="checkbox" id="rest_api"> REST API</label>
    <label><input type="checkbox" id="network_trigger"> Network Trigger</label>
    <label><input type="checkbox" id="chat"> Chat Overlay</label>
    <label><input type="checkbox" id="ai_scenes"> AI Scenes</label>
    <label><input type="checkbox" id="gpu"> GPU Render</label>
    <label><input type="checkbox" id="collab"> Collaborative</label>
    <label><input type="checkbox" id="remote_control"> Remote Control</label>
    <label><input type="checkbox" id="unicode_bars"> Unicode Bars</label>
  </div>
</div>

<div class="btn-row">
  <button type="button" class="btn btn-cancel" onclick="cancelRun()">Cancel</button>
  <button type="button" class="btn btn-start" onclick="startRun()">&#9654;  Start</button>
</div>
</form>

<script>
// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.panel).classList.add('active');
  });
});

// Load current config
(async () => {
  try {
    const r = await fetch('/api/config');
    const c = await r.json();
    if (c) {
      const fields = ['audio','source','youtube','playlist','capture_seconds','fps','sensitivity',
        'speed_min','speed_max','terminal_switch_min','terminal_switch_max','seed','theme',
        'preset','scene_sync','quality_mode','theme_mode','bass_threshold','ui_style',
        'banner_text','banner_align','banner_anim',
        'banner_size','record_file','record_mode','plugin','video_hook','mqtt','osc','scene_pack','scene_pack_file'];
      fields.forEach(f => {
        const el = document.getElementById(f);
        if (el && c[f] !== undefined && c[f] !== null) el.value = c[f];
      });
      const bools = ['play','show_banner','keep_converted','alert_tones','defender_ai','diagnostics',
        'mission_timeline','audio_fx','normalize','profile','adaptive_fps','high_contrast',
        'detect_player','theme_transition','web','rest_api','network_trigger','chat','ai_scenes',
        'gpu','collab','remote_control','unicode_bars'];
      bools.forEach(f => {
        const el = document.getElementById(f);
        if (el && c[f] !== undefined) el.checked = !!c[f];
      });
    }
  } catch(e) {}
})();

function collectConfig() {
  const cfg = {};
  const fields = ['audio','source','youtube','playlist','capture_seconds','fps','sensitivity',
    'speed_min','speed_max','terminal_switch_min','terminal_switch_max','theme',
    'preset','scene_sync','quality_mode','theme_mode','bass_threshold','ui_style',
    'banner_text','banner_align','banner_anim',
    'banner_size','record_file','record_mode','plugin','video_hook','mqtt','osc','scene_pack','scene_pack_file'];
  fields.forEach(f => {
    const el = document.getElementById(f);
    cfg[f] = el ? el.value : '';
  });
  const seedEl = document.getElementById('seed');
  cfg.seed = seedEl && seedEl.value ? parseInt(seedEl.value) : null;
  const bools = ['play','show_banner','keep_converted','alert_tones','defender_ai','diagnostics',
    'mission_timeline','audio_fx','normalize','profile','adaptive_fps','high_contrast',
    'detect_player','theme_transition','web','rest_api','network_trigger','chat','ai_scenes',
    'gpu','collab','remote_control','unicode_bars'];
  bools.forEach(f => {
    const el = document.getElementById(f);
    cfg[f] = el ? el.checked : false;
  });
  // Convert numeric strings
  ['capture_seconds','fps'].forEach(f => { cfg[f] = parseInt(cfg[f]) || 30; });
  ['sensitivity','speed_min','speed_max','terminal_switch_min','terminal_switch_max','bass_threshold'].forEach(f => { cfg[f] = parseFloat(cfg[f]) || 1.0; });
  return cfg;
}

async function startRun() {
  const cfg = collectConfig();
  if (cfg.source === 'file' && !cfg.youtube && !cfg.audio && !cfg.playlist) {
    alert('YouTube URL, audio file path, or playlist file is required when source is file.');
    return;
  }
  try {
    const r = await fetch('/api/start', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(cfg)});
    const d = await r.json();
    if (d.status === 'ok') {
      document.body.innerHTML = '<div style="text-align:center;padding:80px;color:#00ff9f;font-family:monospace"><h2>Starting CMD-AUDIO...</h2><p style="color:#8b949e">Redirecting to live controls...</p></div>';
      setTimeout(function() { window.location.href = '/live-controls'; }, 1500);
    } else {
      alert('Error: ' + (d.message || 'Unknown error'));
    }
  } catch(e) {
    alert('Failed to start: ' + e.message);
  }
}

async function cancelRun() {
  try { await fetch('/api/cancel'); } catch(e) {}
  document.body.innerHTML = '<div style="text-align:center;padding:80px;color:#f85149;font-family:monospace"><h2>Cancelled.</h2><p style="color:#8b949e">You can close this tab.</p></div>';
}
</script>
</body>
</html>"""

SETTINGS_HTML = SETTINGS_HTML.replace("{{THEME_OPTIONS}}", _theme_options_html)