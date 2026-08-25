# fix-desktop-esc-and-window-jump - Work Plan

## TL;DR (For humans)

**What you'll get:** The handwrite window will stop jumping to the bottom-right corner of the screen when you click on the desktop then activate handwriting, or when you Alt+Tab away from a text field and click back. ESC will work reliably because the window stays where it belongs — near the cursor or near the text field you were using.

**Why this approach:** Two tiny targeted guards — one that ignores a "zeroed cursor position" signal from IBus (which fires when you leave a text field), and one that tells the window "if we're already the active window, stay put." Both are 2-3 line changes that fix the root causes without touching anything else.

**What it will NOT do:** Change how ESC works, change how focus grabbing works, change trackpad behavior, or touch anything outside the two positioning functions.

**Effort:** Quick
**Risk:** Low — two single-line guards in one file, both reversible
**Decisions to sanity-check:** (1) Treating cursor (0,0) as "unknown" is correct for IBus. (2) Keeping window position when we're already the active window is always right.

Your next move: approve this plan. Full execution detail follows below.

---

> TL;DR (machine): Quick, Low — two guard conditions in `_position_window()` and `do_set_cursor_location()` fix window-jumping-to-bottom-right and restore ESC reliability.

## Scope
### Must have
1. Guard `do_set_cursor_location()` against zeroed cursor (x=0,y=0) — skip `_position_window()` call
2. Fix `_position_window()` when `active == our_gdk_win` — return early (keep position)
3. Fix `_position_window()` when `active is None` — use `self._cx/self._cy` cursor location if available, bottom-right only as first-show fallback
4. Verify via GTK window position check + xdotool ESC test

### Must NOT have (guardrails, anti-slop, scope boundaries)
- No changes to ESC handling (`on_key_esc`, `do_process_key_event`, `on_key`)
- No changes to `_grab_focus_if_needed()`, `do_enable()`, `do_focus_in()`, `do_focus_out()`
- No changes to evdev, GTK drawing, recognition, packaging, CI
- No refactoring beyond the two targeted function modifications

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after — verify via GTK window position checks + xdotool key simulation (same methodology as fix-candidate-tap-regression)
- Evidence: .omo/evidence/fix-desktop-esc-and-window-jump/test-results.txt

## Execution strategy
### Parallel execution waves
Wave 1: Apply both code fixes (single file, two locations). Then test.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. Apply fixes | — | 2. Verify | — |
| 2. Verify | 1. Apply fixes | — | — |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->

- [ ] 1. Apply two-position fix in ibus-engine-handwrite-chinese
  **What to do / Must NOT do:**
  Apply exactly TWO changes to `src/ibus-engine-handwrite-chinese`:

  **Change A — `do_set_cursor_location()` guard (line 938-944):**
  Change from:
  ```python
  def do_set_cursor_location(self, x, y, w, h):
      self._cx = x
      self._cy = y
      self._cw = w
      self._ch = h
      if self.win and self.win.get_visible():
          self._position_window()
  ```
  To:
  ```python
  def do_set_cursor_location(self, x, y, w, h):
      self._cx = x
      self._cy = y
      self._cw = w
      self._ch = h
      if self.win and self.win.get_visible() and (x > 0 or y > 0):
          self._position_window()
  ```
  Rationale: IBus sends (0,0,0,0) after `do_focus_out` (focus loss). Repositioning with zeroed cursor data is always wrong — don't do it.

  **Change B — `_position_window()` fallback (line 946-976):**
  Change from:
  ```python
  def _position_window(self):
      if not self.win:
          return
      screen = Gdk.Screen.get_default()
      display = screen.get_display()
      win_w = 400
      win_h = self.win.get_allocated_height() or 370
      our_gdk_win = self.win.get_window()
      active = screen.get_active_window()
      if active is None or active == our_gdk_win:
          mon = display.get_primary_monitor()
          wa = mon.get_workarea()
          wx = wa.x + wa.width - win_w - 12
          wy = wa.y + wa.height - win_h - 12
          self.win.move(int(wx), int(wy))
          return
      rect = active.get_frame_extents()
      ...
  ```
  To:
  ```python
  def _position_window(self):
      if not self.win:
          return
      screen = Gdk.Screen.get_default()
      display = screen.get_display()
      win_w = 400
      win_h = self.win.get_allocated_height() or 370
      our_gdk_win = self.win.get_window()
      active = screen.get_active_window()
      if active is None:
          # No active window (desktop focused). Position near cursor if available.
          if self._cx > 0 or self._cy > 0:
              mon = display.get_primary_monitor()
              wa = mon.get_workarea()
              wx = min(self._cx, wa.x + wa.width - win_w - 12)
              wy = min(self._cy + 30, wa.y + wa.height - win_h - 12)
              wx = max(wx, wa.x)
              wy = max(wy, wa.y)
              self.win.move(int(wx), int(wy))
              return
          # First-show fallback: bottom-right of primary monitor
          mon = display.get_primary_monitor()
          wa = mon.get_workarea()
          wx = wa.x + wa.width - win_w - 12
          wy = wa.y + wa.height - win_h - 12
          self.win.move(int(wx), int(wy))
          return
      if active == our_gdk_win:
          # User clicked on our window — keep current position
          return
      rect = active.get_frame_extents()
      ...
  ```

  **Must NOT do:** Change any other function, add any new imports, refactor variable names, change indentation style, touch docstrings, or modify anything outside these two function blocks.
  
  **Parallelization:** Wave 1 | Blocked by: — | Blocks: Todo 2
  **References (executor has NO interview context - be exhaustive):**
  - `src/ibus-engine-handwrite-chinese:938-944` — `do_set_cursor_location()`
  - `src/ibus-engine-handwrite-chinese:946-976` — `_position_window()` with fallback at 955-960
  - `src/ibus-engine-handwrite-chinese:871-872` — `_cx=0, _cy=0` init
  - `.omo/drafts/fix-desktop-esc-and-window-jump.md` — Findings section with confirmed root causes
  - `.omo/evidence/fix-candidate-tap-regression/test-results.txt` — Prior test methodology (xdotool-based)
  - `tests/test_esc_key_routing.py` — Prior automated ESC test (run as sanity check)
  - Verification commands:
    ```bash
    git diff --check
    python3 -c "compile(open('src/ibus-engine-handwrite-chinese').read(), 'engine', 'exec')"
    ```
  **Acceptance criteria (agent-executable):**
  1. `grep -n 'x > 0 or y > 0' src/ibus-engine-handwrite-chinese` returns a match in `do_set_cursor_location`
  2. `grep -n 'active == our_gdk_win' src/ibus-engine-handwrite-chinese` shows the return-before-move guard
  3. `grep -n 'self._cx > 0' src/ibus-engine-handwrite-chinese` shows the cursor-location check in the `active is None` branch
  4. Python syntax check passes: `python3 -c "compile(open('src/ibus-engine-handwrite-chinese').read(), 'engine', 'exec')"` → no SyntaxError
  **QA scenarios (name the exact tool + invocation):**
  - Happy path: `grep -n -E '(x > 0 or y > 0|active == our_gdk_win|self._cx > 0)' src/ibus-engine-handwrite-chinese` shows all three guards present
  - Compile check: `python3 -c "compile(open('src/ibus-engine-handwrite-chinese').read(), 'engine', 'exec')"` exits 0
  - Evidence: `.omo/evidence/fix-desktop-esc-and-window-jump/code-fix-verification.txt`
  **Commit:** N (single commit after verification)

- [ ] 2. Verify fix via xdotool simulation
  **What to do / Must NOT do:**
  Run the same xdotool-based test script used for fix-candidate-tap-regression to verify:
  (a) Window does NOT jump to bottom-right when activating on desktop
  (b) Window does NOT jump when Alt+Tabbing away and clicking to resume
  (c) ESC still works in both scenarios

  Test procedure (adapt from .omo/evidence/fix-candidate-tap-regression/test-results.txt):
  1. Ensure engine is installed and IBus is running
  2. Clear /tmp/hw.log
  3. Click desktop (xdotool search --desktop 0 . windowfocus)
  4. Enable engine: `ibus engine handwrite-chinese`
  5. Sleep 2s
  6. Capture window position: `xdotool getwindowgeometry $(xdotool search --name "Chinese Handwriting")`
  7. Verify window is NOT at bottom-right (not at x>1800 or y>1000 for 1920×1200 display)
  8. Send ESC: `xdotool key Escape`
  9. Verify ESC logged: `grep "on_key_esc: _state=0" /tmp/hw.log`
  10. Activate terminal with text field, enable engine
  11. Alt+Tab away: `xdotool key alt+Tab` (or use wmctrl)
  12. Click on our window: `xdotool search --name "Chinese Handwriting" windowactivate`
  13. Verify window position did NOT jump to bottom-right
  14. Check /tmp/hw.log for `do_set_cursor_location` with zero values NOT triggering _position_window

  **Must NOT do:** Any code changes, any changes to test infrastructure

  **Parallelization:** Wave 1 | Blocked by: Todo 1 | Blocks: —
  **References (executor has NO interview context - be exhaustive):**
  - `.omo/evidence/fix-candidate-tap-regression/test-results.txt` — Prior test script methodology
  - `src/ibus-engine-handwrite-chinese:938-944` — do_set_cursor_location guard
  - `src/ibus-engine-handwrite-chinese:946-976` — _position_window fallback fix
  - Previous session findings: window jump confirmed at (2148, 1185) on 1920×1200
  **Acceptance criteria (agent-executable):**
  1. Window position after desktop-activate is NOT bottom-right (not at x/y > 80% of screen dimensions)
  2. `grep "on_key_esc: _state=0" /tmp/hw.log` returns match for ESC test
  3. Window position after click-to-resume from Alt+Tab is NOT bottom-right
  4. `grep "do_set_cursor_location.*0.*0.*0.*0" /tmp/hw.log` shows no call to `_position_window()` after focus-loss
  **QA scenarios (name the exact tool + invocation):**
  - Happy path A: Desktop activate → window at reasonable position (not bottom-right) → ESC works
  - Happy path B: Alt+Tab → click our window → window stays put → ESC works
  - Failure: If window jumps to bottom-right, capture full xdotool geometry output as evidence
  - Evidence: `.omo/evidence/fix-desktop-esc-and-window-jump/test-results.txt`
  **Commit:** Y | `fix: prevent handwrite window from jumping to bottom-right on desktop activation and focus resume`

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit — verify only the two specified functions were changed (grep for any other diffs)
- [ ] F2. Code quality review — check for SyntaxError, style consistency with surrounding code
- [ ] F3. Real manual QA — run the full test sequence via xdotool + read /tmp/hw.log
- [ ] F4. Scope fidelity — confirm no changes to `_grab_focus_if_needed`, `do_enable`, `do_focus_in/out`, ESC handling, evdev, or any other module

## Commit strategy
Single commit after Todo 2 verification passes, with message:
```
fix: prevent handwrite window from jumping to bottom-right on desktop activation and focus resume

- Guard do_set_cursor_location() against zeroed cursor (IBus focus-loss signal)
- Fix _position_window() fallback: keep position when our window is active,
  use cursor location when desktop is focused, bottom-right only as first-show
- ESC reliability restored as secondary effect of proper window positioning

Fixes two scenarios:
1. Click desktop → enable engine → window at (2148, 1185) on 1920×1200
2. Alt+Tab → click our window → window jumps to bottom-right
```

Push to `origin/main` after commit.

## Success criteria
1. Window does NOT jump to bottom-right on desktop → activate-engine
2. Window does NOT jump on Alt+Tab → click-to-resume
3. ESC works reliably in both scenarios
4. Only two functions modified: `do_set_cursor_location()` and `_position_window()`
5. All existing behavior preserved (candidate taps, text field ESC, trackpad input)
