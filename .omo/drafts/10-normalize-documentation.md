---
slug: 10-normalize-documentation
status: awaiting-approval
intent: clear
pending-action: write .omo/plans/10-normalize-documentation.md
approach: Update all project documents to reflect v0.2.0 ONNX-only reality, normalize terminology to "trackpad", fix badge URLs and inaccuracies, rename zh-Hans/zh-Hant READMEs with CJK suffix.
---

# Draft: 10-normalize-documentation

## Components (topology ledger)
| id | outcome | status | evidence path |
|----|---------|--------|---------------|
| C1 | English README.md | active | README.md:3-4 (badges), :6 (zh links), :15 (touchpad), :33/45 (Fedora), :154 (hardware), :253-254 (repo tree) |
| C2 | zh-Hans README → zh-Hans-汉 | active | README.zh-Hans.md → README.zh-Hans-汉.md (git mv) |
| C3 | zh-Hant README → zh-Hant-漢 | active | README.zh-Hant.md → README.zh-Hant-漢.md (git mv) |
| C4 | Stale accuracy test plan | active | docs/plan-handwriting-accuracy-test.md:1 (Tegaki vs 幽兰百合 refs) |
| C5 | Future plan doc | active | docs/multi-char-composition-with-phrase-boost-plan.md:118 ("touchpad") |
| C6 | IBus component XML | active | xml/handwrite-chinese.xml:15 ("touchpad" in description) |
| C7 | Install script message | active | tools/install.sh:85 ("touchpad access") |
| C8 | RPM packaging refs | active | packaging/build-rpm.sh:31, packaging/ibus-handwrite-chinese.spec:69 |
| C9 | PKGBUILD (pre-existing broken refs) | active | packaging/PKGBUILD:38-39 (zh-CN/zh-TW → must become new names) |
| C10 | Copilot instructions | deferred | .github/copilot-instructions.md — no changes needed |

## Open assumptions (announced defaults)
| assumption | adopted default | rationale | reversible? |
|-----------|----------------|-----------|-------------|
| Badge URLs go to ai-space-lab | Update to ai-space-lab/ibus-handwrite-chinese | Current remote is ai-space-lab, badges won't render | Yes |
| Fedora version | 40+ in BOTH table AND requirements section | CI tests fedora:40/41/latest | Yes |
| Chinese window position — feature desc | Fix both: "avoids active window" → "cursor-proximity" | EN README is correct; CN descriptions are wrong | Yes |
| Chinese window position — usage step | Fix both: "右下角" → "near text cursor" | EN README is correct; CN steps say bottom-right | Yes |
| Historical doc "touchpad" references | Leave as-is (historical artifact) | Accuracy test plan is superseded, normalizing would be revisionist | Yes |
| XML description | Update "touchpad" → "trackpad" | User-facing metadata, part of documentation normalization | Yes |
| docs/multi-char-composition line 118 | Normalize "touchpad" → "trackpad" | In-scope docs file | Yes |
| PKGBUILD pre-existing bug | Fix to new filenames (zh-CN/zh-TW → zh-Hans-汉/zh-Hant-漢) | PKGBUILD already broken referencing nonexistent old names | Yes |

## Findings (cited - path:lines)
1. **Badge URLs**: README.md:3-4, zh-Hans:3-4, zh-Hant:3-4 — point to `vinceyap88`, should be `ai-space-lab`
2. **Terminology**: READMEs use "touchpad" everywhere; code uses "trackpad" (class/method/file names)
3. **Fedora inconsistency**: README.md:33 table says "Fedora 39+", :45 Requirements says "Fedora 40+"
4. **Tested hardware overclaim**: README.md:15 — "Synaptics, ELAN, ALPS, and bcm5974" — only bcm5974 tested
5. **Chinese window position (feature)**: zh-Hans:19, zh-Hant:19 — "avoids active window"
6. **Chinese window position (usage)**: zh-Hans:89, zh-Hant:77 — "bottom-right"
7. **Stale engine comparison**: docs/plan-handwriting-accuracy-test.md — Tegaki vs 幽兰百合, both removed
8. **V2 plan doc touchpad**: docs/multi-char-composition-with-phrase-boost-plan.md:118 — "touchpad"
9. **XML description**: xml/handwrite-chinese.xml:15 — "Chinese handwriting input using touchpad"
10. **Install message**: tools/install.sh:85 — "Installing udev rule for touchpad access..."
11. **README rename blast radius**: README.md:6 (links), :253-254 (tree); both zh-Hans/zh-Hant self-referential tree lines; build-rpm.sh:31; spec:69; PKGBUILD:38-39 (already broken with zh-CN/zh-TW)

## Decisions (with rationale)
1. **Normalize all docs to "trackpad"** (per user). Changes in all READMEs, install.sh, XML, multi-char doc.
2. **Mark accuracy test plan as superseded + keep** (per user). Banner only.
3. **Keep udev rule filename as-is** (per user). Fix only install.sh message.
4. **Tested hardware wording**: Features list becomes `"(tested on MacBook Pro bcm5974 — other touchpads with BTN_TOUCH + ABS_X/ABS_MT_POSITION_X support may work but are untested)"`
5. **Badge URLs**: All 3 READMEs → `ai-space-lab/ibus-handwrite-chinese`.
6. **Rename zh-Hans → zh-Hans-汉, zh-Hant → zh-Hant-漢** (per user). git mv + update all 5 cross-referencing files + fix pre-existing PKGBUILD bug.
7. **PKGBUILD**: Clean-slate fix — update from broken zh-CN/zh-TW references to new zh-Hans-汉/zh-Hant-漢 names.

## Scope IN
- `README.zh-Hans.md` → `README.zh-Hans-汉.md` (git mv + update self refs)
- `README.zh-Hant.md` → `README.zh-Hant-漢.md` (git mv + update self refs)
- `README.md` — rename links + tree + all normalization (badges, terminology, tested hardware, Fedora)
- `README.zh-Hans-汉.md` — all normalization (badges, terminology, tested hardware, Fedora, window x2)
- `README.zh-Hant-漢.md` — all normalization (badges, terminology, tested hardware, Fedora, window x2)
- `docs/plan-handwriting-accuracy-test.md` — superseded banner (top only)
- `docs/multi-char-composition-with-phrase-boost-plan.md` — "touchpad" → "trackpad" line 118
- `xml/handwrite-chinese.xml` — "touchpad" → "trackpad" in `<description>`
- `tools/install.sh` — "touchpad" → "trackpad" in echo message
- `packaging/build-rpm.sh` — update filename refs for renamed READMEs
- `packaging/ibus-handwrite-chinese.spec` — update %doc filename refs
- `packaging/PKGBUILD` — fix pre-existing broken zh-CN/zh-TW refs → new names

## Scope OUT (Must NOT have)
- Do NOT rename code identifiers (TrackpadReader class, start_trackpad/stop_trackpad methods)
- Do NOT rename udev rule file (99-trackpad-handwrite.rules)
- Do NOT touch .omo/ internal plans or .omo/ drafts
- Do NOT change .github/copilot-instructions.md
- Do NOT change bootstrap.sh
- Do NOT touch debian/control or other packaging files beyond the 3 listed
- Do NOT normalize "touchpad" inside the superseded accuracy test plan
- Do NOT change XML component name, author, or version fields
- Do NOT touch source code or CI/CD
- Do NOT fix zinnia references in V2 plan doc

## Open questions
None — all forks resolved.

## Approval gate
status: awaiting-approval
pending action: write .omo/plans/10-normalize-documentation.md
