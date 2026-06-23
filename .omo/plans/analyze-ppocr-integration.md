# Analysis Plan: Integrating PP-OCR into ibus-handwrite-chinese

## Goal
Analyze the feasibility, architecture, and phased approach for replacing or supplementing the current Zinnia-based recognition in `handwrite-chinese-simplified` with a PP-OCR deep-learning model (via ONNX Runtime), informed by the implementation in `ai-space-lab/chinese-brush-ime`.

### CRITICAL CONSTRAINT — Simplified Chinese only
**PP-OCR models (v4/v5/v6) recognize Simplified Chinese characters only.** They do NOT support Traditional Chinese. This repo has two separate IBus engines:
- `handwrite-chinese-simplified` — currently uses 幽兰百合 (9374 chars, primarily simplified) with tegaki zh_CN fallback
- `handwrite-chinese-traditional` — currently uses tegaki zh_TW (11853 chars, traditional)

Any integration plan must account for this asymmetry. PP-OCR cannot replace the traditional engine's recognizer.

---

## Phase 1 — Information Gathering & Reference Study

### Step 1.1 Deep-dive the current engine's recognition path
- [ ] Map every Zinnia API call site in `src/ibus-engine-handwrite-chinese` (ctypes load, model open, character create, classify, result iteration, rerank).
- [ ] Document the `ZinniaHandle` interface contract: `__init__`, `clear`, `add_stroke`, `classify`, `destroy`.
- [ ] Identify all callers of `self.zinnia.*` (9+ sites: update_candidates, clear strokes, add_stroke from evdev/mouse, do_reset, backup fallback).
- [ ] Understand the backup/fallback pattern (`self.zinnia_backup`) — this is a template for hybrid recognition.

### Step 1.2 Study chinese-brush-ime's PP-OCR pipeline
- [ ] **Stroke → Image**: `preprocessing.py` — smoothing, bounding-box scaling, anti-aliased rendering to 128×96 PIL image via OpenCV polylines. Understand the gap-detection logic for disconnected strokes.
- [ ] **Model loading**: `ocr.py` — `ort.InferenceSession` with CPU provider, vocab loading from `dict.txt`, input/output tensor names.
- [ ] **Inference**: NCHW float32 tensor `[1, 3, 48, W]` → raw softmax `[1, T, num_classes]` → CTC decoding → top-K characters.
- [ ] **Ranking**: `ranking.py` — 3-component score (OCR confidence + language model + user frequency). Note the trigram/bigram/unigram fallback.
- [ ] **Script conversion**: OpenCC for simplified/traditional switching.
- [ ] **Model files**: `model.onnx` + `dict.txt`. 4 model variants (v4→v6), sizes 10–21 MB. v4 default (6625 chars), v6 (18708 chars).

---

## Phase 2 — Architecture Analysis

### Step 2.1 Compare Zinnia vs PP-OCR paradigms

| Aspect | Zinnia (current) | PP-OCR via ONNX (target) |
|--------|------------------|--------------------------|
| Input format | Stroke point sequences (1000×1000 virtual grid) | Rendered image (48×W grayscale → 3×48×W NCHW tensor) |
| Model type | SVM-like feature matching | CNN + CTC (deep learning) |
| Library | libzinnia.so via ctypes | onnxruntime Python package |
| Model file | `.model` file (proprietary Zinnia format) | `.onnx` file (standard format) |
| Vocabulary | Embedded in `.model` file | Separate `dict.txt` |
| Output | Raw scores per character | Softmax probabilities per time step (CTC decoding needed) |
| Candidate count | 24 final candidates (96 raw → dedup → rerank) | Top-K configurable (typically 10+ from model) |
| Speed | Very fast (~5-10ms per recognition) | Moderate (~50-200ms on CPU, depends on model size) |
| Accuracy on single chars | ~80% top-1 (幽兰百合) | Higher potential with fine-tuned CNN |

### Step 2.2 Identify integration points in the engine
- [ ] `ZinniaHandle` class (lines ~175-263) — replace entirely with `OnnxHandle` for simplified engine (no Zinnia fallback needed).
- [ ] `HandwriteEngine.update_candidates()` (line ~934) — where `zinnia.classify()` is called. Primary integration point.
- [ ] `HandwriteEngine.__init__()` (line ~782) — model loading and initialization.
- [ ] `TestCommitEngine` (line ~971) — test-mode equivalent must also be updated.
- [ ] Stroke input pipeline: evdev → `on_stroke_end` → `zinnia.add_stroke(pixel_pts)` — strokes are in pixel coords relative to drawing area.
- [ ] Stroke rendering: current `rebuild_pix()` (line ~638) already renders strokes via Cairo. This same Cairo pipeline can render to an offscreen surface → numpy array for ONNX inference.

### Step 2.3 Evaluate dependencies

| Dependency | Needed? | In current project | Notes |
|---|---|---|---|
| `onnxruntime` | **YES** | No | New dependency. Check distro packages: `python3-onnxruntime` (Debian/Ubuntu/Fedora/Arch?). If not available, fallback to `pip install onnxruntime`. CPU-only build (~5 MB). |
| `numpy` | **YES** | No direct dep, but may be transitive | Lightweight, needed for tensor construction. Standard distro package (`python3-numpy`). |
| Cairo (pycairo) | **YES** | **Already a GTK3 dep** ✓ | Comes with `python3-gi` (GTK3 GObject introspection). The engine already imports `cairo` at lines 639/708 and uses `cairo.ImageSurface` for rendering strokes. Can render to an offscreen surface → `get_data()` → numpy array. **No new dep needed for rendering.** |
| OpenCV (cv2) | **NO** | No | chinese-brush-ime uses it, but Cairo can do the same job. Avoid — adds ~200 MB to install. |
| PIL/Pillow | **NO** | No | Cairo+NumPy can handle everything. Avoid unnecessary dep. |
| `opencc-python` | Optional | No | For simplified→traditional conversion if needed. But PP-OCR is simplified-only, so this is only relevant if you want to serve traditional users via conversion. |

**Rendering approach (Cairo → numpy, no OpenCV needed):**
The current `rebuild_pix()` method (line 638-655) already demonstrates Cairo stroke rendering. For ONNX:
```python
import cairo
import numpy as np

# Render strokes to offscreen surface
surface = cairo.ImageSurface(cairo.FORMAT_A8, width, height)
cr = cairo.Context(surface)
# ... draw strokes same as rebuild_pix() ...
buf = surface.get_data()  # returns buffer/memoryview
img = np.frombuffer(buf, dtype=np.uint8).reshape(height, width)
# Now img is a grayscale numpy array → feed to _preprocess()
```
This reuses Cairo (already a dependency) and adds only `numpy`. Zero additional rendering packages.

### Step 2.4 Performance & latency analysis

**Current Zinnia latency:** ~5–10ms per recognition (synchronous, on GTK main thread).

**PP-OCRv6 expected latency:** ~50–200ms on CPU for a 21 MB CNN model. PP-OCRv4 (10 MB) is faster (~30–100ms) but user chose v6. The larger dict (18,708 chars vs 6,625) increases the classification head size, adding to inference time.

**Latency budget breakdown (estimated):**

| Stage | Time |
|---|---|
| Stroke → Cairo render → numpy array | ~1–5ms |
| ONNX inference (PP-OCRv6 on CPU) | ~80–200ms |
| CTC decode + candidate ranking | ~1–5ms |
| **Total synchronous** | **~80–210ms** |

**Impact analysis:**
- Current behavior: stroke end → `zinnia.classify()` (5ms) → GTK idle → redraw candidates. Feels instant.
- With synchronous ONNX: stroke end → UI freezes for 80–200ms → candidates appear. This is noticeable.
- Humans perceive delays >100ms as lag. At 200ms, it feels sluggish.

**Mitigation options:**

| Option | Approach | Trade-off |
|---|---|---|
| **A. Background thread** | Run ONNX inference in a `threading.Thread`, emit results via `GLib.idle_add` back to main thread | Adds thread safety complexity; Cairo render still on main thread (fast). Best UX. |
| **B. chinese-brush-ime style pause** | Wait ~50ms after last stroke before triggering recognition. Acts as debounce, gives user time to finish multi-stroke chars. | Total latency = 50ms pause + 80–200ms inference = ~130–250ms from last stroke. Some users may find the delay frustrating. |
| **C. Accept sync latency** | Run ONNX synchronously. 80–200ms might be tolerable for a handwriting input. | Perceptibly slower than Zinnia but might be acceptable for accuracy gains. |
| **D. Model distillation** | Use PP-OCRv4 (10 MB, ~30–100ms) as primary, v6 as fallback or optional upgrade. | User chose v6; this contradicts the requirement. |

**Recommended:** **Option A** — run ONNX inference in a background thread. The rendering (Cairo → numpy) stays on the main thread (~1–5ms). The result callback updates candidates via `GLib.idle_add`. This keeps the UI responsive.

**Model loading time:** ~200–500ms on first session load. Load during daemon/engine startup, not on first stroke.

### Step 2.5 Traditional Chinese strategy
PP-OCR does NOT support Traditional Chinese. This is not a model-size question — the training data is exclusively simplified. Options:
- [ ] **Zinnia remains forever** for `handwrite-chinese-traditional`. No change to traditional engine.
- [ ] **Find a Traditional Chinese ONNX model** — trOCR (HuggingFace), or fine-tune a separate PP-OCR model on traditional data (requires PaddlePaddle training pipeline, large effort).
- [ ] **Use OpenCC for conversion** — recognize simplified, convert output to traditional via OpenCC (lossy, may miss region-specific characters).
- [ ] **Accept asymmetry**: simplified engine gets the new ONNX backend; traditional engine keeps Zinnia. Both engines coexist as separate IBus components (already the current architecture).

---

## Phase 3 — Design Decision

### User decisions (confirmed)
- **Target model:** PP-OCRv6 (21 MB, 18,708 chars)
- **Backward compatibility:** NOT needed for simplified — PP-OCR fully replaces Zinnia
- **Handwriting accuracy:** PP-OCRv6 is good enough out of the box — no fine-tuning needed

### Chosen design: Full Replacement for simplified, Zinnia unchanged for traditional

```
┌──────────────────────────────────────────────────┐
│  ibus-handwrite-chinese                          │
│                                                  │
│  handwrite-chinese-simplified  ──►  OnnxHandle   │
│                                    (PP-OCRv6,    │
│                                     ONNX Runtime, │
│                                     Cairo→numpy,  │
│                                     background    │
│                                     thread)       │
│                                                  │
│  handwrite-chinese-traditional ──►  ZinniaHandle  │
│                                    (tegaki zh_TW, │
│                                     unchanged)    │
└──────────────────────────────────────────────────┘
```

### What this means:
- **Simplified engine:** Remove ZinniaHandle, replace with `OnnxHandle`. Cairo renders strokes → numpy → ONNX Runtime inference → CTC decode → candidates.
- **Traditional engine:** Completely untouched. Still uses Zinnia + tegaki zh_TW model.
- **libzinnia dependency:** Still required for traditional engine. Cannot remove from packaging.
- **`OnnxHandle` class:** No need for abstract interface if simplified engine is the sole adopter. But designing one makes future backends easier.
- **Background thread:** ONNX inference runs off the main thread to avoid UI freezing (~80–200ms inference).

### Execution plan:
1. Create `OnnxHandle` class with: Cairo → numpy rendering, ONNX session loading, `_preprocess()` tensor construction, inference, CTC decode (`_score_characters()`)
2. Wire into `HandwriteEngine.__init__()` — load ONNX model + dict on engine start
3. Replace `self.zinnia.add_stroke()` / `self.zinnia.classify()` calls with OnnxHandle equivalents
4. Offload classification to `threading.Thread` + `GLib.idle_add` for candidate update
5. Update `TestCommitEngine` with equivalent OnnxHandle path
6. Traditional engine: zero changes

---

## Phase 4 — Implementation Research (Pre-coding)

### Step 4.1 ONNX model sourcing
- [ ] Source PP-OCRv6 model from official `PaddlePaddle/PaddleOCR` GitHub releases: https://github.com/PaddlePaddle/PaddleOCR
- [ ] Export Paddle inference model → ONNX format via `paddle2onnx`, following chinese-brush-ime's colab notebook (`model/colab_training/finetune_ppocrv4_colab.ipynb`).
- [ ] Alternatively, use pre-exported ONNX model if available in chinese-brush-ime's model directory as reference.
- [ ] Determine minimum model files: `model.onnx` + `dict.txt` (18,708 characters for v6).
- [ ] Plan model download/install path (similar to Gitee for 幽兰百合; possible mirror or direct GitHub release asset).
- [ ] Note: `paddle2onnx` conversion is a one-time build step, not a runtime dependency.

### Step 4.2 Stroke → image conversion design
- [ ] Design the image rendering pipeline using **Cairo** (already a GTK dependency):
  ```python
  # Pseudocode for Cairo-based rendering
  surface = cairo.ImageSurface(cairo.FORMAT_A8, width, height)
  cr = cairo.Context(surface)
  for stroke in strokes:
      cr.move_to(stroke[0][0], stroke[0][1])
      for pt in stroke[1:]:
          cr.line_to(pt[0], pt[1])
      cr.stroke()
  buf = surface.get_data()  # returns bytes
  img = np.frombuffer(buf, dtype=np.uint8).reshape(height, width)
  ```
- [ ] Compare with chinese-brush-ime's OpenCV approach — Cairo gives free dependency reuse.
- [ ] Determine optimal rendering dimensions: 48×W (PP-OCR native) vs upscaled canvas.

### Step 4.3 Tensor construction & inference
- [ ] Input tensor: `[1, 3, 48, W]` float32, normalized to [-1, 1].
- [ ] Handle dynamic width W (PP-OCR supports variable-width input).
- [ ] CTC decoding: argmax per time step, collapse repeats, remove blanks.
- [ ] Map output indices to character via loaded `dict.txt`.

### Step 4.4 Candidate integration
- [ ] Map PP-OCR top-K confidence scores → Zinnia-style candidate list.
- [ ] Re-use existing frequency boost in `update_candidates()` or replace with chinese-brush-ime's LM scoring.
- [ ] Decide on number of candidates (v4 default max seq length = 25, adjust).

### Step 4.5 Test strategy
- [ ] Verify ONNX model loads and inference produces reasonable results on synthetic strokes.
- [ ] Test with real touchpad input (compare Zinnia vs PP-OCR top-1 and top-5 accuracy).
- [ ] Latency benchmarks (mean, p95, p99 of inference time).
- [ ] Ensure `TestCommitEngine` has equivalent PP-OCR path.

---

## Phase 5 — Integration Plan Outline

### P0: Foundation
- [ ] Add `onnxruntime`, `numpy` to packaging dependencies (`debian/control`, `.spec`, `PKGBUILD`).
- [ ] Create `RecognizerBackend` ABC/interface protocol in engine source.
- [ ] Extract `ZinniaHandle` into a `ZinniaBackend` class implementing the interface.

### P1: ONNX Backend
- [ ] Create `OnnxBackend` class implementing `RecognizerBackend`.
- [ ] Implement Cairo-based stroke-to-image rendering.
- [ ] Implement tensor construction + ONNX inference + CTC decoding.
- [ ] Wire into `HandwriteEngine` with `IBUS_HANDWRITE_RECOGNIZER` env-var toggle.

### P2: Model Distribution
- [ ] Add ONNX model download to `tools/install.sh` (HuggingFace or Gitee mirror).
- [ ] Support `dict.txt` alongside model.
- [ ] Add model download to `bootstrap.sh`.

### P3: Validation & Tuning
- [ ] Compare accuracy on real handwriting test set.
- [ ] Tune confidence threshold for hybrid mode.
- [ ] Benchmark latency; consider background thread inference if needed.
- [ ] Update `tests/test_recognition.py` with ONNX-based smoke test.

### P4: Polish
- [ ] Remove libzinnia dependency option (once ONNX is proven).
- [ ] Add user-frequency adaptation (from chinese-brush-ime's `Ranker.record_selection()`).
- [ ] Documentation updates.

---

## Appendix — Key Files Referenced

| File | Purpose |
|------|---------|
| `src/ibus-engine-handwrite-chinese` | Current engine — Zinnia ctypes + GTK popup (1158 lines) |
| `src/handwrite_evdev.py` | Evdev multitouch reader — stroke input pipeline |
| `tests/test_recognition.py` | Zinnia smoke test — template for ONNX testing |
| `packaging/debian/control` | Debian packaging deps |
| `packaging/ibus-handwrite-chinese.spec` | RPM packaging deps |
| `packaging/PKGBUILD` | Arch packaging deps |
| `tools/install.sh` | Dependency install + model download |
| `bootstrap.sh` | Cross-distro install entry point |
| `/tmp/chinese-brush-ime/daemon/chinese_brush_ime/ocr.py` | ONNX model loading + inference (reference) |
| `/tmp/chinese-brush-ime/daemon/chinese_brush_ime/preprocessing.py` | Stroke → image rendering (reference) |
| `/tmp/chinese-brush-ime/daemon/chinese_brush_ime/ranking.py` | Candidate ranking + LM + user freq (reference) |

## Appendix — Answered Questions (Decisions Recorded)

| # | Question | Decision |
|---|----------|----------|
| 1 | ONNX model source | **PP-OCRv6** from official `PaddlePaddle/PaddleOCR` GitHub releases (https://github.com/PaddlePaddle/PaddleOCR). Export from Paddle format to ONNX via `paddle2onnx` as shown in chinese-brush-ime's colab notebook. |
| 2 | Rendering dependency | **Cairo** (already a dep via GTK3) → numpy. No OpenCV, no Pillow. |
| 3 | Latency acceptability | **~80–200ms expected**. Must use **background thread** to avoid UI freeze. |
| 4 | Backward compatibility | **Not needed** for simplified. Zinnia fully replaced by PP-OCRv6. |
| 5 | Model fine-tuning | **Not needed** — PP-OCRv6 is good enough for handwriting out of the box. |
| 6 | Traditional Chinese support | **PP-OCR does NOT support Traditional Chinese** (hard constraint). Traditional engine stays on Zinnia. |
| 7 | Model version | **PP-OCRv6** (21 MB, 18,708 chars). |
| 8 | Engine separation | **Per-engine**: Simplified → PP-OCRv6. Traditional → Zinnia (unchanged). |
