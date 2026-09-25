from pathlib import Path

import yaml

from vidlib.config import resolve
from vidlib.context import context_block, recent_openings

EXAMPLE = Path(__file__).resolve().parents[1] / "video.config.example.yaml"
CFG = resolve(yaml.safe_load(EXAMPLE.read_text()), EXAMPLE.parent, {"CARTESIA_API_KEY": "x", "PEXELS_API_KEY": "x"})
HOOKS = ["Almost nobody orders tomato juice on the ground"]


def test_shared_context_carries_brand_and_rules_but_not_past_openings():
    # Past openings in the shared block made the copy writer read this video's
    # own script as an example to avoid, and write placeholder copy instead.
    text = context_block(CFG, "A calm explainer about tides.", None, "Lessons (playbook v1): R1 ...")
    assert "Brand: Acme" in text and "R1" in text and "calm explainer about tides" in text
    assert "tomato juice" not in text and "Recent openings" not in text


def test_past_openings_are_a_separate_block_for_the_hook_writer():
    block = recent_openings(HOOKS)
    assert "do not repeat" in block and HOOKS[0] in block
    assert recent_openings([]) == "(none yet)"
