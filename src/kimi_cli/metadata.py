import json
import uuid
from hashlib import md5
from pathlib import Path
from typing import NamedTuple

from pydantic import BaseModel, Field


def get_share_dir() -> Path:
    """Get the shared directory path."""
    share_dir = Path.home() / ".local" / "share" / "kimi"
    share_dir.mkdir(parents=True, exist_ok=True)
    return share_dir


def get_metadata_file() -> Path:
    return get_share_dir() / "kimi.json"


class WorkDirMeta(BaseModel):
    """Metadata for a work directory."""

    path: str
    """The full path of the work directory."""

    last_session_id: str | None = None
    """Last session ID of this work directory."""

    @property
    def sessions_dir(self) -> Path:
        path = get_share_dir() / "sessions" / md5(self.path.encode()).hexdigest()
        path.mkdir(parents=True, exist_ok=True)
        return path


class Metadata(BaseModel):
    """Kimi metadata structure."""

    work_dirs: list[WorkDirMeta] = Field(default_factory=list, description="Work directory list")


def _load_metadata() -> Metadata:
    if not get_metadata_file().exists():
        return Metadata()
    with open(get_metadata_file(), encoding="utf-8") as f:
        data = json.load(f)
        return Metadata(**data)


def _save_metadata(metadata: Metadata):
    with open(get_metadata_file(), "w", encoding="utf-8") as f:
        json.dump(metadata.model_dump(), f, indent=2, ensure_ascii=False)


class Session(NamedTuple):
    """A session of a work directory."""

    id: str
    work_dir: WorkDirMeta

    @property
    def history_file(self) -> Path:
        path = self.work_dir.sessions_dir / f"{self.id}.jsonl"
        if not path.exists():
            path.touch()
        return path


def new_session(work_dir: Path) -> Session:
    """Create a new session for a work directory."""
    metadata = _load_metadata()
    work_dir_meta = next((wd for wd in metadata.work_dirs if wd.path == str(work_dir)), None)
    if work_dir_meta is None:
        work_dir_meta = WorkDirMeta(path=str(work_dir))
        metadata.work_dirs.append(work_dir_meta)
    session_id = str(uuid.uuid4())
    work_dir_meta.last_session_id = session_id
    _save_metadata(metadata)
    return Session(id=session_id, work_dir=work_dir_meta)


def continue_session(work_dir: Path) -> Session | None:
    """Get the last session for a work directory."""
    metadata = _load_metadata()
    work_dir_meta = next((wd for wd in metadata.work_dirs if wd.path == str(work_dir)), None)
    if work_dir_meta is None:
        return None
    if work_dir_meta.last_session_id is None:
        return None
    return Session(id=work_dir_meta.last_session_id, work_dir=work_dir_meta)
