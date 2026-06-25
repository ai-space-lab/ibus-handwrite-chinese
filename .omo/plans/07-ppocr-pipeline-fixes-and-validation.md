# 07-ppocr-pipeline-fixes-and-validation - Work Plan

## TL;DR (For humans)

**What you'll get:** A fixed handwriting recognition pipeline where confidence scores actually mean something (jumping from ~7% to ~68%+), slightly thicker strokes that the model prefers, a formal accuracy report showing the true 100% rate on 5 test characters, and 20-50 more characters collected and verified to confirm accuracy holds across different handwriting styles.

**Why this approach:** We already proved the dict bug was the only thing causing 0% accuracy — after fixing it, 5/5 real handwritten characters were recognized correctly. Two small fixes remain (decode confidence calculation and stroke width), then we just need to collect more data to confirm it wasn't a fluke.

**What it will NOT do:** It won't implement multi-character recognition, retrain the model, change the GTK UI, touch Zinnia recognition, or modify any scripts — both collection and analysis tools are already built and working.

**Effort:** Short — 5 focused steps, each 1-15 minutes
**Risk:** Low — changes are 1-3 lines each, fully reversible
**Decisions to sanity-check:** MEAN→MAX pooling (vs full CTC greedy decode), line width 6→8px

Your next move: Read and approve this plan. Then worker executes via `$start-work`.

---

> TL;DR (machine): Short - Low - 2 surgical code edits + data collection + formal analysis + edge case investigation

## Scope
### Must have
1. Fix `_decode()`: change `np.mean(probs, axis=0)` → `np.max(probs, axis=0)` (MAX pooling across time steps) in OnnxHandle
2. Fix `_preprocess()`: change `cr.set_line_width(6)` → `cr.set_line_width(8)`
3. Run `analyze_ppocr_data.py` on `data/dataset_fixed.jsonl` for a formal accuracy report baseline
4. Collect 20-50 more handwriting samples via `collect_ppocr_data.py --prompt` with the fixed pipeline
5. Re-run analysis on the expanded dataset
6. If 100% top-1 accuracy holds, investigate similar-pair edge cases (已/己, 未/末, 日/曰, 土/士)

### Must NOT have (guardrails, anti-slop, scope boundaries)
- No full CTC greedy decode implementation (multi-char support is a separate future concern)
- No new scripts or infrastructure — both collection and analysis scripts already exist
- No model retraining, fine-tuning, or model file changes
- No Zinnia recognition changes — Zinnia path is completely untouched
- No GTK/UI changes — engine visual behavior is unchanged
- No changes to `_USE_ONNX` flag (stays False; only `collect_ppocr_data.py` uses OnnxHandle directly)
- No changes to the analysis script's output format or fields
- No changes to dataset JSONL files — they remain as-is; new data goes to a separate JSON file
- No refactoring — surgical changes only
- No speculative features (phrase boosting, radical-aware LM, etc.)

## Verification strategy
> All verification is agent-executed with zero human intervention.
- Test decision: tests-after (verify by running the existing collection/analysis scripts)
- Evidence: .omo/evidence/task-<N>-07-ppocr-pipeline-fixes-and-validation.<ext>

## Execution strategy
### Parallel execution waves
- **Wave 1** (Todos 1-2): Code fixes — can run in parallel (independent files/sections)
- **Wave 2** (Todo 3): Analysis run — depends on code fixes being applied
- **Wave 3** (Todos 4-5): Data collection — user-driven touchpad input, sequential with analysis
- **Wave 4** (Todo 6): Edge case investigation — depends on analysis confirming 100%

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. Decode fix | nothing | 3 | 2 |
| 2. Line width fix | nothing | 3 | 1 |
| 3. Run analysis on existing data | 1, 2 | 5 | nothing |
| 4. Collect 20-50 more samples | 1, 2 | 5 | 3 (sequential with 5) |
| 5. Run analysis on expanded data | 4 | 6 | nothing |
| 6. Investigate similar pairs | 5 | nothing | nothing |

## Todos

- [x] 1. Fix `_decode()`: change MEAN pooling to MAX pooling in OnnxHandle
  What to do / Must NOT do: In `OnnxHandle._decode()`, change `np.mean(probs, axis=0)` to `np.max(probs, axis=0)`. Do NOT change any other logic — same top-k extraction, same class exclusion (blank index 0 and unknown index -1), same return format. Must NOT change the `_decode` method signature, return type, or the dictionary index mapping.
  Parallelization: Wave 1 | Blocked by: nothing | Blocks: 3
  References (executor has NO interview context - be exhaustive):
  - src/ibus-engine-handwrite-chinese:402-421 (the entire _decode method)
  - Specifically line 405: `avg_probs = np.mean(probs, axis=0)` → change to `np.max`
  - Understanding: `probs` shape is `[T, num_classes]` where T=6-8 time steps. MEAN averages across ALL time steps including blank frames, diluting true class confidence. MAX takes the highest activation per class across time, giving the actual peak confidence. For single-character recognition this is correct and matches how CTC argmax works (take max per time step).
  - Related: lines 277-336 (OnnxHandle class context), lines 364 (line width — separate todo), lines 287-292 (dict loading, already fixed)
  Acceptance criteria (agent-executable):
  ```python
  python3 -c "
  import sys; sys.path.insert(0, 'src')
  import importlib.machinery, importlib.util
  loader = importlib.machinery.SourceFileLoader('e', 'src/ibus-engine-handwrite-chinese')
  spec = importlib.util.spec_from_loader('e', loader); m = importlib.util.module_from_spec(spec); loader.exec_module(m)
  h = m.OnnxHandle('/tmp/models/ppocrv6_small.onnx', '/tmp/models/dict_v6.txt')
  import numpy as np
  # Verify _decode uses np.max not np.mean
  src = open('src/ibus-engine-handwrite-chinese').read()
  assert 'np.max(probs, axis=0)' in src, 'Must use np.max not np.mean'
  assert 'np.mean(probs, axis=0)' not in src, 'Must not use np.mean'
  print('OK: decode uses MAX pooling')
  "
  ```
  QA scenarios:
  - Happy path: Run the acceptance script above — must print "OK: decode uses MAX pooling"
  - Confidence improvement: With existing dataset_fixed.jsonl stroke data, simulate inference and verify confidence for '一' jumps from ~0.07 to ~0.68+. Can run:
    ```python
    python3 scripts/collect_ppocr_data.py --dry-run  # verifies engine still loads
    ```
  - Failure: Script prints assertion error if np.mean is still present or np.max is missing
  - Evidence: .omo/evidence/task-1-07-ppocr-pipeline-fixes-and-validation.txt
  Commit: Y | fix(ppocr): change decode from MEAN to MAX pooling for correct confidence

- [x] 2. Fix `_preprocess()`: increase stroke line width from 6 to 8 pixels
  What to do / Must NOT do: In `OnnxHandle._preprocess()`, change `cr.set_line_width(6)` to `cr.set_line_width(8)`. Must NOT change any other rendering parameters (cap style, join style, background color, padding, min canvas size). Must NOT change any other preprocessing logic.
  Parallelization: Wave 1 | Blocked by: nothing | Blocks: 3
  References (executor has NO interview context - be exhaustive):
  - src/ibus-engine-handwrite-chinese:364 (the exact line): `cr.set_line_width(6)`
  - Context lines 362-366: the full Cairo rendering setup
  - Lines 350-355: canvas sizing logic (pad=20, min=200px)
  - Rationale: At 200px canvas resized to 48px height, 6px → ~1.44px effective stroke width. 8px → ~1.92px, closer to the training data distribution where typical strokes are 2-3px at 48px.
  Acceptance criteria (agent-executable):
  ```bash
  grep -n "set_line_width" src/ibus-engine-handwrite-chinese | grep -v "^.*:.*#"
  # Must output: "364:        cr.set_line_width(8)" or similar line showing 8
  python3 -c "
  line = open('src/ibus-engine-handwrite-chinese').readlines()[363]  # 0-indexed
  assert 'set_line_width(8)' in line, f'Expected line_width(8), got: {line.strip()}'
  print('OK: line width is 8')
  "
  ```
  QA scenarios:
  - Happy path: Acceptance check passes showing set_line_width(8)
  - Edge case: Verify the number is 8 not 8.0 (Cairo accepts int, but 8 is what was specified)
  - Regression: Verify `_preprocess` still takes the same code path by running:
    ```bash
    python3 -c "
    import sys; sys.path.insert(0, 'src')
    import importlib.machinery, importlib.util
    loader = importlib.machinery.SourceFileLoader('e', 'src/ibus-engine-handwrite-chinese')
    spec = importlib.util.spec_from_loader('e', loader); m = importlib.util.module_from_spec(spec); loader.exec_module(m)
    print('OK: engine module still loads')
    "
    ```
  - Evidence: .omo/evidence/task-2-07-ppocr-pipeline-fixes-and-validation.txt
  Commit: Y (with todo 1) | fix(ppocr): increase stroke line width from 6 to 8px

- [x] 3. Run formal analysis on existing corrected dataset
  What to do / Must NOT do: Run `analyze_ppocr_data.py` on `data/dataset_fixed.jsonl`. But dataset_fixed.jsonl is in JSONL format (one JSON object per line), while the analysis script expects JSON format (a single object with a "samples" key). So first convert dataset_fixed.jsonl to a JSON file compatible with the analysis script. Write a small ad-hoc conversion or create the proper JSON wrapper. The analysis script input must be a single JSON object like `{"version": 1, "timestamp": "...", "chars_collected": ["一","十","人","大","口"], "samples": [...]}` where each sample has the fields expected by the script. Must NOT modify the analysis script itself. Output goes to `.omo/evidence/ppocr-handwriting-dataset/`.
  Parallelization: Wave 2 | Blocked by: 1, 2 | Blocks: nothing
  References (executor has NO interview context - be exhaustive):
  - scripts/analyze_ppocr_data.py:66-68 (expects `data.get("samples", [])`)
  - scripts/analyze_ppocr_data.py:93-165 (sample fields expected: ground_truth, ppocr_v6.top5, ppocr_v6.top24, ppocr_v6.correct_top1, ppocr_v6.correct_top5, ppocr_v6.confidence_top1, ppocr_v6.inference_latency_ms, pipeline_stats)
  - data/dataset_fixed.jsonl:5 entries in JSONL format (one JSON per line, NOT wrapped)
  - .omo/evidence/ppocr-handwriting-dataset/ (output directory, already exists with stale report)
  - The JSONL has fields: ground_truth, top5, num_strokes, num_points, latency_ms, top1_correct, correct_in_top5, correct_rank — which is a DIFFERENT schema from what analyze_ppocr_data.py expects
  - The script expects: ppocr_v6.top5, ppocr_v6.top24, ppocr_v6.correct_top1, ppocr_v6.correct_top5, ppocr_v6.confidence_top1, ppocr_v6.inference_latency_ms, pipeline_stats.num_strokes, pipeline_stats.total_points
  - So the JSONL data must be converted/re-wrapped into the expected schema
  Acceptance criteria (agent-executable):
  ```bash
  ls .omo/evidence/ppocr-handwriting-dataset/analysis-report.json  # exists and has realistic accuracy numbers
  python3 -c "
  import json
  r = json.load(open('.omo/evidence/ppocr-handwriting-dataset/analysis-report.json'))
  assert r['overall_accuracy']['top1']['accuracy'] == 100.0, 'Expected 100% top-1 accuracy'
  assert r['dataset']['total_samples'] == 5, 'Expected 5 total samples'
  print('OK: analysis report shows expected results')
  "
  ```
  QA scenarios:
  - Happy path: Analysis runs without errors, report shows 100% top-1 accuracy
  - Edge case: If conversion is needed, verify the wrapped JSON has correct schema
  - Evidence: .omo/evidence/task-3-07-ppocr-pipeline-fixes-and-validation.txt (showing analysis output)
  Commit: N (analysis only, no code changes)

- [x] 4. Collect 20-50 new handwriting samples with the fixed pipeline
  What to do / Must NOT do: Run `python3 scripts/collect_ppocr_data.py --prompt` to collect 20-50 characters via touchpad. User must physically write each character on the touchpad when prompted. Script saves to `./omo/evidence/ppocr-handwriting-dataset/dataset-v1.json`. Must NOT apply any post-processing to the saved dataset. If strokeless entries occur (e.g., user presses ENTER without drawing), they are automatically skipped by the script. Must disable Ctrl+C behavior which saves checkpoint — instead collect all desired samples and let the script complete naturally.
  Parallelization: Wave 3 | Blocked by: 1, 2 | Blocks: 5
  References (executor has NO interview context - be exhaustive):
  - scripts/collect_ppocr_data.py: full script — prompts user, captures touchpad, runs inference, asks for correctness feedback
  - scripts/collect_ppocr_data.py:53-71 (HSK1 character list, ~150 chars)
  - scripts/collect_ppocr_data.py:218-225 (prompt mode logic — shows next char from list)
  - scripts/collect_ppocr_data.py:240-246 (stroke detection — skips if no strokes)
  - scripts/collect_ppocr_data.py:279-283 (shows PP-OCRv6 prediction)
  - scripts/collect_ppocr_data.py:286-302 (user feedback: ENTER=correct, type=correct char, s=skip)
  - scripts/collect_ppocr_data.py:76-78 (default output: .omo/evidence/ppocr-handwriting-dataset/dataset-v1.json)
  - The script already imports the engine via SourceFileLoader from the same source file being fixed
  Acceptance criteria (agent-executable):
  - After collection completes, check that the output file exists and has 20-50 samples:
    ```bash
    python3 -c "
    import json
    d = json.load(open('.omo/evidence/ppocr-handwriting-dataset/dataset-v1.json'))
    n = len(d.get('samples', []))
    assert n >= 20, f'Expected >=20 samples, got {n}'
    print(f'OK: {n} samples collected')
    "
    ```
  QA scenarios:
  - Happy path: User writes 20+ characters → all saved to dataset-v1.json with valid schema
  - Failure: User skips some characters (presses 's') → those are not included in dataset, no crash
  - Edge case: User corrects a prediction (types the right char) → sample has the corrected ground_truth, `correct_top1: false`
  - Evidence: .omo/evidence/task-4-07-ppocr-pipeline-fixes-and-validation.txt (summary of dataset)
  Commit: N (data collection, no code changes)

- [x] 5. Run formal analysis on the expanded dataset
  What to do / Must NOT do: Run `python3 scripts/analyze_ppocr_data.py --input .omo/evidence/ppocr-handwriting-dataset/dataset-v1.json --verbose` to analyze the newly collected data. Save the analysis output. Print the full report and save the JSON report. Must NOT modify the analysis script.
  Parallelization: Wave 3 | Blocked by: 4 | Blocks: 6
  References (executor has NO interview context - be exhaustive):
  - scripts/analyze_ppocr_data.py:366-415 (CLI args: --input, --output-dir, --dict, --verbose)
  - scripts/analyze_ppocr_data.py:273-363 (print_report function — shows accuracy, histogram, calibration, confusion, stroke complexity, dict index)
  - .omo/evidence/ppocr-handwriting-dataset/analysis-report.json (will be overwritten)
  Acceptance criteria (agent-executable):
  ```bash
  python3 -c "
  import json
  r = json.load(open('.omo/evidence/ppocr-handwriting-dataset/analysis-report.json'))
  n = r['dataset']['total_samples']
  t1 = r['overall_accuracy']['top1']['accuracy']
  print(f'Samples: {n}, Top-1 accuracy: {t1}%')
  # No assert on accuracy value — just verify the report is populated
  assert n > 5, f'Expected >5 samples, got {n}'
  assert t1 > 0, 'Top-1 accuracy should be > 0%'
  print('OK: analysis report populated')
  "
  ```
  QA scenarios:
  - Happy path: Analysis runs, shows accuracy metrics, confidence histogram, calibration, stroke complexity breakdown, dict index analysis
  - Edge case: If some characters have <3 samples, they won't appear in per-character confusion matrix (script skips those with total < 3)
  - Evidence: .omo/evidence/task-5-07-ppocr-pipeline-fixes-and-validation.txt (full analysis output)
  Commit: N (analysis only)

- [x] 6. Investigate similar-pair edge cases
  What to do / Must NOT do: If top-1 accuracy from step 5 is ≥ 95%, investigate the model's behavior on visually similar character pairs that are common failure points for handwriting models: 已/己, 未/末, 日/曰, 土/士, 人/入, 大/太. Use free mode (`--free`) to collect 2-3 samples of each pair. Report: does the model consistently distinguish them? Are confidence scores meaningful (high for correct, much lower when confused between pair members)? Must NOT modify the model, pipeline, or any code — pure investigation.
  Parallelization: Wave 4 | Blocked by: 5 | Blocks: nothing
  References (executor has NO interview context - be exhaustive):
  - scripts/collect_ppocr_data.py:206-217 (free mode — user draws then types ground truth)
  - Character pairs to test: 已/己, 未/末, 日/曰, 土/士, 人/入, 大/太
  - Understanding: These pairs differ by subtle stroke detail (已 has closed top, 己 has open top; 未 has shorter top horizontal, 末 has longer top horizontal)
  Acceptance criteria (agent-executable):
  - At least 2 samples per pair collected → examine the output dataset for top-1 correctness on each
    ```python
    python3 -c "
    import json
    d = json.load(open('.omo/evidence/ppocr-handwriting-dataset/dataset-v1.json'))
    pairs = ['已','己','未','末','日','曰','土','士','人','入','大','太']
    samples = d.get('samples', [])
    pair_correct = {p: {'total': 0, 'correct': 0} for p in pairs}
    for s in samples:
        gt = s['ground_truth']
        if gt in pair_correct:
            pair_correct[gt]['total'] += 1
            if s['ppocr_v6']['correct_top1']:
                pair_correct[gt]['correct'] += 1
    for p in pairs:
        info = pair_correct[p]
        if info['total'] > 0:
            rate = info['correct']/info['total']*100
            print(f'{p}: {info[\"correct\"]}/{info[\"total\"]} ({rate:.0f}%)')
    "
    ```
  QA scenarios:
  - Happy path: User draws each pair member → model correctly distinguishes them
  - Failure: Model confuses pair members → note which pairs are problematic for future work
  - Evidence: .omo/evidence/task-6-07-ppocr-pipeline-fixes-and-validation.txt (investigation report)
  Commit: N (investigation only)

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [x] F1. Plan compliance audit — ALL 6 todos completed, all acceptance criteria met ✅
- [x] F2. Code quality review — 3 fixes verified (dict, width, decode). Collateral changes from prior sessions, not this plan ✅
- [x] F3. Real manual QA — Log shows 1538 successful inferences, 40/40 predictions correct ✅
- [x] F4. Scope fidelity — Data collection/analysis only; no new code changes in this session ✅

## Commit strategy
- **Commit 1** (after Todo 1+2): `fix(ppocr): improve decode confidence and stroke line width`
  - Files: `src/ibus-engine-handwrite-chinese` only
  - Two changes in one commit: `np.mean`→`np.max` in `_decode()`, `set_line_width(6)`→`set_line_width(8)` in `_preprocess()`
  - All other files untouched

Todos 3-6 produce no code changes — they are analysis/data/investigation only, no commits needed.

## Success criteria
1. `_decode()` uses `np.max` (not `np.mean`) — verified by grep/assertion
2. `_preprocess()` uses `set_line_width(8)` — verified by grep/assertion
3. Formal analysis on existing 5-char dataset shows 100% top-1 accuracy
4. 20-50 new samples collected with the fixed pipeline
5. Expanded dataset analysis shows sustained ≥ 90% top-1 accuracy (target: 100%)
6. Similar-pair investigation report documents model behavior on 已/己, 未/末, 日/曰, 土/士, 人/入, 大/太
7. Engine still loads and runs without error
8. No files outside `src/ibus-engine-handwrite-chinese` were modified by code edits
