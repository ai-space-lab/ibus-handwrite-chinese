#!/usr/bin/env python3
"""Capture ONE handwriting sample from touchpad, run PP-OCRv6, output JSON.

Usage:
    python3 scripts/capture_one.py <ground_truth>
    python3 scripts/capture_one.py 一

Outputs JSON to stdout with prediction + pipeline stats.
No stdin interaction — waits 4 seconds collecting strokes after clearing buffer.
"""

import importlib.machinery
import importlib.util
import json
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'src'))

# Load engine
_engine_path = os.path.join(SCRIPT_DIR, '..', 'src', 'ibus-engine-handwrite-chinese')
loader = importlib.machinery.SourceFileLoader('engine', _engine_path)
spec = importlib.util.spec_from_loader('engine', loader)
engine = importlib.util.module_from_spec(spec)
loader.exec_module(engine)

MODEL_PATH = "/tmp/models/ppocrv6_small.onnx"
DICT_PATH = "/tmp/models/dict_v6.txt"


def capture_one(ground_truth, wait_secs=4):
    """Capture one sample, run inference, return result dict."""
    from handwrite_evdev import TouchpadCapture

    handle = engine.OnnxHandle(MODEL_PATH, DICT_PATH, max_candidates=24)

    cap = TouchpadCapture()
    if not cap.start():
        print(json.dumps({"error": "no touchpad found"}))
        sys.exit(1)

    # Clear any residual strokes
    cap.read_and_clear()

    # Wait collecting strokes
    time.sleep(0.3)
    cap.read_and_clear()  # clear again after settling

    print(f"  ✏️  Write '{ground_truth}' on touchpad NOW ({wait_secs}s)...",
          file=sys.stderr, flush=True)
    for i in range(wait_secs):
        time.sleep(1)
        print(f"  ... {wait_secs - i - 1}s", file=sys.stderr, flush=True)

    strokes = cap.read_and_clear()
    cap.stop()

    if not strokes:
        handle.destroy()
        return {"error": "no strokes detected", "strokes": [], "ground_truth": ground_truth}

    # Compute bbox from raw strokes
    flat = [pt for stroke in strokes for pt in stroke]
    xs = [p[0] for p in flat]
    ys = [p[1] for p in flat]
    bbox = [min(xs), min(ys), max(xs), max(ys)]

    # Run inference
    for stroke in strokes:
        handle.add_stroke(stroke)

    t0 = time.time()
    results = handle.classify()
    latency_ms = (time.time() - t0) * 1000.0

    # Get pipeline stats
    pipeline = {
        "canvas_size": [],
        "total_points": len(flat),
        "num_strokes": len(strokes),
        "bbox": [round(v, 4) for v in bbox],
        "resized_width": 0,
        "img_min": 0.0,
        "img_max": 0.0,
        "img_mean": 0.0,
    }
    try:
        tensor = handle._preprocess()
        if tensor is not None:
            pipeline["resized_width"] = int(tensor.shape[3])
            pipeline["img_min"] = round(float(tensor.min()), 4)
            pipeline["img_max"] = round(float(tensor.max()), 4)
            pipeline["img_mean"] = round(float(tensor.mean()), 4)
    except Exception:
        pass

    handle.destroy()

    if not results:
        return {"error": "no recognition results", "strokes": strokes, "ground_truth": ground_truth}

    top5 = results[:5]
    top24 = results[:24]
    top1_char = results[0][0]
    top1_score = results[0][1]
    top5_chars = [c for c, _ in top5]

    return {
        "ground_truth": ground_truth,
        "strokes": strokes,
        "ppocr_v6": {
            "top5": [(c, round(s, 4)) for c, s in top5],
            "top24": [(c, round(s, 4)) for c, s in top24],
            "correct_top1": (top1_char == ground_truth),
            "correct_top5": (ground_truth in top5_chars),
            "confidence_top1": round(top1_score, 4),
            "inference_latency_ms": round(latency_ms, 2),
        },
        "pipeline_stats": pipeline,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: capture_one.py <ground_truth> [wait_secs]"}))
        sys.exit(1)
    gt = sys.argv[1]
    wait = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    result = capture_one(gt, wait_secs=wait)
    print(json.dumps(result, ensure_ascii=False, indent=2))
