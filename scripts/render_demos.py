"""Render the program demos of the project page with the Tempo-Zero release code.

Each demo executes one program of a family, renders every simulation tick
between the first and the last sampled frame, and encodes the ticks on the
model clock, so second t of the MP4 is second t of the criteria intervals.
The canonical question and its criteria go to demos.js, which the page reads.

    python3 -I render_demos.py <release-source> <out-dir>
"""
import bisect
import json
import subprocess
import sys
from pathlib import Path

SOURCE, OUT = sys.argv[1], Path(sys.argv[2])
sys.path.insert(0, SOURCE)

from tempo_zero.games import engine  # noqa: E402
from tempo_zero.pipeline import library  # noqa: E402

FPS = 30
HEIGHT = 540
SEEDS = 16
PREFERRED = ("event_grounding", "state_interval", "event_order", "sequence_prediction",
             "path_sequence", "state_delta", "entity_extreme", "motion_rate_trend", "event_count")


def pick(family, used):
    """A verified instance whose canonical question has a timed target.

    Candidates are clips of 6 to 40 s, from level 1 or, when it has none, level 0.
    The pick takes the task used least by earlier families, then the earliest
    task of PREFERRED, then the shortest clip.
    """
    game = engine.family(family)
    for level in (1, 0):
        found = []
        for seed in range(SEEDS):
            try:
                generated = engine.generate(family, 1000 + seed, level, 1.0, option_count=4,
                                            task_index=seed % len(game.TASKS))
            except engine.ContractError:
                continue
            prepared = generated.prepared
            program = prepared.program
            fps = engine.model_fps(program, engine.video_contract(game, program), prepared.selected_ticks)
            duration = engine.clip_duration_s(prepared.selected_ticks, fps)
            criteria = library._criteria(generated, fps, duration)
            asked = library.question_criteria(criteria)
            if asked and asked[0].intervals and 6.0 <= duration <= 40.0 and len(generated.stem) <= 160:
                found.append((generated, fps, duration, criteria, asked, level))
        if found:
            def rank(item):
                task = item[4][0].task
                order = PREFERRED.index(task) if task in PREFERRED else len(PREFERRED)
                return used.get(task, 0), order, item[2]
            return min(found, key=rank)
    raise RuntimeError(f"no instance for {family}")


def tick_at(selected, fps, second):
    """Tick shown at a model second, linear between two sampled frames."""
    times = [index / fps for index in range(len(selected))]
    i = min(max(bisect.bisect_right(times, second) - 1, 0), len(selected) - 2)
    share = (second - times[i]) / (times[i + 1] - times[i])
    return round(selected[i] + share * (selected[i + 1] - selected[i]))


def criterion_row(criterion):
    return {
        "task": criterion.task,
        "role": criterion.role,
        "text": f"{', '.join(criterion.subjects)} {criterion.predicate}".strip(),
        "value": criterion.ground_truth,
        "intervals": [[round(a, 2), round(b, 2)] for a, b in criterion.intervals],
    }


def render(family, used):
    generated, fps, duration, criteria, asked, level = pick(family, used)
    prepared = generated.prepared
    game = engine.family(family)
    selected = prepared.selected_ticks
    first = game.render_frame(prepared.program, prepared.trace, selected[0]).canvas
    scale = f"scale=-2:{HEIGHT}:flags=lanczos" if first.height < HEIGHT else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
    video = OUT / f"{family}.mp4"
    encoder = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{first.width}x{first.height}", "-r", str(FPS), "-i", "-", "-vf", scale,
         "-c:v", "libx264", "-crf", "20", "-preset", "slow", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", str(video)],
        stdin=subprocess.PIPE)
    cache = {}
    for frame in range(int(duration * FPS) + 1):
        tick = tick_at(selected, fps, frame / FPS)
        if tick not in cache:
            cache = {tick: bytes(game.render_frame(prepared.program, prepared.trace, tick).canvas.pixels)}
        encoder.stdin.write(cache[tick])
    encoder.stdin.close()
    encoder.wait()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{duration * 0.4:.2f}", "-i", str(video),
                    "-frames:v", "1", "-q:v", "3", str(OUT / f"{family}.jpg")], check=True)
    target = asked[0]
    return {
        "family": family,
        "name": family.replace("_", " ").capitalize(),
        "level": level,
        "duration": round(duration, 2),
        "task": target.task,
        "stem": generated.stem,
        "options": list(generated.options.surfaces),
        "answer": generated.options.answer,
        "asked": [criterion_row(c) for c in asked],
    }


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    demos, used = [], {}
    for family in engine.FAMILIES:
        demos.append(render(family, used))
        used[demos[-1]["task"]] = used.get(demos[-1]["task"], 0) + 1
        print("done", family, flush=True)
    (OUT / "demos.js").write_text("// Generated by scripts/render_demos.py from the Tempo-Zero release code.\n"
                                  f"const DEMOS = {json.dumps(demos, separators=(',', ':'))};\n")
    for demo in demos:
        print(demo["family"], demo["task"], demo["duration"], demo["stem"])
