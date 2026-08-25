# fix-root-ibus-daemon — Draft

## Meta
- **intent**: clear
- **review_required**: false
- **status**: plan-written
- **pending_action**: wait for execution signal
- **approach**: fix restore.sh and install.sh to NOT run ibus commands as root; instead run them as the real user

## Root Cause Analysis

### What we found

**Two scripts invoke ibus commands as root — not intentionally, but because they run inside a `sudo` context.**

### restore.sh line 28 — PRIMARY BUG
```bash
ibus restart 2>/dev/null || ibus-daemon --replace --daemonize 2>/dev/null || true
```
When the user runs `sudo bash restore.sh` (as instructed), `ibus restart` executes as **root**. Root has no `DBUS_SESSION_BUS_ADDRESS` (sudo strips environment, and `DBUS_SESSION_BUS_ADDRESS` is NOT in `/etc/sudoers` `env_keep`). Root also has no `XDG_RUNTIME_DIR` (no `/run/user/0/`) and no systemd user instance (`pam_systemd` is NOT in `/etc/pam.d/sudo`).

So GLib's GDBus auto-launches a root-owned session dbus-daemon (PID 20892) at `/tmp/dbus-N3Wf0xEO2o`, and `ibus-daemon --replace --daemonize` connects to it (PID 22188). When sudo exits, all these processes become orphans (PPID=1) and persist indefinitely.

### install.sh lines 181-195 — SECONDARY BUG
```bash
# Step 【8】 (line 182-188):
pkill -u root ibus-daemon 2>/dev/null || true  # tries to kill root daemon — but WITHOUT sudo, so it silently fails for non-root users

# Step 【9】 (line 195):
ibus-daemon --daemonize --replace 2>/dev/null || true  # also runs as root if script was invoked with sudo
```

### Systemd/PAM details (why root has no session bus)
| Check | Result |
|-------|--------|
| `sudo` preserves DBUS_SESSION_BUS_ADDRESS? | NO — not in `env_keep` |
| `pam_systemd` in `/etc/pam.d/sudo`? | NO — uses `common-session-noninteractive` (no pam_systemd) |
| `pam_systemd` in `/etc/pam.d/sudo-i`? | YES — but scripts don't use `sudo -i` |
| Root has systemd --user instance? | NO — only mint has one (PID 1736) |
| Root has `/run/user/0/`? | NO — no runtime dir |
| Root's ibus-daemon status? | **ALIVE** (PID 22188, started 04:37:47, PPID=1, env empty) |
| Root's dbus-daemon status? | **ALIVE** (PID 20892, started 04:33:30, socket at `/tmp/dbus-N3Wf0xEO2o`) |
| User mint's ibus-daemon status? | **ALIVE** (PID 23428, started 04:45:45) |

### Evidence from running processes
```
ROOT TREE (PID 22188, orphaned PPID=1, env empty):
  ibus-daemon --replace --daemonize
  ├─ ibus-memconf
  ├─ ibus-ui-gtk3
  ├─ ibus-extension-gtk3
  ├─ ibus-portal
  └─ ibus-engine-simple
  root dbus-daemon (PID 20892) at /tmp/dbus-N3Wf0xEO2o

USER TREE (PID 23428, normal desktop session):
  ibus-daemon --daemonize --replace
  ├─ ibus-memconf
  ├─ ibus-ui-gtk3
  ├─ ibus-extension-gtk3
  ├─ ibus-portal
  └─ ibus-engine-simple
  user dbus-daemon at /run/user/1000/bus
```

## Decisions
- **Fix approach**: Make ibus commands in restore.sh and install.sh run as the original user, not as root:
  - restore.sh: use `sudo -u "$SUDO_USER" ibus restart` or `sudo -u "$SUDO_USER" ibus-daemon --daemonize --replace`
  - install.sh: use `sudo -u "$REAL_USER" ibus-daemon --daemonize --replace`
  - Also fix step 8 to actually kill root daemon when needed
- **Scope**: Only `tools/restore.sh` (line 28) and `tools/install.sh` (lines 183, 195)
- **Not doing**: No changes to the sudo wrapper, no new features, no refactoring
