# Plan: PP-OCRv6 Character-by-Character Data Collection & Analysis

## Goal

Build a data collection loop that lets you write characters one at a time on the touchpad, captures PP-OCRv6's full recognition pipeline internals (stroke data, rendered image, model predictions with scores), and saves everything with your ground-truth label. Then analyze the logs to identify concrete patterns causing low accuracy.

## Why This Matters

Earlier benchmarks with **synthetic strokes** showed PP-OCRv6 achieves only 10% top-1 with uniformly near-zero confidence scores. But synthetic straight-line strokes are worst-case — real handwriting has curves, jitter, and pressure variation. We need **real handwriting data** with ground truth to answer:

1. Does PP-OCRv6 perform any better on real handwriting vs synthetic strokes?
2. What kinds of characters does it consistently get right vs wrong?
3. Are confidence scores meaningful (high when right, low when wrong)?
4. Are there identifiable failure patterns (stroke count, radical complexity, character frequency)?
5. Does the dict loading bug (`strip()` stripping U+3000) measurably affect predictions?

## What Already Exists

| Asset | Location | Notes |
|-------|----------|-------|
| Touchpad capture class | `tests/capture_handwriting_for_test.py:123` | `TouchpadCapture` — evdev reader, calibration, `read_and_clear()` |
| OnnxHandle pipeline | `src/ibus-engine-handwrite-chinese:275-421` | Cairo render → ONNX → `np.mean` decode |
| `_USE_ONNX` flag | line 34, 1358 | True for Simplified Chinese — PP-OCRv6 is the active recognizer |
| Engine import pattern | `tests/test_ppocr_recognition.py:25-34` | `SourceFileLoader` pattern for importing engine module |
| Benchmark script | `scripts/benchmark_ppocr.py` (deleted) | Was created earlier, can reference for synthetic strokes |

## Deliverables

### 1. `scripts/collect_ppocr_data.py` — Data Collection Tool (PP-OCRv6 Only)

A standalone **terminal-based** script (no GTK, no IBus) that:

**Flow per character:**
```
1. Print: "Write character X on touchpad → press ENTER"
2. Capture strokes via TouchpadCapture (reuse from tests/)
3. Create OnnxHandle instance → add strokes → run _preprocess()
4. Record preprocessed image stats (canvas size, grayscale min/max/mean, width after resize)
5. Run OnnxHandle.classify() → get top-24 candidates with scores
6. Record inference latency
7. Print: "PP-OCRv6: top-1='三' (0.0421)  top-5: '三','二','一','工','上'"
8. Ask: "Correct character? [press ENTER if correct, type if wrong, 's' to skip]"
9. Save to JSON dataset: {
     ground_truth: str,
     timestamp: ISO8601,
     strokes: [[(x,y),...], ...],  # fractional coords
     ppocr_v6: {
       top5: [(char, score), ...],
       top24: [(char, score), ...],   # full candidate list
       correct_top1: bool,
       correct_top5: bool,
       confidence_top1: float,
       inference_latency_ms: float,
     },
     pipeline_stats: {
       canvas_size: [width, height],
       total_points: int,
       num_strokes: int,
       bbox: [xmin, ymin, xmax, ymax],
       resized_width: int,          # after bilinear resize to 48px
       image_min: float,
       image_max: float,
       image_mean: float,
     }
   }
```

**Two modes:**
- `--prompt` (default): Script prompts you to write specific characters from a configurable list. Start with HSK level 1 (~150 most common chars). You write the prompted character.
- `--free`: You write anything on the touchpad, then type what it was. For exploratory collection.

**Design decisions:**
- **No GTK** — pure terminal, no X11/Wayland dependency issues
- **Reuses** `TouchpadCapture` from tests/ (extract to shared module if needed)
- **Single recognizer focus** — only PP-OCRv6. No Zinnia calls.
- **Captures full top-24** (not just top-5) to see where the correct character falls
- **Saves stroke data** for potential future replay or preprocessing experiments

### 2. JSON Lines Logging in OnnxHandle

Add lightweight structured logging directly into the engine's OnnxHandle methods so every recognition event in normal use gets logged:

**In `OnnxHandle._preprocess()` (currently line 325):**
```python
# Log after rendering and resize:
log = {
    "event": "preprocess",
    "t": time.time(),
    "num_strokes": len(self.all_points),
    "num_points": sum(len(s) for s in self.all_points),
    "canvas_size": [width, height],
    "resized_width": resized.shape[1],
    "img_min": float(normalized.min()),
    "img_max": float(normalized.max()),
}
```

**In `OnnxHandle._decode()` (currently line 377):**
```python
# Log after computing candidates:
log = {
    "event": "decode",
    "t": time.time(),
    "top5": [(char, score) for char, score in candidates[:5]],
    "num_classes": self.num_classes,
    "time_steps": probs.shape[0],
}
```

**In `OnnxHandle.classify()` (currently line 388):**
```python
# Log after inference:
log = {
    "event": "classify",
    "t": time.time(),
    "latency_ms": (t1 - t0) * 1000,
    "input_shape": list(input_tensor.shape),
}
```

**Log output**: Append JSON Lines to `/tmp/ppocr-recognition.log` — each line a complete log event. New file each session. Includes a session UUID generated at engine init.

### 3. `scripts/analyze_ppocr_data.py` — Analysis Script

Process the collected JSON dataset to generate:

**Overall accuracy:**
```
PP-OCRv6 top-1:  42/150 (28.0%)
PP-OCRv6 top-5:  78/150 (52.0%)
PP-OCRv6 top-10: 95/150 (63.3%)
```

**Confidence distribution histogram** (to check if scores are meaningful):
```
Confidence range  |  Count
0.0  - 0.1        |  85  (56.7%)  ← near-zero = guessing
0.1  - 0.2        |  22  (14.7%)
0.2  - 0.3        |  15  (10.0%)
0.3  - 0.4        |  10  (6.7%)
0.4  - 0.5        |   7  (4.7%)
0.5  - 0.6        |   5  (3.3%)
0.6  - 0.7        |   3  (2.0%)
0.7  - 0.8        |   2  (1.3%)
0.8  - 0.9        |   1  (0.7%)
0.9  - 1.0        |   0  (0.0%)
```

**Confidence calibration** (avg confidence when right vs wrong):
```
When correct: avg confidence = 0.27
When wrong:   avg confidence = 0.08
Ratio: 3.4×
← If ratio > 2, scores have predictive power despite being low
```

**Per-character confusion matrix:**
```
'我' (ground truth, 5 samples):
  → '找' (2×), '成' (1×), '战' (1×), '我' (1×)  ← correct only 20%
  Shared pattern: all contain 戈 radical

'你' (ground truth, 5 samples):
  → '他' (3×), '们' (1×), '你' (1×)  ← correct only 20%
  Shared pattern: all contain 亻 radical
```

**Stroke complexity vs accuracy:**
```
1-3 strokes:   35/50 (70.0%) correct
4-6 strokes:   28/55 (50.9%) correct
7-9 strokes:   12/35 (34.3%) correct
10+ strokes:    3/20 (15.0%) correct
```

**Character frequency vs accuracy** (does the model favor common chars?):
```
HSK-1 (most common):  30/60 (50.0%) correct
HSK-2:                28/55 (50.9%) correct
HSK-3:                15/35 (42.9%) correct
← If no correlation → model isn't just guessing common chars
```

**Dict index analysis** (does accuracy correlate with dict position?):
```
Dict index 0-1000:     25/50 (50.0%) correct
Dict index 1000-5000:  30/75 (40.0%) correct
Dict index 5000+:      10/25 (40.0%) correct
← If dip near index 1748-1800 → confirms U+3000 dict bug impact
```

### 4. `.omo/evidence/ppocr-handwriting-dataset/` — Evidence Directory

- `dataset-v{N}.json` — All collected samples with ground truth (versioned)
- `analysis-report-v{N}.json` — Machine-readable analysis
- `analysis-summary-v{N}.txt` — Human-readable summary

## Implementation Steps

### Step 1: Extract TouchpadCapture to Shared Module

Move `TouchpadCapture` class from `tests/capture_handwriting_for_test.py` into `src/handwrite_evdev.py` (where `TrackpadReader` already lives). This avoids circular import issues when the collection tool imports it.

- **`src/handwrite_evdev.py`**: Add `TouchpadCapture` class
- **`tests/capture_handwriting_for_test.py`**: Change import to `from handwrite_evdev import TouchpadCapture`
- Verify: `python3 -c "from handwrite_evdev import TouchpadCapture; print('OK')"` — runs without errors

### Step 2: Add Logging Instrumentation to OnnxHandle

3 small changes in `src/ibus-engine-handwrite-chinese`:

1. **Near top** (after imports): Add `import json, os, uuid` and a log file path helper
2. **In `_preprocess()`** (after line 374): Insert logging of image stats before return
3. **In `_decode()`** (after line 386): Insert logging of top-5 candidates before return
4. **In `classify()`** (after line 395): Insert logging of latency and input shape

All logs go to `/tmp/ppocr-recognition.log` as JSON Lines.

### Step 3: Create `scripts/collect_ppocr_data.py`

Standalone terminal script (~200 lines):
- Import `TouchpadCapture` from `handwrite_evdev`
- Import engine module via `SourceFileLoader` (same pattern as test files)
- Create `OnnxHandle` instance
- Loop through character list
- For each: prompt → capture → preprocess → classify → collect ground truth → save
- Save to `.omo/evidence/ppocr-handwriting-dataset/dataset-v1.json`

### Step 4: Create `scripts/analyze_ppocr_data.py`

Analysis script (~150 lines):
- Load JSON dataset
- Compute all analyses listed in Deliverable #3
- Print human-readable summary
- Save JSON report to `.omo/evidence/ppocr-handwriting-dataset/`

### Step 5: Collect Data

Run the collection tool for ~30 minutes:
```
python3 scripts/collect_ppocr_data.py
```
Target: 100-150 labeled samples covering a range of stroke counts and character types.

### Step 6: Run Analysis

```
python3 scripts/analyze_ppocr_data.py
```

Review output. The analysis will reveal exactly which accuracy bottlenecks affect real handwriting (not just synthetic strokes), guiding the next fix.

## What We're Building Toward

The analysis answers are meant to feed directly into a follow-up fix plan:

| If analysis shows... | Then next step... |
|---------------------|-------------------|
| Confidence uniformly near-zero (all ~0.0001) | PP-OCRv6 is fundamentally unsuited; drop ONNX path |
| Confidence meaningful but low accuracy on specific radicals | Add radical-aware LM ranking |
| Dict position dip near 1748 | Fix `strip()` → `rstrip("\n")` (apply Strategy 5) |
| Strong stroke-count correlation | Tune canvas padding / stroke width per complexity |
| No clear pattern at all | Model issue; try v4 model or alternative architecture |

## Files to Change

| File | Change | Lines |
|------|--------|-------|
| **MODIFY** `src/handwrite_evdev.py` | Add `TouchpadCapture` class | +~80 |
| **MODIFY** `tests/capture_handwriting_for_test.py` | Import from `handwrite_evdev` instead | ~5 |
| **MODIFY** `src/ibus-engine-handwrite-chinese` | Add JSON Lines logging in OnnxHandle | +~25 |
| **CREATE** `scripts/collect_ppocr_data.py` | Data collection tool | ~200 |
| **CREATE** `scripts/analyze_ppocr_data.py` | Analysis script | ~150 |

## Anti-Strategies

- **No GTK** — terminal-based only (simpler, no X11/Wayland dep)
- **No Zinnia** — collection and analysis focus exclusively on PP-OCRv6
- **No accuracy fixes** in this plan — data gathering only; fixes come after evidence
- **No new Python deps** — all needed libraries (evdev, numpy, json) already in project
- **100-150 samples is enough** — not trying for statistical significance, just signal

## Verification

1. `python3 scripts/collect_ppocr_data.py --dry-run` → prints "Ready" + touchpad detected
2. Write 3 characters → dataset file has 3 valid entries
3. `python3 scripts/analyze_ppocr_data.py` → prints accuracy + confusion + calibration
4. `git status` shows only the 5 planned files changed
