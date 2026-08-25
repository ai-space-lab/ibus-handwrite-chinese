# 14-fix-touchpad-not-working-after-deb-install — Work Plan

## TL;DR (For humans)

**What you'll get:** Installing via `.deb`/`.rpm`/Arch package will give a working touchpad — same as `tools/install.sh`. Right now the UI appears but drawing on the touchpad does nothing.

**Root cause (single blocker):** The engine needs to `import handwrite_evdev` at startup to enable trackpad support. Python can only find this module if there's a symlink at `/usr/local/share/ibus-handwrite-chinese/handwrite_evdev.py → /usr/local/bin/handwrite_evdev.py` (Python adds the engine script's directory to `sys.path`). `install.sh` creates this symlink (line 142); the package post-install scripts do not. Without it, `EVDEV_AVAILABLE = False` and `start_trackpad()` returns immediately — the engine runs in mouse-only mode.

**Why no `usermod` is needed:** The udev rule `TAG+="uaccess"` (systemd-logind standard) already grants the logged-in console user read access to the trackpad device via ACL — no group membership changes required. The postinst already calls `udevadm control --reload-rules && udevadm trigger` (Plan 13, lines 87-90) to apply it. The `sg input` wrapper fallback exists for non-systemd systems where `uaccess` doesn't apply — users on those systems can manually join the `input` group via `sudo usermod -a -G input $USER && reboot` (documented in the README).

**Fix:** Add the missing symlink creation to `.deb` postinst and Arch `.install`. The RPM is left as-is — it already installs `handwrite_evdev.py` directly in the engine directory (no symlink needed since the file is already on Python's `sys.path`).

## Must have
1. Add `handwrite_evdev.py` symlink to `.deb` postinst and Arch `.install` post_install
2. No change to RPM spec — RPM already installs `handwrite_evdev.py` directly in the engine directory (under `/usr/local/share/ibus-handwrite-chinese/`), which is already on Python's `sys.path`. No symlink needed.
3. Keep all existing postinst improvements from Plan 13
4. All bash -n syntax checks pass
5. Release workflow test-packages passes on all 10 distros

## Must NOT have
- Do NOT add `usermod` to postinst (postinst should not manage per-user group membership; `uaccess` handles device access on modern systems)
- Do NOT add stale root ibus-daemon kill, restart polling, or user daemon pgrep check
- Do NOT add automated `ibus restart` block
- Do NOT change install.sh or bootstrap.sh
- Do NOT change release.yml workflow

## Verification strategy
### Symlink check (.deb & Arch)
```bash
readlink /usr/local/share/ibus-handwrite-chinese/handwrite_evdev.py | grep -q '/usr/local/bin/handwrite_evdev.py' && echo "SYMLINK OK" || echo "SYMLINK MISSING"
```

### RPM verification (no symlink needed — file is already in engine dir)
```bash
ls -la /usr/local/share/ibus-handwrite-chinese/handwrite_evdev.py && echo "RPM OK" || echo "RPM MISSING"
```

### Runtime verification
```bash
ibus restart
ibus engine handwrite-chinese
# Draw on trackpad — strokes should appear in the writing UI
```

## Execution strategy
### Parallel batches
Batch 1 (2 parallel): T1 .deb, T2 Arch
Batch 2 (sequential): T3 commit + push + release workflow dispatch

## Todos
- [x] 1. Fix `.deb` postinst
   **File: `packaging/debian/postinst`** — add symlink after wrapper chmod (line 84), before udev reload (line 87):
   ```sh
   # --- handwrite_evdev.py symlink (for Python import) ---
   ln -sf /usr/local/bin/handwrite_evdev.py /usr/local/share/ibus-handwrite-chinese/handwrite_evdev.py
   ```
   No changes needed to `build-deb.sh` or `debian/install` (handwrite_evdev.py already installed to `/usr/local/bin/`).
   
- [x] 2. Fix Arch `.install` post_install
   **`.install` changes** (after wrapper chmod, before udev reload): Add same symlink line as T1.
   **PKGBUILD**: Already installs to `/usr/local/bin/` (line 22) — no change needed.
   **No change to RPM** — `handwrite_evdev.py` is already installed directly in the engine directory (`/usr/local/share/ibus-handwrite-chinese/`), which is on Python's `sys.path`. No symlink needed.

- [x] 3. CI verify: commit pushed (71aa1df), release workflow 16/16 pass ✅

## Commit strategy
Single commit on main:
`fix: add handwrite_evdev.py symlink to .deb and Arch postinsts for trackpad access`

## Success criteria
- [ ] After `.deb` install: `readlink /usr/local/share/ibus-handwrite-chinese/handwrite_evdev.py` → `/usr/local/bin/handwrite_evdev.py`
- [ ] After Arch install: symlink present (same check as .deb)
- [ ] After RPM install: `handwrite_evdev.py` exists at `/usr/local/share/ibus-handwrite-chinese/handwrite_evdev.py` (file already in engine dir — no symlink needed)
- [ ] `ibus restart && ibus engine handwrite-chinese` → engine starts, trackpad strokes appear in UI
- [x] Release workflow test-packages passes on all 10 distros ✅
