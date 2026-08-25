# 16-auto-pause-on-focus-loss - Work Plan

## TL;DR (For humans)
<!-- Fill this LAST, after the detailed plan below is written, so it summarizes the REAL plan. -->
<!-- Plain English for a non-engineer: NO file paths, NO todo numbers, NO wave/agent/tool names. -->

**What you'll get:** When you click Firefox's window title bar while the handwriting panel is visible, the panel will gracefully auto-pause (same as pressing ESC once). Click back into Firefox's input field and it auto-resumes. No more stuck panels.

**Why this approach:** IBus already fires a `do_focus_out` event when an app's input context loses focus — Firefox's web content loses keyboard focus when you click its title bar. The engine currently ignores this event. By making it auto-pause (stop trackpad, show "Paused" overlay) and auto-resume when focus returns, we fix the issue at the correct architectural layer with zero new dependencies.

**What it will NOT do:** Change any key handling (ESC, Enter, Backspace). Change the trackpad, window positioning, or GTK window behavior. Add any X11-specific code or global key grabs. Change test mode behavior. Affect text editors — they don't fire focus-out on title bar clicks, so they're unaffected.

**Effort:** Quick
**Risk:** Low — 2 short methods, 6 lines of new logic, 0 new dependencies
**Decisions to sanity-check:** Auto-resume in do_focus_in even for manually-paused panels (reasoning: returning to the input field is a clear intent to type)

Your next move: Approve execution (e.g. `$start-work`) to apply the fix. Full execution detail follows below.

---

> TL;DR (machine): Quick | Low | Add do_focus_out (auto-pause via on_key_esc) + do_focus_in (auto-resume via on_window_click logic) to HandwriteEngine. 1 file, ~10 lines added.

## Scope
### Must have
1. Implement `do_focus_out()` in `HandwriteEngine` to auto-pause (state 0→1) when IBus input context loses focus
2. Implement `do_focus_in()` in `HandwriteEngine` to auto-resume (state 1→0) when IBus input context regains focus
3. Add logging to both methods for diagnosability

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do NOT modify `HandwriteWin` class — only `HandwriteEngine` methods
- Do NOT modify `do_process_key_event` (already correct from Plan 15)
- Do NOT modify `on_key_esc`, `on_window_click`, or any existing state machine
- Do NOT modify trackpad, window, GTK, or `--test` mode code
- Do NOT add any X11-specific, global-key-grab, or timeout-based alternatives
- Do NOT modify packaging, CI, or documentation

## Verification strategy
> Zero human intervention for all automated checks. F4 (real IBus behavioral test) requires a running desktop session and is explicitly manual.
- Test decision: tests-after — syntax + structural checks via py_compile and grep; behavioral verification in F4 is manual-only (no IBus/X11 in CI)
- Evidence: .omo/evidence/task-1-16-auto-pause-on-focus-loss/

## Execution strategy
### Parallel execution waves
Single task — 1 file, 2 method changes.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| T1 | — | — | — |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [x] 1. Implement do_focus_out (auto-pause) + do_focus_in (auto-resume) in HandwriteEngine

  **File: `src/ibus-engine-handwrite-chinese`**

  **Change A — do_focus_out (line 1027-1028):**
  Replace the existing no-op:
  ```python
  def do_focus_out(self):
      pass
  ```
  With:
  ```python
  def do_focus_out(self):
      """Auto-pause when IBus input context loses focus (e.g., clicking Firefox title bar)."""
      if self.win and self.win.get_visible() and self.win._state == 0:
          self._write_log('do_focus_out: window visible, state=0 -> auto-pause')
          self.win.on_key_esc()
  ```

  **Change B — do_focus_in (add after do_focus_out, around line 1029):**
  Add new method:
  ```python
  def do_focus_in(self):
      """Auto-resume when IBus input context regains focus (e.g., clicking back into input field)."""
      if self.win and self.win.get_visible() and self.win._state == 1:
          self._write_log('do_focus_in: window visible, state=1 -> auto-resume')
          self.win._state = 0
          self.win.darea.queue_draw()
          if not self.win.start_trackpad():
              print("  [engine] ⚠ Trackpad re-grab failed after focus-in. Mouse fallback active.", file=sys.stderr)
          self.update_candidates()
  ```

  **What to do / Must NOT do:**
  - Only modify `HandwriteEngine` methods (do NOT touch `HandwriteWin`, `TestCommitEngine`, or `HandwriteEngine.on_key_esc`, `HandwriteEngine.do_process_key_event`, etc.)
  - `do_focus_out` must use existing `self.win.on_key_esc()` to trigger the standard pause path (state 0→1, stop trackpad, show "Paused" overlay)
  - `do_focus_in` must mimic `on_window_click()` (line 473-478) logic exactly: set state=0, queue_draw, start_trackpad, update_candidates
  - `do_focus_in` **must check the return value** of `start_trackpad()` and print a warning to stderr if it returns False (same pattern as `do_enable` line 988-989)
  - Both methods must guard on `self.win and self.win.get_visible()` and the relevant `_state` value to avoid action when panel is hidden or already in the target state
  - Use `self._write_log()` for diagnostic logging (same pattern as Plan 15)
  - Place the new `do_focus_in` method immediately after the rewritten `do_focus_out`, before `_check_engine`

  **References:**
  - `do_focus_out` current no-op: `src/ibus-engine-handwrite-chinese:1027-1028`
  - `on_key_esc()` (pause logic): `src/ibus-engine-handwrite-chinese:436-453`
  - `on_window_click()` (resume logic): `src/ibus-engine-handwrite-chinese:473-479`
  - `do_enable` with `start_trackpad()` warning pattern: `src/ibus-engine-handwrite-chinese:988-989`
  - `_write_log()`: `src/ibus-engine-handwrite-chinese:1022-1025`
  - `do_process_key_event` (confirming no change needed): `src/ibus-engine-handwrite-chinese:914-930`
  - `_check_engine` (polling, not focus-based): `src/ibus-engine-handwrite-chinese:1030-1038`

  **Acceptance criteria (agent-executable):**
  - `python3 -m py_compile src/ibus-engine-handwrite-chinese` — zero errors
  - `grep -n 'def do_focus_out' src/ibus-engine-handwrite-chinese` shows the method with non-trivial body (not `pass`)
  - `grep -n 'def do_focus_in' src/ibus-engine-handwrite-chinese` shows the method exists
  - `grep -A8 'def do_focus_in' src/ibus-engine-handwrite-chinese | grep -c 'start_trackpad'` equals 1
  - `grep -A8 'def do_focus_in' src/ibus-engine-handwrite-chinese | grep -c 'update_candidates'` equals 1

  **QA scenarios:**
  - Happy: Verify `do_focus_out` body calls `self.win.on_key_esc()` → run `sed -n '/def do_focus_out/,/^    def /p' src/ibus-engine-handwrite-chinese | grep 'on_key_esc'` — must match
  - Happy: Verify `do_focus_in` body sets `_state = 0` and calls `start_trackpad()` with return-value check → run `sed -n '/def do_focus_in/,/^    def /p' src/ibus-engine-handwrite-chinese | grep -c '_state = 0'` equals 1, and `grep -c 'not.*start_trackpad'` equals 1
  - Failure: Verify no crash when `self.win is None` → code has `self.win and` guard (inspect via `sed -n '/def do_focus_out/,/^    def /p' src/ibus-engine-handwrite-chinese`)
  - Failure: Verify no crash when `self.win.get_visible()` is False → guard prevents action (inspect same range)
  - Failure: Verify `do_focus_in` prints warning on trackpad failure → `sed -n '/def do_focus_in/,/^    def /p' src/ibus-engine-handwrite-chinese | grep 'start_trackpad'` shows `if not` pattern
  - Evidence dir: `.omo/evidence/task-1-16-auto-pause-on-focus-loss/`
  - Evidence files: `syntax-check.txt` (output of `python3 -m py_compile ...`), `code-review.txt` (output of grep/sed structural checks)

  **Commit:** Y | `fix: auto-pause on IBus focus-out, auto-resume on focus-in for Firefox title-bar ESC fix`

## Final verification wave
> F1-F3 are agent-executable. F4 is manual-only (requires real IBus + desktop session).
- [x] F1. Python syntax check — `python3 -m py_compile src/ibus-engine-handwrite-chinese` ✅
- [x] F2. Code review — confirm do_focus_out calls on_key_esc(), do_focus_in mirrors on_window_click(), `start_trackpad()` return value checked, guards in place, logging added ✅
- [x] F3. Scope fidelity — no changes outside the two HandwriteEngine methods (verify with `git diff`) ✅
- [ ] F4. [MANUAL] Test with `ibus engine handwrite-chinese` — ESC still pauses/closes, typing unaffected, paused overlay shows when focus lost on Firefox title bar click, auto-resumes when clicking back into input field

## Commit strategy
Single commit on main:
`fix: auto-pause on IBus focus-out, auto-resume on focus-in for Firefox title-bar ESC fix`

## Success criteria
- [x] `python3 -m py_compile src/ibus-engine-handwrite-chinese` — zero errors
- [x] `do_focus_out` calls `self.win.on_key_esc()` when window visible and state=0
- [x] `do_focus_in` sets state=0, queue_draw, start_trackpad, update_candidates when window visible and state=1
- [x] No changes to any file other than `src/ibus-engine-handwrite-chinese`
- [x] No changes to `HandwriteWin`, `TestCommitEngine`, `do_process_key_event`, or `on_key_esc`
