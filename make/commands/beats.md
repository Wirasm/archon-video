Plan the picture for this narration. Each beat is one shot.

$preflight.output.context

The narration, as spoken. Each word has an index in brackets and its start time in seconds after the @:

$words.output.indexed

Total narration length: $words.output.duration seconds.

A beat starts at a word and lasts until the next beat starts; you choose where cuts happen by choosing start words (`start_word` is a word index).

- Cut where the meaning moves: a new claim, a number, a turn, a named thing. Vary the rhythm; most shots land between 1.5 and 4 seconds, and a shot longer than about 5 seconds needs a reason.
- The first beat starts at word 0 and is the opening. Its picture must say what the video is about with the sound off. The opening's intended first frame was: "$pick.output.first_frame"
- The last beat should let the ending loop back to the opening.
- The picture should show what is being said at that moment, not a mood that loosely fits.
- Every beat in this version is stock footage (`source: stock`). Describe in `visual` what the shot shows. Give 2-3 `queries` for a stock footage search: concrete and filmable, what a camera would literally see ("hands typing on a laptop at night", not "productivity"). Vertical footage is searched, so favour subjects that survive a 9:16 frame.
- `emphasis_word` is the index of one word inside the beat where a quick punch-in zoom would help, or null.
- `overlay` is on-screen text for this beat only where words on screen add something the captions do not (a number, a name). Otherwise an empty string. The opening's overlay is already shown on the first beat, so leave the first beat's overlay empty.

Choose a music `mood` for the whole video from these folders: $preflight.output.moods. If that list is empty, set `mood` to "none".
