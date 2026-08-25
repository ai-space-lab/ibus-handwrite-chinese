# 15-firefox-esc-not-working - Work Plan

## TL;DR (For humans)
<!-- Fill this LAST, after the detailed plan below is written, so it summarizes the REAL plan. -->
<!-- Plain English for a non-engineer: NO file paths, NO todo numbers, NO wave/agent/tool names. -->

**What you'll get:** ESC key will pause/close the handwriting panel even when typing in Firefox (currently works in terminal/text editors but not Firefox).

**Why this approach:** Firefox sends ESC key events differently through IBus (possibly with RELEASE_MASK set). The current `do_process_key_event` checks for RELEASE_MASK before reaching the ESC handler, bypassing it entirely. Moving the ESC check before the RELEASE_MASK filter and adding a 300ms debounce fixes it — safe change with no side effects for other applications.

**What it will NOT do:** Change any other key handling (Backspace, Enter still use RELEASE_MASK filter). No changes to Firefox config, GTK settings, or IBus configuration. No changes to trackpad, window positioning, candidate display, or any other engine functionality.

**Effort:** Quick
**Risk:** Low — 2 variables + 2 code lines changed, ESC only fires when window is visible
**Decisions to sanity-check:** Debounce threshold (150ms — Oracle review: 300ms too conservative, may swallow rapid double-ESC)

Your next move: Approve the plan, then I'll implement. Execution detail follows below.

---

> TL;DR (machine): Quick | Low | Move ESC check before RELEASE_MASK filter in do_process_key_event + add 300ms debounce in on_key_esc. 1 file, 4 lines changed.

## Scope
### Must have
1. Move ESC check (`IBUS.KEY_Escape`) before the RELEASE_MASK filter in `do_process_key_event` — so ESC is handled regardless of press/release
2. Add `_last_esc_time` variable in `__init__` for debounce tracking
3. Add time-based debounce (150ms) in `on_key_esc()` to prevent double-fire from press+release events (Oracle review: 300ms too conservative, may swallow rapid double-ESC)
4. **Diagnostic**: Before fixing, check `/tmp/hw.log` for `do_pke: keyval=65307` when pressing ESC in Firefox — confirms whether `do_process_key_event` receives the event at all
5. Verify engine still works: ESC pauses (state 0→1), ESC again closes (state 1→exit), Enter/Backspace/typing unaffected

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do NOT change Backspace/Enter handling (they stay after RELEASE_MASK filter with `_state == 0` guard)
- Do NOT change the `on_key()` GTK handler (used only by `--test` mode)
- Do NOT change window visibility logic, state machine, trackpad, or any other feature
- Do NOT change packaging, CI, or documentation

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: none (no test framework; verified by py_compile + manual assertion)
- Evidence: .omo/evidence/task-1-15-firefox-esc-not-working.md

## Execution strategy
### Parallel execution waves
Single task — one file, 3 code changes.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| T1 | — | — | — |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [x] 1. Fix ESC handling in `do_process_key_event` + add debounce to `on_key_esc`
  
  **File: `src/ibus-engine-handwrite-chinese`**
  
  **Change A — add `_last_esc_time` variable** (after line 389 `self._last_redraw = 0.0`):
  ```python
  self._last_esc_time = 0.0
  ```
  
  **Change B — add debounce to `on_key_esc`** (at the start of the function, line 435):
  ```python
  def on_key_esc(self):
      now = time.time()
      if now - self._last_esc_time < 0.15:  # 150ms debounce (Oracle recommendation)
          return
      self._last_esc_time = now
      self._write_log('on_key_esc: _state=%d' % self._state)
      ...
  ```
  
  **Change C — move ESC before RELEASE_MASK** in `do_process_key_event` (lines 909-916):
  
  BEFORE:
  ```python
  def do_process_key_event(self, keyval, keycode, state):
      self._write_log('do_pke: keyval=%d state=%d visible=%s' % (keyval, state, str(self.win.get_visible() if self.win else False)))
      if state & IBus.ModifierType.RELEASE_MASK:
          return super(HandwriteEngine, self).do_process_key_event(keyval, keycode, state)
      if keyval in (IBus.KEY_Escape,) and self.win and self.win.get_visible():
          self.win.on_key_esc()
          return True
      if keyval in (IBus.KEY_BackSpace, IBus.KEY_Return) and self.win and self.win.get_visible() and self.win._state == 0:
  ```
  
  AFTER:
  ```python
  def do_process_key_event(self, keyval, keycode, state):
      self._write_log('do_pke: keyval=%d state=%d visible=%s' % (keyval, state, str(self.win.get_visible() if self.win else False)))
      # Handle ESC on press OR release — Firefox may send release-only events
      if keyval in (IBus.KEY_Escape,) and self.win and self.win.get_visible():
          self.win.on_key_esc()
          return True
      # Skip release events for all other keys
      if state & IBus.ModifierType.RELEASE_MASK:
          return super(HandwriteEngine, self).do_process_key_event(keyval, keycode, state)
      if keyval in (IBus.KEY_BackSpace, IBus.KEY_Return) and self.win and self.win.get_visible() and self.win._state == 0:
  ```
  
  **Verification:**
  - `python3 -m py_compile src/ibus-engine-handwrite-chinese` passes with zero errors
  - `ibus engine handwrite-chinese` starts without crash
  - ESC pauses panel (state 0→1) in terminal — still works
  - ESC again closes panel (state 1→exit) — still works
  - Typing (Enter/Backspace/letters) still works as before
  - Rapid double-ESC press doesn't skip pause state (debounce prevents double-fire)
  
  References: `src/ibus-engine-handwrite-chinese:392`, `src/ibus-engine-handwrite-chinese:435-448`, `src/ibus-engine-handwrite-chinese:909-916`
  Acceptance criteria: Python syntax check passes; existing ESC flow in terminal stays intact

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [x] F1. Python syntax check — `python3 -m py_compile src/ibus-engine-handwrite-chinese`
- [x] F2. Code review — confirm ESC moved before RELEASE_MASK, debounce active, no other changes
- [x] F3. Test with `ibus engine handwrite-chinese` — ESC pauses/closes, typing unaffected
- [x] F4. Scope fidelity — no changes outside the ESC handling path

## Commit strategy
Single commit on main:
`fix: handle ESC before RELEASE_MASK filter for Firefox compatibility`

## Success criteria
- [x] `python3 -m py_compile src/ibus-engine-handwrite-chinese` — zero errors
- [x] In terminal: ESC pauses panel (state 0→1), ESC again closes panel (state 1→exit)
- [x] Enter/Backspace still work while writing
- [x] Rapid ESC presses don't skip states (debounce working)
- [x] No changes to any file other than `src/ibus-engine-handwrite-chinese`
