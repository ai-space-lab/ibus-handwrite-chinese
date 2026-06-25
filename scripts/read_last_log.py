#!/usr/bin/env python3
"""Read the most recent recognition events from the JSON Lines log.

Usage:
    python3 scripts/read_last_log.py
    python3 scripts/read_last_log.py --last 3
"""

import argparse
import json
import os
import sys


def read_events(path, n_last=1):
    """Read the last N complete log entries (each JSON line)."""
    if not os.path.exists(path):
        return []
    events = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events[-n_last:]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default="/tmp/ppocr-recognition.log")
    parser.add_argument("--last", type=int, default=3)
    args = parser.parse_args()

    events = read_events(args.log, n_last=args.last)
    if not events:
        print("No log events found. Write a character first.")
        sys.exit(1)

    for ev in events:
        etype = ev.get("event", "?")
        ts = ev.get("t", 0)
        sid = ev.get("session_id", "?")

        if etype == "preprocess":
            print(f"[{sid}] preprocess: {ev.get('num_strokes')} strokes, "
                  f"{ev.get('num_points')} pts, "
                  f"canvas={ev.get('canvas_size')}, "
                  f"resized_w={ev.get('resized_width')}")

        elif etype == "decode":
            top5 = ev.get("top5", [])
            top5_str = "  ".join(f"'{c}'({s})" for c, s in top5)
            print(f"[{sid}] decode: {top5_str}")
            print(f"  classes={ev.get('num_classes')}, steps={ev.get('time_steps')}")

        elif etype == "classify":
            print(f"[{sid}] classify: latency={ev.get('latency_ms')}ms, "
                  f"input_shape={ev.get('input_shape')}")

        else:
            print(f"[{sid}] {etype}: {json.dumps(ev, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
