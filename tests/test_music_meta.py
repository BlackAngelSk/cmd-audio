"""The renderer must always show a song name -- never a URL and never a temp path."""

from __future__ import annotations

import os

from cmd_audio import music_meta

TEMP = "/tmp/hacker_youtube_ab12cd.wav"


def test_clean_name_strips_extension_and_youtube_id() -> None:
    assert music_meta.clean_name("Turboslash - Access Denied [VPZQdPivqFw].mp3") == "Turboslash - Access Denied"


def test_clean_name_strips_directories_and_noise_tags() -> None:
    assert music_meta.clean_name("/home/x/music/Artist_-_Song_(Official Video).flac") == "Artist - Song"


def test_clean_name_handles_empty() -> None:
    assert music_meta.clean_name("") == ""
    assert music_meta.clean_name("   ") == ""


def test_track_display_name_never_returns_a_url(monkeypatch) -> None:
    monkeypatch.setattr(music_meta, "youtube_title", lambda url, fetch=True, timeout=20.0: "Rick Astley - Never Gonna Give You Up")
    name = music_meta.track_display_name("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert name == "Rick Astley - Never Gonna Give You Up"
    assert "http" not in name


def test_track_display_name_url_without_title_is_not_the_link(monkeypatch) -> None:
    monkeypatch.setattr(music_meta, "youtube_title", lambda url, fetch=True, timeout=20.0: "")
    name = music_meta.track_display_name("https://youtu.be/dQw4w9WgXcQ", fetch=False)
    assert "youtu" not in name
    assert "http" not in name


def test_track_display_name_demo_and_markers() -> None:
    assert music_meta.track_display_name("") == "DEMO"
    assert music_meta.track_display_name("(demo mode)") == "DEMO"


def test_track_display_name_temp_file_never_leaks_the_path(monkeypatch) -> None:
    import cmd_audio.audio_input as ai

    monkeypatch.setattr(ai, "get_last_youtube_title", lambda: "Some Song Title")
    name = music_meta.track_display_name(TEMP)
    assert name == "Some Song Title"
    assert "hacker_youtube" not in name


def test_track_display_name_local_file(tmp_path) -> None:
    p = tmp_path / "Nirvana - Smells Like Teen Spirit [abc123def45].mp3"
    p.write_bytes(b"\x00" * 16)
    assert music_meta.track_display_name(str(p)) == "Nirvana - Smells Like Teen Spirit"


def test_track_display_name_missing_file_is_cleaned_not_pathed() -> None:
    name = music_meta.track_display_name("/does/not/exist/Aphex_Twin_-_Xtal.mp3")
    assert name == "Aphex Twin - Xtal"
    assert os.sep not in name


def test_is_temp_source() -> None:
    assert music_meta.is_temp_source(TEMP)
    assert music_meta.is_temp_source("/tmp/hacker_sync_zz.wav")
    assert not music_meta.is_temp_source("/home/x/song.mp3")
