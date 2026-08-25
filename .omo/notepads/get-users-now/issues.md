# Issues — get-users-now

Problems and gotchas encountered during work on this plan.

_Auto-scaffolded by /start-work. Append new entries below - never overwrite._

---

## 2026-08-25 — Hard external blockers prevent plan completion

All 15 remaining tasks are blocked by inputs only the user can provide. Marked `- [~]` in the plan.

**Hardware blockers (user's MacBook Pro):**
- B1.1 — Record 15s demo GIF + 30s MP4 (trackpad draw → candidates → tap → ESC)
- B2.1 — Capture 4-5 screenshots (panel, 6-tab prefs, model download, shortcuts, user dict)

**Account blockers (user's social/GitHub accounts):**
- B3.1 — Deploy GitHub Pages (depends on B1.1/B2.1 assets)
- B3.2 — Post English to r/linux, r/archlinux, r/Fedora, r/Ubuntu
- B3.3 — Post Chinese to r/linuxcn, V2EX, 少数派
- B3.4 — Tweet thread + Mastodon + Bluesky
- B4.2 — Monitor GitHub Traffic / Reddit for 7 days

**Post-launch-data blockers (no data yet):**
- B4.3 — Collect FAQ from comments/issues
- B4.4 — Fix critical install bugs → v0.6.1
- F1–F5 — Final verification wave (needs assets + posts + account)

**Resolution:** Worker completed all 10 automatable tasks (committed locally as `015f156`, not pushed). Remaining work requires user action. Plan is in terminal `- [~]` state pending user input.

---

## 2026-08-25 — `--test` mode window unmapped (10×10, IsUnMapped)

**Symptom:** Running `ibus-engine-handwrite-chinese --test` created a window that was 10×10 pixels, `Map State: IsUnMapped`, and could not be captured with `import`.

**Root cause:** The `main()` function unconditionally pre-created `_HANDWRITE_WIN_GLOBAL = HandwriteWin(None)` → `.realize()` → `.hide()` BEFORE the `if args.test` branch. This hidden window became the **WM_CLIENT_LEADER** (group leader) for the test window (verified via `xprop`). xfwm4 refuses to map a window whose group leader is hidden/unmapped — even `xdotool windowmap` could not force the map.

**Evidence:**
- `xprop` showed `WM_CLIENT_LEADER(WINDOW): window id # 0x4800001` — the XID of the hidden global window
- `xwininfo` confirmed `Map State: IsUnMapped` despite `show_all()` + `present()` being called
- `xdotool windowmap` also failed (WM actively refused the map)
- After fix, group leader changed to the test window's own XID and mapping succeeded

**Fix:** Moved `if args.test: ... return` BEFORE the global window creation. In `--test` mode, no global window is created, so the test window has no hidden group leader. The IBus path (after the `return`) still creates the global window as before.

**File modified:** `src/ibus-engine-handwrite-chinese` only (surgical change to `main()`).

**Verification (post-fix):**
- `xdotool getwindowgeometry`: WIDTH=400, HEIGHT=370 ✓
- `xwininfo`: Map State: IsViewable ✓
- `import -window <WINID> /tmp/hw-panel.png`: IMPORT_OK ✓
- Captured image: 400×370 pixels ✓

**Gotcha — session activation for testing:** The OpenCode bash tool runs in session c2 (user chloeng, `Active=no`). xfwm4 only maps windows from the active login session. Before testing, run `loginctl activate c2` to activate the user's XFCE session. Without this, even `xeyes` and plain GTK windows stay unmapped.
