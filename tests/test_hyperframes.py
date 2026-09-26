from pathlib import Path

import yaml

from vidlib.hyperframes import missing_skills, skill_roots

EDITOR_SKILLS = next(
    n["skills"]
    for n in yaml.safe_load((Path(__file__).resolve().parents[1] / "make/make.yaml").read_text())["nodes"]
    if n["id"] == "editor"
)


def install(root: Path, name: str) -> None:
    (root / name).mkdir(parents=True)
    (root / name / "SKILL.md").write_text("---\nname: x\n---\n")


def test_every_editor_skill_must_be_installed_somewhere(tmp_path):
    project, home = tmp_path / "project", tmp_path / "home"
    roots = skill_roots(project, home)
    assert missing_skills(EDITOR_SKILLS, roots) == EDITOR_SKILLS

    # A Claude user install covers most; a Codex-only install covers the last one.
    for name in EDITOR_SKILLS[:-1]:
        install(home / ".claude/skills", name)
    assert missing_skills(EDITOR_SKILLS, roots) == EDITOR_SKILLS[-1:]
    install(home / ".codex/skills", EDITOR_SKILLS[-1])
    assert missing_skills(EDITOR_SKILLS, roots) == []


def test_a_folder_without_skill_md_is_not_an_install(tmp_path):
    (tmp_path / "home/.claude/skills/hyperframes-core").mkdir(parents=True)
    assert missing_skills(["hyperframes-core"], skill_roots(tmp_path / "project", tmp_path / "home")) == ["hyperframes-core"]
