# fix-root-ibus-daemon — Work Plan

## TL;DR (For humans)

**What you'll get:** The Chinese handwriting install and restore scripts will no longer leave a stale root-owned ibus-daemon running alongside the user's daemon. This eliminates the "two ibus tray icons" bug.

**Why this approach (not adding `sudo` to `pkill`):** The root cause is that `restore.sh` and `install.sh` run `ibus restart` and `ibus-daemon` commands as **root** (because they execute inside `sudo`), not as the real user. Root has no `DBUS_SESSION_BUS_ADDRESS`, no `XDG_RUNTIME_DIR`, and no systemd user instance — so GLib auto-launches a root-owned session dbus-daemon, spawns a root ibus-daemon, and both persist as orphans after sudo exits. The fix is to run ibus commands as the **original user** (`$REAL_USER`), not as root.

**What it will NOT do:** It won't modify `bootstrap.sh`, won't modify any Python files, won't add new features. It won't add `sudo` as a workaround for the `pkill` — it eliminates the reason a root ibus-daemon exists in the first place.

**Effort:** Small — 2 files, 3 line changes.
**Risk:** Low — `sudo -u "$REAL_USER" ibus restart` (with `$SUDO_USER`→`$USER`→`root` fallback) is the standard pattern for running user commands after sudo escalation.

## Scope
### Must have
1. Fix `restore.sh` line 28: `ibus restart` and `ibus-daemon` must run as the original user via `sudo -u "$REAL_USER"`, not as root
2. Fix `install.sh` step 【9】 (line 195): `ibus-daemon --daemonize --replace` must run as `$REAL_USER`, not as root
3. Fix `install.sh` step 【8】 (line 183): `pkill -u root ibus-daemon` must use `sudo` to actually succeed when a stale root daemon exists (safety net)
4. Clean up existing stale root ibus-daemon and root dbus-daemon from the system
5. Verify only ONE user ibus-daemon runs after fix

### Must NOT have (guardrails)
- No changes to `bootstrap.sh`
- No changes to Python source files
- No changes to CI/CD workflows
- No new files or features
- No refactoring of the sudo wrapper or script structure
- No changes to `install.sh` beyond the two ibus command lines (183, 195)

## Background (why ibus runs as root)

| Check | Finding |
|-------|---------|
| `DBUS_SESSION_BUS_ADDRESS` after sudo? | **Stripped** — not in `/etc/sudoers` `env_keep` |
| `pam_systemd` in `/etc/pam.d/sudo`? | **No** — uses `common-session-noninteractive` |
| Root has systemd --user? | **No** — only mint has one |
| Root has `/run/user/0/`? | **No** — no XDG_RUNTIME_DIR |
| What happens when `ibus restart` runs as root? | GLib auto-launches root dbus-daemon at `/tmp/dbus-*`, ibus-daemon connects to it, both become PPID=1 orphans when sudo exits |

## Verification strategy
- Test decision: tests-after (manual shell-based verification)
- Evidence: `.omo/evidence/fix-root-ibus-daemon/` with command outputs
- Verify by: (a) checking current dual-daemon state, (b) applying fix, (c) cleaning root daemon, (d) confirming only user daemon remains

## Execution strategy
### Todos

### todo 1 — Fix restore.sh: run ibus commands as real user, not root

**What to do:**
Add a `REAL_USER` variable at the top of `restore.sh` (after the preamble, before the `echo` statements):
```bash
REAL_USER="${SUDO_USER:-${USER:-root}}"
```

Then change `tools/restore.sh` line 28 from:
```bash
ibus restart 2>/dev/null || ibus-daemon --replace --daemonize 2>/dev/null || true
```
to:
```bash
# Run ibus commands as the original user (not root), so they connect
# to the user's D-Bus session bus instead of auto-launching a root one.
sudo -u "$REAL_USER" ibus restart 2>/dev/null || \
  sudo -u "$REAL_USER" ibus-daemon --replace --daemonize 2>/dev/null || true
```

Key difference from the previous version: uses `$REAL_USER` (with `$USER` fallback) instead of `$SUDO_USER` (empty when run without sudo).

**Rationale:** `$SUDO_USER` is automatically set by `sudo` to the original calling user. When `bash restore.sh` runs normally (no sudo), `$SUDO_USER` is empty and `$USER` falls back to the current user. When `sudo bash restore.sh` runs, `$SUDO_USER` = `mint`.

**Must NOT do:**
- Do NOT change any other line in `restore.sh`
- Do NOT remove `|| true` (fallback for failure cases)
- Do NOT change the udevadm or rm commands earlier in restore.sh (those correctly run as root)

**References:** `tools/restore.sh:28`, sudoers `env_keep` config, exploration findings

**Acceptance criteria (agent-executable):**
```bash
# Verify REAL_USER variable was added at top:
grep -q 'REAL_USER="\${SUDO_USER:-\${USER:-root}}"' /home/mint/projects/ibus-handwrite-chinese/tools/restore.sh

# Verify fix applied with $REAL_USER (not $SUDO_USER):
grep -q 'sudo -u "\$REAL_USER" ibus restart' /home/mint/projects/ibus-handwrite-chinese/tools/restore.sh

# Verify shell syntax:
bash -n /home/mint/projects/ibus-handwrite-chinese/tools/restore.sh

# Verify that running the command as the real user does NOT create a root ibus-daemon:
pgrep -u root ibus-daemon >/dev/null && echo "root daemon exists (needs cleanup)" || echo "no root daemon"
```

**QA scenarios:**
- Happy: After cleanup, `sudo pkill -u root ibus-daemon; sudo pkill -f "dbus-daemon.*session" -U root`, then `sudo bash restore.sh` leaves no root ibus-daemon
- `bash restore.sh` without sudo: `$SUDO_USER` empty → `$REAL_USER` falls back to `$USER` (e.g., mint) → `sudo -u "mint" ibus restart` works correctly
- `sudo bash restore.sh`: `$SUDO_USER` set → `$REAL_USER=mint` → same behavior, ibus runs as mint

**Evidence:** `.omo/evidence/fix-root-ibus-daemon/restore-sh-fix.txt`

**Commit:** Y | `fix(restore): run ibus restart as real user, not root`

### todo 2 — Fix install.sh steps 8 and 9: kill root daemon with sudo, restart as real user

**What to do:**

Change A — Step 【8】 (line 183): make the kill actually work by adding `sudo`:
```bash
# Before:
pkill -u root ibus-daemon 2>/dev/null || true
# After:
sudo pkill -u root ibus-daemon 2>/dev/null || true
```

Change B — Step 【9】 (line 195): ensure ibus-daemon restarts as the real user, not root. Must NOT use `sudo -u "$REAL_USER"` unconditionally because the `sudo() { "$@"; }` wrapper (active when running as root) strips `-u` flags — `sudo -u "$REAL_USER" ibus-daemon` becomes trying to run `-u` as a command.
```bash
# Before:
ibus-daemon --daemonize --replace 2>/dev/null || true
# After — conditional: if already root run directly, else use sudo -u:
{ if [ "$(id -u)" -eq 0 ]; then
    ibus-daemon --daemonize --replace 2>/dev/null
  else
    sudo -u "$REAL_USER" ibus-daemon --daemonize --replace 2>/dev/null
  fi; } || true
```

**Rationale for Change A:** `pkill -u root ibus-daemon` without sudo silently fails when called by a non-root user (Linux signal permission model). Adding `sudo` makes it work as a safety net when a stale root daemon exists.

**Rationale for Change B:** `$REAL_USER` is already defined at line 30 as `"${SUDO_USER:-${USER:-root}}"`. When install.sh runs via `sudo ./install.sh`, `SUDO_USER=mint` → `REAL_USER=mint`. When running without sudo, `USER=mint` → `REAL_USER=mint`. In Docker CI (as root), `SUDO_USER` is unset, `USER` is unset → `REAL_USER=root`.  

The conditional form handles all three invocation modes correctly:
- **Root mode** (Docker CI, `sudo ./install.sh`): `$(id -u) -eq 0` is true → runs `ibus-daemon` directly (no `-u` wrapper issue) → connects to whatever bus is available (which is fine — CI has no desktop session)
- **Non-root mode** (`./install.sh` via bootstrap): `$(id -u)` ≠ 0 → runs `sudo -u "$REAL_USER" ibus-daemon` with the REAL `sudo` command → runs as the user, connects to user's session bus ✓

**Must NOT do:**
- Do NOT change any other line in `install.sh`
- Do NOT remove `|| true` from either line
- Do NOT change the `REAL_USER` variable definition (line 30)

**References:** `tools/install.sh:181-201`, `tools/install.sh:30`

**Acceptance criteria (agent-executable):**
```bash
# Verify sudo pkill fix:
grep -q 'sudo pkill -u root' /home/mint/projects/ibus-handwrite-chinese/tools/install.sh

# Verify step 9 conditional — checks for the id -u pattern:
grep -q 'id -u.*-eq 0.*ibus-daemon' /home/mint/projects/ibus-handwrite-chinese/tools/install.sh

# Verify shell syntax:
bash -n /home/mint/projects/ibus-handwrite-chinese/tools/install.sh

# Verify the conditional logic is correct — when running as root,
# the ibus-daemon command should NOT go through sudo -u:
grep -A5 'if \[ "\$(id -u)" -eq 0 \]' /home/mint/projects/ibus-handwrite-chinese/tools/install.sh | grep -q 'sudo -u' && echo "FAIL: sudo -u used in root path" || echo "PASS: no sudo -u in root path"
```

**QA scenarios:**
- Happy: After cleanup and fix, `sudo pkill -u root ibus-daemon; sudo pkill -f "dbus-daemon.*session" -U root`, then `bash bootstrap.sh` starts ibus-daemon as mint only
- Root mode (Docker CI, `sudo ./install.sh`): `$(id -u) -eq 0` → runs `ibus-daemon` directly → no `-u` wrapper issue → `|| true` catches any failure (Docker has no desktop ibus)
- Non-root mode (`./install.sh` from bootstrap): `$(id -u) ≠ 0` → runs `sudo -u "$REAL_USER" ibus-daemon` with real `sudo` → connects to user's session bus
- No stale root daemon: `sudo pkill` exits 1 (no match), `|| true` swallows it — same behavior as before

**Evidence:** `.omo/evidence/fix-root-ibus-daemon/install-sh-fix.txt`

**Commit:** Y | `fix(install): run ibus-daemon as real user; fix root daemon kill`

### todo 3 — Clean up existing stale root ibus-daemon and verify

**What to do:**
1. Kill the existing stale root ibus-daemon and its dbus-daemon:
   ```bash
   sudo pkill -u root ibus-daemon
   sudo pkill -u root ibus-memconf ibus-ui-gtk3 ibus-extension-gtk3 ibus-portal ibus-engine-simple
   sudo kill 20892  # root's dbus-daemon PID, or:
   sudo pkill -f "dbus-daemon --syslog-only.*--session" -U root
   ```
2. Verify only the user's ibus-daemon remains:
   ```bash
   pgrep -u root ibus-daemon >/dev/null && echo "FAIL: root daemon still alive" || echo "PASS: root daemon gone"
   pgrep -u mint ibus-daemon >/dev/null && echo "PASS: user daemon alive" || echo "WARN: no user daemon"
   ```
3. Restart user's ibus-daemon if needed:
   ```bash
   ibus-daemon --daemonize --replace
   ```
4. Verify engine still works:
   ```bash
   timeout 3 ibus engine 2>/dev/null
   ```

**Must NOT do:**
- Do NOT modify any scripts (this is a one-time cleanup)
- Do NOT kill mint's ibus-daemon or dbus-daemon

**References:** `ps -elf` output, `/proc/*/environ` evidence

**Acceptance criteria (agent-executable):**
```bash
# No root ibus-daemon:
[ "$(pgrep -u root -x ibus-daemon 2>/dev/null | wc -l)" -eq 0 ]
# Only user's ibus-daemon:
[ "$(pgrep -u mint -x ibus-daemon 2>/dev/null | wc -l)" -eq 1 ]
```

**QA scenarios:**
- Happy: Both checks pass, `ibus engine` returns engine name
- Failure: If root daemon won't die, use `sudo kill -9` or check with `pstree`
- Edge: No user daemon after cleanup — restart with `ibus-daemon --daemonize --replace`

**Evidence:** `.omo/evidence/fix-root-ibus-daemon/cleanup-verify.txt`

**Commit:** N (cleanup only, no code changes)

## Final verification wave
> All must APPROVE. Surface results and wait for user's explicit okay.

- [x] F1. Plan compliance — all 3 todos complete, acceptance criteria met
- [x] F2. Code quality — `bash -n` passes on both scripts
- [x] F3. Real manual QA — no root ibus-daemon after fix+cleanup
- [x] F4. Scope fidelity — only `restore.sh` and `install.sh` changed

## Commit strategy
Two commits (one per script):

1. `fix(restore): run ibus restart as real user, not root` — `tools/restore.sh` only
2. `fix(install): run ibus-daemon as real user; fix root daemon kill` — `tools/install.sh` (lines 183, 195)

## Success criteria
1. ✅ `sudo bash restore.sh` leaves NO root ibus-daemon (commands run as real user)
2. ✅ `bash bootstrap.sh` leaves NO root ibus-daemon (install.sh steps 8+9 work correctly)
3. ✅ `pgrep -u root ibus-daemon | wc -l` = 0 after any script invocation
4. ✅ `pgrep -u mint ibus-daemon | wc -l` = 1 (user's daemon is the only one)
5. ✅ `bash -n` passes on both modified scripts
6. ✅ No changes outside `tools/restore.sh` and `tools/install.sh`
