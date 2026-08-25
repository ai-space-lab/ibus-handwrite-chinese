---
slug: 16-auto-pause-on-focus-loss
status: drafting
intent: clear
review_required: true
pending-action: write .omo/plans/16-auto-pause-on-focus-loss.md
approach: Implement do_focus_out (auto-pause) + do_focus_in (auto-resume) in HandwriteEngine
---

# Draft: 16-auto-pause-on-focus-loss

## Components (topology ledger)
| id | outcome (one line) | status | evidence path |
|---|---|---|---|
| do_focus_out handler | Auto-pause writing UI when IBus input context loses focus (Firefox title bar click) | active | src/ibus-engine-handwrite-chinese:1027-1028 |
| do_focus_in handler | Auto-resume writing UI when IBus input context regains focus (click back into input field) | active | src/ibus-engine-handwrite-chinese:1029 (to be added) |

## Open assumptions (announced defaults)
| assumption | adopted default | rationale | reversible? |
|---|---|---|---|
| Firefox fires do_focus_out on title bar click | Trust IBus API contract | IBus spec: focus-out fires when app's input context loses focus. Firefox's web content loses keyboard focus when title bar is clicked. | N/A (IBus-defined) |
| Text editors (Gedit) do NOT fire do_focus_out on title bar click | Trust GTK behavior | Clicking WM decorations in GTK apps doesn't move keyboard focus from text widget. Verified by user report: text editors work fine. | N/A (app-defined) |
| Auto-resume on focus-in is safe even for manual ESC pause | Accept as reasonable | User clicking back into input field is a clear signal they want to type. If they manually paused, Tab-away, Tab-back — they expect to continue. | Yes — can be gated behind a flag if problematic |

## Findings (cited - path:lines)
- `do_focus_out` at line 1027: `pass` — currently a no-op
- `do_focus_in` at line N/A: **not defined** at all in HandwriteEngine
- `do_process_key_event` at line 914-930: ESC handled before RELEASE_MASK filter (Plan 15 fix), but only called when IBus context is active — Firefox doesn't forward keys when context has no focus
- `on_key_esc()` at line 436-453: state 0→1 (pause): `stop_trackpad()`, show "Paused" overlay; state 1→0 would be (close/hide)
- `on_window_click()` at line 473-479: resume from state 1: `_state = 0`, `darea.queue_draw()`, `start_trackpad()`, `engine.update_candidates()`
- `_check_engine` at line 1030-1038: 500ms poll detects external engine switch only — not focus changes
- Window `set_accept_focus(False)` at line 268: prevents focus-stealing but means panel can't receive GTK key events directly

## Decisions (with rationale)
1. **do_focus_out auto-pause**: Call `self.win.on_key_esc()` when focus-out fires and window is visible in state 0. Uses the existing pause mechanism (state 0→1, stop trackpad, show overlay). No new logic needed.
2. **do_focus_in auto-resume**: Set `_state = 0`, `queue_draw()`, `start_trackpad()`, `update_candidates()` when focus-in fires and window is visible in state 1. Mirrors `on_window_click()` behavior but for programmatic focus events.
3. **No global key grab**: The focus-out/focus-in approach is cleaner, uses the IBus API correctly, and doesn't require X11-specific code. Global key grabs would be more invasive and could conflict with other applications.

## Scope IN
- Implement `do_focus_out()` in `HandwriteEngine` — auto-pause on focus loss
- Implement `do_focus_in()` in `HandwriteEngine` — auto-resume on focus regain
- Add logging to both methods for debuggability

## Scope OUT (Must NOT have)
- No changes to `HandwriteWin` class (only `HandwriteEngine`)
- No changes to `do_process_key_event` (already fixed in Plan 15)
- No changes to `on_window_click`, `on_key_esc`, or any existing state machine logic
- No changes to trackpad handling, window visibility, or GTK event handling
- No changes to test mode (`TestCommitEngine` — not affected by IBus focus events)
- No packaging, CI, or documentation changes

## Open questions
None — approach is fully determined from exploration.

## Modifications from Metis review
- M1: Added `start_trackpad()` return-value check with warning log in `do_focus_in` (was ignoring failure silently)
- M2: Clarified F4 as manual-only in verification strategy (was claiming "zero human intervention" while requiring real IBus/X11)
- M3: Strengthened acceptance criteria with more robust grep/sed checks (was relying on fragile `-A5`/`-A8` line counts)

## Approval gate
status: approved
dual-review-passed: true
metis-verdict: 4 issues found, 3 applied (M1-M3), 1 acknowledged (auto-resume assumption documented as reversible)
mommus-verdict: OKAY — no blockers. Plan quality high, all references verified, code provided.
oracle-verdict: OKAY with comments — no blocking issues. All 7 technical questions checked out. Minor async classify race noted (pre-existing).
modifications-applied: true
