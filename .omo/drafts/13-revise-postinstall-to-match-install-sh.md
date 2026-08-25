---
slug: 13-revise-postinstall-to-match-install-sh
status: drafting
intent: clear
review_required: true
pending-action: write .omo/plans/13-revise-postinstall-to-match-install-sh.md
approach: Align all 3 package post-install scripts (.deb postinst, .rpm %post, Arch .install) with the reference tools/install.sh
---

# Draft: 13-revise-postinstall-to-match-install-sh

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
| id | outcome | status | evidence path |
|----|---------|--------|---------------|
| C1 | .deb postinst revised | active | packaging/debian/postinst |
| C2 | .rpm %post revised | active | packaging/ibus-handwrite-chinese.spec |
| C3 | Arch .install revised | active | packaging/ibus-handwrite-chinese.install |

## Open assumptions (announced defaults)
<!-- Record any default you adopt instead of asking, so the user can veto it at the gate. -->
| assumption | adopted default | rationale | reversible? |
|------------|----------------|-----------|-------------|
| input group membership | NOT added in postinst — postinst runs as root with no $SUDO_USER guaranteed | Adding user to `input` group requires a known username; postinst runs during `dpkg -i` / `rpm -i` where $SUDO_USER may not be set. The `sg input` fallback in the wrapper handles runtime access. | Yes, if user wants to pass username via env var |
| set engine | NOT done in postinst | `ibus engine handwrite-chinese` runs for the root user during package install, not the desktop user. The user selects the engine from their IBus menu. | Yes |
| IBus dependency check | NOT added | Package Depends/Requires already declares ibus — it's always present at install time | Trivially |
| post-install message | ADDED telling user to `ibus restart` + select engine | The user must manually restart IBus and select the engine from their desktop menu — postinst cannot do this (runs as root, no D-Bus). The message is standard for IBus packages (ibus-table, ibus-libpinyin, etc.) | Trivially |

## Findings (cited - path:lines)

### Reference: tools/install.sh (265 lines)
Full install flow: deps → model download → engine files → venv+onnx → wrapper (with `sg input`) → component XML → udev rule → input group → diagnose_trackpad → restore → icons → IBus check → kill stale root daemon → restart+5-cycle polling → set engine

**Package postinst only ports the system-level phases** (model download, venv, wrapper, udev, diagnose_trackpad). The session-level phases are intentionally excluded because postinst runs as root with no predictable D-Bus: stale root daemon kill (needs interactive sudo context), restart+5-cycle polling (rarely inherits D-Bus), set engine (runs as root, not desktop user), and automated `ibus restart`. Instead, a post-install message tells the user to `ibus restart` + select engine — it's always correct, always actionable.

### Current post-install gaps

**Common to all 3 packages:**
1. Wrapper script at `/usr/local/bin/ibus-engine-handwrite-chinese` lacks `sg input` fallback:
   - install.sh:119-127 has `if ! groups | grep -q '\binput\b'; then exec sg input -c "exec $0 $*" 2>/dev/null || true; fi`
   - .deb postinst:66-77 — no sg input
   - .rpm %post:118-128 — no sg input
   - .install post_install — no wrapper at all
2. No post-install message telling user to restart IBus + select engine

**Arch `.install` only:**
4. Downloads Zinnia/幽兰百合 model (line 5-14) instead of PP-OCRv6
5. No Python venv + onnxruntime creation
6. No wrapper script at all (engine binary is directly the script)

**diagnose_trackpad.sh:**
7. Not included in any package file list
   - Tools ships tools/diagnose_trackpad.sh (mode 755)

### .deb-specific: debian/install (line 1-6)
Installs `ibus-engine-handwrite-chinese` to `/usr/local/bin/` (direct — overwritten by postinst wrapper)
Engine file goes to `/usr/local/share/ibus-handwrite-chinese/` but build-deb.sh:34 also installs there
The install file is actually a `dh_install` config — but build-deb.sh doesn't use debhelper, it builds manually

## Decisions (with rationale)

1. **Port `sg input` fallback to all 3 wrappers** — critical for evdev access without input group
2. **Arch `.install`: rewrite to PP-OCRv6 model + venv + wrapper** — current Zinnia model is outdated/wrong
3. **Arch `.install`: fix `post_upgrade` to not re-download** — add model-exists guard
4. **Add diagnose_trackpad.sh to all 3 packages** — useful debugging tool
5. **Remove automated `ibus restart` from all postinsts** — session-level operation with no reliable D-Bus; the post-install message is the single source of truth
6. **Update Arch PKGBUILD pkgdesc** — "Zinnia-based recognition" → "PP-OCRv6 ONNX-based recognition"
6. **Add post-install message** — tell user to `ibus restart` + select engine from menu (standard for IBus packages)
7. **Do NOT port stale root ibus-daemon kill** — postinst has no reliable user/D-Bus context; this is a session-level fix for `sudo install.sh`, not a package concern
8. **Do NOT port restart polling** — same reason as above
9. **Do NOT port input group addition** — postinst can't know the real user
10. **Do NOT port "set engine"** — postinst runs as root, not the desktop user
11. **Do NOT port IBus dependency install** — package deps guarantee it

## Scope IN
- .deb postinst: wrapper `sg input` fallback, diagnose_trackpad.sh install, **remove automated ibus restart block**, add post-install message
- .rpm %post: same, plus diagnose_trackpad.sh in %files
- Arch .install: full rewrite — PP-OCRv6 model, venv+onnx, wrapper with sg input, diagnose_trackpad.sh install, fix post_upgrade, **remove ibus restart block**, post-install message, **update PKGBUILD pkgdesc**
- Release workflow CI test: keep current Restart IBus step (already has display/D-Bus guard)

## Scope OUT (Must NOT have)
- Do NOT change install.sh or bootstrap.sh
- Do NOT add input group membership to postinst
- Do NOT add `ibus engine handwrite-chinese` to postinst
- Do NOT keep the automated `ibus restart` block in any postinst (must be removed and replaced with message)
- Do NOT change the release workflow's test-packages job logic (only post-install scripts)
- Do NOT restructure build-deb.sh or build-rpm.sh

## Open questions
- (none — all forks resolved by exploration)

## Review findings (dual Momus, 2026-07-05)

### Review 1: REVISE AND RE-REVIEW → 3 critical blockers found, plan updated
| # | Issue | Severity | Fix applied |
|---|-------|----------|-------------|
| R1.1 | `bash -n` on .spec will always fail (RPM syntax) | Critical | Replaced with `sed` extraction of %post section + bash -n |
| R1.2 | Arch PKGBUILD doesn't install engine to ENGINE_DIR; wrapper breaks | Major | Added PKGBUILD install line for ENGINE_DIR |
| R1.3 | T3: "Must NOT change PKGBUILD" contradicts "Also update depends" | Major | Clarified Must NOT to allow depends & install changes |
| R1.4 | T1: "Must NOT change build-deb.sh" vs task says add cp line | Minor | Aligned per-task Must NOT with overall plan |
| R1.5 | Job count: plan says 15, actual is 16 | Minor | Fixed to 16 |
| R1.6 | Version mismatch: v0.4.2 tag vs 0.1.0 in files | Minor | Added version bump step to T4 |

### Review 2: APPROVE with issues — all addressed
| # | Issue | Severity | Fix applied |
|---|-------|----------|-------------|
| R2.1 | `$DPKG_ROOT` doesn't exist in Debian maintainer scripts | Major | Replaced with `chmod` on already-installed file |
| R2.2 | `$USER` in postinst is root, not desktop user | Major | Changed to `$(logname 2>/dev/null || echo "$SUDO_USER")` |
| R2.3 | `debian/install` unused by build-deb.sh | Minor | Kept for dpkg-buildpackage path (harmless) |
| R2.4 | Arch pip fallback not explicit | Minor | Added fallback: rm venv + use system Python if pip fails |
| R2.5 | Restart polling adds ~5s on desktop | Minor | Acceptable — matches install.sh behavior |

## Review findings (Momus + Oracle, 2026-07-05) — SECOND ROUND

### Momus: APPROVE ✅ — minor issues found
| # | Issue | Severity | Status |
|---|-------|----------|--------|
| M3.1 | `sed` extraction accepts `%post` but `bash -n` treats `%post` as a valid shell token (confirmed empirically - passes) | ⚠️ Non-issue | Verified working |
| M3.2 | `sudo pkill` in install.sh block may fail if `sudo` not installed in minimal containers | Minor | `|| true` catches it; post-kill check also catches surviving daemon |
| M3.3 | T4 version bump "or skip" leaves ambiguity; developer should bump | Minor | Already flagged as minor in R1.6 |

### Oracle: APPROVE with notes — 2 minor issues
| # | Issue | Severity | Status |
|---|-------|----------|--------|
| O3.1 | `logname` + `$SUDO_USER` in postinst — both may be empty in dpkg/rpm context (no tty, no sudo). `pgrep -u ""` would be called, which shows warning but doesn't break (restart block is gated on display/D-Bus, so only runs on desktop installs where `$SUDO_USER` is available) | Minor | Acceptable — correct behavior expected for desktop installs where D-Bus is present |
| O3.2 | Arch `.install` changes are NOT tested by CI (Arch CI uses `install.sh --skip-deps`, not the `.install` script). Plan's acceptance criteria "CI passes on Arch" only validates install.sh, not the .install rewrite | Minor | Pre-existing; plan's T3 changes are self-contained and syntactically validated by `bash -n` |
| O3.3 | `sed` extraction for `bash -n` on .spec (`/^%post/,/^%[a-z]/p`) would break if RPM spec conditionals (`%if`, `%endif`) are added inside `%post` | Minutiae | Not currently present; acceptable limitation |
| O3.4 | Venv cleanup added to Arch `pre_remove()` but not to Debian `prerm` or RPM `%preun` — minor inconsistency | Minor | Intentional — scope limited to Arch rewrite |

### Verdict (superseded — plan revised below)
**APPROVE** — both reviewers approve the revised plan. 0 new blockers found. All previous fixes verified correct.

## Revision 2 (2026-07-05): removed `ibus restart` block from all postinsts
Based on user review: automated `ibus restart` (from Plan 12) is a session-level operation — it needs D-Bus and a desktop user session, which postinst doesn't reliably have. Removing it makes the post-install message the single source of truth for the user.

Before, the user saw mixed signals:
```
Restarting IBus...              ← automated (might've succeeded, might've not)
  ibus restart failed ...
  ───────────────────────────
  Chinese Handwriting installed!
  To activate:  ibus restart     ← tell user to do it again?
  ───────────────────────────
```

After removal: no restart attempt, just the clean instruction — always correct, always actionable.
- Scope IN now: remove ibus restart block + replace with post-install message (all 3 packages)
- Scope OUT now also excludes: ibus restart (automated), plus previous session-level ops
- Plan file updated to match
- New high-accuracy reviews below

## Approval gate
status: approved
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->
