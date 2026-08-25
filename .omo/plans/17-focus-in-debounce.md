# 17-focus-in-debounce - Work Plan

## TL;DR (For humans)

**What you'll get:** Clicking Firefox's title bar while the handwriting panel is visible will now actually show the "Paused" overlay, instead of flickering back to active instantly.

**Why this approach:** `/tmp/hw.log` showed Firefox sends `do_focus_in` within microseconds of `do_focus_out` when clicking the title bar. The old code auto-resumed immediately, undoing the pause before it was visible. Adding a 300ms debounce gate in `do_focus_in` skips auto-resume when focus-in happens suspiciously fast (<300ms after focus-out). A genuine user returning (alt-tab, clicking back into field) always takes longer than 300ms.

**What it will NOT do:** Change any ESC/Enter/Backspace handling. Change normal auto-resume behavior when the user genuinely returns focus (>300ms after focus-out). Change anything in HandwriteWin, TestCommitEngine, or key event handling.

**Effort:** Quick
**Risk:** Low — 3 lines added, 1 file, `time` already imported
**Decisions to sanity-check:** 300ms threshold — should be long enough for Firefox glitch (<50ms), short enough for genuine focus-return (>300ms)

Your next move: Approve via `$start-work`. Full execution detail follows below.

---

> TL;DR (machine): Quick | Low | Add 300ms time gate in `do_focus_in` — skip auto-resume if `do_focus_in` fires within 300ms of `do_focus_out`. 3 changes in 1 file.

## Scope
### Must have
1. Add `self._last_focus_out_time = 0.0` to `HandwriteEngine.__init__`
2. Record `self._last_focus_out_time = time.time()` in `do_focus_out` when auto-pause triggers
3. Add time gate in `do_focus_in`: skip if `time.time() - self._last_focus_out_time < 0.3`

### Must NOT have (guardrails, anti-slop, scope boundaries)
- No changes to `HandwriteWin`, `TestCommitEngine`, or any other class
- No changes to key handling (`do_process_key_event`, `on_key_esc`, `on_window_click`)
- No changes to the ESC debounce (separate 150ms debounce, different concern)

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: none — verified by py_compile + grep structural checks + behavioral log analysis
- Evidence: .omo/evidence/task-1-17-focus-in-debounce/

## Execution strategy
### Parallel execution waves
Single task — 1 file, 3 precise edits.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| T1 | — | — | — |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [x] 1. Add 300ms debounce time gate in do_focus_in to prevent immediate auto-resume

  **File: `src/ibus-engine-handwrite-chinese`**

  **Change A — Add `_last_focus_out_time` to `HandwriteEngine.__init__` (line 874, after `self._engine_name = None`)**
  ```python
  self._engine_name = None
  self._last_focus_out_time = 0.0
  ```

  **Change B — Record timestamp in `do_focus_out` (add inside the guard, before `self.win.on_key_esc()`, around line 1030)**
  ```python
  if self.win and self.win.get_visible() and self.win._state == 0:
      self._last_focus_out_time = time.time()
      self._write_log('do_focus_out: window visible, state=0 -> auto-pause')
      self.win.on_key_esc()
  ```

  **Change C — Add 300ms time gate in `do_focus_in` (around line 1035)**
  BEFORE:
  ```python
  if self.win and self.win.get_visible() and self.win._state == 1:
  ```
  AFTER:
  ```python
  if self.win and self.win.get_visible() and self.win._state == 1 and (time.time() - self._last_focus_out_time) >= 0.3:
  ```

  **What to do / Must NOT do:**
  - Only modify `HandwriteEngine` class (NOT `HandwriteWin`, `TestCommitEngine`)
  - Do NOT change the 150ms ESC debounce (that's `_last_esc_time` in `HandwriteWin`, separate)
  - Do NOT change any other method or logic
  - `_last_focus_out_time = 0.0` ensures first-ever `do_focus_in` without prior focus-out is allowed (since `time.time() - 0.0` > 0.3)

  **References:**
  - `HandwriteEngine.__init__`: `src/ibus-engine-handwrite-chinese:862-873`
  - `do_focus_out` (add timestamp): `src/ibus-engine-handwrite-chinese:1027-1031`
  - `do_focus_in` (add time gate): `src/ibus-engine-handwrite-chinese:1033-1041`
  - `time` is already imported at line 5

  **Acceptance criteria (agent-executable):**
  - `python3 -m py_compile src/ibus-engine-handwrite-chinese` — zero errors
  - `grep '_last_focus_out_time' src/ibus-engine-handwrite-chinese` — found in 3 places (init, do_focus_out, do_focus_in)
  - `grep '_last_focus_out_time = 0.0' src/ibus-engine-handwrite-chinese` — init has it
  - `grep '_last_focus_out_time = time.time()' src/ibus-engine-handwrite-chinese` — do_focus_out has it
  - `grep '_last_focus_out_time' src/ibus-engine-handwrite-chinese | grep '0.3\|>= 0.3\|>=0.3'` — do_focus_in has the gate

  **QA scenarios:**
  - Happy: Trace that `_last_focus_out_time` is set in `do_focus_out` before `on_key_esc()` call
  - Happy: Trace that `do_focus_in` gate checks `(time.time() - self._last_focus_out_time) >= 0.3` — rapid focus-in skipped, delayed focus-in allowed
  - Failure: Verify first-ever `do_focus_in` without prior focus-out works (`_last_focus_out_time = 0.0` means `time.time() - 0.0 > 0.3` for any real time since epoch)
  - Evidence: `.omo/evidence/task-1-17-focus-in-debounce/`

  **Commit:** Y | `fix: add 300ms debounce gate in do_focus_in to prevent immediate auto-resume after focus-out`

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Python syntax check — `python3 -m py_compile src/ibus-engine-handwrite-chinese`
- [ ] F2. Code review — confirm time gate added, timestamp recorded in do_focus_out, init variable present
- [ ] F3. Behavioral check — check `/tmp/hw.log` after testing: `do_focus_out` fires, `do_focus_in` no longer immediately follows
- [ ] F4. Scope fidelity — no changes outside the three planned locations

## Commit strategy
Single commit on main:
`fix: add 300ms debounce gate in do_focus_in to prevent immediate auto-resume after focus-out`

## Success criteria
- [ ] `python3 -m py_compile src/ibus-engine-handwrite-chinese` — zero errors
- [ ] `_last_focus_out_time` initialized in `__init__`
- [ ] `do_focus_out` records timestamp before calling `on_key_esc()`
- [ ] `do_focus_in` checks `time.time() - self._last_focus_out_time >= 0.3` before auto-resuming
- [ ] No changes to any file other than `src/ibus-engine-handwrite-chinese`
- [ ] No changes to `HandwriteWin`, `TestCommitEngine`, key handling, or ESC debounce
