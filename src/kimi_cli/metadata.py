import json
from pathlib import Path

from pydantic import BaseModel, Field

from kimi_cli.config import get_share_dir


class Session(BaseModel):
    """Session information."""

    name: str
    work_dir: str | None = None


class Metadata(BaseModel):
    """Kimi metadata structure."""

    sessions: list[Session] = Field(default_factory=list, description="Session list")


def _get_metadata_file() -> Path:
    """Get metadata file path."""
    return get_share_dir() / "kimi.json"


def load_metadata() -> Metadata:
    """Load metadata."""
    metadata_file = _get_metadata_file()
    if not metadata_file.exists():
        return Metadata()

    try:
        with open(metadata_file, encoding="utf-8") as f:
            data = json.load(f)
        return Metadata(**data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return Metadata()


def save_metadata(metadata: Metadata) -> None:
    """Save metadata."""
    metadata_file = _get_metadata_file()
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata.model_dump(), f, indent=2, ensure_ascii=False)
