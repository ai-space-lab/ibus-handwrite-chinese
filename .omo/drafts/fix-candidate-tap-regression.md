---
slug: fix-candidate-tap-regression
status: awaiting-approval
intent: clear
pending-action: update .omo/plans/fix-candidate-tap-regression.md with todos
approach: Remove unconditional present() from do_enable() — defer focus grab to _grab_focus_if_needed() guarded by _focused_since_enable flag + screen.get_active_window() check.
---

# Draft: fix-candidate-tap-regression

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->
- `src/ibus-engine-handwrite-chinese` | Remove present() from do_enable(), add _focused_since_enable flag + _grab_focus_if_needed() guard | active
- `.omo/drafts/fix-candidate-tap-regression.md` | Document review findings, corrected approach, revert strategy | active

## Open assumptions (announced defaults)
<!-- Record any default you adopt instead of asking, so the user can veto it at the gate. -->
<!-- assumption | adopted default | rationale | reversible? -->
- WM behavior: `present()` with `set_accept_focus(True)` steals focus from text fields on strict-focus WMs | Default: assume modern WMs (XFCE/xfwm4, GNOME/mutter, KDE/kwin) honor focus-steal-prevention for UTILITY windows, but don't rely on it — gate aggressively | Reversible: can always add more guards
- `GLib.PRIORITY_LOW` ensures `do_focus_in` fires before idle callback | Default: D-Bus dispatch is higher priority than idle callbacks; this ordering is correct in practice | Reversible: fall back to `GLib.timeout_add(50)` if race observed
- Wayland: `Gdk.Screen.get_active_window()` returns None | Default: guard is silently bypassed → present() always fires → same regression risk on Wayland. Documented as known limitation, scoped as future work | Reversible: implement Wayland-safe fallback

## Findings (cited - path:lines)
1. Commit `03cffa3` implements unconditional `set_accept_focus(True)` + `present()` in `do_enable()` (`git show 03cffa3:src/ibus-engine-handwrite-chinese | grep -n "present\|accept_focus"`). This steals focus from active text fields → candidate taps silently drop characters.
2. Pre-`03cffa3` code had `present()` WITHOUT `set_accept_focus(True)` — candidate taps worked because WM denied focus to windows that can't accept it. (`git show 7836f39^:src/ibus-engine-handwrite-chinese | grep -n "present\|accept_focus"`)
3. Both Momus and Oracle reviews (2026-07-08) confirmed the same critical issue: `present()` in `do_enable()` runs before any guard.
4. `GLib.idle_add(priority=GLib.PRIORITY_LOW)` ensures pending D-Bus events (including `do_focus_in` from IBus) fire before the idle callback — GConditional dispatch ordering in GLib main loop.
5. `Gdk.Screen.get_active_window()` is deprecated in GTK4 and unreliable on Wayland (returns None on most compositors).

## Decisions (with rationale)
1. **Remove `present()` from `do_enable()` entirely.** Rationale: window visibility via `show_all()` is sufficient. Only grab focus via `present()` INSIDE `_grab_focus_if_needed()` where `_focused_since_enable` + `screen.get_active_window()` guards gate it. This eliminates the unconditional focus steal.
2. **Keep `set_accept_focus(True)` in `do_enable()`.** Rationale: allows the window to accept focus when the user clicks on it (e.g., to resume after pause). Without it, clicking the panel wouldn't give it keyboard focus for GTK `on_key` to catch ESC.
3. **Use `GLib.idle_add(priority=GLib.PRIORITY_LOW)` instead of `GLib.timeout_add(50)`.** Rationale: no fixed delay, more responsive, and the low priority maximizes chance of `do_focus_in` arriving first.
4. **Accept Wayland limitation for now.** Rationale: target environment is X11 (XFCE). Wayland focus management is fundamentally different and requires compositor-specific APIs.

## Scope IN
- Fix candidate tap regression: when a text field has focus and user taps a candidate, the character must output to the text field
- Preserve ESC pause when no text field has focus (GTK path)
- Preserve ESC pause when text field has focus (IBus path)
- Preserve auto-pause/resume on focus-out/focus-in (Phase 6)
- Update plan documentation with GLib.PRIORITY_LOW rationale, screen guard, Wayland caveat
- Candidate-tap test evidence

## Scope OUT (Must NOT have)
- Wayland focus guard implementation (scoped as future work)
- GTK4 migration or Gdk.Display migration (deprecation-only concern)
- Any changes to evdev, GTK drawing, recognition pipeline, or other engine features
- Global key grabs (IBus-only and GTK window-only focus management)
- Changes to postinst, install scripts, or packaging

## Open questions
None — all forks resolved by reviews.

## Approval gate
status: awaiting-approval
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-reading exploration. -->
