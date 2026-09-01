from __future__ import annotations

import hashlib
from pathlib import Path

from sci_ai_verifier.models import SkillDocument


MAX_SKILL_BYTES = 256 * 1024


class SkillInputError(ValueError):
    """The submitted skill cannot be read safely by this prototype."""


def resolve_skill_file(skill_path: str | Path) -> Path:
    path = Path(skill_path).expanduser()
    if not path.exists():
        raise SkillInputError(f"Skill path does not exist: {path}")

    if path.is_dir():
        path = path / "SKILL.md"
        if not path.is_file():
            raise SkillInputError(
                f"Skill directory must contain a top-level SKILL.md file: {path.parent}"
            )

    if not path.is_file():
        raise SkillInputError(f"Skill path is not a regular file: {path}")
    return path.resolve()


def load_skill(skill_path: str | Path) -> SkillDocument:
    path = resolve_skill_file(skill_path)
    raw = path.read_bytes()
    if len(raw) > MAX_SKILL_BYTES:
        raise SkillInputError(
            f"Skill file is {len(raw)} bytes; the prototype limit is {MAX_SKILL_BYTES} bytes."
        )

    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SkillInputError(f"Skill file must be UTF-8 text: {path}") from exc

    if not content.strip():
        raise SkillInputError(f"Skill file is empty: {path}")

    return SkillDocument(
        path=str(path),
        name=path.name,
        content=content,
        sha256=hashlib.sha256(raw).hexdigest(),
    )

