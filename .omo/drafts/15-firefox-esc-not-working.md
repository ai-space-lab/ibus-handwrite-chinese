---
slug: 15-firefox-esc-not-working
status: awaiting-approval
intent: clear
pending-action: implement fix
approach: Move ESC handling before RELEASE_MASK filter in do_process_key_event + add 150ms debounce to on_key_esc
---

# Draft: 15-firefox-esc-not-working

## Components (topology ledger)
| id | outcome | status | evidence path |
|---|---|---|---|
| ESC handler in do_process_key_event | ESC handled before RELEASE_MASK filter so Firefox key events are caught | active | src/ibus-engine-handwrite-chinese:909-925 |
| Debounce in on_key_esc | Prevents double-fire from press+release reaching same handler | active | src/ibus-engine-handwrite-chinese:435-448 |

## Open assumptions (announced defaults)
| assumption | adopted default | rationale | reversible? |
|---|---|---|---|
| Firefox sends ESC with RELEASE_MASK | Move ESC check before the filter | Most likely cause; safe because ESC only fires when window visible + debounce prevents double-fire | Yes — revert easily |
| Debounce threshold | **150ms** (Oracle review: 300ms too conservative, may swallow rapid double-ESC) | Long enough for press+release gap (≤50ms), short enough for deliberate second press (≥150ms) | Yes — adjustable |

## Findings (cited - path:lines)
- `do_process_key_event` at line 909-925: RELEASE_MASK check at line 911 returns early before ESC check at line 914
- Firefox known to have different X11/IBus key event routing compared to terminal/text-editor apps (Firefox's multi-process architecture and GTK IM integration)
- `time` already imported at line 5

## Decisions (with rationale)
1. **Move ESC before RELEASE_MASK**: Firefox likely sends ESC key release (not press) through IBus. The RELEASE_MASK check skips it. Moving ESC handling before the check catches it regardless.
2. **Add 300ms debounce**: Prevents double-fire when both press+release events reach `on_key_esc`. Natural ESC press is <200ms, so 300ms is safe.
3. **Keep Backspace/Enter after RELEASE_MASK**: These only change behavior in active state, and Firefox doesn't have issues with them. No need to change.

## Scope IN
- Fix ESC in `do_process_key_event` — move before RELEASE_MASK
- Add `_last_esc_time` + debounce in `on_key_esc`
- Verify syntax + ESC flow

## Scope OUT (Must NOT have)
- No changes to Backspace/Enter handling
- No changes to `on_key()` GTK handler
- No changes to window, state machine, trackpad
- No changes to packaging, CI, docs

## Open questions
None — outcome is clear.

## Approval gate
status: awaiting-approval
dual-review-passed: true
mommus-verdict: OKAY (APPROVE)
oracle-verdict: APPROVE with modifications (debounce 150ms, add diagnostic step)
modifications-applied: true
