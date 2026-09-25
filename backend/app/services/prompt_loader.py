import json
import re
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
_VERSION_PATTERN = re.compile(r"v[0-9]+")
_AGENT_PATTERN = re.compile(r"[a-z_]+")


def active_prompt_version(agent_name: str) -> str:
    _validate_agent_name(agent_name)
    data = json.loads((PROMPTS_DIR / "active.json").read_text(encoding="utf-8"))
    version = data[agent_name]
    _validate_version(version)
    return version


def load_prompt(agent_name: str, version: str) -> str:
    _validate_agent_name(agent_name)
    _validate_version(version)
    path = PROMPTS_DIR / agent_name / f"{version}.md"
    if not path.is_file():
        raise FileNotFoundError(f"prompt not found: {agent_name}/{version}.md")
    return path.read_text(encoding="utf-8")


def _validate_agent_name(agent_name: str) -> None:
    if not _AGENT_PATTERN.fullmatch(agent_name):
        raise ValueError("invalid agent name")


def _validate_version(version: str) -> None:
    if not _VERSION_PATTERN.fullmatch(version):
        raise ValueError("invalid prompt version")
