## [2026-07-05] — fix-root-ibus-daemon — Execution complete

### Root cause
`restore.sh` and `install.sh` ran `ibus restart` / `ibus-daemon` as **root** (because sudo context), causing GLib to auto-launch a root-owned session dbus-daemon + root ibus-daemon. Root has no `DBUS_SESSION_BUS_ADDRESS`, `XDG_RUNTIME_DIR`, or systemd --user → orphan daemons at PPID=1 after sudo exits.

### Fix applied
**tools/restore.sh:**
- Added `REAL_USER="${SUDO_USER:-${USER:-root}}"` at line 14
- Changed line 28 from bare `ibus restart ...` to `sudo -u "$REAL_USER" ibus restart ...`
- Uses real `sudo` (restore.sh has no `sudo() { "$@"; }` wrapper)

**tools/install.sh:**
- Step 8 (line 183): `pkill` → `sudo pkill -u root ibus-daemon` (works through both real sudo and `sudo() { "$@"; }` wrapper)
- Step 9 (lines 195-199): Replaced `ibus-daemon --daemonize --replace` with conditional:
  - If root (`$(id -u) -eq 0`): run `ibus-daemon` directly (avoids `sudo -u` through the wrapper)
  - If not root: `sudo -u "$REAL_USER" ibus-daemon --daemonize --replace`

### Key gotchas discovered
- `$SUDO_USER` is empty when a script runs without sudo → must use `REAL_USER="${SUDO_USER:-${USER:-root}}"` for fallback
- The `sudo() { "$@"; }` wrapper in install.sh strips `-u` flags → use conditional, not `sudo -u` through wrapper
- Grep-based acceptance criteria fail on multi-line patterns — use `sed -n` or `pcregrep` instead

### Final system state
- Root ibus-daemon: 0 (cleaned, fix prevents regrowth)
- User ibus-daemon: 1 (functional)
- `ibus engine` responds normally
