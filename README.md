# archon-video

An [Archon](https://github.com/coleam00/Archon) workflow pack that turns a topic into an edited vertical short.

You give it a topic. It writes five openings and has a judge compare them in pairs, writes three full scripts from the best three, and stops so you can pick one. After that it runs on its own: narration with word timings, a beat plan anchored to those words, stock footage that an agent picks by looking at contact sheets, an ffmpeg render with brand-styled captions and loudness-normalised audio, measured and vision QC with one retry for bad beats, and a stored bundle with the post copy. A separate `review` run turns a critique you approve into a numbered house rule that every later video follows.

It does not publish anything.

## Status

Early. This version makes one kind of video (`social`) from stock footage only, in the 9:16 formats, with any of four voices. Product, marketing and UGC kinds, motion-graphics beats and AI video come in later versions. Config values for those exist so your file does not change shape, but they fail at preflight with "not supported yet".

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
PEXELS_API_KEY=...       # stock footage. Free: https://www.pexels.com/api/
CARTESIA_API_KEY=...     # voice.provider: cartesia (default). Commercial use needs Cartesia's Pro plan or above.
ELEVENLABS_API_KEY=...   # voice.provider: elevenlabs. Commercial use needs a paid plan.
DEEPGRAM_API_KEY=...     # voice.provider: deepgram
```

Only the keys for the providers your config names are needed; `kokoro` needs none. Preflight checks that they are set and fails before any spend if one is missing.

## Config

Copy [`video.config.example.yaml`](video.config.example.yaml) to your project as `video.config.yaml` and edit it. The parts that matter most:

- **`brand.tokens`** is the main creative lever. Colours, fonts, caption style, the look you want from footage: every agent that writes copy or picks visuals receives the whole block. Add any keys you like. The renderer reads `colors.text`, `colors.accent`, `colors.outline`, `fonts.captions` (a `family`, and optionally a font `file`) and `captions.uppercase`.
- **`format`** is a named output format: `shorts`, `reels` or `tiktok` (all 1080x1920, 9:16). Each format sets the resolution, the caption safe zone and the longest allowed duration. `youtube` (16:9) and `square` (1:1) are known but not supported yet.
- **`voice`** picks the voice: `cartesia` (default), `elevenlabs`, `deepgram`, or `kokoro` (Kokoro-82M, free, runs locally; its 350 MB model downloads once to `~/.cache/archon-video/`). Cartesia and ElevenLabs return word timings with the audio. For Deepgram and Kokoro, or any provider with `timings: align`, a local forced aligner (wav2vec2 through torchaudio) times the script against the narration; the first aligned run installs torch, about 1 GB. Every provider ends in the same `words.json`, so captions and cuts never depend on which voice you use.
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

Each stored video folder holds `video.mp4`, `captions.srt`, `copy.json` (titles, captions and tags per platform), `script.json`, `edl.json` (the cut list), `qc.json`, `narration.wav`, `words.json`, the resolved `config.json` and `manifest.json` (config digest, voice provider and model, music track, and where every clip came from). QC flags that did not fail the run, such as the same stock clip used in two beats, are listed in `qc.json` and `manifest.json`.

### What happens after the render

QC measures the cut (geometry, loudness, dead air, black or frozen frames, cut sync) and checks it for repeated shots: the same clip twice, two beats that look alike, or a shot that appeared in one of the last 20 videos. Stock clips used by those recent videos are left out of new searches. A vision check then looks at every beat's frames. Each beat it flags, and each beat QC flags for a repeat or a black or frozen picture, gets new footage once, with the reviewer's note guiding the new pick; the video is re-rendered and measured again. A beat that is still flagged ships with the flag recorded in `manifest.json`.

## Review and the playbook

```bash
archon workflow run Wirasm/archon-video:review                      # newest video not yet reviewed
archon workflow run Wirasm/archon-video:review --input video=<run-id>
```

A reviewer agent looks at the stored video's frames, script, cut list and QC, gives a verdict, and proposes one change to the playbook: add a rule, revise or retire one by id, or nothing. The run stops at a gate. Approve (your comment is kept with the change) to append it to `playbook.jsonl` in the project's state folder; reject to leave the playbook as it is.

Rules are numbered (R1, R2, ...) and scoped to one kind or to all kinds. Every later `make` run puts the active rules in its prompts and records the playbook version it used in the video's manifest.

## Cost

A stock-only video costs about $0.02-0.05 of Cartesia credit, and Pexels is free. The agent calls run on your Archon provider: roughly 30 calls per video, a few of them with images.

## Develop

```bash
uv run --with pytest --with pyyaml --with requests --with pillow pytest tests -q
```

## Licence

MIT. Footage comes from Pexels under the [Pexels licence](https://www.pexels.com/license/); each stored video records its sources in `manifest.json`.
