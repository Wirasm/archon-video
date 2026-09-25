# archon-video

An [Archon](https://github.com/coleam00/Archon) workflow pack that turns a topic into an edited vertical short.

You give it a topic. It writes five openings and has a judge compare them in pairs, writes three full scripts from the best three, and stops so you can pick one. After that it runs on its own: narration with word timings, a beat plan anchored to those words, stock footage that an agent picks by looking at contact sheets, an ffmpeg render with brand-styled captions and loudness-normalised audio, measured QC, and a stored bundle with the post copy.

It does not publish anything.

## Status

Early. This version makes one kind of video (`social`) from stock footage only, in the 9:16 formats. Product, marketing and UGC kinds, other voice providers, motion-graphics beats, AI video, the vision QC retry loop and the review playbook come in later versions. Config values for those exist so your file does not change shape, but they fail at preflight with "not supported yet".

## Requirements

- Archon with workflow-pack support (`archon plugin install` for workflow packs).
- `ffmpeg` and `ffprobe`, built with libass (Homebrew's `ffmpeg` is).
- [`uv`](https://docs.astral.sh/uv/). Script nodes run on it and install their own Python packages.
- An Archon agent provider. The vision nodes (picking footage from contact sheets) pin `provider: claude` because they must open images.

## Install

```bash
archon plugin install Wirasm/archon-video
archon workflow list        # shows Wirasm/archon-video:make
```

Update with `archon plugin update Wirasm/archon-video`. To change the pack for one project, `archon plugin copy Wirasm/archon-video` writes an editable copy into `.archon/workflows/archon-video/`.

## Keys

Keys go in Archon's env file, `~/.archon/.env` (or `$ARCHON_HOME/.env`), never in the config:

```bash
CARTESIA_API_KEY=...   # narration with word timings. Commercial use needs Cartesia's Pro plan or above.
PEXELS_API_KEY=...     # stock footage. Free: https://www.pexels.com/api/
```

Preflight checks that the keys your config needs are set and fails before any spend if one is missing.

## Config

Copy [`video.config.example.yaml`](video.config.example.yaml) to your project as `video.config.yaml` and edit it. The parts that matter most:

- **`brand.tokens`** is the main creative lever. Colours, fonts, caption style, the look you want from footage: every agent that writes copy or picks visuals receives the whole block. Add any keys you like. The renderer reads `colors.text`, `colors.accent`, `colors.outline`, `fonts.captions` (a `family`, and optionally a font `file`) and `captions.uppercase`.
- **`format`** is a named output format: `shorts`, `reels` or `tiktok` (all 1080x1920, 9:16). Each format sets the resolution, the caption safe zone and the longest allowed duration. `youtube` (16:9) and `square` (1:1) are known but not supported yet.
- **`voice`** picks the voice. Cartesia is the default and the only provider in this version.
- **`music.dir`** is optional: a folder of mood folders (`music/calm/*.mp3`, `music/upbeat/*.mp3`). The beat planner picks a mood; the renderer picks the least recently used track in it and ducks it under the voice.
- **`output.dir`** is where finished videos land. By default they go to Archon's state folder for the project, `~/.archon/workspaces/<owner>/<project>/state/video/videos/<run-id>/`, with a `latest` link to the newest one.

Relative paths in the config resolve from the config file's folder.

## Make a video

```bash
archon workflow run Wirasm/archon-video:make --input topic="Why cities feel lonelier than small towns"
```

The run stops at `pick-gate` and shows the three scripts with the judge's win table. Approve with a comment that says which one you want and any edits, in plain words:

```bash
archon workflow approve <run-id> "Script 2, but cut the last sentence"
```

An empty comment takes the judge's top pick unchanged. Reject to cancel the run.

Each stored video folder holds `video.mp4`, `captions.srt`, `copy.json` (titles, captions and tags per platform), `script.json`, `edl.json`, `qc.json` and `manifest.json` (config digest, voice provider and model, and where every clip came from).

## Cost

A stock-only video costs about $0.02-0.05 of Cartesia credit, and Pexels is free. The agent calls run on your Archon provider: roughly 30 calls per video, a few of them with images.

## Develop

```bash
uv run --with pytest --with pyyaml pytest tests -q
```

## Licence

MIT. Footage comes from Pexels under the [Pexels licence](https://www.pexels.com/license/); each stored video records its sources in `manifest.json`.
