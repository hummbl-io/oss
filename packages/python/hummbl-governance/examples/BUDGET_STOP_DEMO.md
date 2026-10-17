# Four tasks. One budget. The fifth never runs.

This offline example connects the existing `CostGovernor` to a cooperative
runner. Four synthetic tasks each record 0.25 DEMO units. Before task five,
the governor returns `DENY` at the 1.00 hard cap, and the runner stops.
`WARN` remains advisory in this example.

![Budget stop: ALLOW, WARN, then task five denied](https://github.com/hummbl-io/oss/releases/download/demo-budget-stop-2026-10-07/budget-stop-preview.gif)

[Watch the 56-second captioned video](https://github.com/hummbl-io/oss/releases/download/demo-budget-stop-2026-10-07/budget-stop-1080p.mp4)
or read the [transcript](budget-stop-media/transcript.txt).
This is a captioned playback of captured demo output, not a live terminal recording.

## Run it

Use Python 3.11 or newer in a checkout of this repository. From the repository root:

```sh
cd packages/python/hummbl-governance
python -m examples.budget_stop_demo --output budget-demo.json
```

No API key, model, network request, installation or real payment is needed.
The optional JSON filename must not already exist; omit `--output` to rerun
without writing a file. The database is in memory.

Expected decisions are `ALLOW, ALLOW, WARN, WARN, DENY`. The terminal shows
four completed tasks, task five not executed, and 1.00 DEMO units recorded.
The JSON includes these events and the example's limitations.

From the same package directory, run the regression tests:

```sh
python -m pytest tests/test_budget_stop_demo.py tests/test_cost_governor.py -q
```

## What this demonstrates

The runner checks before invoking each task and obeys the returned decision.
The regression test supplies a spy executor and verifies that only tasks
one through four reach it. The library reports decisions; it does not forcibly
stop a process or impose a sandbox.

The governor accounts for reported usage after execution. This fixed-cost,
sequential scenario reaches the cap exactly. It does **not** reserve the next
task's cost, prevent an expensive task from overshooting, coordinate concurrent
reservations, or reconcile provider billing. Those require additional controls.

The JSON is an **unsigned local run summary**. It is not a cryptographically
authenticated receipt, a standard receipt format, or evidence of real spending.

## Rebuild the video

The optional presentation tool needs Pillow 10.1 or newer and an `ffmpeg` executable on PATH;
these are not dependencies of the runnable demo or governance library.
Install Pillow in your chosen development environment, then run:

```sh
python tools/render_budget_video.py --output budget-video
```

Use a new output directory. The tool executes the demo, checks the recorded
decisions before rendering, and writes a 1080p H.264 MP4, a short GIF preview,
SRT captions, transcript, captured JSON and terminal text, and content hashes.
The video is silent with visible captions. Font availability can change rendered
pixels; the synthetic run result should be the same. Pillow's
[sized fallback font](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.load_default)
requires version 10.1 or newer; this video was rendered with Pillow 12.3.0.

The [media manifest](budget-stop-media/manifest.json) records the packaged bytes.
The MP4 and GIF are distributed as demo prerelease assets; the text and source
are in this checkout. Download the two assets alongside the manifest to verify
all media hashes locally. The demo prerelease is not a Python package release.
Its `source_files` are the demo and renderer code. In `files`, `run.json` and
`terminal.txt` are captured inputs; the MP4, GIF, captions and transcript are
presentation outputs. Hashes detect byte changes; they do not authenticate origin.

## Share a reproduction

Run the example, inspect `budget-demo.json`, and open an issue in
[hummbl-io/oss](https://github.com/hummbl-io/oss/issues) with the repository commit,
Python version, observed result and a minimal reproduction. Use synthetic data.
