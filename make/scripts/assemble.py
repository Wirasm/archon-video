"""Gather everything the editor works with into edit/ and room/.

Writes the director's treatment and needs into room/director/, contact sheets
of the fetched clips into room/scout/, copies narration, music, fonts and logo
into edit/assets/, and writes room/INDEX.md, the one shared listing of every
note. Only this script writes the index; each role writes only its own folder.
"""

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib import media, sheets
from vidlib.config import load_resolved
from vidlib.node import artifacts_dir, emit, json_input

out = artifacts_dir()
cfg = load_resolved(out)
room, edit = out / "room", out / "edit"
assets = edit / "assets"
assets.mkdir(parents=True, exist_ok=True)

director = json_input("director")
(room / "director").mkdir(parents=True, exist_ok=True)
(room / "director" / "treatment.md").write_text(director["treatment"].strip() + "\n")
(room / "director" / "needs.json").write_text(json.dumps(director["needs"], indent=1))
needs = {n["id"]: n for n in director["needs"]}

results = json_input("footage")
clips, failed = [], []
for need, r in zip(director["needs"], results):
    if isinstance(r, dict) and not r.get("archon_failed"):
        clips.append(r)
    else:
        failed.append(need["id"])
if not clips:
    raise SystemExit("no footage was fetched for any need")
(room / "scout").mkdir(parents=True, exist_ok=True)
(room / "scout" / "footage.json").write_text(json.dumps(clips, indent=1))

frames_dir = room / "scout" / "frames"
frames_dir.mkdir(exist_ok=True)
groups = []
for c in clips:
    path = edit / c["clip"]
    d = c["duration"]
    shots = [sheets.frame(path, t, frames_dir / f"{c['id']}-{k}.jpg") for k, t in enumerate((0.1, d / 2, d - 0.2))]
    groups.append((f"{c['id']}  {d:.1f}s", shots))
clip_sheets = sheets.build(groups, room / "scout", "clips")

shutil.copy2(out / "narration.wav", assets / "narration.wav")
for role, font in cfg["font_files"].items():
    (assets / "fonts").mkdir(exist_ok=True)
    shutil.copy2(font, assets / "fonts" / Path(font).name)
if cfg["logo_file"]:
    shutil.copy2(cfg["logo_file"], assets / Path(cfg["logo_file"]).name)
music = []
if cfg["music"]["dir"]:
    root = Path(cfg["music"]["dir"])
    for track in cfg["music"]["tracks"]:
        rel = Path(track).relative_to(root)
        dest = assets / "music" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(track, dest)
        music.append(f"- assets/music/{rel.as_posix()} ({media.duration(dest):.1f} s)")

listing = ["## Footage (conformed: H.264, keyframe every second, no audio)"]
for c in clips:
    n = needs.get(c["id"], {})
    listing.append(f"- {c['clip']} ({c['duration']:.1f} s): {n.get('shows', '')}. Scout: {c['reason']}")
if failed:
    listing.append(f"No footage could be found for: {', '.join(failed)}. Cover those moments another way.")
listing.append(f"\n## Narration\n- assets/narration.wav ({media.duration(assets / 'narration.wav'):.2f} s)")
listing.append("\n## Music\n" + ("\n".join(music) if music else "(no music library configured)"))
if cfg["font_files"]:
    listing.append("\n## Fonts\n" + "\n".join(f"- assets/fonts/{Path(f).name} ({role})" for role, f in cfg["font_files"].items()))
if cfg["logo_file"]:
    listing.append(f"\n## Logo\n- assets/{Path(cfg['logo_file']).name}")
assets_md = "\n".join(listing)
(edit / "ASSETS.md").write_text(assets_md + "\n")

notes = sorted(p for p in room.rglob("*.md") if p.name != "INDEX.md")
index = ["# Room index", "Every note, by the role that wrote it. Read what you need; only the author edits a note."]
index += [f"- {p.relative_to(room)}: {p.read_text().strip().splitlines()[0][:120] if p.read_text().strip() else ''}" for p in notes]
index += [f"- {p.relative_to(room)}: contact sheet of the fetched clips" for p in clip_sheets]
(room / "INDEX.md").write_text("\n".join(index) + "\n")

emit({"sheets": [str(p) for p in clip_sheets], "assets": assets_md, "failed": failed})
