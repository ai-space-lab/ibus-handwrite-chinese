#!/usr/bin/env python3
"""Interactive character collection with GTK writing UI.

Launches the GTK writing panel in background, then runs an interactive
terminal loop prompting the user to draw characters one at a time.
Reads recognition results from the log file.
"""

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_PATH = os.path.join(SCRIPT_DIR, "..", "src", "ibus-engine-handwrite-chinese")
LOG_PATH = "/tmp/ppocr-recognition.log"
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", ".omo", "evidence", "ppocr-handwriting-dataset")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "dataset-gtk-v1.json")

# HSK level 1 character list
HSK1_CHARS = [
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
]


def get_log_line_count():
    """Get current number of lines in the log file."""
    if not os.path.exists(LOG_PATH):
        return 0
    with open(LOG_PATH, "r") as f:
        return sum(1 for _ in f)


def read_log_lines(start_line):
    """Read new log lines since start_line. Returns (new_count, events)."""
    if not os.path.exists(LOG_PATH):
        return start_line, []
    events = []
    count = 0
    with open(LOG_PATH, "r") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            count = i + 1
            if i >= start_line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return count, events


def extract_prediction(events):
    """Extract the latest prediction from log events.
    Returns (top5_list, latency_ms) or (None, None)."""
    classify_event = None
    decode_event = None
    for ev in events:
        if ev.get("event") == "classify":
            classify_event = ev
        elif ev.get("event") == "decode":
            decode_event = ev
    
    if decode_event and decode_event.get("top5"):
        latency = classify_event.get("latency_ms", 0) if classify_event else 0
        return decode_event["top5"], latency
    return None, None


def load_existing_dataset():
    """Load existing dataset if it exists."""
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "version": 1,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "chars_collected": [],
        "samples": [],
    }


def save_dataset(dataset):
    """Save dataset to disk."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"\n  [saved: {len(dataset['samples'])} samples → {OUTPUT_PATH}]")


def run_collection():
    # Load existing dataset
    dataset = load_existing_dataset()
    existing_chars = set(dataset["chars_collected"])
    samples = dataset["samples"]

    # Filter character list to exclude already-collected chars
    char_list = [c for c in HSK1_CHARS if c not in existing_chars]
    if not char_list:
        char_list = HSK1_CHARS  # start over if all done

    total = len(char_list) + len(existing_chars)
    print(f"\n  Characters in dataset: {len(existing_chars)}")
    print(f"  Remaining to collect: {len(char_list)}")
    print()

    # Record initial log position
    log_pos = get_log_line_count()

    try:
        for idx, ch in enumerate(char_list, 1):
            # Wait until we get new log entries
            print(f"\n  --- Character {idx}/{len(char_list)}: '{ch}' ---")
            print(f"  ▶ Draw '{ch}' on the touchpad in the GTK window")
            print(f"  ▶ When you see the result in the GTK window, type 'y' + ENTER")

            while True:
                inp = input("  Ready? (y=done, s=skip, q=quit): ").strip().lower()
                if inp == "q":
                    print("  Quitting...")
                    save_dataset(dataset)
                    return
                if inp == "s":
                    print("  Skipped!")
                    break
                if inp == "y":
                    break
                print("  (enter 'y', 's', or 'q')")

            if inp == "s":
                continue

            # Read new log entries since last check
            new_pos, events = read_log_lines(log_pos)
            log_pos = new_pos

            # Try to get prediction from recent log entries
            prediction, latency = extract_prediction(events)

            if prediction is None:
                # Maybe no new events — try reading last few from full log
                _, all_events = read_log_lines(max(0, log_pos - 20))
                prediction, latency = extract_prediction(all_events)
                if prediction is None:
                    print("  (no recent recognition found in log — you may not have drawn)")
                    continue

            top1_char, top1_conf = prediction[0] if prediction else ("?", 0)
            top5_str = "  ".join(f"'{c}'({s:.2f})" for c, s in prediction[:5])

            print(f"\n  PP-OCRv6: top-1='{top1_char}'({top1_conf:.4f})")
            print(f"  top-5: {top5_str}")

            # Ask user for feedback
            while True:
                feedback = input(
                    f"  Correct? [ENTER=yes / type correct char / 's'=skip]: "
                ).strip().lower()
                if feedback == "s":
                    print("  Skipped!")
                    break
                if feedback == "":
                    corrected_gt = ch
                else:
                    corrected_gt = feedback

                correct_top1 = prediction[0][0] == corrected_gt if prediction else False
                top5_chars = [c for c, _ in prediction[:5]] if prediction else []
                correct_top5 = corrected_gt in top5_chars

                sample = {
                    "ground_truth": corrected_gt,
                    "ppocr_v6": {
                        "top5": [(c, round(s, 4)) for c, s in (prediction or [])[:5]],
                        "top24": [(c, round(s, 4)) for c, s in (prediction or [])[:24]],
                        "correct_top1": correct_top1,
                        "correct_top5": correct_top5,
                        "confidence_top1": round(prediction[0][1], 4) if prediction else 0,
                        "inference_latency_ms": round(latency, 2) if latency else 0,
                    },
                    "pipeline_stats": {
                        "num_strokes": 0,
                        "total_points": 0,
                    },
                }
                samples.append(sample)
                tick = "✓" if correct_top1 else "✗"
                print(f"  → saved ({tick} top-1). Total: {len(samples)}")
                break

            # Tell user to clear GTK window
            print("  ▶ Press ESC in the GTK window to clear, then press ENTER")
            input("  [ENTER when cleared]: ")

    except KeyboardInterrupt:
        print("\n\n  Ctrl+C — saving...")
    finally:
        dataset["chars_collected"] = sorted(set(s["ground_truth"] for s in samples))
        dataset["samples"] = samples
        dataset["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        save_dataset(dataset)

    print(f"\n  Done! {len(samples)} samples collected.")
    print(f"  Dataset saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    print("=" * 56)
    print("  PP-OCRv6 Handwriting Data Collection (GTK UI)")
    print("=" * 56)
    print()
    print("  The GTK writing window should already be visible.")
    print("  If not, run in another terminal:")
    print(f"    python3 {ENGINE_PATH} --test")
    print()
    run_collection()
