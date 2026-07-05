# Plan: Ensure ESC key works immediately after install without logout/login

## Root Cause Analysis

### Symptom
ESC key on the handwriting panel was non-functional. Pressing ESC had no effect (no pause overlay, no close/restore-engine). The `do_process_key_event` method was never called by IBus across 4 separate engine process instances.

### Timeline of discovery
1. ESC code from commit `5e272cc` ("Fix Esc behavior") was verified **fully intact** in HEAD
2. `do_process_key_event` (lines 909–922) is correct: `RELEASE_MASK` guard → ESC/BS/Return dispatch → correct super() calls
3. **BUT**: `/tmp/hw.log` showed zero `do_pke` entries across 4 engine restarts (PIDs 19978, 20111, 23038, 27149) — only `do_enable` was called
4. User logged out and logged back in → everything works (ESC + trackpad + handwriting)
5. **[Key insight]** The `input` group membership (`getent group input` shows user `mint` is in the group) was **not active** in the session — `cat /proc/$$/status` showed no `995` (input GID) in `Groups:` line
6. All 13 `/dev/input/event*` devices returned `Permission denied` (EACCES)
7. The installed binary at `/usr/local/share/ibus-handwrite-chinese/ibus-engine-handwrite-chinese` is **identical** to the source (same md5sum) — no stale code

### Root Cause
**Two environmental issues combined:**

| Issue | Effect | 
|-------|--------|
| **#1: `input` group not active** | User was added to `input` group during install but never logged out. Supplementary groups are fixed at login time. All evdev devices inaccessible. |
| **#2: Stale root `ibus-daemon`** | From initial sudo-based install, a root-owned ibus-daemon was intercepting D-Bus communication. The engine process (user-owned) couldn't properly route key events through the root daemon. The 4 restarts were IBus respawning an engine whose key event channel was blocked. |

After logout+login: both issues resolved → `input` group active + fresh user-owned ibus-daemon → `do_process_key_event` receives key events → ESC works.

### Why the code appeared "correct but unreachable"
The `do_process_key_event` handler was **never called by IBus** because:
1. The stale root ibus-daemon owned the D-Bus session bus
2. The user engine registered with its own bus connection, but the root daemon didn't forward key events
3. IBus restarted the engine 4 times (each time it timed out waiting for key event processing)
4. `do_enable` was called (basic registration worked) but the full key event pipeline was blocked

---

## Fix Items

### T1: Kill stale root ibus-daemon reliably in install & prevent re-creation

**Problem**: After killing the stale root daemon (step 8), `install.sh` step 9 (lines 195–196) can restart ibus-daemon **as root** when `sudo ./install.sh` is used, because `$(id -u) -eq 0` is true and the root branch runs `ibus-daemon --daemonize --replace` directly. This recreates the stale root daemon.

**Fix A** — Never restart ibus-daemon as root:
Replace lines 195–199 in `tools/install.sh`:
```bash
# BEFORE (bug): when run as root, ibus-daemon restarts as root
{ if [ "$(id -u)" -eq 0 ]; then
    ibus-daemon --daemonize --replace 2>/dev/null
  else
    sudo -u "$REAL_USER" ibus-daemon --daemonize --replace 2>/dev/null
  fi; } || true
```

```bash
# AFTER (fixed): always run ibus-daemon as the real user
{ if [ "$(id -u)" -eq 0 ] && [ "$REAL_USER" != "root" ]; then
    su -c "ibus-daemon --daemonize --replace 2>/dev/null || true" "$REAL_USER"
  else
    ibus-daemon --daemonize --replace 2>/dev/null || true
  fi; } || true
```

**Fix B** — Preserve `DBUS_SESSION_BUS_ADDRESS` through sudo:
When `sudo -u "$REAL_USER"` is used, sudo's `env_reset` default strips `DBUS_SESSION_BUS_ADDRESS`. Without it, ibus-daemon may connect to the wrong bus, making the engine invisible to the desktop session.

Explicitly preserve the variable before the restart:
```bash
# After fixing Fix A above, add DBUS address preservation
DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-}"
export DBUS_SESSION_BUS_ADDRESS
{ if [ "$(id -u)" -eq 0 ] && [ "$REAL_USER" != "root" ]; then
    su -c "ibus-daemon --daemonize --replace 2>/dev/null || true" "$REAL_USER"
  else
    ibus-daemon --daemonize --replace 2>/dev/null || true
  fi; } || true
```

**Fix C** — Demote the post-kill `exit 1` to a non-fatal warning:
A persistent root ibus-daemon is a user-attention issue, not an install blocker. Change to:
```bash
if pgrep -u root ibus-daemon > /dev/null 2>&1; then
    echo "⚠ WARNING: Could not kill root ibus-daemon. ESC may not work."
    echo "  Manual: sudo pkill -9 -u root ibus-daemon"
    # Continue installation — user can fix later
fi
```

**Fix D** — Verify user ibus-daemon is running after restart, not just absence of root daemon:
After the restart block, add:
```bash
sleep 1
pgrep -u "$REAL_USER" ibus-daemon >/dev/null 2>&1 \
    && echo "  ✓ User ibus-daemon confirmed running" \
    || echo "  ⚠ User ibus-daemon not confirmed — run: ibus-daemon --daemonize --replace"
```

### T2: Add `input` group activation in install script
**Problem**: `usermod -a -G input $USER` adds the user to the group, but the change only takes effect on next login.

**Fix**: In `tools/install.sh`, after adding the user to the `input` group:

**Option A (preferred — immediate effect via udev ACL):**
The existing udev rule at `tools/99-trackpad-handwrite.rules` uses `TAG+="uaccess"`. On systemd systems with `systemd-logind`, this grants ACL access to the device for the logged-in user WITHOUT needing `input` group membership. Verify the udev tag is correctly applied:

```bash
# After install, verify uaccess tag gives access:
getfacl /dev/input/event* 2>/dev/null | grep -q "$USER" || echo "ACL not applied — try: sudo udevadm control --reload-rules && sudo udevadm trigger"
```

**Option B (immediate via `sg input`):**
In the wrapper script `/usr/local/bin/ibus-engine-handwrite-chinese`, add a re-exec under the `input` group when the group isn't active in the current session:

```bash
# In the wrapper script /usr/local/bin/ibus-engine-handwrite-chinese, before the exec:
if ! groups | grep -q '\binput\b'; then
    exec sg input -c "exec $0 $*" 2>/dev/null || true
fi
```

This re-execs the wrapper under the `input` group when the group isn't active. The `sg` command is safe — it requires the user to already be a member of the `input` group (which `usermod -a -G input $USER` ensures). No privilege escalation risk. The `"exec $0 $*"` quoting handles simple arguments correctly (IBus args like `--ibus` are simple).

On the re-exec, the child process has `input` in its supplementary groups, so `groups | grep '\binput\b'` succeeds and the script falls through to the normal `exec` path. No infinite recursion.

**Option C (informational):**
At the end of install, check and warn:

```bash
if ! groups "$USER" | grep -q '\binput\b'; then
    echo "⚠ You need to log out and back in for trackpad access."
    echo "  Run: sudo usermod -a -G input $USER && reboot"
fi
```

**Recommendation**: Implement **A → B → C** fallback chain:
1. **Option A (primary)**: udev `uaccess` ACL — works on systemd systems immediately, no wrapper modification needed.
2. **Option B (fallback)**: `sg input` re-exec in wrapper — works on non-systemd systems (WSL, containers, OpenRC) where `uaccess` is a no-op.
3. **Option C (last resort)**: Warning to user — for cases where neither ACL nor `sg` are available.

Add a check to detect which path is needed:
```bash
# After udev rule is applied, detect if ACL was granted
if getfacl /dev/input/event* 2>/dev/null | grep -q "user:$USER"; then
    echo "  ✓ udev ACL active (immediate trackpad access)"
else
    echo "  ⚠ udev ACL not applied (non-systemd?). Installing sg fallback..."
    # Option B is implemented in the wrapper script (installed by install.sh)
fi
```

### T3: Add post-install verification that ESC key event path works
Add a lightweight test to `tests/` that can be run after install:

```python
# tests/test_esc_key_routing.py
"""Verify ESC key reaches the engine's do_process_key_event."""
# Strategy: Start engine in --test mode, programmatically send a 
# Gdk.EventKey(GDK.KEY_Escape) to the window, verify on_key_esc is called.
```

This should:
1. Start the engine in `--test` mode
2. Create the `HandwriteWin` window
3. Send a synthesized ESC key event
4. Verify `_state` transitions from 0 to 1 (pause state)
5. Verify `_state` transitions from 1 to close

### T4: Add ESC diagnostic to `tools/diagnose_trackpad.sh`
The existing `diagnose_trackpad.sh` script should also check the `input` group and IBus key routing:

```bash
# Check input group
echo "=== Input Group ==="
groups "$USER" | grep -q '\binput\b' && echo "✅ User is in input group" || echo "❌ User is NOT in input group (logout required)"
cat /proc/$$/status | grep -q "Groups:.*995" && echo "✅ Input group active in session" || echo "❌ Input group NOT active (need logout/login)"

# Check no stale root ibus-daemon
echo "=== IBus Daemon ==="
pgrep -u root ibus-daemon > /dev/null && echo "❌ ROOT ibus-daemon running (kill with: sudo pkill -u root ibus-daemon)" || echo "✅ No root ibus-daemon"
pgrep -u "$USER" ibus-daemon > /dev/null && echo "✅ User ibus-daemon running" || echo "⚠ ibus-daemon not running (start with: ibus-daemon --daemonize --replace)"
```

### T5: Add `ibus restart` call to install script (verify it's happening)
**Status**: Already present in `install.sh`. Verify it still runs after the fix-root-ibus-daemon changes.

Check `tools/install.sh` step order:
1. Kill root ibus-daemon → 2. Install files → 3. `ibus restart` → 4. `ibus engine handwrite-chinese`

If `ibus restart` happens AFTER the engine is set as active, the engine might be reset. The correct order:
1. Install files
2. `ibus restart` 
3. Wait for ibus-daemon to be ready
4. `ibus engine handwrite-chinese`

---

## Verification

After implementing all fix items:

### Manual test
```bash
# 1. Clean test: start from a fresh terminal (no input group)
#    Verify that tools/diagnose_trackpad.sh shows the issue

# 2. Run install (or re-run install)
sudo ./tools/install.sh

# 3. Verify the udev ACL is applied
getfacl /dev/input/event* 2>/dev/null | grep -c "user:$USER"

# 4. Test ESC in test mode
python3 src/ibus-engine-handwrite-chinese --test
# Press ESC in the test window → should show "Paused" overlay
# Press ESC again → should close

# 5. Test ESC in IBus mode
ibus engine handwrite-chinese
# Draw something, press ESC → should pause with overlay
# Press ESC again → should close and restore previous engine
```

### Automated test
```bash
cd tests/
python3 test_esc_key_routing.py  # (to be implemented in T3)
```

### Key indicators of success
- [ ] `getfacl /dev/input/event*` shows user has `rw` access immediately after install
- [ ] ESC in `--test` mode pauses and closes correctly
- [ ] ESC in IBus mode pauses and closes correctly
- [ ] No stale root `ibus-daemon` after install
- [ ] `diagnose_trackpad.sh` reports all checks green

---

## Notes
- This plan builds on top of `fix-root-ibus-daemon.md` (already executed) — both issues (root daemon + input group) needed to be fixed for ESC to work.
- The `input` group membership is a fundamental Linux limitation: supplementary groups are fixed at login time and can only be changed by:
  - Logging out and back in
  - Using `newgrp` / `sg` (per-process, not inherited)
  - Using `sudo` (security concern)
  - Using udev `uaccess` ACL (systemd-logind, best option)
- The udev `uaccess` approach is the recommended fix because it grants device access to the currently logged-in user immediately, without logout and without group membership.
