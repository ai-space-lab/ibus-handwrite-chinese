# Draft: sudo-less-install

## Intent
- Intent: **CLEAR**
- Review required: **false** (the change is mechanical — replace root guard with internal sudo)
- Status: **awaiting-approval**

## Approach
Remove top-level `sudo` requirement from `tools/install.sh`, `tools/restore.sh`, and `bootstrap.sh`. Instead, prefix individual commands that need root with `sudo`. This is a mechanical transformation — every file write to `/usr`, `/etc`, every package-manager call, every `udevadm` gets `sudo`; user-context commands (`ibus restart`, `wget`, `git clone`) remain unsudoed.

## Files Changed
1. `tools/install.sh` — remove EUID guard, add sudo to ~15 system commands
2. `tools/restore.sh` — remove EUID guard, add sudo to rm/udevadm commands
3. `bootstrap.sh` — remove EUID guard, add sudo to package-manager install functions
4. `README.md` — update install instructions to drop `sudo` from `./tools/install.sh`

## Not Changed (with reasoning)
- `.github/workflows/*.yml` — run as root in containers; `sudo` works fine there
- `tools/build-test-usb-iso.sh` — inherently requires root (chroot/mount); outside scope
- `packaging/debian/postinst`, `prerm` — run as root from dpkg; no change needed
- `packaging/build-deb.sh`, `build-rpm.sh`, `PKGBUILD` — packaging scripts, not user-facing install

## Decision Log
| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Use `sudo` prefix, not `sudo -E` or `SUDO_ASKPASS` | Package-manager env vars (DEBIAN_FRONTEND) passed inline; sudo preserves inline vars |
| 2 | Wrapper script: `sudo tee` instead of heredoc redirect | `cat > /usr/local/bin/...` needs root; `sudo tee > /dev/null << 'EOF'` is the cleanest pattern |
| 3 | Keep `apt-get` error handling pattern | The existing `|| echo "⚠ ..."` pattern should be preserved for resilience |
| 4 | `ibus restart` runs WITHOUT sudo | This is actually a bugfix — `ibus restart` as root is wrong; should run as calling user |

## Evidence Ledger
- `tools/install.sh` line 11-14: `[ "$EUID" -ne 0 ]` → remove
- `tools/restore.sh` line 4-7: `[ "$EUID" -ne 0 ]` → remove
- `bootstrap.sh` line 12-15: `[ "$EUID" -ne 0 ]` → remove
- `tools/install.sh` line 23-28: `apt-get` needs sudo
- `tools/install.sh` lines 80-136: all file operations to /usr, /etc need sudo
- `tools/install.sh` lines 126-127: `udevadm` needs sudo
- `bootstrap.sh` lines 50-67: all package manager calls need sudo

## Verification Plan
1. `shellcheck -e SC1091 bootstrap.sh tools/install.sh tools/restore.sh` — all pass
2. Run `./tools/install.sh --skip-deps --no-restart` as normal user — confirms sudo prompts for system writes
3. Run `./tools/restore.sh` as normal user — confirms sudo prompts for deletes
4. Run `bash bootstrap.sh` in CI container (as root) — confirms sudo commands work in root shell
5. Verify no "Please run as root" message appears for any of the three scripts
