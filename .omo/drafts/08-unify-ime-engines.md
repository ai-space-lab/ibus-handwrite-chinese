---
slug: 08-unify-ime-engines
status: awaiting-approval
intent: clear
pending-action: write .omo/plans/08-unify-ime-engines.md
approach: Merge the two IBus engines into one unified ONNX-only engine using PP-OCRv6 for both simplified and traditional scripts. Remove the --traditional flag, all Zinnia/tegaki fallback code, and both old icons. Replace with pure ONNX recognition and a new 中 icon in chop red.
---

# Draft: 08-unify-ime-engines

## Components (topology ledger)
| id | outcome | status | evidence path |
|----|---------|--------|---------------|
| C1 | Engine code: remove --traditional flag AND Zinnia fallback; always ONNX only | active | src/ibus-engine-handwrite-chinese:1376-1398, :1231-1240, :1317-1333 |
| C2 | IBus XML: replace 2 files with 1 unified XML | active | xml/handwrite-chinese-simplified.xml, xml/handwrite-chinese-traditional.xml |
| C3 | Icon: new 中 icon in chop red (#c41e3a), replace both old icons | active | icons/handwrite-chinese-simplified.svg (#2d5a27, 写), icons/handwrite-chinese-traditional.svg (#8b4513, 寫) |
| C4 | Install scripts: remove tegaki-zinnia deps & model downloads; update paths to single engine | active | tools/install.sh:84-192, tools/restore.sh:15, bootstrap.sh:62-138 |
| C5 | Packaging: remove tegaki-zinnia dependencies; update all packaging/* to single engine | active | packaging/ (8 files reference the split) |
| C6 | CI/CD: remove tegaki-zinnia installs, zinnia.so verification, simplified/traditional loops | active | .github/workflows/ci.yml:19-197, release.yml:211 |
| C7 | Tests: update test_recognition.py to remove Zinnia-based tests | active | tests/test_recognition.py:128-130 |
| C8 | Documentation: update READMEs for single-engine, pure-ONNX architecture | active | README.md, README.zh-Hans.md, README.zh-Hant.md |
| C9 | Copilot instructions: update XML validation refs | deferred | .github/copilot-instructions.md:32 |

## Open assumptions (announced defaults)
| assumption | adopted default | rationale | reversible? |
|------------|----------------|-----------|-------------|
| New engine name | `handwrite-chinese`, longname "Chinese Handwriting" | No qualifier needed — it handles both scripts; shortest, cleanest | yes — trivial XML change |
| Icon | New icon: 中 in chop red (#c41e3a, 朱红/vermillion) | 中 is script-neutral (same in simplified + traditional); chop red is culturally authentic. Replaces both old icons. | yes |
| Zinnia/tegaki fallback | Remove entirely — ONNX only | PP-OCRv6 covers 18,707 chars (proven 100% on 40 real chars), outpaces all Zinnia models combined. No fallback needed. Simpler code, fewer deps. | yes |
| Backward compat | Drop old engine IDs, no aliases | Old engine IDs were separate processes; can't alias across different IBus engines. Users re-add the one new engine. | N/A |
| --traditional flag | Remove entirely | Unused after unification — ONNX handles both scripts | yes — re-add if needed |

## Findings (cited - path:lines)
1. PP-OCRv6 dict covers 18,707 chars including ALL common simplified AND traditional characters. 0/113 traditional test chars missing. (verified: dict_v6.txt)
2. The entire engine split is driven by ONE CLI flag `--traditional` at line 1376. (src/ibus-engine-handwrite-chinese:1376)
3. When --traditional is set, _USE_ONNX = False — the traditional path doesn't use PP-OCRv6 at all. (src/ibus-engine-handwrite-chinese:1389)
4. 26 files across the repo reference the simplified/traditional split. (exploration sweep)
5. The traditional XML invokes `--ibus --traditional` at the OS level. (xml/handwrite-chinese-traditional.xml:5)
6. CI iterates `for m in simplified traditional; do` in 3 distro test blocks. (.github/workflows/ci.yml:170,183,197)

## Decisions (with rationale)
- **Unify to one engine** — PP-OCRv6 covers both scripts comprehensively. The traditional path was inferior (Zinnia-only, 11,853 chars vs 18,707). Users shouldn't guess which script mode before writing.
- **Engine ID: `handwrite-chinese`** — Simple, neutral, one entry in the IBus menu.
- **Pure ONNX — no Zinnia, no tegaki** — PP-OCRv6 dict (18,707 chars) exceeds all Zinnia models combined (zh_CN 6,763 + zh_TW 11,853 + 幽兰百合 ~9,374, all overlapping). 100% accuracy on 40 real chars, 14/14 similar pairs correct. Removing Zinnia eliminates ctypes dependency, model download/management, and a whole code path (~150 LOC).
- **Icon: 中 in chop red** — `handwrite-chinese.svg` with #c41e3a (朱红 / vermillion seal red) background and 中 character. 中 is identical in simplified + traditional, and the chop red is culturally authentic. Replaces both old icons (green 写 and brown 寫).
- **--traditional flag: remove** — Dead code after unification.

## Scope IN
1. Engine code: remove `--traditional` flag, remove all Zinnia/tegaki code, make ONNX the only recognition path
2. IBus XML: create `xml/handwrite-chinese.xml`, remove old simplified/traditional XMLs
3. Icon: create `icons/handwrite-chinese.svg` (64×64, #c41e3a bg, white 中), remove both old icons
4. Install scripts: remove tegaki-zinnia deps & model downloads; install only the new XML + icon
5. Packaging: remove tegaki-zinnia dependencies; update all files to reference single XML + icon + engine name
6. CI: remove tegaki-zinnia installs, zinnia.so verification, simplified/traditional loops
7. Tests: update test_recognition.py to remove Zinnia-based test paths
8. READMEs: remove split-engine instructions, document single unified ONNX engine
9. Copilot instructions: update XML lint command

## Scope OUT (Must NOT have)
- No changes to PP-OCRv6 recognition logic or model files
- No changes to GTK UI behavior
- No changes to evdev touchpad input handling
- No changes to the --test mode (already works as unified)
- No frequency model changes
- No multi-character composition (separate future concern)

## Open questions
None — all forks resolved by adopted defaults above.

## Approval gate
status: awaiting-approval
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->
