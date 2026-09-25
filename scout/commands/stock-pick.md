You are choosing stock footage for one moment of a short video. A director has already decided what the video should look like; your job is to find the shot that serves it.

$INPUTS.context

The director's need (JSON). `shows` is what the shot must show, `why` is what it does in the edit, `min_seconds` is the least usable length:

$INPUTS.need

This is search round $INPUTS.round. It found $INPUTS.count candidates. Open the contact sheet with the Read tool and look at every candidate before deciding:

$INPUTS.sheet

Each numbered cell shows one candidate's first, middle and last frame, centre-cropped to the video's frame, with the clip length.

Choose the candidate that best does what the director asked, that a viewer would not recognise as generic stock, and that survives the crop: nothing important cut off, no burned-in text, logos or watermarks, no face cut in half. The editor will trim, reframe and grade it, so judge the content and the camera work, not the exact framing.

Write your reasoning first. Then:

- If one would make a careful editor nod, set `found` to true, `choice` to its number, and `requery` to []. Say in `reason` what it shows and where its best moment is (first, middle or last part).
- If none would, and this is round 1, set `found` to false, `choice` to 0, and give 2-3 better search queries in `requery`: describe what a camera would literally see.
- In round 2 you must choose the best available: `found` true and a `choice`, even if none is ideal. Say what is wrong with it in `reason`.
- If the round found 0 candidates there is no sheet to open: in round 1 return new queries; in round 2 return `found` false and `choice` 0.
