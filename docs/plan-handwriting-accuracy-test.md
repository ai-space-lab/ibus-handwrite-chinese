# Plan: Real Handwriting Accuracy Test — Tegaki vs 幽兰百合

> ⚠️ **Superseded** — both engines compared (Tegaki, 幽兰百合) were removed in v0.2.0.
> The project now uses PP-OCRv6 ONNX only. See [README.md PP-OCRv6 Integration section](../README.md#pp-ocrv6-integration) for current validation results.

## Objective

Compare recognition accuracy of **Tegaki zh_CN** (6,763 chars) vs **幽兰百合 Community v1.1.0** (9,374 chars) using actual handwriting strokes captured from the MacBook Pro touchpad (bcm5974), rather than synthetic strokes.

## Test Characters (30 total)

Three categories to test different aspects of accuracy:

### A. Common characters (10) — both models should handle these
`一 十 人 大 中 国 我 的 是 不`

Test: which model produces the correct character as top-1/top-5 more often.

### B. Medium-complexity characters (10) — tests nuanced recognition
`家 爱 学 书 长 用 为 会 没 进`

Test: stroke order variations + moderate stroke count (6-10 strokes).

### C. 幽兰百合-only characters (10) — tests extended coverage

Selected from the 1,485 chars in 幽兰百合 but not in Tegaki CN+TW:
`犇 猋 灥 晿 珎 勓 婯 媠 濷 覎`

Test: can 幽兰百合 recognize them (any non-zero score), and does Tegaki return gibberish.

## Capture Tool Design

A new script `capture_handwriting_for_test.py` (standalone, no GTK/IBus dependency):

### How it works

```
for each test_char in test_set:
    print(f"Write '{test_char}' on touchpad, then press ENTER")
    
    # Background thread: evdev reader captures strokes
    # Main thread: wait for keyboard ENTER
    
    on ENTER:
        save current strokes as fractional coords (0.0-1.0)
        classify with both models
        print comparison
        advance to next char
    
at end:
    print summary table
```

### Implementation details

**Coord pipeline** (matches engine's normalization):

```
evdev raw (0..x_max)  →  fractional (0.0-1.0)  →  pixel (0-1000)
                                                        ↓
                                               bounding-box center + scale
                                                        ↓
                                               zinnia classify (0-1000)
```

**Threading**:
- Main thread: stdin reading (ENTER key), terminal prompts
- Background thread: evdev read_loop(), appends strokes to a shared buffer
- Thread-safe buffer: list of `[(stroke_id, [(x_frac, y_frac), ...]), ...]`

**Device access**: uses the same udev `uaccess` grant the engine already relies on. The user is in the `input` group and the device is accessible.

### What gets saved

A single JSON file `captured_strokes.json`:

```json
{
  "metadata": {"device": "bcm5974", "date": "..."},
  "samples": [
    {
      "char": "中",
      "strokes": [
        [[0.12, 0.34], [0.13, 0.36], ...],
        [[0.45, 0.12], ...]
      ]
    },
    ...
  ]
}
```

## Classification & Comparison

After each character is written, the script immediately:

1. Loads both models (Tegaki zh_CN + 幽兰百合)
2. Feeds the stroke data through each model's `classify()`
3. Records:
   - Top-1 character and score
   - Top-5 characters
   - Whether `expected` character is in top-1/top-5

At session end, prints:

```
========================================
ACCURACY RESULTS
========================================
                 | Tegaki zh_CN | 幽兰百合
-----------------+--------------+----------
Top-1 hits       |  7/30 (23%)  | 12/30 (40%)
Top-5 hits       | 15/30 (50%)  | 18/30 (60%)

Char  Expected  | Tegaki top-1 (score) | 幽兰百合 top-1 (score)
------+---------+----------------------+------------------------
 一   | 一      | 一 (0.92) ✓         | 一 (3.90) ✓
 十   | 十      | 十 (0.88) ✓         | 十 (1.26) ✓
 人   | 人      | 卜 (0.42) ✗         | 人 (0.58) ✓
 ...
```

## Execution

### Prerequisites
1. This laptop (MacBook Pro, bcm5974 touchpad, Mint 22.3 Xfce) — already working
2. User `chloeng` with touchpad access — already configured
3. Both models downloaded — already done
4. `python3-evdev` — already installed

### Running the test
```bash
cd /tmp/ibus-handwrite-chinese
python3 capture_handwriting_for_test.py
# Follow prompts: write each char on touchpad, press ENTER to confirm
```

### Time estimate
- ~30 chars × 10 seconds each (write + press ENTER) = ~5 minutes

## Metrics

| Metric | Description |
|--------|-------------|
| Top-1 accuracy | % of chars where correct char is top candidate |
| Top-5 accuracy | % where correct char is in top 5 |
| Average score | Mean confidence score for correct predictions |
| Score distribution | For top-1 results, spread of confidence scores |
| OOV detection rate | For chars not in Tegaki, does 幽兰百合 find them? |

## Files to Create

1. `capture_handwriting_for_test.py` — interactive capture + comparison script (~250 lines)
2. `plan-handwriting-accuracy-test.md` — this plan
