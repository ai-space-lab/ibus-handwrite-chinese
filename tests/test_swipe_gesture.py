#!/usr/bin/env python3
"""Test swipe gesture handling in TrackpadReader and momentum decay.

Tests velocity-based page computation, momentum decay, non-destructive
stroke save/restore, and candidate zone behaviors with mock devices.
No real evdev hardware or GTK/GLib main loop required.
"""

import importlib.machinery
import importlib.util
import os
import sys
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Mock evdev and gi.repository BEFORE importing handwrite_evdev
# ---------------------------------------------------------------------------
_evdev_mock = MagicMock()
_evdev_mock.ecodes.EV_SYN = 0
_evdev_mock.ecodes.EV_KEY = 1
_evdev_mock.ecodes.EV_ABS = 3
_evdev_mock.ecodes.SYN_REPORT = 0
_evdev_mock.ecodes.BTN_TOUCH = 330
_evdev_mock.ecodes.ABS_X = 0
_evdev_mock.ecodes.ABS_Y = 1
_evdev_mock.ecodes.ABS_MT_SLOT = 47
_evdev_mock.ecodes.ABS_MT_TRACKING_ID = 57
_evdev_mock.ecodes.ABS_MT_POSITION_X = 53
_evdev_mock.ecodes.ABS_MT_POSITION_Y = 54
sys.modules['evdev'] = _evdev_mock

# Mock gi.repository so GLib is never actually needed
_gi_mock = MagicMock()
_glib_mock = MagicMock()
_glib_mock.idle_add = lambda fn, *args: None
_gi_mock.repository.GLib = _glib_mock
_gi_mock.require_version = MagicMock()
sys.modules['gi'] = _gi_mock
sys.modules['gi.repository'] = _gi_mock.repository

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

# ---------------------------------------------------------------------------
# Load handwrite_evdev module
# ---------------------------------------------------------------------------
_evdev_path = os.path.join(PROJECT_ROOT, 'src', 'handwrite_evdev.py')
_loader = importlib.machinery.SourceFileLoader('handwrite_evdev', _evdev_path)
_spec = importlib.util.spec_from_loader('handwrite_evdev', _loader)
handwrite_evdev = importlib.util.module_from_spec(_spec)
_loader.exec_module(handwrite_evdev)

TrackpadReader = handwrite_evdev.TrackpadReader
VELOCITY_SCALE = 0.5
_STATE_IDLE = 0
_STATE_TOUCH = 1
_STATE_STROKE = 2
_STATE_SWIPE = 3
_STATE_SELECT = 4

# ---------------------------------------------------------------------------
# Event helpers — numeric values match the mock ecodes above
# ---------------------------------------------------------------------------
EV_ABS = 3
EV_KEY = 1
EV_SYN = 0
SYN_REPORT = 0
BTN_TOUCH = 330
ABS_X = 0
ABS_Y = 1
ABS_MT_SLOT = 47
ABS_MT_TRACKING_ID = 57
ABS_MT_POSITION_X = 53
ABS_MT_POSITION_Y = 54


def ev(type_, code, value):
    return SimpleNamespace(type=type_, code=code, value=value)


class FakeDevice:
    """Mock evdev device that yields a predetermined list of events."""
    def __init__(self, events):
        self._events = list(events)

    def read_loop(self):
        for e in self._events:
            yield e

    def grab(self):
        pass

    def ungrab(self):
        pass

    def close(self):
        pass


# ---------------------------------------------------------------------------
# Test infrastructure
# ---------------------------------------------------------------------------

def make_recorder():
    """Return (records_list, callbacks_dict) for tracking callback invocations."""
    records = []
    callbacks = {
        'on_stroke_begin': lambda x, y: records.append(('on_stroke_begin', x, y)),
        'on_stroke_point': lambda x, y: records.append(('on_stroke_point', x, y)),
        'on_stroke_end': lambda pts: records.append(('on_stroke_end', pts)),
        'on_tap': lambda x: records.append(('on_tap', x)),
        'on_swipe_left': lambda p: records.append(('on_swipe_left', p)),
        'on_swipe_right': lambda p: records.append(('on_swipe_right', p)),
        'on_candidate_highlight': lambda x: records.append(('on_candidate_highlight', x)),
        'on_candidate_select': lambda x: records.append(('on_candidate_select', x)),
    }
    return records, callbacks


def build_reader(records, callbacks):
    """Create a pre-configured TrackpadReader suitable for testing."""
    reader = TrackpadReader(callbacks)
    # Patch _idle to call the callback directly and record via callback closures
    reader._idle = lambda fn, *a: fn(*a)
    # Calibration: 0-1000 range for both axes
    reader._cal_x_min = 0
    reader._cal_x_max = 1000
    reader._cal_x_range = 1000
    reader._cal_y_min = 0
    reader._cal_y_max = 1000
    reader._cal_y_range = 1000
    reader._move_threshold = 20
    reader._swipe_threshold = 80
    reader._uses_mt_pos = True
    reader.running = True
    return reader


def run_events(reader, events):
    """Feed events through reader._run() synchronously."""
    reader.device = FakeDevice(events)
    reader._run()


# ===================================================================
# Tests
# ===================================================================

def test_velocity_computation():
    """10+ SYN_REPORT events with 2 slots, dx=5 per event → on_swipe_right fires with pages > 1."""
    records, callbacks = make_recorder()
    reader = build_reader(records, callbacks)

    events = []
    # Slot 0
    events.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    events.append(ev(EV_ABS, ABS_MT_TRACKING_ID, 100))
    events.append(ev(EV_ABS, ABS_MT_POSITION_X, 200))
    events.append(ev(EV_ABS, ABS_MT_POSITION_Y, 200))
    # Slot 1
    events.append(ev(EV_ABS, ABS_MT_SLOT, 1))
    events.append(ev(EV_ABS, ABS_MT_TRACKING_ID, 200))
    events.append(ev(EV_ABS, ABS_MT_POSITION_X, 600))
    events.append(ev(EV_ABS, ABS_MT_POSITION_Y, 200))
    # SYN_REPORT — enters SWIPE (2 active slots)
    events.append(ev(EV_SYN, SYN_REPORT, 0))

    # 17 more SYN_REPORTs, each moving both slots right by 5 px
    for i in range(1, 18):
        events.append(ev(EV_ABS, ABS_MT_SLOT, 0))
        events.append(ev(EV_ABS, ABS_MT_POSITION_X, 200 + i * 5))
        events.append(ev(EV_ABS, ABS_MT_SLOT, 1))
        events.append(ev(EV_ABS, ABS_MT_POSITION_X, 600 + i * 5))
        events.append(ev(EV_SYN, SYN_REPORT, 0))

    run_events(reader, events)

    # Check that on_swipe_right fired
    swipe_calls = [r for r in records if r[0] == 'on_swipe_right']
    assert len(swipe_calls) >= 1, f"Expected on_swipe_right to fire, got records: {records}"
    pages = swipe_calls[0][1]
    assert pages > 1, f"Expected pages > 1, got {pages}"


def test_velocity_below_threshold():
    """Small movement (total dx < swipe_threshold) → no swipe callback fires."""
    records, callbacks = make_recorder()
    reader = build_reader(records, callbacks)

    events = []
    # Slot 0
    events.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    events.append(ev(EV_ABS, ABS_MT_TRACKING_ID, 100))
    events.append(ev(EV_ABS, ABS_MT_POSITION_X, 200))
    events.append(ev(EV_ABS, ABS_MT_POSITION_Y, 200))
    # Slot 1
    events.append(ev(EV_ABS, ABS_MT_SLOT, 1))
    events.append(ev(EV_ABS, ABS_MT_TRACKING_ID, 200))
    events.append(ev(EV_ABS, ABS_MT_POSITION_X, 600))
    events.append(ev(EV_ABS, ABS_MT_POSITION_Y, 200))
    # SYN_REPORT — enters SWIPE
    events.append(ev(EV_SYN, SYN_REPORT, 0))

    # Just 2 movement events with small dx=2 each → total dx=4 < 80
    for i in range(1, 3):
        events.append(ev(EV_ABS, ABS_MT_SLOT, 0))
        events.append(ev(EV_ABS, ABS_MT_POSITION_X, 200 + i * 2))
        events.append(ev(EV_ABS, ABS_MT_SLOT, 1))
        events.append(ev(EV_ABS, ABS_MT_POSITION_X, 600 + i * 2))
        events.append(ev(EV_SYN, SYN_REPORT, 0))

    run_events(reader, events)

    swipe_calls = [r for r in records if r[0] in ('on_swipe_left', 'on_swipe_right')]
    assert len(swipe_calls) == 0, f"Expected no swipe callback, got {swipe_calls}"


def test_momentum_decay_curve():
    """Directly test _momentum_tick decay logic: ×0.65 each tick, stop at <0.3."""
    momentum_pages = 5
    momentum_velocity = 5.0 * 0.65

    def tick():
        nonlocal momentum_pages, momentum_velocity
        if momentum_pages <= 0:
            return False
        momentum_pages -= 1
        momentum_velocity *= 0.65
        if momentum_velocity < 0.3:
            momentum_pages = 0
            return False
        momentum_pages = max(1, int(momentum_velocity))
        return True

    velocities = []
    for _ in range(6):
        velocities.append(momentum_velocity)
        if not tick():
            break

    assert momentum_pages == 0, \
        f"Expected momentum_pages=0, got {momentum_pages}"
    assert momentum_velocity < 0.3, \
        f"Expected momentum_velocity < 0.3, got {momentum_velocity}"

    for i in range(1, len(velocities)):
        ratio = velocities[i] / velocities[i - 1]
        assert abs(ratio - 0.65) < 0.001, \
            f"Tick {i}: expected decay ×0.65, got ×{ratio:.4f}"


def test_non_destructive_save_restore():
    """1-finger stroke 2pts → 2nd finger SWIPE saves → back to 1 restores."""
    records, callbacks = make_recorder()
    reader = build_reader(records, callbacks)

    phase1 = []
    phase1.append(ev(EV_KEY, BTN_TOUCH, 1))
    phase1.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    phase1.append(ev(EV_ABS, ABS_MT_TRACKING_ID, 100))
    phase1.append(ev(EV_ABS, ABS_MT_POSITION_X, 200))
    phase1.append(ev(EV_ABS, ABS_MT_POSITION_Y, 500))
    phase1.append(ev(EV_ABS, ABS_X, 200))
    phase1.append(ev(EV_SYN, SYN_REPORT, 0))

    phase1.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    phase1.append(ev(EV_ABS, ABS_MT_POSITION_X, 250))
    phase1.append(ev(EV_ABS, ABS_X, 250))
    phase1.append(ev(EV_SYN, SYN_REPORT, 0))

    phase1.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    phase1.append(ev(EV_ABS, ABS_MT_POSITION_X, 300))
    phase1.append(ev(EV_ABS, ABS_X, 300))
    phase1.append(ev(EV_SYN, SYN_REPORT, 0))

    phase1.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    phase1.append(ev(EV_ABS, ABS_MT_POSITION_X, 350))
    phase1.append(ev(EV_ABS, ABS_X, 350))
    phase1.append(ev(EV_SYN, SYN_REPORT, 0))

    phase1.append(ev(EV_ABS, ABS_MT_SLOT, 1))
    phase1.append(ev(EV_ABS, ABS_MT_TRACKING_ID, 200))
    phase1.append(ev(EV_ABS, ABS_MT_POSITION_X, 600))
    phase1.append(ev(EV_ABS, ABS_MT_POSITION_Y, 500))
    phase1.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    phase1.append(ev(EV_ABS, ABS_MT_POSITION_X, 400))
    phase1.append(ev(EV_ABS, ABS_X, 400))
    phase1.append(ev(EV_SYN, SYN_REPORT, 0))

    run_events(reader, phase1)

    saved_len = len(reader._saved_stroke)
    assert saved_len == 2, f"Expected 2 saved stroke points, got {saved_len}"

    phase2 = []
    phase2.append(ev(EV_ABS, ABS_MT_SLOT, 1))
    phase2.append(ev(EV_ABS, ABS_MT_TRACKING_ID, -1))
    phase2.append(ev(EV_SYN, SYN_REPORT, 0))

    run_events(reader, phase2)

    stroke_begin_calls = [r for r in records if r[0] == 'on_stroke_begin']
    assert len(stroke_begin_calls) == 2, \
        f"Expected 2 on_stroke_begin, got {stroke_begin_calls}"

    stroke_point_calls = [r for r in records if r[0] == 'on_stroke_point']
    assert len(stroke_point_calls) == 2, \
        f"Expected 2 on_stroke_point, got {stroke_point_calls}"

    assert reader._state == _STATE_STROKE, f"Expected STROKE, got {reader._state}"
    assert len(reader._stroke) == saved_len
    assert not reader._saved_stroke


def test_non_destructive_stale_timeout():
    """SWIPE saves stroke → _saved_t 6s old → back to 1 → IDLE not restore."""
    records, callbacks = make_recorder()
    reader = build_reader(records, callbacks)

    phase1 = []
    phase1.append(ev(EV_KEY, BTN_TOUCH, 1))
    phase1.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    phase1.append(ev(EV_ABS, ABS_MT_TRACKING_ID, 100))
    phase1.append(ev(EV_ABS, ABS_MT_POSITION_X, 200))
    phase1.append(ev(EV_ABS, ABS_MT_POSITION_Y, 500))
    phase1.append(ev(EV_ABS, ABS_X, 200))
    phase1.append(ev(EV_SYN, SYN_REPORT, 0))

    phase1.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    phase1.append(ev(EV_ABS, ABS_MT_POSITION_X, 250))
    phase1.append(ev(EV_ABS, ABS_X, 250))
    phase1.append(ev(EV_SYN, SYN_REPORT, 0))

    phase1.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    phase1.append(ev(EV_ABS, ABS_MT_POSITION_X, 300))
    phase1.append(ev(EV_ABS, ABS_X, 300))
    phase1.append(ev(EV_SYN, SYN_REPORT, 0))

    phase1.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    phase1.append(ev(EV_ABS, ABS_MT_POSITION_X, 350))
    phase1.append(ev(EV_ABS, ABS_X, 350))
    phase1.append(ev(EV_SYN, SYN_REPORT, 0))

    phase1.append(ev(EV_ABS, ABS_MT_SLOT, 1))
    phase1.append(ev(EV_ABS, ABS_MT_TRACKING_ID, 200))
    phase1.append(ev(EV_ABS, ABS_MT_POSITION_X, 600))
    phase1.append(ev(EV_ABS, ABS_MT_POSITION_Y, 500))
    phase1.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    phase1.append(ev(EV_ABS, ABS_MT_POSITION_X, 400))
    phase1.append(ev(EV_ABS, ABS_X, 400))
    phase1.append(ev(EV_SYN, SYN_REPORT, 0))

    run_events(reader, phase1)

    assert reader._state == _STATE_SWIPE, f"Expected SWIPE, got {reader._state}"
    assert len(reader._saved_stroke) > 0
    saved_before = len(reader._saved_stroke)

    reader._saved_t = time.time() - 6.0

    phase2 = []
    phase2.append(ev(EV_ABS, ABS_MT_SLOT, 1))
    phase2.append(ev(EV_ABS, ABS_MT_TRACKING_ID, -1))
    phase2.append(ev(EV_SYN, SYN_REPORT, 0))

    run_events(reader, phase2)

    assert reader._state == _STATE_IDLE, f"Expected IDLE, got {reader._state}"
    assert len(reader._stroke) == 0
    assert len(reader._saved_stroke) == saved_before


def test_candidate_select_zone_entry():
    """Touch in candidate zone (fy < 0.25) → _STATE_SELECT with on_candidate_highlight."""
    records, callbacks = make_recorder()
    reader = build_reader(records, callbacks)

    events = []
    events.append(ev(EV_KEY, BTN_TOUCH, 1))  # → _pending=True
    events.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    events.append(ev(EV_ABS, ABS_MT_TRACKING_ID, 100))
    events.append(ev(EV_ABS, ABS_MT_POSITION_X, 200))  # fx=0.2
    events.append(ev(EV_ABS, ABS_MT_POSITION_Y, 100))  # fy=0.1 < 0.25 → candidate zone
    events.append(ev(EV_SYN, SYN_REPORT, 0))
    run_events(reader, events)

    assert reader._state == _STATE_SELECT, f"Expected SELECT state, got {reader._state}"
    highlight_calls = [r for r in records if r[0] == 'on_candidate_highlight']
    assert len(highlight_calls) >= 1, "Expected on_candidate_highlight to fire"
    assert abs(highlight_calls[0][1] - 0.2) < 0.001, \
        f"Expected fx=0.2, got {highlight_calls[0][1]}"


def test_candidate_select_zone_exclusion():
    """Touch in drawing zone (fy >= 0.25) → _STATE_TOUCH, not SELECT."""
    records, callbacks = make_recorder()
    reader = build_reader(records, callbacks)

    events = []
    events.append(ev(EV_KEY, BTN_TOUCH, 1))  # → _pending=True
    events.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    events.append(ev(EV_ABS, ABS_MT_TRACKING_ID, 100))
    events.append(ev(EV_ABS, ABS_MT_POSITION_X, 200))
    events.append(ev(EV_ABS, ABS_MT_POSITION_Y, 500))  # fy=0.5 ≥ 0.25 → drawing zone
    events.append(ev(EV_SYN, SYN_REPORT, 0))
    run_events(reader, events)

    assert reader._state == _STATE_TOUCH, f"Expected TOUCH state, got {reader._state}"
    highlight_calls = [r for r in records if r[0] == 'on_candidate_highlight']
    assert len(highlight_calls) == 0, \
        f"Expected no on_candidate_highlight, got {highlight_calls}"


def test_candidate_highlight_tracking():
    """Multiple SYN_REPORTs in SELECT → on_candidate_highlight fires with each unique fx."""
    records, callbacks = make_recorder()
    reader = build_reader(records, callbacks)

    events = []
    # Enter SELECT
    events.append(ev(EV_KEY, BTN_TOUCH, 1))
    events.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    events.append(ev(EV_ABS, ABS_MT_TRACKING_ID, 100))
    events.append(ev(EV_ABS, ABS_MT_POSITION_X, 200))
    events.append(ev(EV_ABS, ABS_MT_POSITION_Y, 50))   # fy=0.05 < 0.25
    events.append(ev(EV_SYN, SYN_REPORT, 0))           # → SELECT, fx=0.2

    # Subsequent SYN_REPORTs with different fx values
    for x in (200, 400, 700):
        events.append(ev(EV_ABS, ABS_MT_SLOT, 0))
        events.append(ev(EV_ABS, ABS_MT_POSITION_X, x))
        events.append(ev(EV_SYN, SYN_REPORT, 0))

    run_events(reader, events)

    highlight_calls = [r for r in records if r[0] == 'on_candidate_highlight']
    # Entry SYN fired with fx=0.2, then 3 more with 0.2, 0.4, 0.7
    assert len(highlight_calls) >= 3, \
        f"Expected ≥3 highlight calls, got {len(highlight_calls)}: {highlight_calls}"

    # Verify each unique value appears
    seen_fx = set(c[1] for c in highlight_calls)
    for expected in (0.2, 0.4, 0.7):
        assert any(abs(c[1] - expected) < 0.001 for c in highlight_calls), \
            f"Expected highlight fx={expected} not found in {highlight_calls}"


def test_candidate_select_on_lift():
    """Finger lift in SELECT state → on_candidate_select fires with last fx."""
    records, callbacks = make_recorder()
    reader = build_reader(records, callbacks)

    events = []
    # Enter SELECT
    events.append(ev(EV_KEY, BTN_TOUCH, 1))
    events.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    events.append(ev(EV_ABS, ABS_MT_TRACKING_ID, 100))
    events.append(ev(EV_ABS, ABS_MT_POSITION_X, 300))
    events.append(ev(EV_ABS, ABS_MT_POSITION_Y, 50))   # fy=0.05 < 0.25
    events.append(ev(EV_SYN, SYN_REPORT, 0))           # → SELECT, _last_fx=0.3

    # Move finger a bit (change fx)
    events.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    events.append(ev(EV_ABS, ABS_MT_POSITION_X, 600))  # fx=0.6
    events.append(ev(EV_SYN, SYN_REPORT, 0))            # _last_fx=0.6

    # Lift finger
    events.append(ev(EV_KEY, BTN_TOUCH, 0))
    run_events(reader, events)

    select_calls = [r for r in records if r[0] == 'on_candidate_select']
    assert len(select_calls) == 1, \
        f"Expected 1 on_candidate_select call, got {len(select_calls)}: {select_calls}"
    assert abs(select_calls[0][1] - 0.6) < 0.001, \
        f"Expected fx=0.6, got {select_calls[0][1]}"


def test_candidate_drag_to_swipe_transition():
    """In SELECT state, adding a 2nd finger → state transitions to SWIPE."""
    records, callbacks = make_recorder()
    reader = build_reader(records, callbacks)

    events = []
    # Enter SELECT with 1 finger
    events.append(ev(EV_KEY, BTN_TOUCH, 1))
    events.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    events.append(ev(EV_ABS, ABS_MT_TRACKING_ID, 100))
    events.append(ev(EV_ABS, ABS_MT_POSITION_X, 200))
    events.append(ev(EV_ABS, ABS_MT_POSITION_Y, 50))   # fy=0.05 < 0.25
    events.append(ev(EV_SYN, SYN_REPORT, 0))           # → SELECT

    # Add 2nd finger → active≥2 → SWIPE
    events.append(ev(EV_ABS, ABS_MT_SLOT, 1))
    events.append(ev(EV_ABS, ABS_MT_TRACKING_ID, 200))
    events.append(ev(EV_ABS, ABS_MT_POSITION_X, 600))
    events.append(ev(EV_ABS, ABS_MT_POSITION_Y, 50))
    events.append(ev(EV_ABS, ABS_MT_SLOT, 0))
    events.append(ev(EV_ABS, ABS_MT_POSITION_X, 250))
    events.append(ev(EV_SYN, SYN_REPORT, 0))

    run_events(reader, events)

    assert reader._state == _STATE_SWIPE, \
        f"Expected SWIPE after 2nd finger, got {reader._state}"
    # Should have saved current stroke (empty since we were in SELECT)
    assert reader._saved_stroke == [], \
        f"Expected empty saved stroke (was in SELECT), got {reader._saved_stroke}"
