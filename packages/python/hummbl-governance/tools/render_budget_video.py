# Copyright 2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0
"""Render a captioned playback of a real offline demo run (Pillow + ffmpeg).

Run python tools/render_budget_video.py --output NEW_DIRECTORY from the package root.
This is a presentation of captured output, not a live terminal recording.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
BG, PANEL, WHITE, MUTED = "#091321", "#121F31", "#F3F6FB", "#A7B7CB"
TEAL, AMBER, RED = "#5EE2C2", "#FFD080", "#FF8C96"


def font(size: int, mono: bool = False):
    candidates = (["C:/Windows/Fonts/consola.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
                  if mono else ["C:/Windows/Fonts/segoeui.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size=size)


def subtitle_time(seconds: int) -> str:
    return f"{seconds // 3600:02}:{seconds // 60 % 60:02}:{seconds % 60:02},000"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not shutil.which("ffmpeg"):
        parser.error("ffmpeg must be installed and available on PATH")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    package = Path(__file__).resolve().parents[1]
    run = subprocess.run(
        [sys.executable, "-m", "examples.budget_stop_demo", "--output", str(out / "run.json")],
        cwd=package, capture_output=True, text=True, encoding="utf-8", check=True,
    )
    (out / "terminal.txt").write_text(run.stdout, encoding="utf-8")
    result = json.loads((out / "run.json").read_text(encoding="utf-8"))
    # Refuse to render a success narrative if the recorded demonstration disagrees.
    if (result["completed_tasks"] != [1, 2, 3, 4] or result["blocked_task"] != 5
            or result["recorded_spend"] != 1.0
            or [e["decision"] for e in result["events"]] != ["ALLOW", "ALLOW", "WARN", "WARN", "DENY"]):
        raise RuntimeError("Captured run does not support this storyboard")
    scenes = [
        (6, "Four tasks. One budget.", "The fifth task never runs.", 0,
         "An offline demonstration of a runner obeying a budget decision."),
        (7, "Run it locally.", "Python 3.11+  /  no API keys  /  no real charges", 0,
         "From the package directory, run python -m examples.budget_stop_demo."),
        (7, "Check before each task.", "Each completed task records 0.25 DEMO units.", 2,
         "Tasks one and two are allowed. The ledger records half of the hard cap."),
        (7, "A warning is a decision.", "This runner treats WARN as advisory.", 4,
         "Tasks three and four run with warnings. Recorded usage reaches 1.00 DEMO."),
        (8, "DENY means: do not call it.", "The runner stops before task five.", 5,
         "The hard cap is reached. Task five never reaches the executor."),
        (7, "Keep the result inspectable.", "Optional JSON: events, totals and limitations.", 5,
         "The JSON is an unsigned local run summary, not an authenticated receipt."),
        (8, "Know the boundary.", "Recorded usage. Sequential runner. Fixed synthetic cost.", 5,
         "There is no reservation for future or concurrent costs, and no forced process termination."),
        (6, "Run it. Inspect it. Reproduce it.", "github.com/hummbl-io/oss", 5,
         "Open an issue with your commit, Python version and a synthetic reproduction."),
    ]
    srt, transcript, full, preview = [], [], [], []
    elapsed = 0
    for i, (duration, title, sub, count, caption) in enumerate(scenes):
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        d.text((100, 65), "HUMMBL  /  GOVERNED AGENT FLEETS", font=font(28), fill=TEAL)
        d.text((100, 126), title, font=font(69), fill=WHITE)
        d.text((100, 224), sub, font=font(35), fill=MUTED)
        d.rounded_rectangle((100, 320, 1820, 850), radius=24, fill=PANEL)
        d.text((140, 350), "$ python -m examples.budget_stop_demo", font=font(29, True), fill=WHITE)
        d.text((140, 404), "SYNTHETIC / OFFLINE / NO REAL CHARGES", font=font(26, True), fill=MUTED)
        d.text((140, 451), "CAP 1.00 DEMO       TASK COST 0.25 DEMO", font=font(28, True), fill=MUTED)
        for j, e in enumerate(result["events"][:count]):
            color = RED if e["decision"] == "DENY" else AMBER if e["decision"] == "WARN" else TEAL
            outcome = "executed" if e["executed"] else "NOT EXECUTED"
            line = f"Task {e['task']}    {e['decision']:<5}    before {e['spend_before']:.2f}    {outcome}"
            d.text((140, 513 + j * 52), line, font=font(33, True), fill=color)
        d.text((100, 900), caption, font=font(29), fill=WHITE)
        d.text((100, 980), "Captured demo output / captioned playback / unsigned local summary",
               font=font(23), fill=MUTED)
        d.rectangle((100, 1040, 1820, 1047), fill=PANEL)
        d.rectangle((100, 1040, 100 + int(1720 * (i + 1) / len(scenes)), 1047), fill=TEAL)
        filename = f"scene-{i:02}.png"
        img.save(out / filename)
        full.extend([f"file '{filename}'", f"duration {duration}"])
        preview.extend([f"file '{filename}'", "duration 1.5"])
        srt.append(f"{i+1}\n{subtitle_time(elapsed)} --> {subtitle_time(elapsed + duration)}\n{caption}\n")
        transcript.append(f"{subtitle_time(elapsed)[:8]}  {title}\n{caption}\n")
        elapsed += duration
    full.append(f"file 'scene-{len(scenes)-1:02}.png'")
    preview.append(f"file 'scene-{len(scenes)-1:02}.png'")
    (out / "video.ffconcat").write_text("\n".join(full) + "\n", encoding="utf-8")
    (out / "preview.ffconcat").write_text("\n".join(preview) + "\n", encoding="utf-8")
    (out / "captions.srt").write_text("\n".join(srt), encoding="utf-8")
    (out / "transcript.txt").write_text("\n".join(transcript), encoding="utf-8")
    common = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-n"]
    subprocess.run(common + ["-f", "concat", "-safe", "1", "-i", "video.ffconcat", "-t", str(elapsed),
                   "-vf", "fps=24,format=yuv420p", "-c:v", "libx264", "-preset", "fast", "-crf", "21",
                   "-movflags", "+faststart", "budget-stop-1080p.mp4"], cwd=out, check=True)
    subprocess.run(common + ["-f", "concat", "-safe", "1", "-i", "preview.ffconcat", "-t", "12",
                   "-vf", "fps=2,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse",
                   "-loop", "0", "budget-stop-preview.gif"], cwd=out, check=True)
    manifest = {}
    for p in sorted(out.iterdir()):
        if p.is_file():
            manifest[p.name] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"duration_seconds": elapsed, "output": str(out), "artifacts": manifest}, indent=2))


if __name__ == "__main__":
    main()
