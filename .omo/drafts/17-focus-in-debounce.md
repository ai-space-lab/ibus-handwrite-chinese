---
slug: 17-focus-in-debounce
status: ready
intent: clear
pending-action: implement .omo/plans/17-focus-in-debounce.md
approach: Add 300ms time gate in do_focus_in — skip auto-resume if do_focus_in fires within 300ms of do_focus_out
---

# Draft: 17-focus-in-debounce

## Components (topology ledger)
| id | outcome (one line) | status | evidence path |
|---|---|---|---|
| _last_focus_out_time variable | Track when focus-out last fired | active | src/ibus-engine-handwrite-chinese:874 |
| do_focus_out time recording | Record timestamp on auto-pause | active | src/ibus-engine-handwrite-chinese:1030 |
| do_focus_in time gate | Skip auto-resume if <300ms since focus-out | active | src/ibus-engine-handwrite-chinese:1035 |

## Findings (cited - path:lines)
- `/tmp/hw.log` shows: `do_focus_out` → `do_focus_in` fires immediately after
- Firefox sends `do_focus_in` within <50ms of `do_focus_out` when clicking title bar
- This undoes the auto-pause before the user sees it (state 0→1→0 in one event loop cycle)
- `do_focus_in` currently has no time guard — it always resumes if state=1 and window visible

## Decisions (with rationale)
1. **300ms time gate**: Long enough to filter out Firefox's spurious immediate focus-in (<50ms), short enough that a genuine focus-return (alt-tab, clicking back into field) is >300ms. Consistent with Oracle's original suggestion (150-300ms range).
2. **No separate flag needed**: Pure time-based approach is simplest — no boolean state to manage, no need to distinguish "auto-paused" vs "manually paused".

## Scope IN
- Add `_last_focus_out_time` to `HandwriteEngine.__init__`
- Record `time.time()` in `do_focus_out` when auto-pause triggers
- Skip auto-resume in `do_focus_in` if `time.time() - self._last_focus_out_time < 0.3`

## Scope OUT (Must NOT have)
- No changes to any other method, class, or file
- No changes to the 150ms ESC debounce (separate concern)
- No changes to `HandwriteWin`, `TestCommitEngine`, or `do_process_key_event`

## Open questions
None

## Approval gate
status: ready
dual-review-passed: true
mommus-verdict: OKAY — plan specificity excellent, all references verified, no blockers
oracle-verdict: OKAY — technically correct. Optional improvement: use `time.monotonic()` instead of `time.time()` for NTP-step immunity (low priority)
modifications-applied: true
committed: true
commit: ca5c4e21604869d02297b0a1ffe67c1aec9b5c94
