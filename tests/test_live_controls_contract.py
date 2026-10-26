"""The live-controls page and the /api/live handler must agree.

Both directions matter, and both used to fail silently:

* a control the page sends that the backend does not understand is a dead knob;
* a backend key the page never reads means the control never reflects reality
  (``theme`` vs the snapshot's ``theme_name`` was exactly that bug).

The backend now reports the keys it applied, so the contract can be checked
instead of assumed.
"""

from __future__ import annotations

import json
import re
import urllib.request

import pytest

from cmd_audio.web_server import AudioServer, load_live_controls_html

from .test_web_server import _state


def _page_controls() -> dict:
    """Map control id -> input type for every input/select on the page."""
    html = load_live_controls_html()
    controls = {}
    for tag in re.findall(r"<(?:input|select)\b[^>]*>", html):
        m = re.search(r'\bid="([^"]+)"', tag)
        if not m:
            continue
        t = re.search(r'\btype="([^"]+)"', tag)
        kind = t.group(1) if t else ("select" if tag.startswith("<select") else "text")
        controls[m.group(1)] = kind
    return controls


def _page_startup_only() -> list:
    html = load_live_controls_html()
    m = re.search(r"var STARTUP_ONLY = \[(.*?)\];", html, re.S)
    assert m, "live_controls.html must declare STARTUP_ONLY"
    return re.findall(r"'([^']+)'", m.group(1))


def _value_for(kind: str):
    if kind == "checkbox":
        return True
    if kind in ("range", "number"):
        return 2.5
    if kind == "select":
        return None  # filled from the element's own options below
    return "x"


def _post(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read().decode())


@pytest.fixture()
def server():
    srv = AudioServer("127.0.0.1", 0, live_on_root=True)
    srv.set_live_state(_state())
    assert srv.start(), srv.bind_error
    yield srv
    srv.stop()


def test_every_live_control_is_understood_by_the_backend(server) -> None:
    startup_only = set(_page_startup_only())
    controls = _page_controls()
    assert controls, "no controls parsed out of live_controls.html"

    for cid, kind in sorted(controls.items()):
        if cid in startup_only:
            continue
        value = _value_for(kind)
        if value is None:  # a <select>: send something plausible
            value = "adaptive"
        if kind == "range":
            value = 2.5
        payload = _post(f"http://127.0.0.1:{server.port}/api/live", {cid: value})
        assert payload["status"] == "ok"
        assert cid in payload["applied"], (
            f"control '{cid}' is sent by the page but the backend ignores it"
        )


def test_backend_keys_are_all_read_by_the_page(server) -> None:
    """Every key the backend applies must be consumed by the page's state sync."""
    html = load_live_controls_html()
    sync_block = html[html.index("var fieldMap"): html.index("var bools")]
    sync_block += html[html.index("var bools"): html.index("var bools") + 400]

    # keys the page writes back into the form
    mapped = set(re.findall(r"\['([a-z_]+)','[a-z_]+'\]", sync_block))
    mapped |= set(re.findall(r"'([a-z_]+)'", html[html.index("var bools"): html.index("var bools") + 300]))
    mapped |= {"sensitivity", "speed_min", "speed_max",
               "terminal_switch_min", "terminal_switch_max"}

    # applied outside fieldMap/bools, or pure status readouts
    handled_elsewhere = {"music_file", "music_status", "frame_drops", "quit_requested"}
    assert "if (s.music_file)" in html, "the page must show the current song"

    snap = server._state().snapshot()
    for key in vars(snap):
        if key in handled_elsewhere:
            continue
        assert key in mapped, f"backend reports '{key}' but the page never applies it"


def test_startup_only_controls_are_not_pretended_to_be_live(server) -> None:
    for cid in _page_startup_only():
        payload = _post(f"http://127.0.0.1:{server.port}/api/live", {cid: 1})
        assert cid in payload["ignored"], (
            f"'{cid}' is marked startup-only in the page but the backend accepted it"
        )
