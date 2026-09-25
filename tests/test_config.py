from pathlib import Path

import pytest
import yaml

from vidlib.config import ConfigError, resolve

EXAMPLE = Path(__file__).resolve().parents[1] / "video.config.example.yaml"
KEYS = {"CARTESIA_API_KEY": "x", "PEXELS_API_KEY": "x"}


def example() -> dict:
    return yaml.safe_load(EXAMPLE.read_text())


def problems(raw: dict, kind: str = "social", env: dict | None = None) -> list[str]:
    with pytest.raises(ConfigError) as err:
        resolve(raw, kind, EXAMPLE.parent, KEYS if env is None else env)
    return err.value.problems


def test_example_config_resolves():
    cfg = resolve(example(), "social", EXAMPLE.parent, KEYS)
    assert cfg["format"]["width"] == 1080 and cfg["format"]["height"] == 1920
    assert cfg["voice"]["provider"] == "cartesia"
    assert cfg["music"]["moods"] == []


def test_missing_keys_are_named():
    found = problems(example(), env={})
    assert any("CARTESIA_API_KEY" in p for p in found)
    assert any("PEXELS_API_KEY" in p for p in found)


@pytest.mark.parametrize("name", ["youtube", "square"])
def test_known_but_unbuilt_formats_fail_clearly(name):
    raw = example() | {"format": name}
    assert any("not supported yet" in p for p in problems(raw))


def test_bare_aspect_is_not_a_format():
    raw = example() | {"format": "9:16"}
    assert any("unknown format" in p for p in problems(raw))


def test_length_must_fit_the_format_ceiling():
    raw = example() | {"length_s": {"min": 30, "max": 400}}
    assert any("ceiling" in p for p in problems(raw))


def test_avatar_is_off_by_default_and_refused_when_enabled():
    raw = example()
    raw["kinds"]["ugc"]["avatar"]["enabled"] = True
    assert any("avatar" in p for p in problems(raw))


def test_unbuilt_kind_is_refused():
    assert any("not supported yet" in p for p in problems(example(), kind="product"))
