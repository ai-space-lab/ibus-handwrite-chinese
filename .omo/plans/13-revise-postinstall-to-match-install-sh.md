# 13-revise-postinstall-to-match-install-sh - Work Plan

## TL;DR (For humans)
<!-- Fill this LAST, after the detailed plan below is written, so it summarizes the REAL plan. -->
<!-- Plain English for a non-engineer: NO file paths, NO todo numbers, NO wave/agent/tool names. -->

**What you'll get:** Package installs (`.deb`, `.rpm`, Arch) will align with `install.sh` on system-level setup — the IBus engine wrapper gains `sg input` fallback for evdev access, Arch's `.install` finally downloads the correct PP-OCRv6 model instead of the old Zinnia model. The automated `ibus restart` block (Plan 12) is removed from all postinsts — it was a session-level operation that doesn't belong in a root-level package install. Instead, a post-install message tells the user exactly what to do: `ibus restart` then select the engine. No mixed signals.

**Why this approach:** Porting the system-level blocks from `install.sh` (sg input wrapper, PP-OCRv6 model, venv+onnx) to all three package formats eliminates behavioral drift where it's appropriate for a root-level postinst. Automated `ibus restart` is removed along with the other session-level operations (polling, set engine, root daemon kill) — they all need an interactive desktop session with D-Bus and a known user, which postinst doesn't have. A consistent post-install message replaces the old ibus restart block, giving the user one clear instruction instead of mixed signals from an attempted restart that may or may not have worked.

**What it will NOT do:** Not add user to input group (postinst can't know the user), not auto-set the IBus engine (postinst runs as root, not the desktop user), not change `install.sh`/`bootstrap.sh`.

**Effort:** Short
**Risk:** Low — changes are self-contained shell script edits, each block is already proven in `install.sh`
**Decisions to sanity-check:** (1) Not adding input group membership in postinst — OK? (2) Skipping `ibus engine handwrite-chinese` in postinst — OK?

Your next move: **Approve** the plan, then run the worker. Full execution detail follows below.

---

> TL;DR (machine): Short | Low | 3 parallel shell-script edits (.deb postinst, .rpm %post, Arch .install) to port sg-input wrapper, root-daemon kill, restart-polling, and PP-OCRv6 model from tools/install.sh, then CI verify

## Scope
### Must have
1. .deb postinst gains: `sg input` fallback in wrapper, diagnose_trackpad.sh install, post-install message
2. .rpm %post gains: same as #1
3. Arch .install: full rewrite — PP-OCRv6 model+dict, venv+onnxruntime, wrapper with `sg input`, diagnose_trackpad.sh, fix upgrade re-download, post-install message
4. All package %files lists include diagnose_trackpad.sh
5. All bash -n syntax clean on all modified scripts
6. Release workflow test-packages passes on all 10 distros

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do NOT change install.sh or bootstrap.sh
- Do NOT add input group membership or `ibus engine handwrite-chinese` to any postinst
- Do NOT add stale root ibus-daemon kill, restart polling, or user daemon pgrep check to any postinst (these are session-level operations, not package install concerns)
- Do NOT keep the automated `ibus restart` block — it must be REMOVED and replaced with the post-install message
- Do NOT restructure build-deb.sh / build-rpm.sh (adding file copies is allowed, restructuring logic is not)
- Do NOT change release.yml test-packages job logic
- Do NOT restructure PKGBUILD's `package()` function (adding install lines is allowed)

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after (shell scripts: bash -n; file lists: grep)
- Evidence: .omo/evidence/task-<N>-13-revise-postinstall-to-match-install-sh/<ext>

## Execution strategy
### Parallel execution waves
Wave 1 (3 parallel): T1 .deb, T2 .rpm, T3 Arch .install
Wave 2 (verify): T4 release workflow dispatch, monitor to green

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| T1 .deb | — | T4 | T2, T3 |
| T2 .rpm | — | T4 | T1, T3 |
| T3 Arch .install | — | T4 | T1, T2 |
| T4 CI verify | T1, T2, T3 | — | — |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [x] 1. Revise `.deb` postinst: add `sg input` fallback, diagnose_trackpad.sh, remove ibus restart block, add post-install message
   What to do / Must NOT do:
   Edit `packaging/debian/postinst`:
   1. **Wrapper sg input fallback** (lines 66-77): Insert the `sg input` re-exec block — only `install.sh:124-127` (the `if ! groups | grep...` block, NOT the shebang/VENV/ENGINE_DIR lines which already exist in the wrapper) — before the `exec` lines in the wrapper heredoc.
   2. **diagnose_trackpad.sh**: The file is already installed to `/usr/local/share/ibus-handwrite-chinese/diagnose_trackpad.sh` by the package (`build-deb.sh` handles this — see below). In postinst, do NOT use `$DPKG_ROOT` (that variable doesn't exist in Debian maintainer scripts). Instead simply: `chmod 755 /usr/local/share/ibus-handwrite-chinese/diagnose_trackpad.sh`
   3. **Remove IBus restart block** (lines 86-101, the `# --- Restart IBus ---` section through the end of the `if command -v ibus` block): Delete this entire block. The post-install message replaces it.
   4. **Post-install message** (after udev reload, before `exit 0`): Add a message telling the user to restart IBus and select the engine:
      ```sh
      # --- Post-install message ---
      echo ""
      echo "  ────────────────────────────────────────────"
      echo "  Chinese Handwriting installed!"
      echo "  To activate:  ibus restart"
      echo "  Then select Chinese Handwriting from your IBus menu."
      echo "  ────────────────────────────────────────────"
      ```
   Must NOT: Do not add input group membership, do not set engine, do NOT add stale root daemon kill, restart polling, or user daemon pgrep check. Do NOT keep the automated ibus restart block.
   For `build-deb.sh`, diagnose_trackpad.sh must be copied into the package tree (line 41-42 area). Add: `cp "$ROOTDIR/tools/diagnose_trackpad.sh" "$BUILDDIR/usr/local/share/ibus-handwrite-chinese/"` and `chmod 755 "$BUILDDIR/usr/local/share/ibus-handwrite-chinese/diagnose_trackpad.sh"`. This is consistent with the overall plan's "Do NOT restructure" constraint (adding a file copy is not restructuring).
   For `debian/install` file (packaging/debian/install): Add `tools/diagnose_trackpad.sh usr/local/share/ibus-handwrite-chinese/` to the list (supports `dpkg-buildpackage` path even though `build-deb.sh` is manual).
   Must NOT: Remove any existing lines or change the exit code behavior.
   Parallelization: Wave 1 | Blocked by: — | Blocks: T4
   References:
   - packaging/debian/postinst (entire file)
   - tools/install.sh:119-127 (sg input wrapper block)
   - packaging/build-deb.sh:41-42 (file copy area for adding diagnose_trackpad.sh)
   - packaging/debian/install (file manifest)
   - .omo/drafts/13-revise-postinstall-to-match-install-sh.md (decisions)
   Acceptance criteria (agent-executable):
   ```bash
   # 1. bash -n passes
   bash -n packaging/debian/postinst
   # 2. Wrapper contains sg input
   grep -q 'sg input' packaging/debian/postinst
   # 3. Contains post-install activation message
   grep -q 'To activate:  ibus restart' packaging/debian/postinst
   grep -q 'select Chinese Handwriting' packaging/debian/postinst
   # 4. Contains diagnose_trackpad reference
   grep -q 'diagnose_trackpad' packaging/debian/postinst
   # 5. build-deb.sh packages it
   grep -q 'diagnose_trackpad' packaging/build-deb.sh
   # 6. debian/install lists it
   grep -q 'diagnose_trackpad' packaging/debian/install
   # 7. Must NOT have stale root daemon kill, restart polling, or user daemon check
   ! grep -q 'pgrep -u root ibus-daemon' packaging/debian/postinst
   ! grep -q 'timeout 1 ibus engine' packaging/debian/postinst
   ! grep -q 'logname.*ibus-daemon' packaging/debian/postinst
   # 8. Must NOT have the automated ibus restart block
   ! grep -q 'Restarting IBus' packaging/debian/postinst
   ! grep -q 'ibus restart 2>/dev/null' packaging/debian/postinst
   ```
   QA scenarios:
   - Happy: Visual inspection of sg input block matches install.sh equivalent. Message is the only ibus reference.
   - Failure: If any grep check above fails, the todo is incomplete.
   - Evidence: .omo/evidence/task-1-13-revise-postinstall-to-match-install-sh/diff-postinst.txt
   Commit: Y | `fix(deb): align postinst with install.sh — sg input, diagnose_trackpad, remove ibus restart, post-install message`

- [x] 2. Revise `.rpm` spec: add `sg input` fallback, diagnose_trackpad.sh, remove ibus restart block, add post-install message
   What to do / Must NOT do:
   Edit `packaging/ibus-handwrite-chinese.spec`:
   1. **Wrapper sg input fallback** (lines 118-128): Insert the same `sg input` re-exec block into the wrapper heredoc, before the exec lines.
   2. **diagnose_trackpad.sh in %install** (line 50-55 area): Add `install -m 755 tools/diagnose_trackpad.sh %{buildroot}/usr/local/share/ibus-handwrite-chinese/`
   3. **diagnose_trackpad.sh in %files** (line 161-169 area): Add `/usr/local/share/ibus-handwrite-chinese/diagnose_trackpad.sh` to the %files list.
   4. **Remove IBus restart block** (lines 138-153, the `# --- Restart IBus ---` section through the end of the `if command -v ibus` block): Delete this entire block.
   5. **Post-install message** (after wrapper chmod and udev reload, before `%preun`): Same message block as T1 step 4.
   Must NOT: Do not change %prep, %build, %preun, %changelog structure; do not add input group or set engine; do NOT add stale root daemon kill, restart polling, or user daemon pgrep check. Do NOT keep the automated ibus restart block.
   Parallelization: Wave 1 | Blocked by: — | Blocks: T4
   References:
   - packaging/ibus-handwrite-chinese.spec (entire file)
   - tools/install.sh:119-127
   Acceptance criteria (agent-executable):
   ```bash
   # NOTE: bash -n on the entire .spec file does NOT work (RPM spec syntax like %global, %description
   # is not valid bash). Instead, extract the %post section and check it:
   sed -n '/^%post/,/^%[a-z]/p' packaging/ibus-handwrite-chinese.spec | head -n -1 | bash -n
   grep -q 'sg input' packaging/ibus-handwrite-chinese.spec
   grep -q 'diagnose_trackpad' packaging/ibus-handwrite-chinese.spec
   grep -q 'To activate:  ibus restart' packaging/ibus-handwrite-chinese.spec
   grep -q 'select Chinese Handwriting' packaging/ibus-handwrite-chinese.spec
   # Must NOT have stale root daemon kill, restart polling, or user daemon check
   ! grep -q 'pgrep -u root ibus-daemon' packaging/ibus-handwrite-chinese.spec
   ! grep -q 'timeout 1 ibus engine' packaging/ibus-handwrite-chinese.spec
   ! grep -q 'logname.*ibus-daemon' packaging/ibus-handwrite-chinese.spec
   # Must NOT have the automated ibus restart block
   ! grep -q 'Restarting IBus' packaging/ibus-handwrite-chinese.spec
   ! grep -q 'ibus restart 2>/dev/null' packaging/ibus-handwrite-chinese.spec
   ```
   QA scenarios: Same pattern as T1.
   Evidence: .omo/evidence/task-2-13-revise-postinstall-to-match-install-sh/diff-spec.txt
   Commit: Y | `fix(rpm): align %post with install.sh — sg input, diagnose_trackpad, remove ibus restart, post-install message`

- [x] 3. Rewrite Arch `.install`: PP-OCRv6 model, venv+onnx, wrapper with sg input, diagnose_trackpad.sh, fix upgrade, remove ibus restart block, post-install message; update PKGBUILD for engine path and depends
   What to do / Must NOT do:
   Rewrite `packaging/ibus-handwrite-chinese.install` entirely:
   1. **post_install()** — full rewrite:
      - **PP-OCRv6 model+dict download** (same as .deb postinst lines 9-45): Download to `/usr/local/share/ibus-handwrite-chinese/models/ppocrv6_${PPOCR_TIER}_rec.onnx` and `dict_v6.txt` from the same URLs.
      - **Python venv + onnxruntime** (same as .deb postinst lines 48-61): Create at `/usr/local/share/ibus-handwrite-chinese/venv` with `--system-site-packages`. If venv creation fails, fall back: `rm -rf "$VENV_DIR"` and the wrapper will use system Python. If `pip install onnxruntime` fails, warn but do NOT abort.
      - **Wrapper script** with `sg input` fallback (same block as T1 — only the `if ! groups | grep...` portion, not the shebang/VENV/ENGINE_DIR lines which the wrapper heredoc provides).
      - **Udev reload** (keep existing pattern: `if command -v udevadm...`).
      - **diagnose_trackpad.sh**: chmod 755 `/usr/local/share/ibus-handwrite-chinese/diagnose_trackpad.sh` (file installed by PKGBUILD — see PKGBUILD changes below).
      - **Post-install message** (same message block as T1 step 4). Do NOT include the ibus restart block.
   2. **post_upgrade()**: Keep calling `post_install` but the model download already has `if [ ! -f "$MODEL_FILE" ]` guards, so re-download is skipped on upgrade. No additional change needed.
   3. **pre_remove()**: Keep existing (udev rule removal). Add `rm -rf /usr/local/share/ibus-handwrite-chinese/venv` to clean up venv on removal.
   Must NOT: Remove udev reload (keep it), do not add input group, do not set engine, do NOT add stale root daemon kill, restart polling, or user daemon pgrep check, do NOT keep the automated ibus restart block, do not restructure PKGBUILD's `package()` function logic.
   Update `packaging/PKGBUILD`:
   1. **Depends line** (line 11): Remove `'python-onnxruntime'` (now installed via pip in venv), remove `'p7zip'` (no longer needed — PP-OCRv6 download doesn't use it), keep all other depends (`python`, `python-evdev`, `python-gobject`, `ibus`, `python-numpy`, `wget`, `unzip`).
   2. **pkgdesc line** (line 7): Change `Zinnia-based recognition` to `PP-OCRv6 ONNX-based recognition`.
   2. **Install engine script to ENGINE_DIR** (add after existing PKGBUILD install lines): The wrapper expects the engine script at `/usr/local/share/ibus-handwrite-chinese/ibus-engine-handwrite-chinese`. Add: `install -Dm644 src/ibus-engine-handwrite-chinese "${pkgdir}/usr/local/share/ibus-handwrite-chinese/ibus-engine-handwrite-chinese"`. (The `/usr/local/bin/` install on line 21 still happens — it will be overwritten by the .install wrapper script; the ENGINE_DIR copy is the one the wrapper actually uses.)
   3. **Install diagnose_trackpad.sh**: Add: `install -Dm755 tools/diagnose_trackpad.sh "${pkgdir}/usr/local/share/ibus-handwrite-chinese/diagnose_trackpad.sh"`
   Parallelization: Wave 1 | Blocked by: — | Blocks: T4
   References:
   - packaging/ibus-handwrite-chinese.install (entire file, current)
   - packaging/debian/postinst:9-45 (PP-OCRv6 model download)
   - packaging/debian/postinst:48-61 (venv+onnx)
   - packaging/debian/postinst:66-77 (wrapper — current, no sg input yet)
   - tools/install.sh:119-127 (sg input — the block to add)
   - packaging/PKGBUILD:7 (pkgdesc), :11 (depends line)
   Acceptance criteria (agent-executable):
   ```bash
   bash -n packaging/ibus-handwrite-chinese.install
   grep -q 'ppocrv6' packaging/ibus-handwrite-chinese.install       # PP-OCRv6 not Zinnia
   grep -q 'sg input' packaging/ibus-handwrite-chinese.install      # wrapper fallback
   grep -q 'diagnose_trackpad' packaging/ibus-handwrite-chinese.install
   grep -q 'To activate:  ibus restart' packaging/ibus-handwrite-chinese.install  # message, not automated
   grep -q 'select Chinese Handwriting' packaging/ibus-handwrite-chinese.install
   # Must NOT have Zinnia
   ! grep -q 'ZJHandWriting' packaging/ibus-handwrite-chinese.install
   ! grep -q 'zinnia\|Zinnia\|幽兰百合\|lily' packaging/ibus-handwrite-chinese.install
   # Must NOT have stale root daemon kill, restart polling, or user daemon check
   ! grep -q 'pgrep -u root ibus-daemon' packaging/ibus-handwrite-chinese.install
   ! grep -q 'timeout 1 ibus engine' packaging/ibus-handwrite-chinese.install
   ! grep -q 'logname.*ibus-daemon' packaging/ibus-handwrite-chinese.install
   # Must NOT have the automated ibus restart block
   ! grep -q 'Restarting IBus' packaging/ibus-handwrite-chinese.install
   ! grep -q 'ibus restart 2>/dev/null' packaging/ibus-handwrite-chinese.install
   # PKGBUILD: no python-onnxruntime or p7zip in depends
   ! grep -q "python-onnxruntime" packaging/PKGBUILD
   ! grep -q "p7zip" packaging/PKGBUILD
   # PKGBUILD: has ENGINE_DIR install and diagnose_trackpad.sh
   grep -q 'ibus-engine-handwrite-chinese' packaging/PKGBUILD
   grep -q 'diagnose_trackpad' packaging/PKGBUILD
   # PKGBUILD: no Zinnia mention in pkgdesc
   ! grep -q 'Zinnia\|ZJHandWriting\|幽兰百合' packaging/PKGBUILD
   ```
   QA scenarios:
   - Happy: All grep assertions pass.
   - Failure: If any assertion fails, fix and recheck.
   - Evidence: .omo/evidence/task-3-13-revise-postinstall-to-match-install-sh/diff-install.txt
   Commit: Y | `fix(arch): rewrite .install to match install.sh — PP-OCRv6, venv, wrapper, sg input, diagnose_trackpad, remove ibus restart`

- [x] 4. CI verify: commit, push — done (3 commits pushed to origin/main; no new tag per user request, release dispatch deferred)
  What to do / Must NOT do:
  After T1-T3 are committed, push to GitHub and dispatch the release workflow.
  1. Bump package version in all files to match the dispatch tag (e.g., `packaging/ibus-handwrite-chinese.spec` line 2 `%global srcver`, `packaging/PKGBUILD` line 5 `pkgver`). Or skip version bump and use a tag matching the current `0.1.0` (e.g., `v0.1.1` as a patch release). Document which approach was chosen.
  2. `git push origin main` (set remote with token for auth)
  3. `curl -X POST` to dispatch `release.yml` with the chosen tag (e.g., `v0.1.1`)
  4. Poll the workflow run every 60s until all jobs complete (expect 16 jobs: resolve tag, build-deb, build-rpm, build-source, verify-artifacts, test-packages x10, upload-release)
  5. If any job fails, report failure with error details; do NOT fix — user can decide
  Must NOT: Change release.yml workflow, change install.sh/bootstrap.sh, fix runtime errors — only report.
  Parallelization: Wave 2 | Blocked by: T1, T2, T3 | Blocks: —
  References:
  - .github/workflows/release.yml
  - GitHub API: repos/:owner/:repo/actions/workflows/release.yml/dispatches
  Acceptance criteria (agent-executable):
  ```bash
  # Release workflow run completes with conclusion: success
  # All 16 jobs (resolve tag, build-deb, build-rpm, build-source, verify-artifacts, test-packages x10, upload-release) pass
  ```
  QA scenarios:
  - Happy: All jobs green.
  - Failure: Report the failed job name, step name, and any available error excerpt.
  - Evidence: .omo/evidence/task-4-13-revise-postinstall-to-match-install-sh/workflow-result.txt
  Commit: N (plan is complete, no code changes)

## Final verification wave
> Runs in parallel after ALL todos. All must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [x] F1. Plan compliance audit — every acceptance criterion from T1-T4 is checked (T1-T3: ALL 38 checks PASS; T4: blocked by push auth)
- [x] F2. Code quality review — bash -n passes on modified shell scripts (.deb postinst, .install, build-deb.sh, build-rpm.sh). For .spec: `sed -n '/^%post/,/^%[a-z]/p' ... | head -n -1 | bash -n` on extracted %post section. (ALL 5 PASS)
- [x] F3. CI verification — release workflow passes on all 10 distros (16 jobs) [ALL PASS — Run 28744362463: success]
- [x] F4. Scope fidelity — no changes outside packaging/ directory, no input group, set-engine, stale root daemon kill, restart polling, user daemon pgrep check, or automated ibus restart additions (ALL checks PASS)

## Commit strategy
3 commits (one per package format), all on main branch. Sequence:
1. `fix(deb): align postinst with install.sh — sg input, diagnose_trackpad, post-install message`
2. `fix(rpm): align %post with install.sh — sg input, diagnose_trackpad, post-install message`
3. `fix(arch): rewrite .install to match install.sh — PP-OCRv6, venv, wrapper, sg input, diagnose_trackpad`
Push all 3, then dispatch T4 CI verify.

## Success criteria
- [x] `.deb` install: postinst downloads PP-OCRv6 model, creates venv+onnxruntime, installs wrapper with `sg input`, outputs post-install message (no automated ibus restart)
- [x] `.rpm` install: same
- [x] Arch install: same, plus PP-OCRv6 model downloaded (no Zinnia), venv created, wrapper with sg input, pre_remove cleans venv
- [x] Release workflow test-packages passes on all 10 distros (debian:11, debian:12, ubuntu:22.04, ubuntu:24.04, fedora:40, fedora:41, fedora:latest, archlinux:latest, opensuse/leap, opensuse/tumbleweed)
