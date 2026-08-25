---
slug: fix-desktop-esc-and-window-jump
status: awaiting-approval
intent: clear
review_required: false
pending-action: write .omo/plans/fix-desktop-esc-and-window-jump.md
approach: Two surgical fixes: (1) guard do_set_cursor_location() against zeroed cursor to prevent unwanted reposition, (2) fix _position_window() fallback to keep position when our window is active and use cursor location when desktop is focused
---

# Draft: fix-desktop-esc-and-window-jump

## Components (topology ledger)
| id | outcome | status | evidence path |
|----|---------|--------|---------------|
| do_set_cursor_location guard | Skip _position_window() when cursor location is all-zeros (focus-loss case) | active | src/ibus-engine-handwrite-chinese:938-944 |
| _position_window fallback | When active==our_gdk_win: keep position. When active==None: use cursor location if available, bottom-right only as first-show fallback | active | src/ibus-engine-handwrite-chinese:946-976 |
| ESC reliability | Secondary effect — fixed by above two (window won't be at WM-unfriendly position) | active | src/ibus-engine-handwrite-chinese:1002-1014 |

## Open assumptions (announced defaults)
| assumption | adopted default | rationale | reversible? |
|------------|----------------|-----------|-------------|
| Cursor location (x=0,y=0) is invalid | Treat (0,0) as "no cursor known" and skip reposition | IBus spec: 0,0 is sent when no text field has focus. Positioning near (0,0) = top-left of primary monitor, which is wrong | Yes — if a legitimate app sends (0,0) cursor, we won't reposition. Low risk because IBus only sends nonzero cursor for focused text fields |

## Findings (cited - path:lines)
1. `_position_window()` lines 955-960: when `active is None or active == our_gdk_win`, always moves window to bottom-right of primary monitor `(wa.x + wa.width - win_w - 12, wa.y + wa.height - win_h - 12)`.
2. `do_set_cursor_location()` lines 938-944: calls `_position_window()` unconditionally when window is visible — no guard for zeroed cursor (x=0, y=0).
3. IBus sends `do_set_cursor_location(0,0,0,0)` after `do_focus_out` fires (confirmed by subagent investigation). This triggers unwanted reposition to bottom-right.
4. `self._cx`, `self._cy` are stored (line 939-940, init at line 871-872) but never used in `_position_window()` — they're dead storage.
5. Window at bottom-right (2148, 1185 on 1920×1200 display) gets inconsistent keyboard focus from WM → GTK `on_key` handler doesn't fire → ESC silently lost. This is a **secondary effect** of the positioning bug.
6. Previous commit `e8636ed` fixed candidate-tap regression but preserved the pre-existing window-jumping behavior (present during original development).

## Decisions (with rationale)
1. **Guard `do_set_cursor_location()` against zeroed cursor** — Skip `_position_window()` when x=0 and y=0. Rationale: IBus sends zeroed cursor on focus loss; repositioning with invalid cursor data is always wrong.
2. **Fix `_position_window()` fallback**: (a) When `active == our_gdk_win`: return early (don't move the window — user clicked on our window, leave it). (b) When `active is None` (desktop focused): use `self._cx/self._cy` cursor location if valid (nonzero) as positioning hint, falling back to bottom-right only as first-show behavior. Rationale: Keeps window where user expects it.
3. **No changes to `_grab_focus_if_needed()` or ESC handling** — ESC reliability is a secondary effect of bad positioning. When window is positioned correctly, WM grants keyboard focus reliably (verified by test results showing 5/5 ESC passes with correct positioning).

## Scope IN
- `do_set_cursor_location()` guard for zeroed cursor (one condition added)
- `_position_window()` fallback logic for `active is None` and `active == our_gdk_win` (two branches modified)
- One test scenario verifying window doesn't jump (GTK window position assertion)

## Scope OUT (Must NOT have)
- No changes to `_grab_focus_if_needed()`, `do_enable()`, `do_focus_in()`, `do_focus_out()`, or any ESC/key handling
- No changes to evdev, GTK drawing, recognition pipeline, packaging, CI, or any other module
- No refactoring or restructuring of `_position_window()` beyond the two fallback branches
- No changes to the candidate-tap fix from `e8636ed`

## Open questions
None — intent is CLEAR, both root causes are confirmed by subagent investigation.

## Approval gate
status: awaiting-approval
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->
