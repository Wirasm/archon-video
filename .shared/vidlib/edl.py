"""Beat plan (word indices) -> edit decision list (seconds).

The planner chooses cuts by word; this module turns them into times. A beat
ends where the next one starts, so gaps and overlaps cannot exist.
"""

from __future__ import annotations

from .words import Word

TAIL_S = 0.45  # breathing room after the last word


class PlanError(ValueError):
    pass


def build(plan_beats: list[dict], words: list[Word], duration: float, fps: int) -> list[dict]:
    n = len(words)
    bad = [b["start_word"] for b in plan_beats if not (0 <= b["start_word"] < n)]
    if bad:
        raise PlanError(f"start_word out of range 0..{n - 1}: {bad}")
    if not plan_beats:
        raise PlanError("the plan has no beats")

    beats = sorted(plan_beats, key=lambda b: b["start_word"])
    beats[0] = beats[0] | {"start_word": 0}
    deduped: list[dict] = []
    for b in beats:
        start = 0.0 if b["start_word"] == 0 else words[b["start_word"]].start
        # Two start words inside the same frame are one cut; keep the first.
        if deduped and round(start * fps) <= round(deduped[-1]["start"] * fps):
            continue
        deduped.append(b | {"start": start})

    end_of_video = duration + TAIL_S
    out = []
    for i, b in enumerate(deduped):
        end = deduped[i + 1]["start"] if i + 1 < len(deduped) else end_of_video
        last_word = deduped[i + 1]["start_word"] if i + 1 < len(deduped) else n
        emphasis = b.get("emphasis_word")
        emphasis_t = None
        if isinstance(emphasis, int) and b["start_word"] <= emphasis < last_word and emphasis > 0:
            emphasis_t = round(words[emphasis].start - b["start"], 3)
        out.append(
            {
                "id": f"b{i + 1:02d}",
                "index": i,
                "source": b.get("source", "stock"),
                "start_word": b["start_word"],
                "start": round(b["start"], 3),
                "end": round(end, 3),
                "duration": round(end - b["start"], 3),
                "span": " ".join(w.text for w in words[b["start_word"]:last_word]),
                "visual": b.get("visual", ""),
                "queries": b.get("queries", []),
                "emphasis_t": emphasis_t,
                "overlay": b.get("overlay", "") if i > 0 else "",
            }
        )
    for i, b in enumerate(out):
        b["neighbours"] = {
            "previous": out[i - 1]["visual"] if i > 0 else None,
            "next": out[i + 1]["visual"] if i + 1 < len(out) else None,
        }
    return out


def table(beats: list[dict]) -> str:
    lines = ["| beat | start | dur | words | visual |", "|---|---|---|---|---|"]
    lines += [f"| {b['id']} | {b['start']:.2f} | {b['duration']:.2f} | {b['span']} | {b['visual']} |" for b in beats]
    return "\n".join(lines)
