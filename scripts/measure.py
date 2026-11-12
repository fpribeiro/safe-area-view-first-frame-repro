#!/usr/bin/env python3
"""Open one page N times on an attached Android device and count the frames it
draws before its bars settle where its insets put them.

    python3 scripts/measure.py safe-area-view [runs]
    python3 scripts/measure.py hook [runs]

Needs adb (one device attached, or ANDROID_SERIAL set), ffmpeg and ffprobe on
PATH, and the app installed and showing its home screen. Standard library only.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time

REMOTE = "/data/local/tmp/safe-area-repro.mp4"


def adb(*args):
    return subprocess.run(["adb", *args], capture_output=True, text=True, check=True).stdout


def screen_size():
    out = adb("shell", "wm", "size")
    sizes = re.findall(r"(\d+)x(\d+)", out)
    w, h = sizes[-1]  # an override size, when set, is listed last
    return int(w), int(h)


def frame_times(path):
    out = subprocess.run(
        ["ffprobe", "-loglevel", "error", "-select_streams", "v", "-show_entries", "frame=pts_time", "-of", "json", path],
        capture_output=True, text=True, check=True).stdout
    return [float(f["pts_time"]) for f in json.loads(out)["frames"]]


def columns(path, x, h):
    """The pixel column at x of every frame, as rows of (r, g, b)."""
    # The recording's colour planes are subsampled in 2x2 blocks, so the crop is two pixels wide.
    raw = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-i", path, "-fps_mode", "passthrough",
         "-vf", f"crop=2:{h}:{x - x % 2}:0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True).stdout
    size = h * 6
    return [[tuple(raw[i + 6 * y:i + 6 * y + 3]) for y in range(h)] for i in range(0, len(raw) - size + 1, size)]


def red_top(col):
    return next((y for y, (r, g, b) in enumerate(col) if r > 200 and g < 80 and b < 80), None)


def blue_bottom(col):
    return next((y for y in range(len(col) - 1, -1, -1) if col[y][2] > 200 and col[y][0] < 80 and col[y][1] < 80), None)


def on_screen(text):
    xml = adb("shell", "uiautomator dump /data/local/tmp/repro-ui.xml >/dev/null 2>&1; "
                       "cat /data/local/tmp/repro-ui.xml; rm -f /data/local/tmp/repro-ui.xml")
    return f'text="{text}"' in xml


def run_once(page, w, h, workdir, n):
    if not on_screen("Open the SafeAreaView page"):
        raise SystemExit(f"run {n}: the app is not on its home screen")
    tap_y = h // 4 if page == "safe-area-view" else 3 * h // 4
    rec = subprocess.Popen(["adb", "shell", f"screenrecord --time-limit 3 {REMOTE}"])
    time.sleep(0.8)
    adb("shell", "input", "tap", str(w // 2), str(tap_y))
    rec.wait()
    local = os.path.join(workdir, f"{page}-{n}.mp4")
    adb("pull", REMOTE, local)
    adb("shell", "rm", "-f", REMOTE)
    times = frame_times(local)
    marks = [(red_top(c), blue_bottom(c)) for c in columns(local, w // 4, h)]
    shown = [(t, m) for t, m in zip(times, marks) if m[0] is not None]
    if not shown:
        raise SystemExit(f"run {n}: the page never appeared in the recording")
    settled = shown[-1][1]
    early = [(t, m) for t, m in shown if m != settled]
    name = "SafeAreaView page" if page == "safe-area-view" else "useSafeAreaInsets page"
    if not on_screen(name):
        raise SystemExit(f"run {n}: the {name} is not on screen after the tap")
    adb("shell", "input", "tap", str(w // 2), str(h // 2))  # the page's middle goes back
    time.sleep(1.2)
    return settled, early


def main():
    page = sys.argv[1] if len(sys.argv) > 1 else ""
    if page not in ("safe-area-view", "hook"):
        raise SystemExit(__doc__)
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    w, h = screen_size()
    with tempfile.TemporaryDirectory() as workdir:
        hit = 0
        for n in range(1, runs + 1):
            settled, early = run_once(page, w, h, workdir, n)
            hit += bool(early)
            detail = ", ".join(f"red top {m[0]}, blue bottom {m[1]} at +{t - early[0][0]:.3f}s" for t, m in early)
            print(f"run {n}: settled red top {settled[0]}, blue bottom {settled[1]}; "
                  f"{len(early)} earlier frame(s) elsewhere{': ' + detail if early else ''}")
        print(f"{page}: {hit} of {runs} openings drew a frame before the bars settled")


if __name__ == "__main__":
    main()
