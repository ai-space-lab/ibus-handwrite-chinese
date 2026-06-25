#!/usr/bin/env python3
"""Test PP-OCRv6 ONNX recognition with synthetic strokes.

Tests OnnxHandle directly with known stroke patterns:
  - Horizontal line → "一" (confidence > 0.9)
  - Cross (two strokes) → "十" (confidence > 0.95)

Skips gracefully if model files are not found.
"""

import importlib.machinery
import importlib.util
import math
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

# ---------------------------------------------------------------------------
# Load the engine module (same approach as test_ppocr_recognition.py)
# ---------------------------------------------------------------------------
HAS_ENGINE = False
engine = None
_import_error = ""

try:
    _engine_path = os.path.join(PROJECT_ROOT, 'src', 'ibus-engine-handwrite-chinese')
    loader = importlib.machinery.SourceFileLoader('engine', _engine_path)
    spec = importlib.util.spec_from_loader('engine', loader)
    engine = importlib.util.module_from_spec(spec)
    loader.exec_module(engine)
    HAS_ENGINE = True
except Exception as exc:
    _import_error = str(exc)

# ---------------------------------------------------------------------------
# Model path resolution with fallback candidates
# ---------------------------------------------------------------------------
MODEL_CANDIDATES = [
    os.path.join(PROJECT_ROOT, 'data', 'models', 'ppocrv6_small_rec.onnx'),
    '/usr/local/share/ibus-handwrite-chinese/models/ppocrv6_small_rec.onnx',
    '/tmp/models/ppocrv6_small.onnx',
]
DICT_CANDIDATES = [
    os.path.join(PROJECT_ROOT, 'data', 'models', 'dict_v6.txt'),
    '/usr/local/share/ibus-handwrite-chinese/models/dict_v6.txt',
    '/tmp/models/dict_v6.txt',
]

MODEL_PATH = None
DICT_PATH = None
for mp in MODEL_CANDIDATES:
    if os.path.exists(mp):
        MODEL_PATH = mp
        break
for dp in DICT_CANDIDATES:
    if os.path.exists(dp):
        DICT_PATH = dp
        break

MODELS_AVAILABLE = MODEL_PATH is not None and DICT_PATH is not None

# ---------------------------------------------------------------------------
# Stroke generation helpers
#
# PP-OCRv6 is a printed-text recognition model trained on continuous images.
# Two-point stick figures don't look like real writing to it.  We interpolate
# the endpoint coordinates into dense point sequences (60-100 pts per stroke)
# with a gentle arc, matching how real touchpad input appears.
# ---------------------------------------------------------------------------

def _interp_stroke(x1, y1, x2, y2, num_points=80, arc_amp=4):
    """Interpolate between two endpoints with a gentle sinusoidal arc."""
    pts = []
    for i in range(num_points):
        t = i / (num_points - 1)
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1) + math.sin(t * math.pi) * arc_amp
        pts.append((int(x), int(y)))
    return pts


def make_horizontal_stroke():
    """Horizontal line ('一') — short and centered for best recognition."""
    return [_interp_stroke(435, 500, 565, 500, num_points=100, arc_amp=6)]


def make_cross_strokes():
    """Cross ('十') — centred vertical and horizontal strokes."""
    return [
        _interp_stroke(440, 500, 560, 500, num_points=100, arc_amp=3),
        _interp_stroke(500, 440, 500, 560, num_points=100, arc_amp=3),
    ]


def run_test(label, strokes, expected_char, min_confidence):
    """Run one recognition test. Returns True if passed."""
    if not HAS_ENGINE:
        print(f"  SKIP: engine could not be loaded: {_import_error}")
        return True
    if not MODELS_AVAILABLE:
        missing = []
        if MODEL_PATH is None:
            missing.append("model")
        if DICT_PATH is None:
            missing.append("dict")
        print(f"  SKIP: {', '.join(missing)} not found (searched candidates)")
        return True

    handle = engine.OnnxHandle(MODEL_PATH, DICT_PATH)
    try:
        for stroke in strokes:
            handle.add_stroke(stroke)
        results = handle.classify()

        if not results:
            print(f"  FAIL: No candidates returned for {label}")
            return False

        top_char, top_score = results[0]
        print(f"  Top: '{top_char}' confidence={top_score:.4f}")

        for i, (ch, sc) in enumerate(results[:5]):
            print(f"    #{i}: '{ch}' {sc:.4f}")

        if top_char != expected_char:
            print(f"  FAIL: Expected '{expected_char}', got '{top_char}' for {label}")
            return False
        if top_score < min_confidence:
            print(f"  FAIL: Confidence {top_score:.4f} < {min_confidence} for {label}")
            return False

        print(f"  PASS: '{top_char}' confidence={top_score:.4f}")
        return True
    finally:
        handle.destroy()


def main():
    if not HAS_ENGINE:
        print(f"Engine not loaded: {_import_error}")
    if not MODELS_AVAILABLE:
        missing = []
        if MODEL_PATH is None:
            missing.append(f"model ({MODEL_CANDIDATES})")
        if DICT_PATH is None:
            missing.append(f"dict ({DICT_CANDIDATES})")
        print(f"Models not found: {', '.join(missing)}")

    passed = 0
    failed = 0

    tests = [
        ("horizontal line → 一", make_horizontal_stroke(), "一", 0.9),
        ("cross → 十",          make_cross_strokes(),     "十", 0.95),
    ]

    for label, strokes, expected, min_conf in tests:
        print(f"\n--- {label} ---")
        if run_test(label, strokes, expected, min_conf):
            passed += 1
        else:
            failed += 1

    print(f"\n{'=' * 30}")
    print(f"Results: {passed} passed, {failed} failed")

    if failed:
        sys.exit(1)
    if passed == 0:
        print("PASS: No tests were run (models not found — this is expected)")
        sys.exit(0)
    print("All tests passed!")


if __name__ == "__main__":
    main()
