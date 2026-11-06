"""Lyrics are either timed and syncable, or they are not shown at all.

The skull only opens its jaw on *timed* lines, so the parser has to be strict
about the difference and honest when it has nothing.
"""

from __future__ import annotations

import os

from cmd_audio import lyrics

LRC = """[ar:Turboslash]
[ti:Access Denied]
[offset:+250]
[00:01.00]first line
[00:04.50]second line
[00:09.25][01:20.00]chorus line
[00:12.00]
[00:15.75]last line
"""


def test_parse_lrc_reads_times_and_skips_metadata() -> None:
    lines = lyrics.parse_lrc(LRC)
    times = [round(line.t, 2) for line in lines]
    # metadata tags carry no timestamp; the +250ms offset applies to every line
    assert times == [1.25, 4.75, 9.5, 12.25, 16.0, 80.25]
    assert lines[0].text == "first line"
    assert lines[2].text == "chorus line"  # two stamps on one line
    assert lines[-1].text == "chorus line"


def test_parse_lrc_keeps_blank_lines_as_breaks() -> None:
    lines = lyrics.parse_lrc(LRC)
    assert lines[3].text == ""
    assert lines[3].t == 12.25


def test_parse_lrc_sorts_out_of_order_input() -> None:
    lines = lyrics.parse_lrc("[00:10.00]ten\n[00:02.00]two\n")
    assert [line.text for line in lines] == ["two", "ten"]


def test_parse_lrc_dedupes_identical_stamps() -> None:
    lines = lyrics.parse_lrc("[00:03.00]hel\n[00:03.00]hello\n")
    assert len(lines) == 1
    assert lines[0].text == "hello"


def test_at_returns_current_and_next_line() -> None:
    parsed = lyrics.from_text(LRC)
    assert parsed.timed

    idx, text, nxt = parsed.at(0.5)
    assert (idx, text, nxt) == (-1, "", "first line")

    idx, text, nxt = parsed.at(1.3)
    assert (idx, text, nxt) == (0, "first line", "second line")

    idx, text, nxt = parsed.at(4.75)
    assert text == "second line"

    # inside the gap marked by the empty line, nothing is sung
    idx, text, _ = parsed.at(13.0)
    assert (idx, text) == (3, "")

    idx, text, nxt = parsed.at(999.0)
    assert (idx, text, nxt) == (5, "chorus line", "")


def test_untimed_lyrics_are_not_marked_timed() -> None:
    plain = lyrics.from_text("just\nsome\nwords\n")
    assert plain.lines
    assert plain.timed is False
    # nothing can be "current" without timestamps
    assert plain.at(10.0) == (-1, "", "just")


def test_from_sidecar_reads_the_file_next_to_the_track(tmp_path) -> None:
    track = tmp_path / "song.mp3"
    track.write_bytes(b"\x00")
    (tmp_path / "song.lrc").write_text(LRC, encoding="utf-8")

    found = lyrics.from_sidecar(str(track))
    assert found is not None and found.timed
    assert found.lines[0].text == "first line"
    assert found.source == "song.lrc"


def test_from_sidecar_ignores_a_missing_or_empty_file(tmp_path) -> None:
    track = tmp_path / "song.mp3"
    track.write_bytes(b"\x00")
    assert lyrics.from_sidecar(str(track)) is None

    (tmp_path / "song.lrc").write_text("   \n", encoding="utf-8")
    assert lyrics.from_sidecar(str(track)) is None


def test_load_for_track_prefers_a_timed_sidecar(tmp_path, monkeypatch) -> None:
    track = tmp_path / "song.mp3"
    track.write_bytes(b"\x00")
    (tmp_path / "song.lrc").write_text(LRC, encoding="utf-8")

    def explode(*_a, **_k):
        raise AssertionError("must not hit the network when a sidecar exists")

    monkeypatch.setattr(lyrics, "fetch_online", explode)
    found = lyrics.load_for_track(str(track), "Artist - Song", 200.0)
    assert found.timed and found.lines


def test_load_for_track_falls_back_to_online(monkeypatch, tmp_path) -> None:
    track = tmp_path / "song.mp3"
    track.write_bytes(b"\x00")
    monkeypatch.setattr(lyrics, "from_tags", lambda _p: None)
    monkeypatch.setattr(lyrics, "fetch_online", lambda *a, **k: LRC)

    found = lyrics.load_for_track(str(track), "Artist - Song", 200.0)
    assert found.timed
    assert found.source == "lrclib"


def test_load_for_track_without_any_source_is_falsy(monkeypatch, tmp_path) -> None:
    track = tmp_path / "song.mp3"
    track.write_bytes(b"\x00")
    monkeypatch.setattr(lyrics, "from_tags", lambda _p: None)
    monkeypatch.setattr(lyrics, "fetch_online", lambda *a, **k: None)

    found = lyrics.load_for_track(str(track), "Unknown - Nothing", 0.0)
    assert not found
    assert found.timed is False


def test_load_for_track_keeps_untimed_lyrics_but_marks_them_unsyncable(monkeypatch, tmp_path) -> None:
    track = tmp_path / "song.mp3"
    track.write_bytes(b"\x00")
    monkeypatch.setattr(lyrics, "from_tags", lambda _p: lyrics.from_text("one\ntwo\n"))
    monkeypatch.setattr(lyrics, "fetch_online", lambda *a, **k: None)

    found = lyrics.load_for_track(str(track), "", 0.0)
    assert found.lines
    assert found.timed is False


def test_lrclib_cache_roundtrip(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(lyrics, "CACHE_DIR", str(tmp_path / "cache"))
    lyrics._write_cache("Artist", "Song", 200.0, LRC)
    assert lyrics._read_cache("Artist", "Song", 200.0) == LRC
    assert lyrics._read_cache("Other", "Song", 200.0) is None


def test_split_artist_title() -> None:
    assert lyrics.split_artist_title("Daft Punk - Get Lucky") == ("Daft Punk", "Get Lucky")
    assert lyrics.split_artist_title("Daft Punk – Get Lucky") == ("Daft Punk", "Get Lucky")
    assert lyrics.split_artist_title("Just A Title") == ("", "Just A Title")


def test_loader_thread_reports_result(monkeypatch) -> None:
    monkeypatch.setattr(lyrics, "load_for_track", lambda *a, **k: lyrics.from_text(LRC))
    loader = lyrics.load_async("/tmp/x.mp3", "Artist - Song")
    found = loader.wait(timeout=5)
    assert found.timed
    assert loader.done is True


def test_loader_thread_swallows_errors(monkeypatch) -> None:
    def boom(*_a, **_k):
        raise RuntimeError("nope")

    monkeypatch.setattr(lyrics, "load_for_track", boom)
    loader = lyrics.load_async("/tmp/x.mp3")
    found = loader.wait(timeout=5)
    assert not found
    assert loader.done is True


def test_cache_dir_lives_under_the_user_cache() -> None:
    assert os.path.basename(lyrics.CACHE_DIR) == "lyrics"
