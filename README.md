# archon-video

An [Archon](https://github.com/coleam00/Archon) workflow pack in which agents write, direct and edit a short video from your brief.

You describe the video in your own words: the topic, who it is for, how it should feel. The pack writes five openings, has a judge compare them in pairs, writes three full scripts from the best three, and stops so you can pick one. Then a small team of agents makes the video. A director writes the treatment: structure, rhythm, look, text on screen, motion, sound. Footage scouts search stock libraries and pick shots by looking at contact sheets. An editor builds the whole edit as a [HyperFrames](https://github.com/heygen-com/hyperframes) composition and checks it with snapshots. The composition is rendered exactly as written; code only masters loudness to the format's target, measures the result and stores it.

No edit decision is made in code. A calm explainer and a hype teaser come out edited differently because the brief is different.

It does not publish anything.

## Status

Early. Footage comes from Pexels stock, in the 9:16 formats, with any of four voices. Planned next: a critic that watches rough cuts and sends notes back to the editor, a rough-cut gate, motion-design and sound specialists working in parallel, your own footage and reference videos as inputs, and AI video.

## Requirements

- Archon with workflow-pack support (`archon plugin install` for workflow packs).
- `ffmpeg` and `ffprobe`.
- Node 22 or newer (`npx` runs the pinned HyperFrames CLI, which downloads its own Chrome on first use).
- [`uv`](https://docs.astral.sh/uv/). Script nodes run on it and install their own Python packages.
- An Archon agent provider. The footage picker pins `provider: claude` because it must open images; the director and editor use the `large` tier.

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

Copy [`video.config.example.yaml`](video.config.example.yaml) to your project as `video.config.yaml`. It holds design tokens and sources only, never editing choices:

- **`brand`**: name, colours, fonts (give a font `file` to use it in the video), logo, look, voice and tone, audience, `constraints` (plain-language musts and must-nots) and optional `facts`. Every agent receives the whole block as guidance to interpret, not a template.
- **`voice`**: `cartesia` (default), `elevenlabs`, `deepgram`, or `kokoro` (Kokoro-82M, free, runs locally; its 350 MB model downloads once to `~/.cache/archon-video/`). Cartesia and ElevenLabs return word timings with the audio. For Deepgram and Kokoro, or any provider with `timings: align`, a local forced aligner (wav2vec2 through torchaudio) times the script against the narration; the first aligned run installs torch, about 1 GB.
- **`format`**: a named output format, `shorts`, `reels` or `tiktok` (all 1080x1920, 9:16), with its resolution, safe zone and longest allowed duration. `youtube` (16:9) and `square` (1:1) are known but not supported yet. `length_s` sets the narration length.
- **`music.dir`**: an optional library of tracks. The director and editor choose by file name and length, so name files and folders descriptively.
- **`output.dir`**: where finished videos land. By default they go to Archon's state folder for the project, `~/.archon/workspaces/<owner>/<project>/state/video/videos/<run-id>/`, with a `latest` link to the newest one.

Relative paths in the config resolve from the config file's folder.

## Make a video

```bash
archon workflow run Wirasm/archon-video:make \
  --input brief="A calm, patient explainer on why the sea is salty, for curious adults. Slow, unhurried, lots of water."
```

The run stops at `pick-gate` and shows the three scripts with the judge's win table. Approve with a comment that says which one you want and any edits, in plain words:

```bash
archon workflow approve <run-id> "Script 2, but cut the last sentence"
```

An empty comment takes the judge's top pick unchanged. Reject to cancel the run.

After that: narration and word timings, the director's treatment and footage needs, one scout per need, then the editor writes `edit/index.html` and checks it with `hyperframes lint`, `check` and `snapshot`. The render takes several minutes; a footage-heavy 45 s video takes about ten on an Apple Silicon Mac.

Each stored video folder holds `video.mp4`, `captions.srt` (an accessibility sidecar that follows the narration), `copy.json` (titles, captions and tags per platform), `script.json`, the composition under `edit/`, the team's notes under `room/` (treatment, footage needs, scout picks and contact sheets), review sheets under `frames/`, `qc.json`, `narration.wav`, `words.json`, the resolved `config.json` and `manifest.json` (brief, config digest, voice, render time, editor's summary, and where every clip came from). QC fails the run only on format or loudness specs; silence, still frames and shots that look like a recent video's are recorded as flags.

## Review and the playbook

```bash
archon workflow run Wirasm/archon-video:review                      # newest video not yet reviewed
archon workflow run Wirasm/archon-video:review --input video=<run-id>
```

A reviewer agent looks at the stored video's frames, brief, script, treatment and QC, gives a verdict, and proposes one change to the playbook: add a lesson, revise or retire one by id, or nothing. The run stops at a gate. Approve (your comment is kept with the change) to append it to `playbook.jsonl` in the project's state folder; reject to leave the playbook as it is.

Lessons are numbered (R1, R2, ...), each with its evidence. Every later `make` run gives the active lessons to its agents as evidence to weigh, not rules, and records the playbook version it used in the video's manifest.

## Cost

Pexels is free and Cartesia narration costs about $0.03 per video. The agent calls (about 40, several with images, and a long editor session) run on your Archon provider; on a Claude subscription they use quota rather than money.

## Develop

```bash
uv run --with pytest --with pyyaml --with requests --with pillow pytest tests -q
```

## Licence

MIT. Footage comes from Pexels under the [Pexels licence](https://www.pexels.com/license/); each stored video records its sources in `manifest.json`.
