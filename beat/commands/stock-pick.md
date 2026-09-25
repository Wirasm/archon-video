You are choosing the stock shot that plays under one beat of a short vertical video.

$INPUTS.context

The beat (JSON). `span` is the narration spoken during it, `visual` is the planner's intent, `duration` is in seconds, `neighbours` are the shots before and after:

$INPUTS.beat

This is search round $INPUTS.round. It found $INPUTS.count candidates. Open the contact sheet with the Read tool and look at every candidate before deciding:

$INPUTS.sheet

Each numbered cell shows one candidate's first, middle and last frame, already centre-cropped to the video's frame, with the clip length.

Choose the candidate whose subject is the thing being said, that a viewer would not recognise as generic stock, and that survives the crop: nothing important cut off, no burned-in text, logos or watermarks, no face cut in half. Prefer footage whose light and colour sit well next to the neighbouring shots and that fits the brand's look.

Write your reasoning first. Then:

- If one would make a careful editor nod, set `found` to true, `choice` to its number, and `requery` to [].
- If none would, and this is round 1, set `found` to false, `choice` to 0, and give 2-3 better search queries in `requery`: describe what a camera would literally see.
- In round 2 you must choose the best available: `found` true and a `choice`, even if none is ideal. Say what is wrong with it in `reason`.
- If the round found 0 candidates there is no sheet to open: in round 1 return new queries; in round 2 return `found` false and `choice` 0.
