# 10-normalize-documentation - Work Plan

## TL;DR (For humans)

**What you'll get:** Project documentation cleaned up after v0.2.0 release — all references to "touchpad" become "trackpad" to match the code, the Chinese README filenames get CJK suffixes (汉/漢), badge URLs point to the right repo, tested hardware claims are accurate (only MacBook Pro was tested), Fedora version is consistent, Chinese READMEs correctly describe the window position, and a stale plan doc is marked as superseded.

**Why this approach:** Single coordinated pass avoids inconsistent partial fixes. Grouping the README rename with all its cross-reference updates ensures no broken links. Normalizing to "trackpad" aligns docs with the codebase naming (TrackpadReader, start_trackpad(), 99-trackpad-handwrite.rules).

**What it will NOT do:** Rename code identifiers or the udev rule file. Edit internal .omo/ plans or bootstrap.sh. Normalize terminology inside the superseded historical doc. Touch source code, CI/CD, or packaging beyond the 3 files that reference README filenames.

**Effort:** Short (7 files modified, 2 files renamed, ~200 lines changed across all)
**Risk:** Low — all changes are text substitutions and renames, no logic changes, no CI-impacting changes
**Decisions to sanity-check:** The zh-Hans-汉 and zh-Hant-漢 filenames (CJK suffix), and the PKGBUILD pre-existing bug fix (zh-CN/zh-TW → new names).

Your next move: approve, then run with `$start-work`.

---

> TL;DR (machine): Short effort, Low risk. 7 doc files updated + 2 renamed + 3 packaging refs fixed. Terminology normalized to "trackpad". Badge URLs fixed. PKGBUILD stale refs cleaned up as side-effect.

## Scope
### Must have
1. Rename `README.zh-Hans.md` → `README.zh-Hans-汉.md` (git mv)
2. Rename `README.zh-Hant.md` → `README.zh-Hant-漢.md` (git mv)
3. Update all cross-references to renamed files in:
   - `README.md` (language switcher link + repo tree)
   - `README.zh-Hans-汉.md` (repo tree — self-reference)
   - `README.zh-Hant-漢.md` (repo tree — self-reference)
   - `packaging/build-rpm.sh` (tarball file list)
   - `packaging/ibus-handwrite-chinese.spec` (%doc list)
   - `packaging/PKGBUILD` (broken zh-CN/zh-TW refs → new names)
4. Normalize "touchpad" → "trackpad" in:
   - `README.md` (all occurrences)
   - `README.zh-Hans-汉.md` (all occurrences — after rename)
   - `README.zh-Hant-漢.md` (all occurrences — after rename)
   - `xml/handwrite-chinese.xml` (`<description>` string)
   - `tools/install.sh` (echo message)
   - `docs/multi-char-composition-with-phrase-boost-plan.md` (line 118)
5. Fix badge URLs in all 3 READMEs: `vinceyap88` → `ai-space-lab`
6. Fix Fedora version in all 3 READMEs: table "39+" → "40+"
7. Fix tested hardware claim in all 3 READMEs features list: drop "Synaptics, ELAN, ALPS" → state only bcm5974 tested
8. Fix Chinese window position in zh-Hans-汉 and zh-Hant-漢:
   - Feature description: "avoids active window" → "cursor-proximity"
   - Usage step: "bottom-right" → "near text cursor"
9. Add superseded banner to `docs/plan-handwriting-accuracy-test.md`

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do NOT rename code identifiers (TrackpadReader class, start_trackpad/stop_trackpad methods)
- Do NOT rename udev rule file (99-trackpad-handwrite.rules)
- Do NOT touch .omo/ internal plans or .omo/ drafts
- Do NOT change .github/copilot-instructions.md
- Do NOT change bootstrap.sh
- Do NOT touch debian/control or other packaging files beyond the 3 listed
- Do NOT normalize "touchpad" inside the superseded accuracy test plan (leave as historical artifact)
- Do NOT change XML component name, author, or version fields
- Do NOT touch source code or CI/CD
- Do NOT fix zinnia references in V2 plan doc

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: none (no logic changes, all text substitutions)
- Evidence: verify via `grep` + `git diff` + file existence checks

## Execution strategy
### Parallel execution waves
- **Wave 1 (parallelizable):** git mv both READMEs, update all cross-references simultaneously
- **Wave 2 (parallelizable):** apply all text substitutions across all affected files
- **Wave 3:** superseded banner + final verification pass

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1-2 (rename + refs) | — | 3,4,5,6,7,8 | — |
| 3 (trackpad normalization) | — | — | 4,5,6,7,8 |
| 4 (badge URLs) | — | — | 3,5,6,7,8 |
| 5 (Fedora version) | — | — | 3,4,6,7,8 |
| 6 (tested hardware) | — | — | 3,4,5,7,8 |
| 7 (window position) | — | — | 3,4,5,6,8 |
| 8 (superseded banner) | — | — | 3,4,5,6,7 |
| 9 (final verify) | 1-8 | — | — |
| 10 (commit) | 9 | — | — |

## Todos
> Implementation + Test = ONE todo. Never separate.
- [ ] 1. Rename README zh-Hans and zh-Hant + update all cross-references
  What to do:
   1. `git mv README.zh-Hans.md README.zh-Hans-汉.md`
   2. `git mv README.zh-Hant.md README.zh-Hant-漢.md`
   3. Update `README.md` line 6: `README.zh-Hans.md` → `README.zh-Hans-汉.md`, `README.zh-Hant.md` → `README.zh-Hant-漢.md`
   4. Update `README.md` lines 253-254 in repo tree with new filenames
   5. Update `README.zh-Hans-汉.md` lines 256-257 in repo tree with new filenames
   6. Update `README.zh-Hant-漢.md` lines 256-257 in repo tree with new filenames
   7. Update `packaging/build-rpm.sh` line 31: both filename refs
   8. Update `packaging/ibus-handwrite-chinese.spec` line 69: both filename refs
   9. Update `packaging/PKGBUILD` lines 38-39: replace broken `zh-CN.md`/`zh-TW.md` refs with `zh-Hans-汉.md`/`zh-Hant-漢.md`
  Must NOT do: Do NOT rename any other files. Do NOT touch debian/control.
  Parallelization: Wave 1 | Blocked by: — | Blocks: 9,10
  References: README.md:6, :253-254; README.zh-Hans.md:256-257; README.zh-Hant.md:256-257; packaging/build-rpm.sh:31; packaging/ibus-handwrite-chinese.spec:69; packaging/PKGBUILD:38-39
  Acceptance criteria: `git diff --stat` shows 2 renames + 6 files with updated refs. `grep -r "README.zh-Hans[^-汉]" --include="*.md" --include="*.sh" --include="*.spec" --include="PKGBUILD"` returns zero matches (except the new filenames themselves). Files exist at new paths.
  QA scenarios: happy: `ls README.zh-Hans-汉.md README.zh-Hant-漢.md` succeeds, old paths fail. failure: grep for old filenames returns only intentional self-references within the new files.
  Commit: N (part of final commit)

- [ ] 2. Normalize "touchpad" → "trackpad" across all docs
  What to do: Replace "touchpad" with "trackpad" (case-sensitive, whole-word) in:
   - `README.md` (all occurrences — features, troubleshooting, etc.)
   - `README.zh-Hans-汉.md` (all occurrences)
   - `README.zh-Hant-漢.md` (all occurrences)
   - `xml/handwrite-chinese.xml` line 15: `<description>Chinese handwriting input using trackpad</description>`
   - `tools/install.sh` line 85: "Installing udev rule for trackpad access..."
   - `docs/multi-char-composition-with-phrase-boost-plan.md` line 118: replace "touchpad" with "trackpad"
  Must NOT do: Do NOT change "touchpad" inside `docs/plan-handwriting-accuracy-test.md` (historical artifact). Do NOT change code identifiers. Do NOT change "touchscreen".
  Parallelization: Wave 2 | Blocked by: 1 | Blocks: 9
  References: README.md:15, :104, :107; zh-Hans:13, :102, :105; zh-Hant:13, :90, :93; xml/handwrite-chinese.xml:15; tools/install.sh:85; docs/multi-char-composition-with-phrase-boost-plan.md:118
  Acceptance criteria: `grep -rn "touchpad" README.md README.zh-Hans-汉.md README.zh-Hant-漢.md xml/handwrite-chinese.xml tools/install.sh docs/multi-char-composition-with-phrase-boost-plan.md` returns zero matches (case-sensitive "touchpad"). Superseded doc `docs/plan-handwriting-accuracy-test.md` still has "touchpad".
  QA scenarios: happy: verify zero "touchpad" hits in modified files, verify "trackpad" appears. failure: grep for "touchpad" in modified files should be empty.
  Commit: N (part of final commit)

- [ ] 3. Fix badge URLs in all 3 READMEs
  What to do: Replace `vinceyap88/ibus-handwrite-chinese` with `ai-space-lab/ibus-handwrite-chinese` in badge URLs in:
   - `README.md` lines 3-4
   - `README.zh-Hans-汉.md` lines 3-4
   - `README.zh-Hant-漢.md` lines 3-4
  The badges are: `https://github.com/vinceyap88/ibus-handwrite-chinese/actions/workflows/ci.yml/badge.svg` → `https://github.com/ai-space-lab/ibus-handwrite-chinese/actions/workflows/ci.yml/badge.svg`
  Same for the release badge.
  Must NOT do: Do NOT change the link text or alt text.
  Parallelization: Wave 2 | Blocked by: 1 | Blocks: 9
  References: README.md:3-4; README.zh-Hans-汉.md:3-4; README.zh-Hant-漢.md:3-4
  Acceptance criteria: `grep "vinceyap88" README.md README.zh-Hans-汉.md README.zh-Hant-漢.md` returns zero matches (except URLs matching the author field).
  QA scenarios: happy: badge URLs now start with `https://github.com/ai-space-lab/`. failure: verify no remaining vinceyap88 in badge lines.
  Commit: N (part of final commit)

- [ ] 4. Fix Fedora version in all 3 READMEs
  What to do: In the cross-distro support table, change "Fedora 39+" to "Fedora 40+" in:
   - `README.md` (table row)
   - `README.zh-Hans-汉.md` (table row)
   - `README.zh-Hant-漢.md` (table row)
  Requirements section already says "Fedora 40+" — no change needed there.
  Parallelization: Wave 2 | Blocked by: 1 | Blocks: 9
  References: README.md:33; README.zh-Hans-汉.md:33; README.zh-Hant-漢.md:33
  Acceptance criteria: `grep -n "Fedora.*39" README.md README.zh-Hans-汉.md README.zh-Hant-漢.md` returns zero matches.
  QA scenarios: happy: table shows "Fedora 40+" consistently. failure: verify no remnant "39+".
  Commit: N (part of final commit)

- [ ] 5. Fix tested hardware claim in all 3 READMEs
  What to do: In the features list section, replace vendor list with accurate tested-hardware statement.
  Current text (varies slightly by language): "all modern Synaptics, ELAN, ALPS, and bcm5974 touchpads"
  Replacement text:
   - English: "(tested on MacBook Pro bcm5974 — other touchpads with BTN_TOUCH + ABS_X/ABS_MT_POSITION_X support may work but are untested)"
   - zh-Hans: "(已在 MacBook Pro bcm5974 上测试通过——其他支持 BTN_TOUCH + ABS_X/ABS_MT_POSITION_X 的触摸板可能可用，但未经测试)"
   - zh-Hant: "(已在 MacBook Pro bcm5974 上測試通過——其他支援 BTN_TOUCH + ABS_X/ABS_MT_POSITION_X 的觸控板可能可用，但未經測試)"
  Note: All Chinese "touchpad" references will be normalized to "trackpad" in todo 2 — apply this fix AFTER the normalization pass to avoid conflicts.
  Must NOT do: Do NOT change the Known Limitations section — it's already accurate.
  Parallelization: Wave 2 | Blocked by: 1, 2 | Blocks: 9
  References: README.md:15; README.zh-Hans-汉.md:13; README.zh-Hant-漢.md:13; README.md:154 (limitations — DO NOT TOUCH)
  Acceptance criteria: Features list no longer claims Synaptics/ELAN/ALPS support. Limitations section unchanged.
  QA scenarios: happy: features list mentions only bcm5974 tested. failure: verify no leftover "Synaptics", "ELAN", or "ALPS" in features section.
  Commit: N (part of final commit)

- [ ] 6. Fix Chinese window position descriptions (zh-Hans-汉 and zh-Hant-漢)
  What to do: Two fixes per file:
   - **Feature description**: Replace text about "avoids active window" with "cursor-proximity positioning" matching English README.
     - zh-Hans: "智能窗口定位：弹出面板自动避开当前活动窗口" → "智能窗口定位：弹出面板自动出现在文本光标附近，不遮挡应用程序视图"
     - zh-Hant: "智慧視窗定位：彈出面板自動避開當前活動視窗" → "智慧視窗定位：彈出面板自動出現在文字游標附近，不遮擋應用程式畫面"
   - **Usage step**: Replace "bottom-right" with "near text cursor".
     - zh-Hans: "深色浮动面板将在屏幕右下角出现" → "深色浮动面板将出现在您的文本光标附近"
     - zh-Hant: "深色浮動面板將在螢幕右下角出現" → "深色浮動面板將出現在您的文字游標附近"
  Must NOT do: Do NOT change the English README (already correct).
  Parallelization: Wave 2 | Blocked by: 1 | Blocks: 9
  References: zh-Hans:19 (feature), :89 (usage); zh-Hant:19 (feature), :77 (usage)
  Acceptance criteria: "右下角" does not appear in either Chinese README. "自动避开" (auto-avoid) does not appear in feature description. Both files have "cursor" or "光标"/"游標" in window position descriptions.
  QA scenarios: happy: features list describes cursor-proximity, usage step says near cursor. failure: verify no remaining "右下角" or "自动避开" in window position sections.
  Commit: N (part of final commit)

- [ ] 7. Add superseded banner to docs/plan-handwriting-accuracy-test.md
  What to do: Insert at the very top of the file (after title, before content):
  ```
  > ⚠️ **Superseded** — both engines compared (Tegaki, 幽兰百合) were removed in v0.2.0.
  > The project now uses PP-OCRv6 ONNX only. See [README.md PP-OCRv6 Integration section](../README.md#pp-ocrv6-integration) for current validation results.
  ```
  Must NOT do: Do NOT modify any other content in the file. Do NOT normalize "touchpad" inside. Do NOT delete the file.
  Parallelization: Wave 3 | Blocked by: — | Blocks: 9
  References: docs/plan-handwriting-accuracy-test.md:1-5
  Acceptance criteria: File begins with the superseded warning banner. Original content unchanged after the banner.
  QA scenarios: happy: banner visible at top of file. failure: verify no accidental deletions below the banner.
  Commit: N (part of final commit)

- [ ] 8. Final verification pass
  What to do: Run all acceptance criteria checks:
   1. `ls README.zh-Hans-汉.md README.zh-Hant-漢.md` — both new files exist
   2. `ls README.zh-Hans.md README.zh-Hant.md 2>&1` — old names gone
   3. `grep -rn "touchpad" README.md README.zh-Hans-汉.md README.zh-Hant-漢.md xml/handwrite-chinese.xml tools/install.sh docs/multi-char-composition-with-phrase-boost-plan.md | grep -v "^Binary"` — zero matches
   4. `grep "touchpad" docs/plan-handwriting-accuracy-test.md` — still has "touchpad" (historical artifact)
   5. `grep -n "vinceyap88" README.md README.zh-Hans-汉.md README.zh-Hant-漢.md | grep "github.com" | grep -v "author"` — zero badge URL matches
   6. `grep -n "Fedora.*39\|Fedora.*39" README.md README.zh-Hans-汉.md README.zh-Hant-漢.md` — zero matches
   7. `grep -n "Synaptics\|ELAN\|ALPS" README.md README.zh-Hans-汉.md README.zh-Hant-漢.md` — zero matches in features section
   8. `grep "右下角" README.zh-Hans-汉.md README.zh-Hant-漢.md` — zero matches
   9. `grep "README.zh-Hans\[^-汉\]" README.md packaging/build-rpm.sh packaging/ibus-handwrite-chinese.spec packaging/PKGBUILD` — zero matches (all updated)
   10. `grep "README.zh-Hant\[^-漢\]" README.md packaging/build-rpm.sh packaging/ibus-handwrite-chinese.spec packaging/PKGBUILD` — zero matches (all updated)
  Must NOT do: Do NOT change any files during verification.
  Parallelization: Wave 3 | Blocked by: 1-7 | Blocks: 9
  References: All files in scope
  Acceptance criteria: All 10 checks pass
  QA scenarios: happy: all checks pass cleanly.
  Commit: N (prerequisite for commit)

- [ ] 9. Commit all changes
  What to do:
   ```
   git add -A
   git commit -m "docs: normalize terminology to trackpad, rename zh READMEs, fix badge URLs and inaccuracies"
   git push origin main
   ```
  Parallelization: — | Blocked by: 8 | Blocks: —
  References: git status, git log
  Acceptance criteria: `git log --oneline -1` shows the commit message. `git status` is clean.
  QA scenarios: happy: commit succeeds, push succeeds. failure: if push fails (branch protection), surface the error for user.
  Commit: Y (single commit)

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit — verify todos 1-9 executed to spec
- [ ] F2. Code quality review — verify no unintended changes in git diff
- [ ] F3. Real manual QA — spot-check README.md renders correctly, links work
- [ ] F4. Scope fidelity — verify all Must NOT have items were not touched

## Commit strategy
Single commit: `docs: normalize terminology to trackpad, rename zh READMEs, fix badge URLs and inaccuracies`
No squash or amend needed — all changes are documentation-only.

## Success criteria
- `README.zh-Hans-汉.md` and `README.zh-Hant-漢.md` exist; old names deleted
- Zero occurrences of "touchpad" in any modified file (except superseded doc)
- Badge URLs point to `ai-space-lab/ibus-handwrite-chinese`
- Fedora version consistent at 40+
- Tested hardware: only bcm5974 mentioned as tested
- Chinese READMEs: window position says "cursor-proximity"/"near cursor"
- docs/plan-handwriting-accuracy-test.md has superseded banner at top
- All packaging file references updated to new README names
- PKGBUILD no longer references nonexistent zh-CN/zh-TW filenames
