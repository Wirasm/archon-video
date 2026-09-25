"""Cut, caption, mix and encode the video.

Reads  : config.json, edl.json, words.json, narration.wav, the bound `footage`
         aggregate and the picked script's `overlay`
Writes : video.mp4, captions.ass, captions.srt, render.json, segments/
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib import captions, render
from vidlib import words as wordsmod
from vidlib.config import load_resolved
from vidlib.node import artifacts_dir, emit, json_input, log, state_dir, text_input

out = artifacts_dir()
cfg = load_resolved(out)
fmt = cfg["format"]
edl = json.loads((out / "edl.json").read_text())
beats = edl["beats"]
words = wordsmod.read(out / "words.json")

footage = json_input("footage")
failed = [
    f"{beats[i]['id']}: {r.get('error', 'failed')}"
    for i, r in enumerate(footage)
    if not isinstance(r, dict) or r.get("archon_failed")
]
if failed:
    raise SystemExit("footage failed for some beats, so the video cannot be cut:\n- " + "\n- ".join(failed))
clips = {r["id"]: Path(r["clip"]) for r in footage}
missing = [b["id"] for b in beats if b["id"] not in clips]
if missing:
    raise SystemExit(f"no footage result for beats {missing}")

segments_dir = out / "segments"
segments_dir.mkdir(exist_ok=True)
spans = render.frame_spans(beats, fmt["fps"])
segment_paths = []
for beat, (_, frames) in zip(beats, spans):
    dest = segments_dir / f"{beat['id']}.mp4"
    render.render_segment(beat, clips[beat["id"]], frames, fmt, dest)
    segment_paths.append(dest)
    log(f"{beat['id']}: {frames} frames")

concat_list = segments_dir / "concat.txt"
concat_list.write_text("".join(f"file '{p.name}'\n" for p in segment_paths))
picture = out / "picture.mp4"
render.media.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
                  "-i", str(concat_list), "-c", "copy", str(picture)])

total = sum(n for _, n in spans) / fmt["fps"]
music = render.pick_music(cfg["music"]["dir"], edl.get("mood"), state_dir() / "library.jsonl")
audio = out / "mix.wav"
loudness = render.mix_audio(out / "narration.wav", total, music, cfg["music"]["duck"], out, audio)

overlays = [(0.0, beats[0]["end"], text_input("overlay", ""))]
overlays += [(b["start"], b["end"], b["overlay"]) for b in beats[1:] if b.get("overlay")]
ass = out / "captions.ass"
ass.write_text(captions.build_ass(words["words"], fmt, cfg["captions"], overlays))
(out / "captions.srt").write_text(captions.build_srt(words["words"]))

font_file = cfg["captions"]["font_file"]
video = out / "video.mp4"
render.final(picture, audio, ass, Path(font_file).parent if font_file else None, fmt["fps"], total, video)
picture.unlink()

info = {
    "video": str(video),
    "srt": str(out / "captions.srt"),
    "duration": round(total, 3),
    "music_track": str(music) if music else None,
    "mood": edl.get("mood"),
    "loudness_before": {k: loudness[k] for k in ("input_i", "input_tp", "input_lra")},
}
(out / "render.json").write_text(json.dumps(info, indent=1))
emit(info)
