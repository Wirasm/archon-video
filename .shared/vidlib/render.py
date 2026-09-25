"""EDL + clips + narration -> the finished video.

Cuts come from edl.json (already on word starts), rounded to frames so the
segments add up exactly to the video length. Dimensions come from the format.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import media

DRIFT = 0.04  # slow push-in over a whole shot, so no stock shot sits static
PUNCH = 0.10  # extra zoom at the emphasis word
PUNCH_S = 0.25
MUSIC_GAIN = 0.35
ENCODE = [
    "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
    "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M", "-g", "60", "-bf", "2",
    "-c:a", "aac", "-ar", "48000", "-b:a", "192k", "-movflags", "+faststart",
]


def frame_spans(beats: list[dict], fps: int) -> list[tuple[int, int]]:
    """(first frame, frame count) per beat; counts sum to the video's frames."""
    bounds = [round(b["start"] * fps) for b in beats] + [round(beats[-1]["end"] * fps)]
    return [(bounds[i], bounds[i + 1] - bounds[i]) for i in range(len(beats))]


def render_segment(beat: dict, clip: Path, frames: int, fmt: dict, dest: Path) -> None:
    w, h, fps = fmt["width"], fmt["height"], fmt["fps"]
    seconds = frames / fps
    clip_len = media.duration(clip)
    loop: list[str] = []
    if clip_len >= seconds + 0.1:
        # Stock: use the middle of the clip, where the shot is usually settled.
        offset = (clip_len - seconds) / 2
    else:
        offset = 0.0
        loop = ["-stream_loop", "-1"]
    zoom = f"1+{DRIFT}*t/{seconds:.3f}"
    if beat.get("emphasis_t") is not None:
        te = beat["emphasis_t"]
        zoom += f"+if(gte(t,{te}),{PUNCH}*min(1,(t-{te})/{PUNCH_S}),0)"
    vf = (
        f"fps={fps},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
        f"scale=w='trunc({w}*({zoom})/2)*2':h=-2:eval=frame:flags=bicubic,crop={w}:{h},"
        "setsar=1,format=yuv420p"
    )
    media.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *loop, "-ss", f"{offset:.3f}", "-i", str(clip),
        "-vf", vf, "-frames:v", str(frames), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14",
        str(dest),
    ])


def pick_music(music_dir: str | None, mood: str | None, library: Path) -> Path | None:
    """The least recently used track in the mood folder."""
    if not music_dir or not mood:
        return None
    folder = Path(music_dir) / mood
    tracks = sorted(p for p in folder.iterdir() if p.suffix.lower() in {".mp3", ".wav", ".m4a"})
    if not tracks:
        return None
    last_used: dict[str, int] = {}
    if library.exists():
        for n, line in enumerate(library.read_text().splitlines()):
            if line.strip():
                track = json.loads(line).get("music_track")
                if track:
                    last_used[track] = n
    return min(tracks, key=lambda p: (last_used.get(str(p), -1), p.name))


def mix_audio(narration: Path, total: float, music: Path | None, duck: bool, work: Path, dest: Path) -> dict:
    raw = work / "mix-raw.wav"
    if music:
        voice = f"[0:a]aresample=48000,apad,atrim=0:{total:.3f},asplit=2[v][key]"
        bed = f"[1:a]aresample=48000,volume={MUSIC_GAIN},atrim=0:{total:.3f}[bed]"
        if duck:
            duck_chain = "[bed][key]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=300[ducked]"
        else:
            duck_chain = "[bed]anull[ducked];[key]anullsink"
        graph = f"{voice};{bed};{duck_chain};[v][ducked]amix=inputs=2:duration=first:normalize=0[out]"
        inputs = ["-i", str(narration), "-stream_loop", "-1", "-i", str(music)]
    else:
        graph = f"[0:a]aresample=48000,apad,atrim=0:{total:.3f}[out]"
        inputs = ["-i", str(narration)]
    media.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
               "-filter_complex", graph, "-map", "[out]", "-ac", "2", str(raw)])
    measured = media.loudnorm_two_pass(raw, dest)
    raw.unlink()
    return measured


def final(video: Path, audio: Path, ass: Path, fonts_dir: Path | None, fps: int, total: float, dest: Path) -> None:
    # ass= takes a path relative to cwd, so run in the captions' folder and avoid escaping.
    ass_filter = f"ass={ass.name}" + (f":fontsdir={fonts_dir}" if fonts_dir else "")
    media.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video), "-i", str(audio),
         "-vf", ass_filter, "-map", "0:v", "-map", "1:a", "-r", str(fps), "-t", f"{total:.3f}",
         *ENCODE, str(dest)],
        cwd=ass.parent,
    )
