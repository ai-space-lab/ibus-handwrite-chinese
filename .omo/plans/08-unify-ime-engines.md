---
slug: 08-unify-ime-engines
status: approved
intent: clear
branch: refactor/unify-ime-engines
based-on: feat/ppocr-v6-integration
---

# Plan 08: Unify IME Engines

Merge the two IBus engines (`handwrite-chinese-simplified`, `handwrite-chinese-traditional`) into one unified ONNX-only engine using PP-OCRv6 for both simplified and traditional scripts. Remove the `--traditional` flag, all Zinnia/tegaki fallback code, and both old icons. Replace with pure ONNX recognition and a new `中` icon in chop red.

## Approach

Merge 2 engines → 1. The split is driven by a single `--traditional` CLI flag and a `_USE_ONNX` global. Remove both, hardcode unified identity, strip all Zinnia ctypes code (~88 LOC of ZinniaHandle + 134 references). New icon `中` in seal red (#c41e3a) is script-neutral. Install scripts drop tegaki-zinnia deps. CI drops `simplified traditional` loops.

## Task list

### Icon and XML

1. Create `icons/handwrite-chinese.svg` — 64×64 SVG, background `#c41e3a` (vermillion chop red), white `中` character centered, sans-serif bold
2. Create `xml/handwrite-chinese.xml` — IBus component with:
   - `<name>com.github.vinceyap88.ibus-handwrite-chinese</name>`
   - `<exec>/usr/local/bin/ibus-engine-handwrite-chinese --ibus</exec>`
   - `<name>handwrite-chinese</name>`, `<longname>Chinese Handwriting</longname>`
   - `<icon>/usr/local/share/ibus-handwrite-chinese/icons/handwrite-chinese.svg</icon>`
   - `<language>zh</language>`
3. Delete old XMLs: `xml/handwrite-chinese-simplified.xml`, `xml/handwrite-chinese-traditional.xml`
4. Delete old icons: `icons/handwrite-chinese-simplified.svg`, `icons/handwrite-chinese-traditional.svg`

### Engine code — remove Zinnia infrastructure

5. Remove zinnia ctypes imports and global variables from `src/ibus-engine-handwrite-chinese`:
   - Remove `import ctypes` (line 5)
   - Remove globals: `ZINNIA_MODEL` (31), `ZINNIA_MODEL_LILY` (32), `ZINNIA_MODEL_BACKUP` (33)
   - Remove `_USE_FREQ` (35), `_USE_ONNX` (36), `_FREQ` dict (160-184)
   - Remove `libz = ctypes.CDLL(...)` block and all zinnia ctypes signature setup (lines 65-99)
6. Remove entire `ZinniaHandle` class (lines 186-274)

### Engine code — simplify HandwriteEngine

7. `HandwriteEngine.__init__` (line 978): always create `self.onnx = self._create_onnx_handle()`, remove `self.zinnia`/`self.zinnia_backup` and the `if _USE_ONNX` branch
8. `HandwriteEngine.recognizer` property (line 1004): always return `self.onnx`
9. `HandwriteEngine.update_candidates` (line 1184): keep only `self.onnx.classify_async(self._on_results)`, remove synchronous zinnia classify path
10. `HandwriteEngine.do_enable` (line 1112), `do_disable` (line 1132), `do_reset` (line 1175): remove `if not _USE_ONNX and self.zinnia_backup` lines
11. `HandwriteEngine.destroy` (line 1207): remove `if _USE_ONNX` branch and zinnia backup destruction — only destroy `self.onnx`

### Engine code — simplify TestCommitEngine

12. `TestCommitEngine.__init__` (line 1229): remove `traditional=False` param, remove `self.zinnia`/`self.zinnia_backup`, always create `self.onnx = HandwriteEngine._create_onnx_handle()`
13. `TestCommitEngine.recognizer` property (line 1270): always return `self.onnx`
14. `TestCommitEngine.do_reset` (line 1285): remove `if not _USE_ONNX and self.zinnia_backup` line
15. `TestCommitEngine.update_candidates` (line 1299): remove zinnia classify path, keep only ONNX path
16. Remove `TestCommitEngine.switch_model` entirely (lines 1317-1356)
17. `TestCommitEngine.destroy` (line 1358): remove `if _USE_ONNX` branch and zinnia cleanup — only destroy `self.onnx`

### Engine code — simplify main()

18. `main()` (line 1372):
    - Remove `parser.add_argument('--traditional', ...)` (line 1376)
    - Remove `if args.traditional:` block (lines 1381-1398), including `global ZINNIA_MODEL, ZINNIA_MODEL_BACKUP, _USE_FREQ, _USE_ONNX`
    - Hardcode: `engine_name = "handwrite-chinese"`, `engine_longname = "Chinese Handwriting"`, `engine_language = "zh"`, `component_name = "com.github.vinceyap88.ibus-handwrite-chinese"`
19. Update module docstring (line 2): remove "Zinnia" reference
20. Verify no remaining references to `zinnia`, `ZINNIA`, `_USE_ONNX`, `_USE_FREQ`, `--traditional` in the engine file

### Install scripts

21. `tools/install.sh`:
    - Remove tegaki-zinnia APT installs (lines 84-98)
    - Remove model download blocks for traditional and 幽兰百合 models
    - Copy only `xml/handwrite-chinese.xml`, `icons/handwrite-chinese.svg`
    - Update user guidance messages for single engine
22. `bootstrap.sh`:
    - Remove tegaki-zinnia package installation for all distros
    - Remove 幽兰百合 model download
    - Remove `$lang` parameter and `zh_TW` switch block (lines 62-63)
    - Update echo messages for single-engine install
23. `tools/restore.sh`:
    - Replace old XML/icon removals with new single file references

### Packaging

24. `packaging/build-deb.sh`: replace old XML/icon paths with new single files
25. `packaging/debian/install`: replace old XML/icon paths with new single files
26. `packaging/debian/control`: remove tegaki-zinnia from Recommends; update description
27. `packaging/debian/postinst`: remove tegaki-zinnia model download URLs
28. `packaging/PKGBUILD`: replace old XML/icon paths; remove zinnia AUR dependency
29. `packaging/ibus-handwrite-chinese.spec`: replace old XML/icon paths; update %files list; remove model download postinst
30. `packaging/ibus-handwrite-chinese.install`: remove tegaki-zinnia model download URLs

### CI/CD

31. `.github/workflows/ci.yml`:
    - Lint: validate only `xml/handwrite-chinese.xml` (line 19)
    - Remove tegaki-zinnia APT installs and fallback downloads (lines 49-57, 157-161)
    - Remove file existence checks for old XMLs/icons (lines 102-106)
    - Remove `for m in simplified traditional; do` loops (lines 170, 183, 197)
    - Remove `zinnia.so` verification step
32. `.github/workflows/release.yml`: remove tegaki-zinnia from AUR install (line 211)

### Tests

33. Rewrite `tests/test_recognition.py`:
    - Remove all Zinnia ctypes code (lines 4-117)
    - Replace with PP-OCRv6 ONNX test using `OnnxHandle` directly
    - Test synthetic strokes: horizontal line → `一`, cross → `十`, verify confidence > threshold
    - Remove simplified/traditional model paths

### Documentation

34. `README.md`:
    - Engine IDs: `handwrite-chinese-simplified`/`handwrite-chinese-traditional` → `handwrite-chinese`
    - Longnames: remove "(Simplified)"/"(Traditional)" qualifiers
    - Remove Zinnia/tegaki/幽兰百合 model descriptions
    - Remove dual-engine install instructions and engine switching commands
    - Update PP-OCRv6 section: remove `_USE_ONNX` flag explanation
    - Update Known Limitations: remove Zinnia accuracy comparison
    - Update Quick Install: remove tegaki APT packages
35. `README.zh-Hans.md`: same changes as step 34, in Simplified Chinese
36. `README.zh-Hant.md`: same changes as step 34, in Traditional Chinese

### Housekeeping

37. `.github/copilot-instructions.md`: update `xmllint` command to validate only `xml/handwrite-chinese.xml`
38. Final `git status` / `git diff` review — ensure no stale references remain

## Verification Gates

F1. `grep -ri "zinnia\|ZINNIA\|_USE_ONNX\|--traditional\|handwrite-chinese-simplified\|handwrite-chinese-traditional" src/ xml/ icons/` — zero matches
F2. `xmllint --noout xml/handwrite-chinese.xml` — valid XML
F3. `python3 -c "import py_compile; py_compile.compile('src/ibus-engine-handwrite-chinese', doraise=True)"` — no syntax errors
F4. `python3 src/ibus-engine-handwrite-chinese --test` — GTK window opens, ONNX loads (no zinnia errors)
F5. `ibus engine handwrite-chinese` — engine switches and recognizes characters
F6. All 3 READMEs reviewed for stale split-engine language

## Rollback

1. `git checkout HEAD -- src/ibus-engine-handwrite-chinese xml/ icons/` restores engine and files
2. tegaki-zinnia packages reinstalled via apt if needed
3. Old simplified/traditional XMLs and icons exist in git history
