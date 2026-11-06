"""The skull must not shift, must not draw without a line, and must fit."""

from __future__ import annotations

from cmd_audio import skull
from cmd_audio.utils import visible_len


def test_all_frames_share_one_geometry() -> None:
    """A jaw that changes the skull's size would make the panel jump."""
    for frames in (skull._FRAMES, skull._SMALL_FRAMES):
        heights = {len(frame) for frame in frames}
        widths = {len(row) for frame in frames for row in frame}
        assert len(heights) == 1, heights
        assert len(widths) == 1, widths


def _bottom(rows) -> int:
    for i in range(len(rows) - 1, -1, -1):
        if rows[i].strip():
            return i
    return -1


def test_jaw_frames_actually_travel() -> None:
    """The whole point: the mandible has to move down between frames."""
    closed, half, opened = skull._FRAMES
    assert closed != half and half != opened
    assert _bottom(closed) < _bottom(half) < _bottom(opened)


def test_jaw_open_on_a_fresh_line_and_shut_in_silence() -> None:
    assert skull.jaw_frame(0.02, beat=False, fresh=False) == 0
    assert skull.jaw_frame(0.20, beat=False, fresh=False) == 1
    assert skull.jaw_frame(0.80, beat=False, fresh=False) == 2
    assert skull.jaw_frame(0.10, beat=False, fresh=True) == 2


def test_animator_keeps_moving_on_a_steady_loud_track() -> None:
    """Regression: a level threshold pinned the jaw open for a whole song."""
    anim = skull.JawAnimator(rate=7.0)
    seen = set()
    for _ in range(60):  # 2 s at 30 fps, level never drops
        seen.add(skull.frame_from_amount(anim.update(1 / 30, 0.95)))
    assert seen == {0, 1, 2}, f"jaw stuck on frames {seen}"


def test_animator_stays_shut_in_silence() -> None:
    anim = skull.JawAnimator()
    amounts = [anim.update(1 / 30, 0.0) for _ in range(30)]
    assert max(amounts) < 0.34
    assert {skull.frame_from_amount(a) for a in amounts} == {0}


def test_animator_opens_fully_when_a_line_starts() -> None:
    anim = skull.JawAnimator()
    assert anim.update(1 / 30, 0.0, fresh=True) >= 0.99


def test_animator_clamps_a_long_stall() -> None:
    """A paused window must not jump the mouth open on resume."""
    anim = skull.JawAnimator()
    anim.update(1 / 30, 0.0)
    amount = anim.update(30.0, 0.0)
    assert amount < 0.34            # still a closed frame
    assert anim._env == 0.0         # no phantom beat envelope


def test_no_block_without_a_line() -> None:
    assert skull.render_block(40, 2, "", "next") is None
    assert skull.render_block(40, 2, "   ", "") is None


def test_block_is_exactly_the_panel_width_and_shows_both_lines() -> None:
    block = skull.render_block(40, 1, "hello there", "this comes next")
    assert block is not None
    for row in block:
        assert visible_len(row) == 40
    assert "hello there" in "".join(block)
    assert "this comes next" in "".join(block)


def test_block_colours_the_current_line_bright_and_the_next_one_dim() -> None:
    block = skull.render_block(40, 2, "now", "later", bright="<B>", dim="<D>", reset="</>")
    assert block is not None
    assert any("<B>" in row and "now" in row for row in block)
    assert any("<D>" in row and "later" in row for row in block)


def test_long_lines_are_clipped_to_the_panel() -> None:
    block = skull.render_block(20, 0, "a" * 80, "")
    assert block is not None
    for row in block:
        assert visible_len(row) == 20
    # the lyric row is the one before the trailing spacer
    assert "~" in block[-2]


def test_skull_drops_out_when_the_panel_is_narrower_than_the_art() -> None:
    # A 10 column panel cannot hold even the small skull: draw nothing at all
    # rather than a clipped mess.
    assert skull.render_block(10, 0, "hi", "") is None


def test_narrow_panels_fall_back_to_the_small_skull() -> None:
    block = skull.render_block(20, 0, "hi", "next line")
    assert block is not None
    for row in block:
        assert visible_len(row) == 20
    assert len(block) == skull.block_height(small=True)


def test_short_panels_use_the_small_skull() -> None:
    big = skull.render_block(30, 0, "line", "", small=False)
    small = skull.render_block(30, 0, "line", "", small=True)
    assert big is not None and small is not None
    assert len(small) < len(big)
    assert skull.block_height(small=True) < skull.block_height(small=False)


def test_block_fits_inside_a_small_panel() -> None:
    """The caller reserves block_height() rows; the block must not exceed it."""
    for small in (False, True):
        block = skull.render_block(30, 2, "x", "y", small=small)
        assert block is not None
        assert len(block) <= skull.block_height(small=small)
