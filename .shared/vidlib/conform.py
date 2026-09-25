"""Make fetched footage seekable by the renderer.

HyperFrames seeks every clip frame by frame. Stock files with sparse keyframes
(Pexels ships some with 3-4 s between keyframes) freeze or skip in the render,
which its compiler warns about. So every clip is re-encoded once on intake:
H.264, the format's frame rate, a keyframe every second, no audio track, and no
larger than the output frame needs. Nothing about the picture is changed.
"""

from __future__ import annotations

from pathlib import Path

from . import media


def conform(src: Path, dest: Path, fmt: dict) -> float:
    fps = fmt["fps"]
    # Scale so the clip still covers the output frame, never up, never far beyond it.
    cover = f"scale='if(gt(a,{fmt['width']}/{fmt['height']}),-2,min(iw,{fmt['width']}))':'if(gt(a,{fmt['width']}/{fmt['height']}),min(ih,{fmt['height']}),-2)'"
    media.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-an",
        "-vf", f"{cover},fps={fps},format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
        "-g", str(fps), "-keyint_min", str(fps), "-sc_threshold", "0", "-movflags", "+faststart",
        str(dest),
    ])
    return media.duration(dest)
