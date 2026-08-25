---
slug: 07-ppocr-pipeline-fixes-and-validation
status: drafting
intent: clear
pending-action: write .omo/plans/07-ppocr-pipeline-fixes-and-validation.md
approach: Apply two surgical pipeline fixes (decode confidence pooling, stroke line width), then collect 20-50 more handwriting samples with the fixed pipeline to validate sustained 100% accuracy, run formal analysis, and investigate similar-pair edge cases.
---

# Draft: 07-ppocr-pipeline-fixes-and-validation

## Components (topology ledger)
<!-- id | outcome (one line) | status: active|deferred | evidence path -->
1. engine/_decode() fix (mean→max pooling) | Apply to OnnxHandle._decode | active | src/ibus-engine-handwrite-chinese:402-421
2. engine/_preprocess() line width (6→8px) | Apply to OnnxHandle._preprocess | active | src/ibus-engine-handwrite-chinese:364
3. collect 20-50 more chars with fixed pipeline | Run collect_ppocr_data.py | active | scripts/collect_ppocr_data.py
4. formal analysis on dataset_fixed.jsonl | Run analyze_ppocr_data.py | active | scripts/analyze_ppocr_data.py
5. similar-pair edge cases (已/己, 未/末) | Investigate if 100% holds | deferred | depends on step 3

## Open assumptions (announced defaults)
1. MEAN→MAX pooling is safe enough for now; true CTC greedy (argmax→collapse blanks→collapse repeats→mean conf of non-blank steps) can be done later if multi-character support is needed
2. Line width 8px is the right bump (at 48px canvas, 6/200→1.44px rendered → 8/200→1.92px); if 8px degrades accuracy, step back to 7px
3. 20-50 additional characters is sufficient for statistical signal beyond the existing 5
4. HSK level 1 character list (~150 chars from collect script) is appropriate for validation

## Findings (cited - path:lines)
1. **Dict fix already applied**: `line.rstrip('\n')` at line 290 preserves U+3000. Earlier `line.strip()` bug at dict line 1748 was causing ALL predictions to shift by 1 index — root cause of the pre-fix 0% accuracy. (src/ibus-engine-handwrite-chinese:288-292)
2. **Decode still uses `np.mean`**: Line 405 `avg_probs = np.mean(probs, axis=0)` averages across ALL time steps including blank frames, diluting confidence. 一 shows 7% confidence instead of true ~68% with `np.max`. (src/ibus-engine-handwrite-chinese:402-421)
3. **Line width still 6px**: Line 364 `cr.set_line_width(6)`. At 48px canvas height with 200px source canvas, effective stroke is ~1.44px — slightly thin for the model's training distribution. (src/ibus-engine-handwrite-chinese:364)
4. **5 post-fix characters collected**: dataset_fixed.jsonl — 一, 十, 人, 大, 口 — all 5 correct at top-1 (100%). But using buggy MEAN decode, so confidence scores are artificially low (0.07-0.25). (data/dataset_fixed.jsonl)
5. **7 pre-fix characters collected**: dataset.jsonl — all wrong (0% accuracy), caused by the dict index bug now fixed. (data/dataset.jsonl)
6. **Analysis script ready but stale**: analyze_ppocr_data.py exists but expects JSON format (not JSONL). Last report in .omo/evidence/ shows 0% accuracy from pre-fix data. (scripts/analyze_ppocr_data.py, .omo/evidence/ppocr-handwriting-dataset/analysis-report.json)
7. **Collection script ready**: collect_ppocr_data.py with prompt/free/dry-run modes, TouchpadCapture integration, checkpoint save on Ctrl+C. (scripts/collect_ppocr_data.py)
8. **Model confidence is low even when correct**: 7-25% with current MEAN pooling. Fixing to MAX raises to 68-98%. (src/ibus-engine-handwrite-chinese:405)

## Decisions (with rationale)
1. **Apply MAX pooling decode fix** (not full CTC greedy): Simpler change, directly addresses the confidence issue for single-character recognition. Full CTC greedy (argmax→collapse blanks→collapse repeats) is needed for multi-character support, but we're only doing single-char now.
2. **Bump line width 6→8px**: 8px on 200px canvas → ~1.9px at 48px output, closer to training data typical stroke width. If accuracy drops, roll back to 7px.
3. **Collect via --prompt mode (HSK1 list)**: Uses existing collect_ppocr_data.py with zero additional code. The HSK1 list (~150 chars) covers common radicals and stroke counts.
4. **Re-run analysis on dataset_fixed.jsonl as-is first**: Before collecting new data, run the existing fixed dataset through the analysis script to get a formal accuracy report baseline.

## Scope IN
- Fix `_decode()`: change `np.mean` to `np.max` (or implement proper CTC pooling)
- Fix `_preprocess()`: change line width 6→8px
- Re-run analysis on existing dataset_fixed.jsonl
- Collect 20-50 additional handwriting samples with fixed pipeline
- Run analysis on the expanded dataset
- Investigate similar-pair edge cases if 100% accuracy holds

## Scope OUT (Must NOT have)
- No full CTC greedy decode implementation (that's a multi-character future concern)
- No new scripts or infrastructure — both collection and analysis scripts already exist
- No model retraining or fine-tuning
- No Zinnia recognition changes
- No GTK/UI changes
- No changes to `_USE_ONNX` flag (stays False for engine, but OnnxHandle works standalone)
- No changes to the analysis script format or output

## Open questions
None — all forks were resolved by exploration. User confirmed 5/5 real chars correct post-dict-fix.

## Approval gate
status: approved
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->
