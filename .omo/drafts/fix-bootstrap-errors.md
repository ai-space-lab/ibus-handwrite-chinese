---
slug: fix-bootstrap-errors
status: approved
intent: clear
review_required: false
pending-action: write .omo/plans/fix-bootstrap-errors.md
approach: Restore system to clean state, reproduce errors, identify root causes, then create minimal surgical fixes in bootstrap.sh and install.sh to handle the two failure modes
---

# Draft: fix-bootstrap-errors

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->

| id | outcome | status | evidence path |
|----|---------|--------|---------------|
| bs-apt-update | `bootstrap.sh:install_debian()` runs `sudo apt update`; fails when CD-ROM source is stale | active | `bootstrap.sh:60`, `install.sh:39` |
| bs-apt-install | `bootstrap.sh` runs `sudo apt install ...`; never reached if apt update fails | active | `bootstrap.sh:61` |
| is-apt-update | `install.sh` runs `sudo apt-get update \|\| echo "...continuing"` — already has error handling | active | `install.sh:39` |
| ibus-presence | Neither script ensures `ibus` is installed; `ibus restart` / `ibus engine` fail if absent | active | `install.sh:179,182,192` |
| cdroms-list | `/var/lib/apt/cdroms.list` contains Linux Mint installer CD-ROM entry | active | confirmed via `cat /var/lib/apt/cdroms.list` before removal: `CD::0c06d058567b95b94af55b76555d29d3-2 "Linux Mint 22.3 _Zena_ - Release amd64 20260108";` |

## Open assumptions (announced defaults)
<!-- Record any default you adopt instead of asking, so the user can veto it at the gate. -->
<!-- assumption | adopted default | rationale | reversible? -->

| assumption | adopted default | rationale | reversible? |
|-----------|----------------|-----------|-------------|
| IBus should always be installed | bootstrap.sh will add `ibus` to the apt install list on Debian family | The engine cannot function without ibus; user would expect a functioning install | Yes — can be skipped via env flag |
| CD-ROM apt source fix is only relevant on Mint/Ubuntu desktop installs | Fix will guard-check for `/var/lib/apt/cdroms.list` before apt update | Full distro-agnostic fix without side effects; file either exists or doesn't | Yes |
| Restoration before reproduction | Clean all install artifacts first, recreate cdroms.list, then run bootstrap | Only way to prove the fix actually works | N/A — required step |

## Findings (cited - path:lines)

### Finding 1: CD-ROM source blocks `apt update` in bootstrap.sh
- **File**: `bootstrap.sh:59-62`
- **Evidence**: The `install_debian()` function runs `sudo apt update` with `set -e` active (line 2). When `/var/lib/apt/cdroms.list` contains a stale CD-ROM entry (Linux Mint installs add this automatically), `apt update` exits non-zero and the entire script aborts.
- **Actual file content observed**: `CD::0c06d058567b95b94af55b76555d29d3-2 "Linux Mint 22.3 _Zena_ - Release amd64 20260108";`
- **Impact**: The error message is unhelpful (`E: The repository 'cdrom://...' does not have a Release file.`), and the user has no indication that the bootstrap can recover by simply removing the stale source.

### Finding 2: install.sh already has partial error handling for apt update
- **File**: `install.sh:39`
- **Evidence**: `sudo apt-get update || echo "  ⚠ apt update failed, attempting install anyway"` — this handles the failure gracefully with `||`, then continues to install dependencies. However, `install.sh` is only reachable if `bootstrap.sh` completes its dependency installation first.
- **Impact**: The higher-level entry point (bootstrap.sh) blocks before install.sh ever runs.

### Finding 3: Neither script installs ibus
- **File**: `bootstrap.sh:61`, `install.sh:40`
- **Evidence**: The apt install lines install `python3-evdev wget unzip p7zip-full git python3-venv` — no `ibus`. The install.sh assumes ibus is already present and only uses fallback `|| true` on ibus commands.
- **Impact**: On systems without ibus (minimal/server installs, some distros), `ibus restart` and `ibus engine handwrite-chinese` fail with "Command 'ibus' not found".

### Finding 4: On this test system, ibus was NOT pre-installed — installed by user before bootstrap ran
- **Evidence**: `/var/log/dpkg.log` first entry: `2026-07-05 03:35:46  startup archives unpack`. Immediately followed by `install ibus-data:all <none> 1.5.29-2`. All ibus packages installed at 03:35:51-03:35:54. Bootstrap.sh ran at 04:10:53.
- **Impact**: On a fresh system boot, ibus is NOT pre-installed. The user's reported error "Command 'ibus' not found" is fully reproduced on a clean live ISO. The bootstrap.sh does NOT install ibus — only `python3-evdev wget unzip p7zip-full git python3-venv`.

### Finding 5: Full list of artifacts installed by bootstrap + install scripts
- **Evidence path**: Direct file inspection and `restore.sh:17-22`
- **Files installed**:
  - `/usr/local/bin/handwrite_evdev.py`
  - `/usr/local/bin/ibus-engine-handwrite-chinese`
  - `/usr/local/share/ibus-handwrite-chinese/` (entire directory tree: engine script, venv with onnxruntime, models, icons, restore.sh, diagnose_trackpad.sh)
  - `/usr/share/ibus/component/handwrite-chinese.xml`
  - `/etc/udev/rules.d/99-trackpad-handwrite.rules`
- **Packages installed**: `python3-evdev` (plus python3-venv dependencies)
- **Group change**: user added to `input` group

## Decisions (with rationale)

| Decision | Rationale |
|----------|-----------|
| **D1: Fix bootstrap.sh not install.sh** | The entry point is where the failure happens first. Fixing bootstrap.sh protects both the direct user flow (`bash <(curl ...)`) and the manual flow. |
| **D2: Add CD-ROM source cleanup before apt update** | Simple, minimal, distro-agnostic: check for `/var/lib/apt/cdroms.list` and remove it if present, with a user-visible message. No new dependencies. |
| **D3: Add `|| true` fallback to apt update in bootstrap.sh** | Mirrors the pattern already in install.sh. Prevents non-CD-ROM apt update failures from blocking install. |
| **D4: Add `ibus` to apt install list in bootstrap.sh** | Harmless if already installed (apt skips it), ensures the engine can restart/activate. |
| **D5: Add ibus installation fallback in install.sh** | For the manual install path (`./tools/install.sh`), detect and install ibus if missing. |
| **D6: Restore + reproduce before applying fixes** | Restoration proves the errors are real and the fixes actually resolve them. Without this, we'd be fixing theoretical problems. |

## Scope IN

1. Fix `bootstrap.sh` — handle stale CD-ROM apt sources gracefully before `apt update`
2. Fix `bootstrap.sh` — add error-resilient `apt update` with `|| true` fallback
3. Fix `bootstrap.sh` — add `ibus` to the Debian apt install list
4. Fix `install.sh` — detect and install ibus if missing before restart/engine-set steps
5. Restore system to clean pre-installation state (remove all installed files/packages)
6. Re-create the stale CD-ROM source in `/var/lib/apt/cdroms.list` to reproduce the error
7. Run bootstrap.sh to confirm errors, then run again after fixes to confirm resolution
8. Verify engine activation works after fix

## Scope OUT (Must NOT have)

- Do NOT refactor or restructure the codebase
- Do NOT add new features or change engine behavior
- Do NOT modify CI/CD workflows
- Do NOT change packaging (deb/rpm/PKGBUILD)
- Do NOT modify the Python engine source code
- Do NOT add new flags/environment variables to scripts
- Do NOT change the restore.sh uninstaller
- Do NOT add GUI improvements or user-facing features

## Open questions

None — all forks have been resolved via exploration.
- CD-ROM source format confirmed from system inspection
- ibus pre-install status confirmed
- All script error handling patterns confirmed
- Both fix approaches are minimal, reversible, and distro-agnostic

## High-accuracy review results

### Momus (Plan Critic) — PASS ✅
Plan is clear, verifiable, complete, correct, and safe. No blocking issues.

### Oracle (Technical Depth) — HAS CONCERNS ⚠️ → RESOLVED
Two concerns raised and addressed in revised plan:

| Concern | Resolution |
|---------|-----------|
| Change A: CD-ROM guard targets `/var/lib/apt/cdroms.list` (wrong file — that's the identifier DB, not a source) | Replaced with proper `deb cdrom:` source line guard using `grep -qs '^deb cdrom:'` + `sed -i '/^deb cdrom:/s/^/#/'` targeting all apt sources list files |
| Change D: Cross-distro ibus branches (dnf/pacman/zypper) in install.sh are dead code — Debian-only gate at line 33 rejects non-Debian users via `exit 1` before they reach the ibus block | Changed `exit 1` to a warning + wrapped apt-specific commands in an `else` branch. Non-Debian users now get a warning about python3-evdev but can continue to the ibus check which handles their distro. |

### Additional improvements from review
- Change B expanded: Added `ibus` to ALL 4 distro install functions (Debian, Fedora, Arch, SUSE), not just Debian
- ibus-gtk3 added to install.sh's apt ibus install for proper GTK immodule support

## Approval gate
status: approved
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->
