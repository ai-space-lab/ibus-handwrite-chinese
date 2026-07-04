## TL;DR (For humans)

Remove the "you must run this as root" guard from `install.sh`, `restore.sh`, and `bootstrap.sh`. Instead, individual commands that need root (installing packages, writing to `/usr`, `/etc`) get `sudo` internally. Everything else (downloading files, `ibus restart`, `git clone`) runs as your normal user. The change is purely mechanical — no logic changes, just prefixing ~20 commands with `sudo`.

---

# Plan: sudo-less-install

## Overview

**Goal**: Allow users to run `./tools/install.sh` and `./tools/restore.sh` without `sudo` prefix at the top level. Only commands that genuinely require root privileges get `sudo` internally.

**Source of truth**: This plan. Every change is enumerated. Any deviation must be documented.

**Must-NOT-Have**:
- No new `EUID` checks added
- No `sudo` on user-context commands (`ibus restart`, `ibus-daemon`, `wget`, `git clone`)
- No changes to CI workflows (they run as root, already work)
- No changes to `tools/build-test-usb-iso.sh` (inherently root-only)
- No changes to `packaging/*` (run under dpkg/fakeroot)

---

## Todos

### Todo 1: `tools/install.sh` — Remove root guard + add sudo to apt commands

**Where**: `tools/install.sh` lines 11-28
**Why**: Remove the `EUID -ne 0` block; prefix package manager commands with sudo
**How**: Delete the root-check block; add `sudo` to `apt-get update` and `apt-get install`; preserve `DEBIAN_FRONTEND=noninteractive` inline
**Expected result**: Running `./tools/install.sh` as a normal user no longer exits with "Please run as root"

**Changes**:
- Delete lines 11-14 (`[ "$EUID" -ne 0 ]` block)
- Line 23: `apt-get update` → `sudo apt-get update`
- Line 24: `DEBIAN_FRONTEND=noninteractive apt-get install` → `sudo DEBIAN_FRONTEND=noninteractive apt-get install`
- Line 27: update message to say `./tools/install.sh --skip-deps` (without sudo)

**QA**: `shellcheck tools/install.sh` passes. Run `./tools/install.sh --skip-deps --no-restart` — should NOT print "Please run as root".

---

### Todo 2: `tools/install.sh` — Add sudo to system file operations

**Where**: `tools/install.sh` lines 39-136 (all operations writing to `/usr/local`, `/usr/share`, `/etc`)
**Why**: These paths require root to write
**How**: Prefix every `mkdir -p`, `cp`, `chmod`, `rm -rf`, and `python3 -m venv` that touches system directories with `sudo`. The wrapper script heredoc uses `sudo tee` instead of `cat >`.

**Complete list of lines to change**:

| Line | Current | New |
|------|---------|-----|
| 45 | `mkdir -p "$PPOCR_MODEL_DIR"` | `sudo mkdir -p "$PPOCR_MODEL_DIR"` |
| 52 | `cp "$tmpdir/inference.onnx" "$PPOCR_MODEL_FILE"` | `sudo cp "$tmpdir/inference.onnx" "$PPOCR_MODEL_FILE"` |
| 63 | `cp "$tmpdir/dict.txt" "$PPOCR_DICT_FILE"` | `sudo cp "$tmpdir/dict.txt" "$PPOCR_DICT_FILE"` |
| 80 | `cp src/handwrite_evdev.py /usr/local/bin/` | `sudo cp src/handwrite_evdev.py /usr/local/bin/` |
| 81 | `chmod 644 /usr/local/bin/handwrite_evdev.py` | `sudo chmod 644 /usr/local/bin/handwrite_evdev.py` |
| 87 | `python3 -m venv --system-site-packages "$VENV_DIR"` | `sudo python3 -m venv --system-site-packages "$VENV_DIR"` |
| 94 | `"$VENV_DIR/bin/pip" install onnxruntime` | `sudo "$VENV_DIR/bin/pip" install onnxruntime` |
| 102-113 | wrapper script via `cat >` | Use `sudo tee` (see below) |
| 116 | `cp src/ibus-engine-handwrite-chinese ...` | `sudo cp src/ibus-engine-handwrite-chinese /usr/local/share/ibus-handwrite-chinese/` |
| 117 | `chmod 644 .../ibus-engine-handwrite-chinese` | `sudo chmod 644 /usr/local/share/ibus-handwrite-chinese/ibus-engine-handwrite-chinese` |
| 120 | `mkdir -p /usr/share/ibus/component` | `sudo mkdir -p /usr/share/ibus/component` |
| 121 | `cp xml/handwrite-chinese.xml ...` | `sudo cp xml/handwrite-chinese.xml /usr/share/ibus/component/` |
| 124 | `mkdir -p /etc/udev/rules.d` | `sudo mkdir -p /etc/udev/rules.d` |
| 125 | `cp tools/99-trackpad-handwrite.rules ...` | `sudo cp tools/99-trackpad-handwrite.rules /etc/udev/rules.d/` |
| 126 | `udevadm control --reload-rules` | `sudo udevadm control --reload-rules` |
| 127 | `udevadm trigger` | `sudo udevadm trigger` |
| 130 | `mkdir -p /usr/local/share/ibus-handwrite-chinese` | `sudo mkdir -p /usr/local/share/ibus-handwrite-chinese` |
| 131 | `cp tools/restore.sh ...` | `sudo cp tools/restore.sh /usr/local/share/ibus-handwrite-chinese/` |
| 132 | `chmod 755 .../restore.sh` | `sudo chmod 755 /usr/local/share/ibus-handwrite-chinese/restore.sh` |
| 135 | `mkdir -p .../icons` | `sudo mkdir -p /usr/local/share/ibus-handwrite-chinese/icons` |
| 136 | `cp icons/...` | `sudo cp icons/handwrite-chinese.svg /usr/local/share/ibus-handwrite-chinese/icons/` |

**Wrapper script change** (lines 102-113):
```bash
# Old:
cat > /usr/local/bin/ibus-engine-handwrite-chinese << 'WRAPPER'
...
WRAPPER
chmod 755 /usr/local/bin/ibus-engine-handwrite-chinese

# New:
sudo tee /usr/local/bin/ibus-engine-handwrite-chinese > /dev/null << 'WRAPPER'
...
WRAPPER
sudo chmod 755 /usr/local/bin/ibus-engine-handwrite-chinese
```

**Do NOT change**:
- Line 142: `ibus restart` / `ibus-daemon` — these stay WITHOUT sudo (runs as user)

**Expected result**: All system-wide file operations prompt for sudo password once (then cached).

**QA**: `shellcheck tools/install.sh` passes. Verify no "Permission denied" errors when running `./tools/install.sh --skip-deps --no-restart`.

---

### Todo 3: `tools/restore.sh` — Remove root guard + add sudo to destructive commands

**Where**: `tools/restore.sh` lines 4-23
**Why**: Remove root guard; prefix rm/udevadm with sudo; keep ibus restart as user
**How**: Delete lines 4-7; add sudo to all rm and udevadm lines

**Changes**:
- Delete lines 4-7 (`[ "$EUID" -ne 0 ]` block)
- Line 13: `rm -f /usr/local/bin/ibus-engine-handwrite-chinese` → `sudo rm -f /usr/local/bin/ibus-engine-handwrite-chinese`
- Line 14: `rm -f /usr/local/bin/handwrite_evdev.py` → `sudo rm -f /usr/local/bin/handwrite_evdev.py`
- Line 15: `rm -f /usr/share/ibus/component/handwrite-chinese.xml` → `sudo rm -f /usr/share/ibus/component/handwrite-chinese.xml`
- Line 16: `rm -f /etc/udev/rules.d/99-trackpad-handwrite.rules` → `sudo rm -f /etc/udev/rules.d/99-trackpad-handwrite.rules`
- Line 17: `rm -rf /usr/local/share/ibus-handwrite-chinese` → `sudo rm -rf /usr/local/share/ibus-handwrite-chinese`
- Line 20: `udevadm control --reload-rules` → `sudo udevadm control --reload-rules`
- Line 23: `ibus restart` / `ibus-daemon` → keep WITHOUT sudo

**Expected result**: `./tools/restore.sh` runs as normal user, uses sudo only for delete operations.

**QA**: `shellcheck tools/restore.sh` passes.

---

### Todo 4: `bootstrap.sh` — Remove root guard + add sudo to package manager commands

**Where**: `bootstrap.sh` lines 12-67
**Why**: Remove root guard; prefix distro-specific package install commands with sudo
**How**: Delete the EUID block; add sudo to apt/dnf/pacman/zypper commands

**Changes**:
- Delete lines 12-15 (`[ "$EUID" -ne 0 ]` block)
- Line 50: `apt update` → `sudo apt update`
- Line 51: `apt install -y ...` → `sudo apt install -y ...`
- Line 55: `dnf install -y ...` → `sudo dnf install -y ...`
- Line 59: `pacman -S --noconfirm ...` → `sudo pacman -S --noconfirm ...`
- Line 63: `zypper --no-gpg-checks refresh` → `sudo zypper --no-gpg-checks refresh`
- Line 64: `zypper install -y ...` → `sudo zypper install -y ...`
- Line 66: `zypper --no-gpg-checks install -y ...` → `sudo zypper --no-gpg-checks install -y ...`
- Do NOT change: `git clone`, `mktemp`, `cd`, `exec ./tools/install.sh`

**Expected result**: `bash bootstrap.sh` runs as normal user, uses sudo only for package manager calls.

**QA**: `shellcheck bootstrap.sh` passes.

---

### Todo 5: `README.md` — Update install instructions

**Where**: `README.md` lines around "Quick Install" section
**Why**: Instructions show `sudo ./tools/install.sh` — should be `./tools/install.sh` now
**How**: Replace `sudo ./tools/install.sh` with `./tools/install.sh` (with note that sudo is used internally)

**Changes**:
- Line ~47-50 (Quick Install section): `sudo ./tools/install.sh    # add --skip-deps if deps already installed` → `./tools/install.sh    # add --skip-deps if deps already installed; sudo used internally`
- Keep the `ibus restart` line as-is (it was already user-level)

**Expected result**: README reflects that top-level sudo is no longer needed.

---

### Todo 6: Final verification wave

**Why**: Confirm all changes are correct and consistent
**How**: Run shellcheck on all three scripts, verify no "Please run as root" remains, verify no `sudo` on `ibus restart`

**Checks**:
1. `grep -n "Please run as root" tools/install.sh tools/restore.sh bootstrap.sh` → should return no matches
2. `grep -n "ibus restart\|ibus-daemon" tools/install.sh tools/restore.sh bootstrap.sh` → confirm these lines have NO `sudo` prefix
3. `shellcheck -e SC1091 bootstrap.sh tools/install.sh tools/restore.sh` → all pass
4. `grep -n "EUID" tools/install.sh tools/restore.sh bootstrap.sh` → should return no matches (the `$EUID` ~= USER check inside install.sh for apt availability is OK since it checks `$EUID` vs `$USER` but that's actually on line... wait, no — there's no other EUID usage. Let me verify: the only EUID checks are the ones we're removing.)

**Expected result**: Clean verification output.
