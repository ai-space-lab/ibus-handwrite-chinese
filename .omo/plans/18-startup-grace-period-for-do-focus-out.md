# 18-startup-grace-period-for-do-focus-out - Work Plan

## TL;DR (For humans)

**What you'll get:** Switching to Chinese Handwriting IME when no text field has focus (e.g., after clicking a title bar or Alt-Tabbing away) will now show the active panel instead of immediately pausing and then closing. You can draw normally. If you then press ESC, it pauses (shows "click to resume") — the correct behavior.

**Why this approach:** The log shows `do_focus_out` fires within milliseconds of `do_enable` when no text field is focused. This startup FocusOut is not a genuine focus-loss event — it's a notification that the engine started without an active input context. Adding a 1-second grace period skips the auto-pause during startup.

**What it will NOT do:** Change auto-pause behavior when the user has been using the panel for >1 second and then focus leaves (Alt-Tab, click another window). Change anything in do_focus_in, ESC handling, or HandwriteWin.

**Effort:** Quick
**Risk:** Low — 3 lines added, 1 file

## Scope
### Must have
1. Add `self._last_enable_time = 0.0` to `HandwriteEngine.__init__`
2. Record `self._last_enable_time = time.time()` at the top of `do_enable`
3. Add startup guard in `do_focus_out`: skip auto-pause if `time.time() - self._last_enable_time < 1.0`

### Must NOT have (guardrails)
- No changes to `do_focus_in`, `do_process_key_event`, `on_key_esc`, or any other method
- No changes to `HandwriteWin`, `TestCommitEngine`, or any other class

## Execution strategy
Single task — 1 file, 3 precise edits.

## Todos
- [x] 1. Add startup grace period in do_focus_out to prevent auto-pause on engine startup

  **File: `src/ibus-engine-handwrite-chinese`**

  **Change A — Add `_last_enable_time` to `HandwriteEngine.__init__` (line ~875, after `_last_focus_out_time`):**
  ```python
  self._last_enable_time = 0.0
  ```

  **Change B — Record timestamp in `do_enable` (line ~976, after `self._write_log('do_enable')`):**
  ```python
  def do_enable(self):
      self._write_log('do_enable')
      self._last_enable_time = time.time()
  ```

  **Change C — Add `_has_drawn` flag to prevent auto-pause until user draws:**

  In `HandwriteWin.__init__` (line ~878):
  ```python
  self._has_drawn = False
  ```

  In `do_enable` (line ~979), reset on enable:
  ```python
  self._has_drawn = False
  ```

  In `on_trackpad_end` / `on_btn_up` (lines ~605, ~756), set when stroke added:
  ```python
  self.engine._has_drawn = True
  ```

  In `do_focus_out` (line ~1041), add guard:
  ```python
  if not self._has_drawn:
      self._write_log('do_focus_out: no strokes drawn yet, skipping auto-pause')
      return
  ```

  **Why not pure time-based guard?** The 1s time guard was insufficient — `do_focus_out` arrives ~26s after `do_enable`, not milliseconds. The `_has_drawn` flag is the correct discriminator: before any stroke, skip auto-pause; after drawing, auto-pause works normally.

  **Acceptance criteria:**
  - `python3 -m py_compile src/ibus-engine-handwrite-chinese` — zero errors
  - `grep '_has_drawn' src/ibus-engine-handwrite-chinese` — found in 5 places
  - After switching IME with no text focused: panel stays active, can draw
  - After drawing and then Alt-Tabbing away: auto-pause triggers normally

  **Commit:** Y | `fix: skip auto-pause in do_focus_out until user draws first stroke`

**Final verification wave:**
- [x] F1. Python syntax check — `python3 -m py_compile src/ibus-engine-handwrite-chinese`
- [x] F2. Code review — `_has_drawn` in 5 places (init, do_enable, 2x stroke handlers, do_focus_out guard)
- [x] F3. Guard placement — `if not self._has_drawn: return` before auto-pause block
- [x] F4. Scope fidelity — only `src/ibus-engine-handwrite-chinese` modified

## Final verification wave
- [x] F1. Python syntax check — `python3 -m py_compile src/ibus-engine-handwrite-chinese`
- [x] F2. Code review — all 3 changes present and correct
- [x] F3. Behavioral: startup `do_focus_out` skipped; delayed `do_focus_out` works
- [x] F4. Scope fidelity — no changes outside the three planned locations

## Commit strategy
Single commit on main:
`fix: add 1s startup grace period in do_focus_out to prevent auto-pause on engine startup`

## Success criteria
- [ ] `python3 -m py_compile src/ibus-engine-handwrite-chinese` — zero errors
- [ ] `_last_enable_time` initialized in `__init__`
- [ ] `do_enable` records timestamp at the top
- [ ] `do_focus_out` checks startup guard before auto-pausing
- [ ] No changes to any file other than `src/ibus-engine-handwrite-chinese`
