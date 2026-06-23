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
- [ ] `ZinniaHandle` class (lines ~175-263) — needs recognition-backend abstraction layer.
- [ ] `HandwriteEngine.update_candidates()` (line ~934) — where `zinnia.classify()` is called. Primary integration point.
- [ ] `HandwriteEngine.__init__()` (line ~782) — model loading and initialization.
- [ ] `TestCommitEngine` (line ~971) — test-mode equivalent must also be updated.
- [ ] Stroke input pipeline: evdev → `on_stroke_end` → `zinnia.add_stroke(pixel_pts)` — strokes are in pixel coords relative to drawing area.

### Step 2.3 Evaluate dependencies
- [ ] **onnxruntime** — new dependency, not currently in packaging. Check if available in Debian/Ubuntu/Fedora/Arch repos (`python3-onnxruntime` or pip-based).
- [ ] **numpy** — needed for tensor construction, likely already transitively available.
- [ ] **OpenCV (cv2)** — used in chinese-brush-ime for rendering. Evaluate alternatives:
  - Option A: Use Cairo (already a GTK dependency) to render strokes to a `GdkPixbuf` or Cairo image surface → numpy array. Eliminates OpenCV dependency.
  - Option B: Use pure Python PIL/Pillow (fewer deps than OpenCV).
  - Option C: Accept OpenCV (`python3-opencv` available in most distros but heavy).
- [ ] **opencc-python** — optional, for script conversion in ranking.

### Step 2.4 Performance & latency analysis
- [ ] Compare Zinnia inference time (~5ms) vs PP-OCRv4/v6 on CPU (~50-200ms).
- [ ] Impact on user experience: stroke-end → recognition → candidate display latency.
- [ ] Options to mitigate: run recognition in a background thread, pre-render during stroke drawing, use smaller model (v4 vs v6).
- [ ] Model loading time: ONNX models ~10-20 MB, load time ~200-500ms on first inference.

### Step 2.5 Traditional Chinese strategy
PP-OCR does NOT support Traditional Chinese. This is not a model-size question — the training data is exclusively simplified. Options:
- [ ] **Zinnia remains forever** for `handwrite-chinese-traditional`. No change to traditional engine.
- [ ] **Find a Traditional Chinese ONNX model** — trOCR (HuggingFace), or fine-tune a separate PP-OCR model on traditional data (requires PaddlePaddle training pipeline, large effort).
- [ ] **Use OpenCC for conversion** — recognize simplified, convert output to traditional via OpenCC (lossy, may miss region-specific characters).
- [ ] **Accept asymmetry**: simplified engine gets the new ONNX backend; traditional engine keeps Zinnia. Both engines coexist as separate IBus components (already the current architecture).

---

## Phase 3 — Design Options

### CRITICAL: These options apply ONLY to `handwrite-chinese-simplified`
The `handwrite-chinese-traditional` engine will continue using Zinnia (tegaki zh_TW) in all scenarios unless a Traditional Chinese ONNX model is separately sourced. See Step 2.5 for traditional options.

### Option A: Full Replacement (PP-OCR only, simplified only)
- Replace ZinniaHandle with OnnxHandle for simplified engine.
- Traditional engine stays on Zinnia (asymmetric architecture).
- Remove libzinnia dependency from packaging? NO — traditional still needs it.
- Pros: Cleaner simplified path.
- Cons: libzinnia still needed for traditional; no fallback if ONNX fails.

### Option B: Hybrid Primary (PP-OCR primary, Zinnia fallback)
- Keep ZinniaHandle. Add OnnxHandle as new class.
- Simplified: PP-OCR first → low confidence → Zinnia fallback.
- Traditional: Zinnia only (unchanged).
- Pros: Best simplified accuracy; instant fallback; traditional untouched.
- Cons: libzinnia remains a dependency; two code paths for simplified.

### Option C: Hybrid Parallel (both run on simplified, pick best)
- Run Zinnia and PP-OCR in parallel for simplified.
- Merge candidate lists with score weighting.
- Pros: Highest simplified accuracy.
- Cons: Double compute; complex merging; traditional still Zinnia-only.

### Option D: Dual-Mode Configurable (per engine)
- Add backend selection via env var or config.
- `IBUS_HANDWRITE_RECOGNIZER` = `zinnia` (default) or `ppocr`.
- If set to `ppocr` on traditional engine → fallback to Zinnia with warning.
- Implement abstract `RecognizerBackend` interface.
- Pros: Backward compatible; user choice; incremental migration path.
- Cons: Two code paths; asymmetric behavior between engines.

### Recommendation
**Start with Option D on simplified only, then migrate to Option B**:
1. Implement `RecognizerBackend` abstract interface + `OnnxHandle` class.
2. Add PP-OCR as opt-in for simplified engine (`IBUS_HANDWRITE_RECOGNIZER=ppocr`).
3. After validation, make PP-OCR the default primary for simplified, Zinnia fallback (Option B).
4. Traditional engine stays Zinnia-only throughout.

---

## Phase 4 — Implementation Research (Pre-coding)

### Step 4.1 ONNX model sourcing
- [ ] Check chinese-brush-ime's HuggingFace sources for pre-trained ONNX models.
- [ ] Evaluate PP-OCRv4_rec (6625 chars, 10 MB) vs v6_rec (18708 chars, 21 MB).
- [ ] Determine if fine-tuning on handwriting data is needed (PaddleOCR colab notebook exists).
- [ ] Plan model download/install path (similar to Gitee for 幽兰百合).

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

## Appendix — Key Questions to Resolve

1. **ONNX model source**: Use PP-OCRv4_rec (10 MB, 6625 chars) from HuggingFace? Or fine-tune on handwriting?
2. **Rendering dependency**: Cairo (already have GTK) vs OpenCV (heavy) vs Pillow (lightweight)?
3. **Latency acceptability**: What's the maximum acceptable latency between stroke end and candidate display? If >100ms, need background thread.
4. **Backward compatibility**: Should Zinnia remain the default until PP-OCR is validated, or switch immediately?
5. **Model fine-tuning**: Is the PP-OCR general OCR model good enough for handwriting, or does it need fine-tuning on handwriting data?
6. ~~Traditional Chinese: Does PP-OCR support traditional characters?~~ **CONFIRMED: PP-OCR does NOT support Traditional Chinese.** This is a hard constraint, not a question. See Step 2.5 for Traditional Chinese strategy options.
7. **Model version**: Which PP-OCR version to target? v4 (10 MB, 6625 chars) vs v5 vs v6 (21 MB, 18708 chars). Trade-off between coverage and size/latency.
8. **Engine separation**: Should the `RecognizerBackend` selection be per-engine (simplified vs traditional) or global? Simplified can default to PP-OCR; traditional must default to Zinnia.
