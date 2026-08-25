# Plan: Restart IBus after package install

## Goal

After a user installs a release package (`.deb`, `.rpm`, or Arch PKGBUILD), IBus should be restarted automatically so the engine is immediately available — no manual `ibus restart` needed.

## Current State

All three package formats already run post-install scripts that download the PP-OCRv6 model, create the Python venv with onnxruntime, install the wrapper script, and reload udev rules. **None run `ibus restart`** — the user sees a message like "Restart IBus: ibus restart" and must do it manually.

| Package | Post-install script | Runs `ibus restart`? |
|---------|-------------------|---------------------|
| `.deb` | `packaging/debian/postinst` | ❌ (message only) |
| `.rpm` | `%post` in `packaging/ibus-handwrite-chinese.spec` | ❌ |
| Arch | `post_install` in `packaging/ibus-handwrite-chinese.install` | ❌ (message only) |

Additionally, the CI release workflow (`release.yml`) installs packages during verification but never restarts IBus before testing.

## T1: Add `ibus restart` to `.deb` postinst

**File**: `packaging/debian/postinst`

Add `ibus restart` before the final `exit 0`, wrapped in a non-fatal guard:

```bash
# --- Restart IBus ---
echo "Restarting IBus..."
if command -v ibus >/dev/null 2>&1; then
    if [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
        if [ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
            ibus restart 2>/dev/null || \
                echo "  ⚠ ibus restart failed (will take effect on next login)"
        else
            echo "  ⚠ No D-Bus session — IBus will be available after next login"
        fi
    else
        echo "  ⚠ No display detected — IBus will be available after login"
    fi
else
    echo "  ⚠ ibus command not found"
fi
```

The guard checks:
1. `ibus` binary exists
2. A display (`DISPLAY` or `WAYLAND_DISPLAY`) is set — in Docker/containers without a session, `ibus restart` would fail anyway
3. `DBUS_SESSION_BUS_ADDRESS` is set — this is often stripped by `sudo`'s `env_reset`; without it `ibus restart` cannot reach the user's session bus. If missing, print a warning.
4. If anything fails, print a warning but don't abort the install (`|| true` pattern)

## T2: Add `ibus restart` to `.rpm` spec `%post`

**File**: `packaging/ibus-handwrite-chinese.spec`

Add the same block after line 136 (the `fi` closing the udev reload block, before `%preun` at line 138). `%post` has no explicit closing marker — it ends implicitly before the next `%` section header.

## T3: Add `ibus restart` to Arch `.install` `post_install()`

**File**: `packaging/ibus-handwrite-chinese.install`

Replace lines 22–24:
```bash
    echo ""
    echo "Installation complete. Restart IBus: ibus restart"
    echo "Then select Chinese Handwriting from your IBus menu."
```
with the same `ibus restart` block from T1. Keep the two echo messages as a fallback inside the outer `else` branch (when `ibus` command not found):

```bash
    echo ""
    echo "Restarting IBus..."
    if command -v ibus >/dev/null 2>&1; then
        if [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
            if [ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
                ibus restart 2>/dev/null || \
                    echo "  ibus restart failed (will take effect on next login)"
            else
                echo "  No D-Bus session — IBus will be available after next login"
            fi
        else
            echo "  No display detected — IBus will be available after login"
        fi
        echo "Then select Chinese Handwriting from your IBus menu."
    else
        echo "  ibus command not found"
        echo "Installation complete. Restart IBus: ibus restart"
        echo "Then select Chinese Handwriting from your IBus menu."
    fi
```

## T4: Add `ibus restart` to CI test-packages in release workflow

**File**: `.github/workflows/release.yml`

After package installation + model download + venv setup (step `Install package`), add a step to restart IBus before running the GTK write test:

```yaml
- name: Restart IBus
  run: |
    if command -v ibus >/dev/null 2>&1; then
      ibus restart 2>/dev/null || true
    fi
```

This makes the test-packages job test the actual post-install flow end-to-end.

## T5: Remove `--no-restart` flag from CI Arch install

**File**: `.github/workflows/release.yml` line 223

Currently the Arch test installs with:
```yaml
(cd "$tmpdir" && ./tools/install.sh --skip-deps --no-restart)
```

The `--no-restart` flag was added to avoid failures in containers without a display. Remove `--no-restart` so the test exercises the full `install.sh` flow (including its own restart logic — `ibus-daemon --daemonize --replace` wrapped in `|| true`):

```yaml
(cd "$tmpdir" && ./tools/install.sh --skip-deps)
```

**Note:** Unlike T1/T2/T3, `install.sh` does **not** have a `DISPLAY`/`WAYLAND_DISPLAY` guard — it calls `ibus-daemon --daemonize --replace` directly. In the Arch container (no D-Bus session), this will fail silently (`2>/dev/null || true`) and then enter a 5-second polling loop before timing out. This is non-fatal (the CI step passes), but adds ~5s to the Arch test runtime. If this delay is undesirable, skip T5 and keep `--no-restart` — the Arch CI tests source-based install, not the package post-install, so removing the flag does not directly validate the plan's package-focused goal.

## Acceptance Criteria

- [x] After `dpkg -i ibus-handwrite-chinese_*.deb`, IBus is restarted (user sees "Restarting IBus..." message)
- [x] After `rpm -i ibus-handwrite-chinese-*.rpm`, IBus is restarted
- [x] After Arch PKGBUILD install, IBus is restarted
- [x] `ibus restart` is non-fatal — if run in a container without a display, it prints a warning and exits 0
- [x] CI release workflow test-packages job passes with the restart step included
- [x] `--no-restart` is removed from the Arch CI install in release.yml (or kept if the ~5s poll delay is undesirable — see T5 note)

## Verification

### Per-package manual test
```bash
# .deb test
docker run --rm -it debian:bookworm bash
# install deps, dpkg -i the .deb
# observe "Restarting IBus..." in postinst output
# verify: ibus restart actually ran (check with echo $? — should be 0 or warning)

# .rpm test
docker run --rm -it fedora:latest bash
# install deps, rpm -i the .rpm
# observe "Restarting IBus..." in %post output

# Arch test
# build PKGBUILD, install
# observe "Restarting IBus..." output
```

### CI verification
The release workflow `test-packages` job will automatically test all 10 distro variants. Green CI = pass.

## Non-goals

- This plan does NOT change how `install.sh` or `bootstrap.sh` work — they already restart IBus. Only package post-install scripts are changed.
- T5 is optional: removing `--no-restart` from the Arch CI `install.sh` invocation exercises its restart path (which has no display guard and adds ~5s CI polling timeout). If this is undesirable, skip T5.
