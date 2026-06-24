#!/usr/bin/env python3
"""Interactive data collection tool for PP-OCRv6 handwriting recognition.

Collects touchpad-drawn characters with ground truth, runs PP-OCRv6 inference,
and saves results to a JSON dataset compatible with ``analyze_ppocr_data.py``.

Modes:
  --prompt (default): cycle through HSK-level-1 character list
  --free:            user draws, then types the ground truth
  --dry-run:         verify imports + touchpad detection, print "Ready"
"""

import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Module loading (same pattern as tests/test_ppocr_recognition.py)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "..", "src"))

_HAS_ENGINE = False
_engine = None
_import_error = ""

try:
    import importlib.machinery
    import importlib.util
    _engine_path = os.path.join(SCRIPT_DIR, "..", "src", "ibus-engine-handwrite-chinese")
    _loader = importlib.machinery.SourceFileLoader("engine", _engine_path)
    _spec = importlib.util.spec_from_loader("engine", _loader)
    _engine = importlib.util.module_from_spec(_spec)
    _loader.exec_module(_engine)
    _HAS_ENGINE = True
except Exception as exc:
    _HAS_ENGINE = False
    _import_error = str(exc)

# ---------------------------------------------------------------------------
# Model paths
# ---------------------------------------------------------------------------
MODEL_PATH = "/tmp/models/ppocrv6_small.onnx"
DICT_PATH = "/tmp/models/dict_v6.txt"

# ---------------------------------------------------------------------------
# Default character list — HSK level 1 (~150 most common)
# ---------------------------------------------------------------------------
HSK1_CHARS = list(dict.fromkeys([
    "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
    "人", "大", "小", "上", "下", "不", "中", "国", "我", "你",
    "他", "她", "这", "那", "什", "么", "的", "了", "是", "在",
    "有", "和", "也", "就", "都", "而", "及", "与", "或", "个",
    "们", "来", "去", "说", "看", "知", "道", "会", "可", "以",
    "能", "做", "想", "爱", "吃", "喝", "走", "跑", "坐", "站",
    "买", "卖", "开", "关", "回", "出", "进", "到", "过", "家",
    "学", "书", "水", "火", "山", "石", "田", "土", "木", "林",
    "花", "草", "鸟", "鱼", "马", "牛", "羊", "虫", "风", "云",
    "雨", "雪", "天", "地", "日", "月", "星", "光", "电", "声",
    "色", "味", "香", "长", "短", "高", "低", "远", "近", "多",
    "少", "新", "旧", "快", "慢", "好", "坏", "真", "假", "早",
    "晚", "今", "明", "年", "月", "时", "分", "秒", "元", "角",
    "分", "百", "千", "万", "亿", "白", "黑", "红", "黄", "蓝",
    "绿", "左", "右", "前", "后", "内", "外", "间", "边", "上",
    "面", "里", "头", "手", "足", "口", "目", "耳", "鼻", "身",
    "心",
]))

# ---------------------------------------------------------------------------
# Default output path
# ---------------------------------------------------------------------------
DEFAULT_OUTPUT = os.path.join(
    ".omo", "evidence", "ppocr-handwriting-dataset", "dataset-v1.json"
)


# ===================================================================
# Pipeline stats helpers
# ===================================================================

def _compute_pipeline_stats(strokes):
    """Compute pipeline_stats dict from collected strokes.

    canvas_size uses the same padding + minimum-dimension logic as
    ``OnnxHandle._preprocess()``.
    """
    flat = [pt for stroke in strokes for pt in stroke]
    xs = [p[0] for p in flat]
    ys = [p[1] for p in flat]
    num_points = len(flat)

    if num_points == 0:
        return {
            "canvas_size": [200, 200],
            "total_points": 0,
            "num_strokes": len(strokes),
            "bbox": [0.0, 0.0, 0.0, 0.0],
        }

    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)

    pad = 20
    cw = max(xmax - xmin + 2 * pad, 200)
    ch = max(ymax - ymin + 2 * pad, 200)

    return {
        "canvas_size": [int(cw), int(ch)],
        "total_points": num_points,
        "num_strokes": len(strokes),
        "bbox": [round(xmin, 4), round(ymin, 4), round(xmax, 4), round(ymax, 4)],
    }


def _extract_image_stats(tensor):
    """Extract resized_width and pixel stats from a preprocessed tensor.

    Returns a dict. *tensor* must be the output of ``OnnxHandle._preprocess()``
    (shape ``[1, 3, 48, W]``).
    """
    return {
        "resized_width": int(tensor.shape[3]),
        "img_min": round(float(tensor.min()), 4),
        "img_max": round(float(tensor.max()), 4),
        "img_mean": round(float(tensor.mean()), 4),
    }


# ===================================================================
# Collection core
# ===================================================================

def run_collection(args):
    """Main collection loop.

    Returns the assembled dataset dict.
    """
    # -------------------------------------------------------------------
    # Print greeting
    # -------------------------------------------------------------------
    total_chars = len(args.char_list)
    print("\n  PP-OCRv6 Handwriting Data Collection")
    print(f"  Mode: {'prompt (HSK1)' if not args.free else 'free'}")
    print(f"  Characters: {total_chars}")
    print(f"  Output: {args.output}")
    print()

    # -------------------------------------------------------------------
    # Import touchpad via handwrite_evdev
    # -------------------------------------------------------------------
    from handwrite_evdev import TouchpadCapture

    cap = TouchpadCapture()
    if not cap.start():
        print("Error: No touchpad detected.", file=sys.stderr)
        print("Ensure your user has read/write access to /dev/input/event*", file=sys.stderr)
        sys.exit(1)
    print("  Touchpad detected ✓")
    print()

    # -------------------------------------------------------------------
    # Create OnnxHandle
    # -------------------------------------------------------------------
    handle = _engine.OnnxHandle(MODEL_PATH, DICT_PATH, max_candidates=24)

    # -------------------------------------------------------------------
    # State
    # -------------------------------------------------------------------
    samples = []
    chars_done = []
    dataset_version = 1
    interrupted = False
    next_char_idx = 0

    def _save_checkpoint():
        """Write what we have so far (called on Ctrl+C)."""
        if not samples:
            return
        dataset = _build_dataset(dataset_version, chars_done, samples)
        _write_dataset(dataset, args.output)
        print(f"\n  [checkpoint saved: {len(samples)} samples → {args.output}]")

    def _signal_handler(_sig, _frame):
        nonlocal interrupted
        if not interrupted:
            print("\n\n  Ctrl+C — saving checkpoint and exiting...")
            _save_checkpoint()
        interrupted = True

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # -------------------------------------------------------------------
    # Loop
    # -------------------------------------------------------------------
    try:
        while True:
            if interrupted:
                break

            # ---- Determine ground truth ----
            if args.free:
                # Free mode: prompt generic, user types the char
                print(f"  ▶ Write any character on touchpad, then press ENTER")
                sys.stdout.write("  Ground truth: ")
                sys.stdout.flush()
                gt_line = sys.stdin.readline()
                if interrupted:
                    break
                gt = gt_line.strip()
                if not gt:
                    print("  (empty ground truth, skipping)")
                    continue
            else:
                # Prompt mode: show the next character from the list
                if next_char_idx >= total_chars:
                    print("  All characters in the list have been shown. Done!")
                    break
                gt = args.char_list[next_char_idx]
                n_display = next_char_idx + 1

            # ---- Prompt user ----
            if args.free:
                print(f"  Char: draw '{gt}' → draw on touchpad, press ENTER")
            else:
                print(f"  Char {n_display}/{total_chars}: 写 '{gt}' → draw on touchpad, press ENTER")

            sys.stdout.flush()
            line = sys.stdin.readline()
            if interrupted:
                break

            # ---- Small settle delay ----
            time.sleep(0.15)

            # ---- Capture strokes ----
            strokes = cap.read_and_clear()
            if not strokes or all(len(s) < 2 for s in strokes):
                print("  (no strokes detected, skipping)")
                if not args.free:
                    next_char_idx += 1
                continue

            # ---- Pipeline stats from raw strokes ----
            pipeline_stats = _compute_pipeline_stats(strokes)

            # ---- Run PP-OCRv6 inference ----
            for stroke in strokes:
                handle.add_stroke(stroke)

            # Preprocess once — capture image stats AND reuse for inference
            input_tensor = handle._preprocess()
            if input_tensor is None:
                print("  (preprocessing failed, skipping)")
                handle.clear()
                if not args.free:
                    next_char_idx += 1
                continue
            pipeline_stats.update(_extract_image_stats(input_tensor))

            t0 = time.time()
            output = handle.session.run(None, {"x": input_tensor})[0]
            results = handle._decode(output)
            latency_ms = (time.time() - t0) * 1000
            pipeline_stats["inference_latency_ms"] = round(latency_ms, 2)

            handle.clear()

            if not results:
                print("  (inference returned no candidates, skipping)")
                if not args.free:
                    next_char_idx += 1
                continue

            # ---- Show predictions ----
            top5 = results[:5]
            top5_str = ", ".join(f"'{ch}'({sc:.2f})" for ch, sc in top5)
            top1_char, top1_score = top5[0]
            print(f"  PP-OCRv6: top-1='{top1_char}'({top1_score:.2f})  top-5={top5_str}")

            # ---- Ask user ----
            sys.stdout.write(f"  Correct? [ENTER=yes / type correct char / 's'=skip] ")
            sys.stdout.flush()
            feedback = sys.stdin.readline().strip().lower()
            if interrupted:
                break

            if feedback == "s":
                print("  (skipped)")
                if not args.free:
                    next_char_idx += 1
                continue

            if feedback == "":
                # ENTER — ground_truth is what we expected
                corrected_gt = gt
            else:
                corrected_gt = feedback

            # ---- Determine correctness ----
            correct_top1 = results[0][0] == corrected_gt
            top5_chars = [r[0] for r in results[:5]]
            correct_top5 = corrected_gt in top5_chars

            # ---- Build sample ----
            sample = {
                "ground_truth": corrected_gt,
                "strokes": strokes,
                "ppocr_v6": {
                    "top5": [(ch, round(sc, 4)) for ch, sc in results[:5]],
                    "top24": [(ch, round(sc, 4)) for ch, sc in results[:24]],
                    "correct_top1": correct_top1,
                    "correct_top5": correct_top5,
                    "confidence_top1": round(results[0][1], 4),
                    "inference_latency_ms": round(latency_ms, 2),
                },
                "pipeline_stats": pipeline_stats,
            }
            samples.append(sample)
            chars_done.append(corrected_gt)

            status = "✓" if correct_top1 else "✗"
            print(f"  → saved ({status} top-1). Total: {len(samples)}")

            if not args.free:
                next_char_idx += 1

    finally:
        cap.stop()

    return _build_dataset(dataset_version, chars_done, samples)


# ===================================================================
# Dataset assembly
# ===================================================================

def _build_dataset(version, chars_collected, samples):
    """Wrap collected samples into the final dataset structure."""
    return {
        "version": version,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "chars_collected": sorted(set(chars_collected)),
        "samples": samples,
    }


def _write_dataset(dataset, path):
    """Write dataset JSON to disk, creating parent directories."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    return path


# ===================================================================
# Dry run
# ===================================================================

def dry_run(args):
    """Verify imports, model paths, and touchpad detection."""
    ok = True

    # 1. Engine import
    if not _HAS_ENGINE:
        print(f"FAIL Engine not loaded: {_import_error}", file=sys.stderr)
        ok = False
    else:
        print(f"OK   Engine loaded (_engine)")

    # 2. Model files
    if not os.path.isfile(MODEL_PATH):
        print(f"FAIL Model not found: {MODEL_PATH}", file=sys.stderr)
        ok = False
    else:
        size = os.path.getsize(MODEL_PATH)
        print(f"OK   Model: {MODEL_PATH} ({size / 1024 / 1024:.1f} MB)")

    if not os.path.isfile(DICT_PATH):
        print(f"FAIL Dict not found: {DICT_PATH}", file=sys.stderr)
        ok = False
    else:
        with open(DICT_PATH, "r", encoding="utf-8") as f:
            dc = sum(1 for l in f if l.strip())
        print(f"OK   Dict: {DICT_PATH} ({dc} chars)")

    # 3. OnnxHandle creation
    if _HAS_ENGINE:
        try:
            h = _engine.OnnxHandle(MODEL_PATH, DICT_PATH)
            h.destroy()
            print(f"OK   OnnxHandle creation")
        except Exception as exc:
            print(f"FAIL OnnxHandle creation: {exc}", file=sys.stderr)
            ok = False

    # 4. Touchpad detection
    from handwrite_evdev import TouchpadCapture
    cap = TouchpadCapture()
    has_touchpad = cap.start()
    if has_touchpad:
        cap.stop()
        print(f"OK   Touchpad detected")
    else:
        print(f"WARN No touchpad detected (dry-run ok, collection will fail)")

    # 5. Output path
    out_dir = os.path.dirname(args.output)
    if os.path.isdir(out_dir):
        print(f"OK   Output dir exists: {out_dir}")
    elif os.path.isdir(os.path.dirname(out_dir)):
        print(f"OK   Output dir will be created: {out_dir}")
    else:
        print(f"WARN Parent dir may not exist: {os.path.dirname(out_dir)}")

    print()
    if ok:
        print("Ready")
        return 0
    else:
        print("Not ready — see failures above")
        return 1


# ===================================================================
# CLI
# ===================================================================

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Collect PP-OCRv6 handwriting dataset from touchpad input."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--prompt",
        action="store_true",
        default=True,
        dest="prompt",
        help="Prompt mode: iterate through character list (default)",
    )
    mode.add_argument(
        "--free",
        action="store_true",
        help="Free mode: you type each character after drawing",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Verify imports and touchpad detection, print Ready, then exit",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output JSON path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--chars",
        default=None,
        metavar="CHARS_FILE",
        help="Custom character list text file (one char per line)",
    )
    return parser.parse_args(argv)


def main():
    args = parse_args()

    # Resolve output
    args.output = os.path.abspath(args.output)

    # Resolve character list
    if args.free:
        args.char_list = []
    elif args.chars:
        with open(args.chars, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        args.char_list = lines
        print(f"Loaded {len(lines)} characters from {args.chars}")
    else:
        args.char_list = HSK1_CHARS

    # Dry run
    if args.dry_run:
        sys.exit(dry_run(args))

    # Pre-flight checks
    if not _HAS_ENGINE:
        print(f"Error: Engine could not be loaded: {_import_error}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(MODEL_PATH):
        print(f"Error: Model not found at {MODEL_PATH}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(DICT_PATH):
        print(f"Error: Dict not found at {DICT_PATH}", file=sys.stderr)
        sys.exit(1)

    # Run collection
    dataset = run_collection(args)

    # Save
    if not dataset["samples"]:
        print("\nNo samples collected — nothing to save.")
        sys.exit(0)

    path = _write_dataset(dataset, args.output)
    print(f"\nDataset saved: {path}")
    print(f"  Version: {dataset['version']}")
    print(f"  Samples: {len(dataset['samples'])}")
    print(f"  Unique chars: {len(dataset['chars_collected'])}")


if __name__ == "__main__":
    main()
