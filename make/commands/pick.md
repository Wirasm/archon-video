A person was shown three narration scripts for a short video and asked which one to make. Decide what they chose and apply what they asked for.

The three scripts, in the order they were shown (script 1, 2 and 3):

$present.output.ordered

Their comment:

<comment>
$pick-gate.output
</comment>

- If the comment names or clearly describes one script, use it. If it is empty or only approves ("ok", "looks good") without choosing, use script 1, the judge's top pick.
- If it asks for edits (cut a line, change a word, a different ending, a tone change), apply exactly those edits and nothing else. Keep the script's voice. Keep it plain spoken English with numbers written as words, since a text-to-speech voice reads every character.
- If it asks for something that mixes scripts, do that.

Return the final script. `choice` is the number (1, 2 or 3) of the script you started from, and `changes` says in one sentence what you changed, or "none".
