# fix-esc-pause-no-focus - Work Plan

## TL;DR (For humans)

**What you'll get:** Pressing ESC while the handwriting panel is active will pause it (state 0→1, show "Paused" overlay) even when no text field has focus — e.g., Firefox title bar, desktop, or any non-text-input area.

**Why this approach:** ESC can reach the engine via two paths. The IBus path (`do_process_key_event`) only works when a text-entry widget is focused (IBus input context exists). The GTK path (`on_key` handler) requires the panel to have keyboard focus, but it was prevented by `set_accept_focus(False)`. The previous timer-based fix attempted a brief focus grab but reverted `accept_focus(False)` before the WM processed it — logs proved the grab ran but GTK `on_key` never fired. This fix removes the timer entirely: set `accept_focus(True)` before `present()` in `do_enable` and keep it True for the session, matching exactly what `--test` mode does (where ESC already works). Revert to `False` only in `do_disable`.

**What it will NOT do:** Change auto-pause/resume behavior (`do_focus_out`/`do_focus_in`). Change ESC behavior when a text field IS focused (ESC still works via IBus `do_process_key_event`). Change Enter/Backspace handling. Add any UI elements. Modify `HandwriteWin`, `TestCommitEngine`, or any other class.

**Trade-off:** When a text field IS focused, the panel briefly steals keyboard focus when it appears (same as `--test` mode). The user clicks back to type. The `do_focus_out` startup guard (elapsed < 1s since `do_enable`) and `_has_drawn` guard prevent spurious auto-pause during activation.

**Reviews:** Momus PASS ✅ (Oracle PASS ✅ — both confirm no must-fix items.

**Effort:** Quick — 1 file, 3 edits
**Risk:** Low — identical to working `--test` mode behavior

## Scope

### Must have
1. `do_enable()` (lines 992-995): Replace `show_all()` + `_position_window()` + `present()` + `timeout_add(50, ...)` with `show_all()` + `_position_window()` + `set_accept_focus(True)` + `present()` — synchronous focus grant, no timer
2. `_grab_focus_if_needed()` (lines 1001-1017): Delete entirely — no longer needed
3. `do_disable()` (lines 1026-1027): Add `self.win.set_accept_focus(False)` before `self.win.hide()` — reset for next session

### Must NOT have (guardrails)
- No changes to `HandwriteWin`, `TestCommitEngine`, or any other class/file
- No changes to `do_process_key_event`, `on_key`, `on_key_esc`, or other keyboard handlers
- No changes to auto-pause/resume logic (`do_focus_out`/`do_focus_in`)
- No changes to any file outside `src/ibus-engine-handwrite-chinese`
- No new dependencies

## Verification strategy

1. **Compile check:** `python3 -m py_compile src/ibus-engine-handwrite-chinese` — zero errors
2. **Structural check:** Confirm `_grab_focus_if_needed` no longer exists, `set_accept_focus` is called in `do_enable` and `do_disable`
3. **Functional — no text focus:** Activate engine → click desktop/Firefox title bar → press ESC → panel pauses (Paused overlay, trackpad ungrabbed, trackpad cursor restored)
4. **Regression — text field focus:** Activate engine from text field → press ESC → panel pauses (via IBus `do_process_key_event` path, existing behavior)
5. **Regression — auto-pause:** After drawing strokes, Alt-Tab away → auto-pause still triggers normally via `do_focus_out`

## Execution strategy

Single implementation task: 3 edits in 1 file. Then reinstall with `sudo ./tools/install.sh` and test.

## Todos

- [ ] 1. Implement the 3 changes in `src/ibus-engine-handwrite-chinese`

  **File:** `src/ibus-engine-handwrite-chinese`

  **Change 1 — `do_enable()` around line 992:**
  ```python
  # BEFORE:
          self.win.show_all()
          self._position_window()
          self.win.present()
          GLib.timeout_add(50, self._grab_focus_if_needed)
  # AFTER:
          self.win.show_all()
          self._position_window()
          self.win.set_accept_focus(True)
          self.win.present()
  ```

  **Change 2 — Delete `_grab_focus_if_needed()` (lines 1001-1017):**
  Remove the entire method definition and its docstring.

  **Change 3 — `do_disable()` around line 1026:**
  ```python
  # BEFORE:
      if self.win:
          self.win.hide()
  # AFTER:
      if self.win:
          self.win.set_accept_focus(False)
          self.win.hide()
  ```

  **Acceptance criteria:**
  - `python3 -m py_compile src/ibus-engine-handwrite-chinese` — zero errors
  - `grep '_grab_focus_if_needed' src/ibus-engine-handwrite-chinese` — 0 matches (method deleted)
  - `grep 'set_accept_focus' src/ibus-engine-handwrite-chinese` — 3 matches (init False, do_enable True, do_disable False)
  - Log shows `do_pke:` for text-field ESC but `on_key_esc:` for no-focus ESC (via GTK path)

  **Commit:** N | (single commit at end)

- [ ] 2. Install and test

  **Steps:**
  ```bash
  sudo ./tools/install.sh --skip-deps
  ibus restart
  ```

  **Manual tests:**
  1. No text focus: Click Firefox title bar → activate Chinese HW → press ESC → panel pauses ✅
  2. Text field focus: Click text field → activate Chinese HW → press ESC → panel pauses ✅
  3. Auto-pause regression: Draw strokes → Alt-Tab → auto-pause triggers ✅

  **Commit:** Y | `fix: keep accept_focus(True) for session so GTK on_key catches ESC when no IBus context exists`

## Final verification wave

- [ ] F1. **Plan compliance audit** — all 3 changes present, no unplanned modifications
- [ ] F2. **Python syntax** — `python3 -m py_compile src/ibus-engine-handwrite-chinese` ✅
- [ ] F3. **Manual QA** — Both scenarios tested and verified
- [ ] F4. **Scope fidelity** — only `src/ibus-engine-handwrite-chinese` modified

## Commit strategy

Single commit: `fix: keep accept_focus(True) for session so GTK on_key catches ESC when no IBus context exists`

## Success criteria

- [x] `python3 -m py_compile src/ibus-engine-handwrite-chinese` — zero errors
- [ ] `grep '_grab_focus_if_needed'` — 0 matches (deleted)
- [ ] `grep 'set_accept_focus'` — 3 matches: `False` in `__init__`, `True` in `do_enable`, `False` in `do_disable`
- [ ] User test: no-text scenario → ESC pauses (in real IBus session)
- [ ] User test: text-field scenario → ESC pauses (regression check)
- [ ] No changes to any file other than `src/ibus-engine-handwrite-chinese`
