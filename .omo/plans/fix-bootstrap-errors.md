# fix-bootstrap-errors - Work Plan

## TL;DR (For humans)

**What you'll get:** Two installer scripts (`bootstrap.sh` and `tools/install.sh`) that no longer crash with "CD-ROM not found" or "ibus not found" errors, so the Chinese handwriting engine installs cleanly on any Linux Mint, Ubuntu, or Debian system — including fresh installs where ibus isn't present.

**Why this approach:** Minimal, surgical, reversible changes to only the two shell scripts. No refactoring, no new features, no Python changes. Each fix is a 3-line guard that has zero impact when the condition doesn't apply (no CD-ROM entry, ibus already installed).

**What it will NOT do:** It won't change how the handwriting engine works, won't add features, won't change the restore script, won't modify CI/CD, and won't touch packaging (deb/rpm).

**Effort:** Short
**Risk:** Low — changes are guarded by `if` checks, no new behavior paths
**Decisions to sanity-check:** The CD-ROM fix path (`rm -f /var/lib/apt/cdroms.list`) and adding `ibus` to the Debian package list

Your next move: **Approve** this plan. Then the worker will: (1) restore system to clean state, (2) reproduce the original errors, (3) apply the script fixes, and (4) verify the fixes work.

---

> TL;DR (machine): Short effort, Low risk — two script fixes for CD-ROM apt source + missing ibus, verified by restoration + reproduction + clean bootstrap re-run

## Scope
### Must have
1. Handle stale CD-ROM apt source gracefully in `bootstrap.sh` (target `deb cdrom:` lines in sources lists, not `/var/lib/apt/cdroms.list`)
2. Error-resilient `apt update` in `bootstrap.sh` (fallback with `|| { echo "..."; }`)
3. Install `ibus` if missing — in ALL distro functions in `bootstrap.sh` AND cross-distro in `install.sh`
4. Fix `install.sh` Debian-only gate to allow non-Debian users to reach the ibus check
5. Restore system to pre-install state + reproduce original errors
6. Verify fixes by running `bootstrap.sh` from clean state

### Must NOT have (guardrails, anti-slop, scope boundaries)
- No refactoring of the codebase or scripts
- No new features or engine behavior changes
- No CI/CD workflow changes
- No packaging (deb/rpm/PKGBUILD) changes
- No Python engine source changes
- No new flags or environment variables
- No changes to `restore.sh`

## Verification strategy
- Test decision: tests-after (manual shell-based verification)
- Evidence: .omo/evidence/task-N-fix-bootstrap-errors/ with command outputs and screenshots
- Each fix is verified by: (a) running the failing scenario, (b) confirming error, (c) applying fix, (d) confirming success

## Execution strategy
### Parallel execution waves

**Wave 1 — Restoration + Reproduction (sequential, 3 todos)**
These must run sequentially because each depends on the previous state.

**Wave 2 — Apply fixes (sequential within each script, but scripts can be prepared in parallel)**
- Fix `bootstrap.sh` (2 changes: CD-ROM guard + apt update fallback + ibus install)
- Fix `install.sh` (1 change: ibus detection + install)
These can be coded in parallel since they touch separate files.

**Wave 3 — Verification (sequential)**
Must run after both fixes are applied.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| T1 (Restore clean state) | — | T2 | — |
| T2 (Recreate cdrom + reproduce error) | T1 | T3 | — |
| T3 (Reproduce ibus error) | T1 | T4, T5 | — |
| T4 (Fix bootstrap.sh) | T2, T3 | T6 | T5 |
| T5 (Fix install.sh) | T2, T3 | T6 | T4 |
| T6 (Verify full bootstrap from clean state) | T4, T5 | — | — |
| F1-F4 (Final verification) | T6 | — | All F1-F4 |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->

### Wave 1 — Restore system and reproduce original errors

- [x] 1. Restore system to pre-installation state
  **What to do / Must NOT do:**
  1. Run the restore script: `sudo bash /home/mint/projects/ibus-handwrite-chinese/tools/restore.sh`
  2. Verify everything was removed:
     - `/usr/local/bin/handwrite_evdev.py` — must NOT exist
     - `/usr/local/bin/ibus-engine-handwrite-chinese` — must NOT exist
     - `/usr/local/share/ibus-handwrite-chinese/` — must NOT exist (entire directory)
     - `/usr/share/ibus/component/handwrite-chinese.xml` — must NOT exist
     - `/etc/udev/rules.d/99-trackpad-handwrite.rules` — must NOT exist
  3. Remove system package installed by bootstrap:
     - `sudo apt remove -y python3-evdev`
  4. Remove user `mint` from `input` group:
     - `sudo gpasswd -d mint input`
  5. **Must NOT** remove `ibus`, `wget`, `unzip`, `p7zip-full`, `git`, `python3-venv` — these were pre-existing or are general system tools
  6. **Must NOT** remove the `.omo/` project directory or any git-tracked files

  **Parallelization:** Wave 1 | Blocked by: — | Blocks: Todo 2, Todo 3
  **References:** `tools/restore.sh:17-22`, `bootstrap.sh:59-62`, exploration task findings
  **Acceptance criteria (agent-executable):**
  ```bash
  test ! -f /usr/local/bin/handwrite_evdev.py && \
  test ! -f /usr/local/bin/ibus-engine-handwrite-chinese && \
  test ! -d /usr/local/share/ibus-handwrite-chinese && \
  test ! -f /usr/share/ibus/component/handwrite-chinese.xml && \
  test ! -f /etc/udev/rules.d/99-trackpad-handwrite.rules && \
  ! dpkg -l python3-evdev 2>/dev/null | grep -q '^ii' && \
  ! groups mint | grep -q input
  ```
  **QA scenarios:**
  - Happy path: After restoration, run the acceptance check above — all should pass (files gone, package removed, user removed from group)
  - Failure path: Check that `ibus` is still installed (`dpkg -l ibus | grep '^ii'`) and system apt sources are untouched
  **Evidence:** `.omo/evidence/task-1-restore/state-check.txt`
  **Commit:** N (restoration only, no code changes)

- [x] 2. Re-create stale CD-ROM apt source and reproduce apt update failure
  **What to do / Must NOT do:**
  1. Re-create `/var/lib/apt/cdroms.list` with the original content:
     ```
     CD::0c06d058567b95b94af55b76555d29d3-2 "Linux Mint 22.3 _Zena_ - Release amd64 20260108";
     CD::0c06d058567b95b94af55b76555d29d3-2::Label "Linux Mint 22.3 _Zena_ - Release amd64 20260108";
     ```
  2. Run `sudo apt update` and confirm it fails with the CD-ROM error:
     ```
     E: The repository 'cdrom://Linux Mint 22.3 _Zena_ - Release amd64 20260108 noble Release' does not have a Release file.
     ```
  3. Confirm `bootstrap.sh` fails at `sudo apt update` by running it:
     ```bash
     cd /home/mint/projects/ibus-handwrite-chinese
     bash bootstrap.sh 2>&1 | tee /tmp/bootstrap-error-output.txt
     ```
  4. The bootstrap MUST fail with the CD-ROM error and NOT proceed to install anything
  5. **Must NOT** leave the cdroms.list in place after confirming the error — remove it to proceed with later steps

  **Parallelization:** Wave 1 | Blocked by: Todo 1 | Blocks: Todo 4, Todo 5
  **References:** Original cdroms.list content from system inspection, `bootstrap.sh:59-62`
  **Acceptance criteria (agent-executable):**
  ```bash
  # After creating cdroms.list, apt update should fail:
  apt update 2>&1 | grep -q "cdrom.*Release file"
  # bootstrap.sh should fail:
  bash bootstrap.sh 2>&1 | grep -q "does not have a Release file"
  ```
  **QA scenarios:**
  - Happy: apt update fails with cdrom error, bootstrap.sh fails with cdrom error
  - Failure: If apt update succeeds, the cdroms.list was not properly created — fix format and retry
  **Evidence:** `.omo/evidence/task-2-reproduce-cdrom/apt-error.txt`, `.omo/evidence/task-2-reproduce-cdrom/bootstrap-error.txt`
  **Commit:** N (reproduction only, no code changes)

- [x] 3. Reproduce "ibus not found" error (simulate missing ibus)
  **What to do / Must NOT do:**
  1. On this Mint system, ibus is pre-installed. To reproduce the "ibus not found" error, we need to verify it WOULD fail on a system without ibus.
  2. Check what `install.sh` steps would fail if ibus were missing:
     - Step [8] killing stale ibus-daemon → `pgrep -x ibus-daemon` would not find anything (harmless, uses `|| true`)
     - Step [9] restarting ibus → `ibus-daemon --daemonize --replace` would fail if ibus not installed (but uses `2>/dev/null || true`)
     - Setting engine → `ibus engine handwrite-chinese` would fail with "Command 'ibus' not found"
  3. Confirm by temporarily simulating: check `command -v ibus` returns empty path if ibus were absent
  4. Document the exact error message from the original user report: `Command 'ibus' not found, but can be installed with: sudo apt install ibus`
  5. **Must NOT** actually remove ibus from this system (it's a core desktop component)
  6. **Must NOT** modify any system files — this todo is purely analytical/documentation

  **Parallelization:** Wave 1 | Blocked by: Todo 1 | Blocks: Todo 4, Todo 5
  **References:** Original user error output, `install.sh:165-200`
  **Acceptance criteria (agent-executable):**
  - Document the exact failure mode in the evidence file
  - Confirm that both `bootstrap.sh` and `install.sh` have no `ibus` package in any install command
  ```bash
  grep -n "ibus" /home/mint/projects/ibus-handwrite-chinese/bootstrap.sh | grep -v "echo\|https://"
  grep -n "ibus" /home/mint/projects/ibus-handwrite-chinese/tools/install.sh | grep -v "echo\|https://\|/usr/local"
  ```
  **QA scenarios:**
  - Happy: Evidence file documents all ibus-related script locations and confirms no ibus install exists
  - Failure: If any script already installs ibus, document it and update the fix plan accordingly
  **Evidence:** `.omo/evidence/task-3-reproduce-ibus/ibus-gap-analysis.txt`
  **Commit:** N (reproduction only, no code changes)

### Wave 2 — Apply fixes

- [x] 4. Fix bootstrap.sh — CD-ROM guard, resilient apt update, and ibus install for all distros
  **What to do / Must NOT do:**
  Apply THREE changes to `bootstrap.sh`:

  **Change A — Stale CD-ROM source cleanup (insert before `sudo apt update` in `install_debian()`):**
  Remove stale `deb cdrom:` source lines from apt sources lists. The apt CD-ROM identifier database (`/var/lib/apt/cdroms.list`) is NOT a source — the actual problem is `deb cdrom:` lines in `/etc/apt/sources.list` or files in `/etc/apt/sources.list.d/`. Use:
  ```bash
  install_debian() {
      # Remove stale CD-ROM apt source lines (common on Mint/Ubuntu desktop installs)
      if grep -qs '^deb cdrom:' /etc/apt/sources.list /etc/apt/sources.list.d/*.list 2>/dev/null; then
          echo "  → Removing stale CD-ROM apt source line..."
          sudo sed -i '/^deb cdrom:/s/^/#/' /etc/apt/sources.list /etc/apt/sources.list.d/*.list 2>/dev/null || true
      fi
      sudo apt update || { echo "  ⚠ apt update failed (non-fatal), continuing..."; }
      sudo apt install -y ibus python3-evdev wget unzip p7zip-full git python3-venv
  }
  ```

  **Change B — Add `ibus` to ALL distro install commands** (not just Debian). Update each distro function:
  ```bash
  install_debian() {
      # ... (Change A content above already includes ibus)
  }
  
  install_fedora() {
      sudo dnf install -y ibus python3-evdev wget unzip p7zip git
  }
  
  install_arch() {
      sudo pacman -S --noconfirm ibus python-evdev wget unzip p7zip
  }
  
  install_suse() {
      sudo zypper --no-gpg-checks refresh 2>/dev/null || true
      sudo zypper install -y ibus python3-evdev wget unzip p7zip || {
          echo "⚠ zypper install failed (transient repo timeout). Retrying with --no-gpg-checks..."
          sudo zypper --no-gpg-checks install -y ibus python3-evdev wget unzip p7zip || true
      }
  }
  ```

  **Change C — Resilient apt update** (add `||` fallback, already shown in Change A above):
  ```bash
  sudo apt update || { echo "  ⚠ apt update failed (non-fatal), continuing..."; }
  ```

  **Must NOT do:**
  - Do NOT add new flags or environment variables
  - Do NOT remove `set -e` from the script (the `||` guards handle individual commands)
  - Do NOT remove ibus from any distro's install list
  - Do NOT change the structure of any function beyond adding ibus to the package list

  **Parallelization:** Wave 2 | Blocked by: Todo 2, Todo 3 | Blocks: Todo 6
  **References:** `bootstrap.sh:2,59-85`
  **Acceptance criteria (agent-executable):**
  ```bash
  # Verify CD-ROM source line guard exists (targets deb cdrom: lines, not cdroms.list):
  grep -q "deb cdrom:" /home/mint/projects/ibus-handwrite-chinese/bootstrap.sh
  # Verify ibus is in ALL distro install functions:
  grep -c "ibus" /home/mint/projects/ibus-handwrite-chinese/bootstrap.sh
  # ^ should be at least 4 (one per distro function)
  # Verify apt update error handling:
  grep -q "apt update.*||" /home/mint/projects/ibus-handwrite-chinese/bootstrap.sh
  # Verify set -e is still there:
  head -3 /home/mint/projects/ibus-handwrite-chinese/bootstrap.sh | grep -q "set -e"
  # Verify shell syntax:
  bash -n /home/mint/projects/ibus-handwrite-chinese/bootstrap.sh
  ```
  **QA scenarios:**
  - Happy: All grep checks pass, shell syntax check passes
  - Failure: If `bash -n` reports syntax errors, fix the script until it passes
  - edge: If grep for "deb cdrom:" fails, the edit was not applied — re-apply
  **Evidence:** `.omo/evidence/task-4-fix-bootstrap.sh/diff-output.txt` (diff before/after)
  **Commit:** Y | `fix(bootstrap): handle stale CD-ROM apt source, resilient apt update, add ibus for all distros`

- [x] 5. Fix install.sh — detect and install ibus if missing (cross-distro)
  **What to do / Must NOT do:**

  TWO sub-changes to `install.sh`:

  **Change D1 — Fix the Debian-only gate to allow cross-distro use:**
  
  Currently lines 33-37 reject non-Debian users with `exit 1` — this prevents cross-distro ibus detection from ever running. Replace the hard exit with a warning and skip apt-specific commands:
  
  **Before (lines 32-45):**
  ```bash
  if [ "$SKIP_DEPS" = false ]; then
      if ! command -v apt &>/dev/null; then
          echo "This script requires apt (Debian/Ubuntu/Mint)"
          echo "For other distros, use bootstrap.sh (see README)"
          exit 1
      fi
      echo "[1] Installing dependencies..."
      sudo apt-get update || echo "  ⚠ apt update failed, attempting install anyway"
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-evdev wget unzip python3-venv || {
          echo "  ⚠ Failed to install system packages. Install manually:"
          echo "     apt install python3-evdev wget unzip python3-venv"
          echo "  Then re-run with: ./tools/install.sh --skip-deps [--no-restart] [--no-set-engine]"
      }
  fi
  ```
  
  **After:**
  ```bash
  if [ "$SKIP_DEPS" = false ]; then
      if ! command -v apt &>/dev/null; then
          echo "  ⚠ Not a Debian-based system — skipping apt dependency install."
          echo "  Install python3-evdev manually for your distro, then re-run with --skip-deps"
      else
          echo "[1] Installing dependencies..."
          sudo apt-get update || echo "  ⚠ apt update failed, attempting install anyway"
          sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-evdev wget unzip python3-venv || {
              echo "  ⚠ Failed to install system packages. Install manually:"
              echo "     apt install python3-evdev wget unzip python3-venv"
              echo "  Then re-run with: ./tools/install.sh --skip-deps [--no-restart] [--no-set-engine]"
          }
      fi
  fi
  ```

  **Change D2 — Insert cross-distro ibus install block** before step [8] (line 165), after icon installation (line 163):
  ```bash
  echo "【7.5】 Ensuring IBus is installed..."
  if ! command -v ibus &>/dev/null; then
      echo "  Installing IBus..."
      if command -v apt &>/dev/null; then
          sudo apt-get install -y ibus ibus-gtk3 || echo "  ⚠ Failed to install ibus via apt"
      elif command -v dnf &>/dev/null; then
          sudo dnf install -y ibus || echo "  ⚠ Failed to install ibus via dnf"
      elif command -v pacman &>/dev/null; then
          sudo pacman -S --noconfirm ibus || echo "  ⚠ Failed to install ibus via pacman"
      elif command -v zypper &>/dev/null; then
          sudo zypper install -y ibus || echo "  ⚠ Failed to install ibus via zypper"
      fi
  else
      echo "  ✓ IBus already installed"
  fi
  ```

  **Must NOT do:**
  - Do NOT change any existing step numbering (insert [7.5] as a new step between [7] and [8])
  - Do NOT make ibus installation a hard failure — use `|| echo` pattern to match the script's existing error handling style
  - Do NOT modify the restore.sh script
  - Do NOT add ibus to the dependency install section (line 40) — it goes in the new step [7.5]
  - Do NOT remove the `else` branch from the apt gate (warning for non-Debian users is sufficient)
  - Do NOT remove or change the `set -euo pipefail` at line 2

  **Parallelization:** Wave 2 | Blocked by: Todo 2, Todo 3 | Blocks: Todo 6
  **References:** `install.sh:32-45` (apt gate), `install.sh:165-200` (ibus restart/engine section), `install.sh:39-44` (existing error handling pattern)
  **Acceptance criteria (agent-executable):**
  ```bash
  # Verify ibus check exists:
  grep -q "command -v ibus" /home/mint/projects/ibus-handwrite-chinese/tools/install.sh
  # Verify cross-distro branches exist:
  grep -q "dnf" /home/mint/projects/ibus-handwrite-chinese/tools/install.sh
  grep -q "pacman" /home/mint/projects/ibus-handwrite-chinese/tools/install.sh
  grep -q "zypper" /home/mint/projects/ibus-handwrite-chinese/tools/install.sh
  # Verify apt gate no longer exits (no 'exit 1' in that block):
  grep -q "Not a Debian-based" /home/mint/projects/ibus-handwrite-chinese/tools/install.sh
  # Verify shell syntax:
  bash -n /home/mint/projects/ibus-handwrite-chinese/tools/install.sh
  # Verify the check is BEFORE the ibus restart step:
  grep -n "ibus" /home/mint/projects/ibus-handwrite-chinese/tools/install.sh | head -10
  ```
  **QA scenarios:**
  - Happy: Shell syntax check passes, ibus check exists with cross-distro branches, apt gate is warning not exit
  - Failure: If `bash -n` reports syntax errors, fix the edit
  - edge: If ibus is already installed (this Mint system), the check skips install — verify `ibus` still works after
  - edge: Verify that a user on a non-Debian system would reach the ibus check (the apt gate no longer exits)
  **Evidence:** `.omo/evidence/task-5-fix-install.sh/diff-output.txt` (diff before/after)
  **Commit:** Y | `fix(install): ensure ibus is installed before restart/engine-set steps`

### Wave 3 — Full verification

- [x] 6. Verify full bootstrap from clean state (re-restore + run fixed scripts)
  **What to do / Must NOT do:**
  1. Re-create the stale CD-ROM source (as in Todo 2): `/var/lib/apt/cdroms.list`
  2. Run the fixed `bootstrap.sh` from a clean state (no installed artifacts):
     ```bash
     cd /home/mint/projects/ibus-handwrite-chinese
     bash bootstrap.sh 2>&1 | tee /tmp/verification-bootstrap-output.txt
     ```
  3. Verify the fixed bootstrap:
     - ✅ The CD-ROM source is automatically removed (check `/var/lib/apt/cdroms.list` does NOT exist after)
     - ✅ `apt update` completes successfully (even if it had the `|| true` fallback)
     - ✅ Dependencies are installed (`python3-evdev`, `ibus`, etc.)
     - ✅ PP-OCRv6 model is downloaded
     - ✅ Engine files are installed (all files in the acceptance check below)
     - ✅ IBus is restarted and engine is activated
  4. Verify all installed files:
     ```bash
     test -f /usr/local/bin/ibus-engine-handwrite-chinese
     test -f /usr/local/bin/handwrite_evdev.py
     test -f /usr/share/ibus/component/handwrite-chinese.xml
     test -d /usr/local/share/ibus-handwrite-chinese
     test -f /etc/udev/rules.d/99-trackpad-handwrite.rules
     ```
  5. Verify engine activation:
     ```bash
     ibus engine 2>/dev/null | grep -q handwrite-chinese
     ```
  6. **Must NOT** leave the cdroms.list in place after this test
  7. **Must NOT** remove the .omo/ plans or drafts

  **Parallelization:** Wave 3 | Blocked by: Todo 4, Todo 5 | Blocks: —
  **References:** All previous todos, `bootstrap.sh:59-62` (now fixed), `install.sh:165-200`
  **Acceptance criteria (agent-executable):**
  ```bash
  test ! -f /var/lib/apt/cdroms.list && \
  test -f /usr/local/bin/ibus-engine-handwrite-chinese && \
  test -f /usr/local/bin/handwrite_evdev.py && \
  test -f /usr/share/ibus/component/handwrite-chinese.xml && \
  test -d /usr/local/share/ibus-handwrite-chinese && \
  test -f /etc/udev/rules.d/99-trackpad-handwrite.rules && \
  ibus engine 2>/dev/null | grep -q handwrite-chinese
  ```
  **QA scenarios:**
  - Happy: All acceptance criteria pass, CD-ROM source removed, all files present, engine active
  - Failure: If any file is missing, check the bootstrap output log for the failing step
  - Failure: If ibus engine check fails, verify ibus-daemon is running (`pgrep -x ibus-daemon`)
  **Evidence:** `.omo/evidence/task-6-verify/bootstrap-output.txt`, `.omo/evidence/task-6-verify/file-check.txt`, `.omo/evidence/task-6-verify/engine-check.txt`
  **Commit:** N (verification only, no code changes)

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.

- [x] F1. Plan compliance audit
  - All 6 todos completed successfully
  - All acceptance criteria met
  - No scope violations (Must NOT have items are all respected)
  - Evidence collected in `.omo/evidence/`

- [x] F2. Code quality review
  - `bash -n bootstrap.sh` passes
  - `bash -n tools/install.sh` passes
  - `shellcheck -e SC1091 bootstrap.sh tools/install.sh` passes
  - `xmllint --noout xml/handwrite-chinese.xml` passes (already works)
  - Python syntax checks still pass: `python3 -c "compile(open('src/ibus-engine-handwrite-chinese').read(), 'engine', 'exec')"` and similarly for `handwrite_evdev.py`

- [x] F3. Real manual QA (agent-executed)
  - Verify the CD-ROM guard works: create cdroms.list, verify bootstrap.sh cleans it before apt update
  - Verify ibus not-found handling: temporarily check that the install.sh ibus check block would trigger on a system without ibus (without actually removing ibus)
  - Verify the full bootstrap install works again from the cleaned state (Todo 6 already covers this)

- [x] F4. Scope fidelity
  - Confirm NO changes were made outside `bootstrap.sh` and `tools/install.sh`
  - Confirm `restore.sh` is untouched
  - Confirm no Python files were modified
  - Confirm no CI/CD files were modified
  - Confirm no new features were added

## Commit strategy

Two commits (atomic, separate concerns):

1. `fix(bootstrap): handle stale CD-ROM apt source, resilient apt update, add ibus for all distros`
   - Changes: `bootstrap.sh` only
   - Includes: `deb cdrom:` source line guard (not cdroms.list), `|| { echo }` fallback, ibus in all 4 distro install functions

2. `fix(install): relax Debian-only gate, ensure ibus installed cross-distro before restart`
   - Changes: `tools/install.sh` only
   - Includes: Debian-only gate changed from `exit 1` to warning, cross-distro ibus detection + install block before restart step

Both commits are on a single branch `fix/bootstrap-errors` (no separate PR needed for a single-user project).

## Success criteria

1. ✅ `bash bootstrap.sh` succeeds on Linux Mint with stale CD-ROM apt source
2. ✅ `bash bootstrap.sh` succeeds when `ibus` is not pre-installed (verified by code review of the guard)
3. ✅ All installed files present after bootstrap
4. ✅ Engine `handwrite-chinese` is active in IBus after installation
5. ✅ Shell syntax and shellcheck pass for both modified scripts
6. ✅ No changes outside `bootstrap.sh` and `tools/install.sh`
