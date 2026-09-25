from pathlib import Path

import pytest
import yaml

from vidlib.config import ConfigError, resolve

EXAMPLE = Path(__file__).resolve().parents[1] / "video.config.example.yaml"
KEYS = {"CARTESIA_API_KEY": "x", "PEXELS_API_KEY": "x"}


def example() -> dict:
    return yaml.safe_load(EXAMPLE.read_text())


def problems(raw: dict, env: dict | None = None) -> list[str]:
    with pytest.raises(ConfigError) as err:
        resolve(raw, EXAMPLE.parent, KEYS if env is None else env)
    return err.value.problems


def test_example_config_resolves():
    cfg = resolve(example(), EXAMPLE.parent, KEYS)
    assert cfg["format"]["width"] == 1080 and cfg["format"]["height"] == 1920
    assert cfg["voice"]["provider"] == "cartesia"
    assert cfg["music"]["tracks"] == []


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
    raw["avatar"]["enabled"] = True
    assert any("avatar" in p for p in problems(raw))


def test_retired_edit_settings_are_refused_not_ignored():
    # Kinds and source modes used to steer the edit from config; the brief does now.
    raw = example() | {"kinds": {"social": {}}, "source": {"mode": "stock"}}
    found = problems(raw)
    assert any("`kinds`" in p for p in found) and any("`source`" in p for p in found)


@pytest.mark.parametrize("provider,key", [("elevenlabs", "ELEVENLABS_API_KEY"), ("deepgram", "DEEPGRAM_API_KEY")])
def test_each_keyed_voice_provider_names_its_key(provider, key):
    raw = example()
    raw["voice"]["provider"] = provider
    assert any(key in p for p in problems(raw))


def test_kokoro_needs_no_key():
    raw = example()
    raw["voice"] = {"provider": "kokoro", "voice_id": "af_heart", "timings": "auto"}
    assert resolve(raw, EXAMPLE.parent, {"PEXELS_API_KEY": "x"})["voice"]["provider"] == "kokoro"
