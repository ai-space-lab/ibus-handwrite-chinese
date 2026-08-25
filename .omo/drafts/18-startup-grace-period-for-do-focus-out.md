---
slug: 18-startup-grace-period-for-do-focus-out
status: ready
intent: clear
pending-action: none
implemented: true
committed: true
pushed: true
commit: 70defeb
dual-review-passed: true
momus-verdict: OKAY — code correct, complete, resilient. Minor: init is HandwriteEngine (not HandwriteWin), no impact
oracle-verdict: OKAY — all 8 edge case questions resolved. No race conditions, no logic errors

## Actual fix applied
The 1s time-based guard was insufficient — `do_focus_out` arrives ~26s after `do_enable`, not ms.
Fix: `_has_drawn` flag — skip auto-pause until user draws first stroke.
Reset `_has_drawn = False` in `__init__` and `do_enable`.
Set `_has_drawn = True` in stroke handlers (on_trackpad_end, on_btn_up).
Guard in `do_focus_out`: `if not self._has_drawn: return` before auto-pause block.
dual-review-passed: true
momus-verdict: OKAY — plan precise, references verified, no blockers
oracle-verdict: OKAY — no race conditions, no logic errors, debounce interactions resolved. Optional: add debug log inside guard, use time.monotonic() (non-blocking)
approach: Add 1-second startup grace period in do_focus_out — skip auto-pause if engine was enabled <1s ago
---

# Draft: 18-startup-grace-period-for-do-focus-out

## Problem
When the user switches to Chinese Handwriting IME after clicking a window's title bar (or Alt-Tabbing away), IBus sends `do_focus_out` immediately after `do_enable` because no text field has focus. This triggers auto-pause before the user can even see the active panel. Additionally, an ESC key event (from the IME switch hotkey) then closes the window entirely — the user never gets to use the panel.

## Fix
Add a 1-second startup grace period: skip the auto-pause in `do_focus_out` if the engine was enabled less than 1 second ago.

## Changes (3 lines in 1 file: `src/ibus-engine-handwrite-chinese`)

**Change A — Init `_last_enable_time`** (line ~875, next to `_last_focus_out_time`):
```python
self._last_focus_out_time = 0.0
self._last_enable_time = 0.0
```

**Change B — Record enable timestamp** (in `do_enable`, line ~974, after `self._write_log('do_enable')`):
```python
def do_enable(self):
    self._write_log('do_enable')
    self._last_enable_time = time.time()
    ...
```

**Change C — Add startup guard** (in `do_focus_out`, before the auto-pause block):
```python
def do_focus_out(self):
    """Auto-pause when IBus input context loses focus (e.g., clicking Firefox title bar)."""
    if time.time() - self._last_enable_time < 1.0:
        return
    if self.win and self.win.get_visible() and self.win._state == 0:
        ...
```

## Rationale
- 1 second is long enough to distinguish startup from genuine focus loss
- After 1s, the user has had time to interact with the panel — a focus loss is genuine
- The ESC key then pauses (state 0→1) instead of closing (state 1→close), which is the correct behavior

## Scope IN
- `__init__`: add `self._last_enable_time = 0.0`
- `do_enable`: add `self._last_enable_time = time.time()`
- `do_focus_out`: add startup guard `if time.time() - self._last_enable_time < 1.0: return`

## Scope OUT
- No changes to `do_focus_in`, `do_process_key_event`, or the ESC debounce
- No changes to `HandwriteWin`, `TestCommitEngine`
