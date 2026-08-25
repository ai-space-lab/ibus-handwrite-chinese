---
slug: fix-esc-pause-no-focus
status: approved
intent: clear
review_required: true
pending-action: write-plan
approach: Keep accept_focus(True) for the session — remove timer, set accept_focus(True) before present() in do_enable inline, revert only in do_disable. This lets the GTK on_key handler catch ESC when no IBus input context exists.
momus-verdict: PASS ✅ — approach correct, do_focus_out guards prevent spurious auto-pause, no races. Minor: clarify do_disable block consolidation.
oracle-verdict: PASS ✅ — all 7 technical concerns resolved. Startup guard catches present()-triggered focus-out. Scenarios A (no focus) and B (text focus) both correct. No must-fix items.
---

# Draft: fix-esc-pause-no-focus

## Problem
When the user switches to Chinese Handwriting IME with no text field focused (e.g., Firefox title bar clicked), pressing ESC does NOT pause the panel:

1. No IBus input context exists → `do_process_key_event` never called (logged `do_focus_out` + `do_focus_in` but NO `do_pke`)
2. `set_accept_focus(False)` → WM won't give keyboard focus → GTK `on_key` handler never called
3. ESC reaches the focused non-text window (e.g., desktop/Firefox title bar) → swallowed → nothing happens

## Root cause (diagnosed 2026-07-07)
The previous fix (`_grab_focus_if_needed` with 50ms timer + `set_accept_focus(True)` → `present()` → immediate `set_accept_focus(False)`) failed because:

**The immediate `set_accept_focus(False)` revert (line 1015) happens before the WM processes the `present()` request.** The WM sees `accept_focus(False)` and denies the focus grant. The GTK `on_key` handler never fires.

Evidence from diagnostic (`cat /tmp/hw.log`):
```
126397 _grab_focus_if_needed: grabbing keyboard focus
126397 _grab_focus_if_needed: done
```
No `do_pke: keyval=65307` — IBus path blocked (no input context).
No `on_key_esc` — GTK path failed (WM denied focus).

Control test (xed text field focused) confirmed the IBus path works:
```
126397 do_pke: keyval=65307 state=0 visible=True
126397 on_key_esc: _state=0
```

## Fix (new approach)
Keep `accept_focus(True)` for the entire engine session. Remove the timer. Revert only in `do_disable`.

### Changes to `src/ibus-engine-handwrite-chinese`:

**1. `do_enable()` (around line 993-995):**
- Remove `self.win.present()` (the standalone call)
- Remove `GLib.timeout_add(50, self._grab_focus_if_needed)`
- Add inline: `self.win.set_accept_focus(True)` then `self.win.present()`
- `accept_focus` stays True for the session

```python
self.win.show_all()
self._position_window()
self.win.set_accept_focus(True)    # enable keyboard focus for GTK on_key
self.win.present()                  # present with focus capability
if not self.win.start_trackpad():
    ...
```

**2. Delete `_grab_focus_if_needed()` entirely (lines 1001-1017).**

**3. `do_disable()` (around line 1019+):**
Add before `self.win.hide()`:
```python
self.win.set_accept_focus(False)   # reset for next session
```

### Rationale
- **Matches `--test` mode behavior** (line 1195: `win.set_accept_focus(True)` + `win.present()`, no revert).
- **Keeps `accept_focus(True)` so the WM grants focus**, and the GTK `on_key` handler (connected at line 408) can catch ESC.
- **Reverts in `do_disable`** so the panel won't steal focus in future sessions.
- **Trade-off:** When a text field IS focused, the panel briefly steals keyboard focus when it appears. Same as `--test` mode. User clicks back to type.

## Scope IN
- `src/ibus-engine-handwrite-chinese`: 3 edits (do_enable, delete method, do_disable)

## Scope OUT
- No changes to `HandwriteWin`, `TestCommitEngine`, or any other class/file
- No changes to IBus lifecycle methods
- No changes to GTK window properties, CSS, or UI layout
- No new dependencies

## Review receipts (to be filled)
- [ ] Momus review
- [ ] Oracle review
