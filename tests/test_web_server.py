"""The browser controls must actually be reachable and must actually apply.

These exercise the real HTTP surface the page talks to, because the failure
mode being guarded against is silent: a 404 on /api/live looked identical to a
working control panel.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest

from cmd_audio.control import LiveControlState
from cmd_audio.web_server import AudioServer, load_live_controls_html, start_web_server


def _state(music_file: str = "Test Song") -> LiveControlState:
    return LiveControlState(
        1.0, 0.25, 3.0, 4.0, 11.0,
        "matrix", "manual", "", "center", "off", "normal",
        False, "full", "auto", False, "adaptive",
        False, True, True, True,
        "netrunner", "RECON", "corp-gw", False, music_file,
    )


def _get(url: str):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, r.read().decode("utf-8", "replace")


def _post(url: str, payload: dict):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, json.loads(r.read().decode())


@pytest.fixture()
def server():
    srv = AudioServer("127.0.0.1", 0, live_on_root=True)
    srv.set_live_state(_state())
    assert srv.start(), srv.bind_error
    yield srv
    srv.stop()


def test_live_controls_page_is_served_at_root(server) -> None:
    status, body = _get(f"http://127.0.0.1:{server.port}/")
    assert status == 200
    assert "CMD-AUDIO" in body
    assert "/api/live" in body  # the page that talks to the control API


def test_live_controls_page_is_served_at_live_controls(server) -> None:
    status, body = _get(f"http://127.0.0.1:{server.port}/live-controls")
    assert status == 200
    assert "CMD-AUDIO" in body


def test_setup_form_still_served_when_not_a_live_session() -> None:
    srv = AudioServer("127.0.0.1", 0, live_on_root=False)
    assert srv.start(), srv.bind_error
    try:
        status, body = _get(f"http://127.0.0.1:{srv.port}/")
        assert status == 200
        assert "Configure your run parameters" in body
        # the controls page is still reachable by path
        assert _get(f"http://127.0.0.1:{srv.port}/live-controls")[0] == 200
    finally:
        srv.stop()


def test_live_state_reports_the_song_name(server) -> None:
    status, body = _get(f"http://127.0.0.1:{server.port}/api/live-state")
    assert status == 200
    payload = json.loads(body)
    assert payload["music_file"] == "Test Song"
    # the snapshot key is theme_name -- live_controls.html maps it to the
    # `theme` form control, and a mismatch here is why the theme dropdown used
    # to never reflect the running state.
    assert payload["theme_name"] == "matrix"


def test_post_live_applies_settings(server) -> None:
    status, payload = _post(
        f"http://127.0.0.1:{server.port}/api/live",
        {"sensitivity": 2.5, "theme": "amber", "paused": True, "banner_text": "hi"},
    )
    assert status == 200 and payload["status"] == "ok"
    snap = server._state().snapshot()
    assert snap.sensitivity == pytest.approx(2.5)
    assert snap.theme_name == "amber"
    assert snap.paused is True
    assert snap.banner_text == "hi"


def test_post_live_rejects_unknown_keys_gracefully(server) -> None:
    status, payload = _post(f"http://127.0.0.1:{server.port}/api/live", {"nope": 1})
    assert status == 200 and payload["status"] == "ok"


def test_post_music_requests_a_track_change(server) -> None:
    status, payload = _post(f"http://127.0.0.1:{server.port}/api/music", {"url": "/tmp/song.mp3"})
    assert status == 200 and payload["status"] == "ok"
    assert server._state().consume_music_change() == "/tmp/song.mp3"


def test_post_stop_requests_a_quit(server) -> None:
    assert server._state().snapshot().quit_requested is False
    status, payload = _post(f"http://127.0.0.1:{server.port}/api/stop", {})
    assert status == 200 and payload["status"] == "ok"
    # the render loop polls this and breaks out
    assert server._state().snapshot().quit_requested is True


def test_post_stop_without_live_state_reports_error() -> None:
    srv = AudioServer("127.0.0.1", 0, live_on_root=True)
    srv.live_state = None
    import cmd_audio.web_server as ws

    original = ws._current_live_state
    ws._current_live_state = lambda: None
    try:
        assert srv.start(), srv.bind_error
        status, payload = _post(f"http://127.0.0.1:{srv.port}/api/stop", {})
        assert status == 200 and payload["status"] == "error"
    finally:
        ws._current_live_state = original
        srv.stop()


def test_unknown_api_path_is_404_not_html(server) -> None:
    with pytest.raises(urllib.error.HTTPError) as exc:
        _get(f"http://127.0.0.1:{server.port}/api/does-not-exist")
    assert exc.value.code == 404


def test_live_controls_html_is_bundled() -> None:
    html = load_live_controls_html()
    assert html, "live_controls.html must ship next to the package"
    assert "/api/live-state" in html


def test_start_web_server_walks_to_a_free_port() -> None:
    first = start_web_server("127.0.0.1", 0, live_on_root=True)
    assert first.server is not None
    try:
        second = start_web_server("127.0.0.1", first.port, live_on_root=True)
        try:
            assert second.server is not None, "second server must not silently die"
            assert second.port != first.port
            assert _get(f"http://127.0.0.1:{second.port}/")[0] == 200
        finally:
            second.stop()
    finally:
        first.stop()
