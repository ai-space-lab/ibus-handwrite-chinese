# fix-candidate-tap-regression - Work Plan

## Comparison: With vs Without This Plan

### Without this plan (current state)
Commit `03cffa3` (`set_accept_focus(True)` + `present()` unconditionally in `do_enable`) → **ESC pause works in all scenarios** (with or without text field focus), but **candidate taps silently fail when a text field is focused** because focus is stolen from the IBus input context.

### With this plan (after fix)
`present()` is **removed from `do_enable()`** and **deferred to `_grab_focus_if_needed()`** where `_focused_since_enable` + `screen.get_active_window()` guards gate it:

| Scenario | Without fix | With fix |
|----------|-------------|----------|
| No text focus → ESC pauses | ✅ Works (commit 03cffa3) | ✅ Still works (guard detects no focus → grabs GTK focus → `on_key` catches ESC) |
| Text field focus → ESC pauses | ✅ Works (IBus path) | ✅ Still works (IBus path unchanged) |
| Text field focus → candidate tap → character outputs | ❌ **Broken** (focus stolen → IBus context lost) | ✅ **Fixed** (`_focused_since_enable` is True → guard skips grab → IBus context preserved) |
| Text field focus → switch IME → engine enables | ❌ Broken (present() steals focus) | ✅ Fixed (no present() in do_enable() → text field retains IBus context) |
| Wayland (all scenarios) | ❌ Broken (if present() steals on Wayland compositor) | ⚠️ Same risk (screen.get_active_window() returns None → guard bypassed) |

## TL;DR (For humans)

**What you'll get:** Candidate taps reliably output characters when a text field is focused, while ESC still pauses the handwriting panel when no text field has focus. No more silent character drops.

**Why this approach:** The previous fix was too aggressive — it grabbed keyboard focus every time the panel opened, even when a text field was already active. This fix checks first: "is a text field already focused?" If yes, leave focus alone (IBus handles ESC). If no, grab focus (GTK handles ESC).

**What it will NOT do:** Fix anything on Wayland (the window-manager API doesn't expose active-window info there). Change how the panel looks, how drawing works, or how recognition works.

**Effort:** Short
**Risk:** Medium — this is the third attempt at this fix; the critical must-fix (remove present() from do_enable()) was confirmed by two independent reviews
**Decisions to sanity-check:** (1) Accept Wayland limitation as future work? (2) Risk that `GLib.PRIORITY_LOW` isn't low enough on some systems?

Your next move: Approve this plan, then `/start-work` to execute.

---

> TL;DR (machine): Short effort, Medium risk — remove present() from do_enable(), gate focus grab behind _focused_since_enable + screen.get_active_window() guard. Candidate taps restored. Wayland limitation accepted.

## Scope
### Must have
- Remove `self.win.set_accept_focus(True)` and `self.win.present()` from `do_enable()` in `src/ibus-engine-handwrite-chinese`
- `_grab_focus_if_needed()` as one-shot idle callback at `GLib.PRIORITY_LOW`:
  - Skip if window not visible
  - Skip if `_focused_since_enable` is True (text field has focus)
  - ~~Skip if `screen.get_active_window()` shows a different app window is active~~ **REMOVED during testing** — guard was too aggressive: `get_active_window()` returns the root window when desktop is focused, making `active != our_win` True and blocking the no-text-focus case. `_focused_since_enable` flag alone is sufficient; WM focus-steal prevention provides the safety net for active application windows.
  - Only then: `set_accept_focus(True)` + `present()` to grab focus
- `_focused_since_enable` flag: True in `do_focus_in()`, False in `do_focus_out()` and `do_enable()`
- Fix pseudo-docstrings in `do_focus_out` / `do_focus_in` (move before assignments)
- Update plan documentation with findings, review results, Wayland caveat
- Test: verify candidate tap outputs character when text field has focus

### Must NOT have (guardrails, anti-slop, scope boundaries)
- No changes to any file other than `src/ibus-engine-handwrite-chinese` and `.omo/` artifacts
- No Wayland focus guard (documented limitation)
- No GTK4 migration or Gdk.Display migration
- No changes to evdev, GTK drawing, recognition pipeline, or other engine features
- No global key grabs
- No packaging, install script, or CI changes

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after
- Framework: existing `tests/test_esc_key_routing.py` + new candidate-tap test via `xdotool` simulation
- Evidence: .omo/evidence/fix-candidate-tap-regression/test-results.txt

## Execution strategy
### Parallel execution waves
Wave 1 (2 todos, parallel): code fix + plan docs update
Wave 2 (1 todo): install + test

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. Code fix | — | 3 | 2 |
| 2. Update plan docs | — | — | 1 |
| 3. Install + test | 1 | — | — |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [x] 1. Code: Remove present() from do_enable(), add _focused_since_enable guard + _grab_focus_if_needed()
  What to do / Must NOT do:
  - In `do_enable()`: remove `self.win.set_accept_focus(True)` and `self.win.present()`. Keep `show_all()` + `_position_window()`. Add `GLib.idle_add(self._grab_focus_if_needed, priority=GLib.PRIORITY_LOW)`.
  - Add `self._focused_since_enable = False` in `__init__` and `do_enable()`.
  - Add `_grab_focus_if_needed()` one-shot method: guards for win visible + `_focused_since_enable` + `screen.get_active_window()`, then `set_accept_focus(True)` + `present()`.
  - In `do_focus_in()`: add `self._focused_since_enable = True` as first statement, move docstring before it.
  - In `do_focus_out()`: add `self._focused_since_enable = False` as first statement, move docstring before it.
  - Must NOT change any other code path.
  Parallelization: Wave 1 | Blocked by: — | Blocks: 3
  References (executor has NO interview context - be exhaustive):
  - `.omo/drafts/fix-candidate-tap-regression.md` (full plan with review findings)
  - `.omo/anchored-summary.md` (Phase 7 context, history of commits 7836f39/03cffa3)
  - `src/ibus-engine-handwrite-chinese` lines ~876-879 (__init__), ~978-1002 (do_enable), ~1004-1023 (_grab_focus_if_needed), ~1060-1085 (do_focus_out/do_focus_in)
  - Git: `git show 03cffa3:src/ibus-engine-handwrite-chinese` (the regression fix)
  Acceptance criteria (agent-executable):
  - `grep -n "present\|accept_focus" src/ibus-engine-handwrite-chinese` must show present() only inside `_grab_focus_if_needed`, NOT in `do_enable`
  - `grep -n "_focused_since_enable" src/ibus-engine-handwrite-chinese` must show the flag in __init__, do_enable, do_focus_in, do_focus_out, and _grab_focus_if_needed
  - `grep -n "GLib.idle_add.*_grab_focus_if_needed" src/ibus-engine-handwrite-chinese` must show priority=GLib.PRIORITY_LOW
  QA scenarios (name the exact tool + invocation): happy + failure, Evidence .omo/evidence/fix-candidate-tap-regression/m1-code-fix.diff
  Commit: N (committed together after test)

- [x] 2. Docs: Update plan documentation with review findings, GLib.PRIORITY_LOW rationale, Wayland caveat, revert strategy
  What to do / Must NOT do:
  - Ensure `.omo/drafts/fix-candidate-tap-regression.md` has complete Decisions, Scope IN/OUT, Findings sections
  - Ensure `.omo/plans/fix-candidate-tap-regression.md` has filled TL;DR, todos, comparison table
  - Must NOT change product code
  Parallelization: Wave 1 | Blocked by: — | Blocks: —
  References (executor has NO interview context - be exhaustive): Both review outputs (bg_235b0a9d, bg_abe57df5)
  Acceptance criteria (agent-executable): grep for "GLib.PRIORITY_LOW" in .omo/drafts/ and .omo/plans/ — both must contain the rationale
  QA scenarios: Read the files and verify completeness
  Commit: N (committed together after test)

- [x] 3. Install + test: Install the fix, run ESC routing test + candidate tap test
  What to do / Must NOT do:
  - Install the modified engine: `sudo cp src/ibus-engine-handwrite-chinese /usr/local/share/ibus-handwrite-chinese/ibus-engine-handwrite-chinese && ibus restart`
  - Run the existing ESC routing test in `tests/test_esc_key_routing.py`
  - Write and run a candidate-tap test: enable handwrite engine while text field has focus, simulate candidate tap, verify character output
  - Log results to `/tmp/hw.log` and capture them as evidence
  - Must NOT commit without passing evidence
  Parallelization: Wave 2 | Blocked by: 1 | Blocks: —
  References (executor has NO interview context - be exhaustive): `tests/test_esc_key_routing.py`, `/tmp/hw.log` output format
  Acceptance criteria (agent-executable):
  - ESC routing: both scenarios (text focus + no text focus) produce `on_key_esc: _state=0` in `/tmp/hw.log`
  - Candidate tap: `commit_text()` outputs character to focused text field (verify via `xdotool getactivewindow getwindowfocus getwindowpid` or similar)
  QA scenarios: Test A (no text focus → ESC pause), Test B (text field focus → ESC pause), Test C (text field focus → candidate tap → character output)
  Commit: Y | `fix: gate focus grab behind _focused_since_enable guard to restore candidate taps`

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit — verify all 3 must-fix items from reviews are addressed
- [ ] F2. Code quality review — check diffs, verify no present() in do_enable()
- [ ] F3. Real manual QA — user tests on real hardware with trackpad + text field
- [ ] F4. Scope fidelity — no changes outside scope boundaries

## Commit strategy
Single commit with message: `fix: gate focus grab behind _focused_since_enable guard to restore candidate taps`
Co-authored-by or reviewed-by footers for the dual review receipts.

## Success criteria
1. `grep -n "present\|accept_focus" src/ibus-engine-handwrite-chinese` shows present() ONLY inside `_grab_focus_if_needed`, not in `do_enable` ✅
2. ESC pause works with no text field focus (GTK `on_key` path) ✅
3. ESC pause works with text field focus (IBus `do_process_key_event` path) ✅
4. Candidate tap outputs character when text field has focus (IBus `commit_text()` path) ✅
5. All evidence stored in `.omo/evidence/fix-candidate-tap-regression/` ✅
