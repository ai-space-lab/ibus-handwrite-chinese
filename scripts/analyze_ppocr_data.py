#!/usr/bin/env python3
"""Analyze PP-OCRv6 handwriting dataset — accuracy, confusion, calibration, and bias."""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict


def load_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_dict(path):
    """Return dict mapping char -> index (0-based line number)."""
    char_to_idx = {}
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f):
            char = line.rstrip("\n")
            if char:  # only non-empty lines
                char_to_idx[char] = lineno
    return char_to_idx


def confidence_histogram(confidences, bins=10):
    """Bin confidences [0,1) into <bins> buckets. Returns list of (low, high, count)."""
    bucket_size = 1.0 / bins
    buckets = [(i * bucket_size, (i + 1) * bucket_size, 0) for i in range(bins)]
    counts = [0] * bins
    for c in confidences:
        idx = min(int(c / bucket_size), bins - 1)
        counts[idx] += 1
    return [(lo, hi, counts[i]) for i, (lo, hi, _) in enumerate(buckets)]


def compute_stroke_bucket(num_strokes):
    if num_strokes <= 3:
        return "1-3 strokes"
    elif num_strokes <= 6:
        return "4-6 strokes"
    elif num_strokes <= 9:
        return "7-9 strokes"
    else:
        return "10+ strokes"


STROKE_BUCKET_ORDER = ["1-3 strokes", "4-6 strokes", "7-9 strokes", "10+ strokes"]


def dict_index_bucket(idx):
    if idx < 0:
        return "unknown"
    if idx <= 1000:
        return "0-1000"
    elif idx <= 5000:
        return "1000-5000"
    else:
        return "5000+"


DICT_BUCKET_ORDER = ["0-1000", "1000-5000", "5000+", "unknown"]


def run_analysis(data, dict_path, verbose):
    char_to_idx = load_dict(dict_path)
    samples = data.get("samples", [])
    total = len(samples)

    # --------------- counters ---------------
    top1_correct = 0
    top5_correct = 0
    top10_correct = 0
    top24_correct = 0

    conf_when_correct = []
    conf_when_wrong = []
    all_conf = []

    # char confusion: ground_truth -> list of (predicted_top1, confidence_top1)
    char_confusion = defaultdict(list)

    # stroke buckets: bucket_name -> {total, top1_ok, top5_ok}
    stroke_buckets = {b: {"total": 0, "top1_ok": 0, "top5_ok": 0} for b in STROKE_BUCKET_ORDER}

    # dict index buckets: bucket_name -> {total, top1_ok, top5_ok}
    dict_buckets = {b: {"total": 0, "top1_ok": 0, "top5_ok": 0} for b in DICT_BUCKET_ORDER}

    # per-sample log lines
    sample_logs = []

    for s in samples:
        gt = s.get("ground_truth", "?")
        ppocr = s.get("ppocr_v6", {})
        pipeline = s.get("pipeline_stats", {})

        top1 = ppocr.get("top5", [[None, 0.0]])[0] if ppocr.get("top5") else [None, 0.0]
        top1_char = top1[0]
        top1_conf = top1[1] if top1[1] is not None else 0.0
        top5_chars = [t[0] for t in (ppocr.get("top5") or [])]
        top10_chars = [t[0] for t in (ppocr.get("top24") or [])[:10]]
        top24_chars = [t[0] for t in (ppocr.get("top24") or [])[:24]]
        correct_top1 = ppocr.get("correct_top1", False)
        correct_top5 = ppocr.get("correct_top5", False)

        # top-10 / top-24 from top24 list
        correct_top10 = gt in top10_chars
        correct_top24 = gt in top24_chars

        if correct_top1:
            top1_correct += 1
        if correct_top5:
            top5_correct += 1
        if correct_top10:
            top10_correct += 1
        if correct_top24:
            top24_correct += 1

        all_conf.append(top1_conf)
        if correct_top1:
            conf_when_correct.append(top1_conf)
        else:
            conf_when_wrong.append(top1_conf)

        char_confusion[gt].append((top1_char, top1_conf))

        # stroke bucket
        num_strokes = pipeline.get("num_strokes", 0)
        sb = compute_stroke_bucket(num_strokes)
        stroke_buckets[sb]["total"] += 1
        if correct_top1:
            stroke_buckets[sb]["top1_ok"] += 1
        if correct_top5:
            stroke_buckets[sb]["top5_ok"] += 1

        # dict index bucket
        gt_idx = char_to_idx.get(gt, -1)
        db = dict_index_bucket(gt_idx)
        dict_buckets[db]["total"] += 1
        if correct_top1:
            dict_buckets[db]["top1_ok"] += 1
        if correct_top5:
            dict_buckets[db]["top5_ok"] += 1

        # verbose log line
        if verbose:
            latency = ppocr.get("inference_latency_ms", 0.0)
            strokes = pipeline.get("num_strokes", 0)
            pts = pipeline.get("total_points", 0)
            tick = "✓" if correct_top1 else "✗"
            top5_str = ",".join(top5_chars) if top5_chars else "-"
            sample_logs.append(
                f"  {gt:4s}  top-1='{top1_char or '?'}'({top1_conf:.2f}) {tick}  "
                f"top5∈[{top5_str}]  conf={top1_conf:.2f}  "
                f"latency={latency:.1f}ms  strokes={strokes}  pts={pts}"
            )

    # ========== A. Overall Accuracy ==========
    overall = {
        "top1": {"correct": top1_correct, "total": total, "accuracy": round(top1_correct / total * 100, 1) if total else 0},
        "top5": {"correct": top5_correct, "total": total, "accuracy": round(top5_correct / total * 100, 1) if total else 0},
        "top10": {"correct": top10_correct, "total": total, "accuracy": round(top10_correct / total * 100, 1) if total else 0},
        "top24": {"correct": top24_correct, "total": total, "accuracy": round(top24_correct / total * 100, 1) if total else 0},
    }

    # ========== B. Confidence Distribution Histogram ==========
    hist_bins = confidence_histogram(all_conf, 10)
    hist_total = len(all_conf) or 1
    hist_data = []
    for lo, hi, cnt in hist_bins:
        hist_data.append({"range_low": round(lo, 2), "range_high": round(hi, 2), "count": cnt, "pct": round(cnt / hist_total * 100, 1)})

    # ========== C. Confidence Calibration ==========
    def avg(vals):
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    def median(vals):
        if not vals:
            return 0.0
        s = sorted(vals)
        n = len(s)
        if n % 2 == 1:
            return round(s[n // 2], 2)
        return round((s[n // 2 - 1] + s[n // 2]) / 2, 2)

    calibration = {
        "correct": {"avg": round(sum(conf_when_correct) / len(conf_when_correct), 2) if conf_when_correct else 0,
                     "median": median(conf_when_correct),
                     "n": len(conf_when_correct)},
        "wrong": {"avg": round(sum(conf_when_wrong) / len(conf_when_wrong), 2) if conf_when_wrong else 0,
                  "median": median(conf_when_wrong),
                  "n": len(conf_when_wrong)},
        "ratio": round((sum(conf_when_correct) / len(conf_when_correct)) / (sum(conf_when_wrong) / len(conf_when_wrong) + 1e-9), 1) if conf_when_correct and conf_when_wrong else 0,
    }

    # ========== D. Per-Character Confusion Matrix ==========
    char_results = {}
    # Compute per-character stats from the original samples (has top5 list)
    char_agg = defaultdict(lambda: {"total": 0, "top1_correct": 0, "top5_within": 0, "top1_preds": []})
    for s in samples:
        gt = s.get("ground_truth", "?")
        ppocr = s.get("ppocr_v6", {})
        top5_chars = [t[0] for t in (ppocr.get("top5") or [])]
        top1_char = (ppocr.get("top5") or [[None]])[0][0]
        top1_conf = (ppocr.get("top5") or [[None, 0.0]])[0][1] or 0.0
        char_agg[gt]["total"] += 1
        char_agg[gt]["top1_preds"].append((top1_char, top1_conf))
        if top1_char == gt:
            char_agg[gt]["top1_correct"] += 1
        if gt in top5_chars:
            char_agg[gt]["top5_within"] += 1

    for ch, info in char_agg.items():
        if info["total"] < 3:
            continue
        n = info["total"]
        top1_counter = Counter(p[0] for p in info["top1_preds"])
        char_results[ch] = {
            "samples": n,
            "top1_distribution": dict(top1_counter.most_common(10)),
            "top1_correct": info["top1_correct"],
            "top1_accuracy": round(info["top1_correct"] / n * 100, 1),
            "top5_within": info["top5_within"],
            "top5_within_accuracy": round(info["top5_within"] / n * 100, 1),
        }

    # ========== E. Stroke Complexity vs Accuracy ==========
    stroke_stats = {}
    for b in STROKE_BUCKET_ORDER:
        sb = stroke_buckets[b]
        t = sb["total"]
        stroke_stats[b] = {
            "total": t,
            "top1_correct": sb["top1_ok"],
            "top1_accuracy": round(sb["top1_ok"] / t * 100, 1) if t else 0,
            "top5_correct": sb["top5_ok"],
            "top5_accuracy": round(sb["top5_ok"] / t * 100, 1) if t else 0,
        }

    # ========== F. Dict Index Analysis ==========
    dict_stats = {}
    for b in DICT_BUCKET_ORDER:
        db = dict_buckets[b]
        t = db["total"]
        dict_stats[b] = {
            "total": t,
            "top1_correct": db["top1_ok"],
            "top1_accuracy": round(db["top1_ok"] / t * 100, 1) if t else 0,
            "top5_correct": db["top5_ok"],
            "top5_accuracy": round(db["top5_ok"] / t * 100, 1) if t else 0,
        }

    # ========== Build JSON report ==========
    report = {
        "dataset": {
            "version": data.get("version"),
            "timestamp": data.get("timestamp"),
            "chars_collected": data.get("chars_collected", []),
            "total_samples": total,
        },
        "overall_accuracy": overall,
        "confidence_histogram": hist_data,
        "confidence_calibration": calibration,
        "per_character": dict(sorted(char_results.items())),
        "stroke_complexity": stroke_stats,
        "dict_index_analysis": dict_stats,
    }

    return report, sample_logs


def print_report(report, sample_logs, verbose):
    ds = report["dataset"]
    overall = report["overall_accuracy"]
    hist = report["confidence_histogram"]
    cal = report["confidence_calibration"]
    chars = report["per_character"]
    stroke = report["stroke_complexity"]
    dict_an = report["dict_index_analysis"]

    total = ds["total_samples"]
    sep = "=" * 60

    # Header
    print(sep)
    print(f"  PP-OCRv6 Handwriting Dataset Analysis")
    print(f"  Version: {ds['version']}  |  Timestamp: {ds['timestamp']}")
    print(f"  Total samples: {total}")
    print(sep)

    # A. Overall Accuracy
    print(f"\n{'A. Overall Accuracy':^60}")
    print("-" * 60)
    o = overall
    print(f"  PP-OCRv6 top-1:    {o['top1']['correct']:>4}/{o['top1']['total']} ({o['top1']['accuracy']}%)")
    print(f"  PP-OCRv6 top-5:    {o['top5']['correct']:>4}/{o['top5']['total']} ({o['top5']['accuracy']}%)")
    print(f"  PP-OCRv6 top-10:   {o['top10']['correct']:>4}/{o['top10']['total']} ({o['top10']['accuracy']}%)")
    print(f"  PP-OCRv6 top-24:   {o['top24']['correct']:>4}/{o['top24']['total']} ({o['top24']['accuracy']}%)")

    # B. Confidence Distribution Histogram
    print(f"\n{'B. Confidence Distribution Histogram':^60}")
    print("-" * 60)
    print(f"  {'Confidence range':<18} | {'Count':>5}  {'%':>6}")
    print(f"  {'-'*18}-+-{'-'*12}")
    for h in hist:
        print(f"  {h['range_low']:.2f} - {h['range_high']:.2f}    | {h['count']:>5}  {h['pct']:>5.1f}%")

    # C. Confidence Calibration
    print(f"\n{'C. Confidence Calibration':^60}")
    print("-" * 60)
    print(f"  When CORRECT:  avg confidence = {cal['correct']['avg']:.2f}  (median: {cal['correct']['median']:.2f})")
    print(f"  When WRONG:    avg confidence = {cal['wrong']['avg']:.2f}  (median: {cal['wrong']['median']:.2f})")
    print(f"  Ratio (correct/wrong): {cal['ratio']}x")

    # D. Per-Character Confusion Matrix
    print(f"\n{'D. Per-Character Confusion Matrix':^60}")
    print("-" * 60)
    for ch, info in chars.items():
        n = info["samples"]
        top1_acc = info.get("top1_accuracy", 0)
        top5_acc = info.get("top5_within_accuracy", 0)
        dist = info.get("top1_distribution", {})
        dist_str = " ".join(f"'{c}'({v})" for c, v in dist.items())
        print(f"  '{ch}' ({n} samples):")
        print(f"    top-1: {dist_str}  ← correct {top1_acc}%")
        print(f"    top-5 within: {info.get('top5_within', '?')}/{n} ({top5_acc}%)")

    # E. Stroke Complexity vs Accuracy
    print(f"\n{'E. Stroke Complexity vs Accuracy':^60}")
    print("-" * 60)
    print(f"  {'Stroke count':<18} | {'Samples':>5}  {'Top-1':>16}  {'Top-5':>16}")
    print(f"  {'-'*18}-+-{'-'*5}-+-{'-'*16}-+-{'-'*16}")
    for b in STROKE_BUCKET_ORDER:
        sb = stroke[b]
        t = sb["total"]
        t1 = f"{sb['top1_correct']}/{t} ({sb['top1_accuracy']}%)"
        t5 = f"{sb['top5_correct']}/{t} ({sb['top5_accuracy']}%)"
        print(f"  {b:<18} | {t:>5}  {t1:>16}  {t5:>16}")

    # F. Dict Index Analysis
    print(f"\n{'F. Dict Index Analysis':^60}")
    print("-" * 60)
    print(f"  {'Dict index':<18} | {'Samples':>5}  {'Top-1':>16}  {'Top-5':>16}")
    print(f"  {'-'*18}-+-{'-'*5}-+-{'-'*16}-+-{'-'*16}")
    for b in DICT_BUCKET_ORDER:
        db = dict_an[b]
        t = db["total"]
        t1 = f"{db['top1_correct']}/{t} ({db['top1_accuracy']}%)"
        t5 = f"{db['top5_correct']}/{t} ({db['top5_accuracy']}%)"
        print(f"  {b:<18} | {t:>5}  {t1:>16}  {t5:>16}")

    # G. Per-Sample Log
    if verbose and sample_logs:
        print(f"\n{'G. Per-Sample Log':^60}")
        print("-" * 60)
        for line in sample_logs:
            print(line)

    print()
    print(sep)
    print("  Analysis complete.")
    print(sep)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze PP-OCRv6 handwriting dataset and produce accuracy metrics."
    )
    parser.add_argument(
        "--input", required=True,
        help="Path to dataset JSON file"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Directory for output files (default: .omo/evidence/ppocr-handwriting-dataset/)"
    )
    parser.add_argument(
        "--dict", default="/tmp/models/dict_v6.txt",
        help="Path to dict_v6.txt (default: /tmp/models/dict_v6.txt)"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print per-sample log lines"
    )
    args = parser.parse_args()

    output_dir = args.output_dir or os.path.join(".omo", "evidence", "ppocr-handwriting-dataset")

    if not os.path.isfile(args.input):
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.dict):
        print(f"Error: dict file not found: {args.dict}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading dataset from {args.input} ...")
    data = load_dataset(args.input)
    print(f"Loaded {len(data.get('samples', []))} samples.\n")

    print(f"Loading dict from {args.dict} ...")
    report, sample_logs = run_analysis(data, args.dict, verbose=args.verbose)

    print_report(report, sample_logs, verbose=args.verbose)

    report_path = os.path.join(output_dir, "analysis-report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nReport written to {report_path}")


if __name__ == "__main__":
    main()
