import json
from pathlib import Path

from pydantic import BaseModel, Field

from kimi_cli.config import get_share_dir


class SessionMeta(BaseModel):
    """Session metadata."""

    name: str
    work_dir: str | None = None

    @property
    def directory(self) -> Path:
        return _get_sessions_dir() / self.name


class Metadata(BaseModel):
    """Kimi metadata structure."""

    sessions: list[SessionMeta] = Field(default_factory=list, description="Session list")


class MetadataManager:
    def __init__(self):
        self._metadata_file = get_share_dir() / "kimi.json"
        if not self._metadata_file.exists():
            self._metadata_file.touch()
            self._metadata_file.write_text(
                json.dumps(Metadata().model_dump(), indent=2, ensure_ascii=False)
            )
        self._metadata = self._load()

        self._sessions_dir = _get_sessions_dir()
        self._sessions_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Metadata:
        with open(self._metadata_file, encoding="utf-8") as f:
            data = json.load(f)
        return Metadata(**data)

    def _save(self) -> None:
        with open(self._metadata_file, "w", encoding="utf-8") as f:
            json.dump(self._metadata.model_dump(), f, indent=2, ensure_ascii=False)

    def get_session_by_name(self, session_name: str, work_dir: Path | None = None) -> SessionMeta:
        # look for existing session
        for session in self._metadata.sessions:
            if session.name == session_name:
                break
        else:
            work_dir_str = str(work_dir) if work_dir is not None else None
            session = SessionMeta(name=session_name, work_dir=work_dir_str)
            self._metadata.sessions.append(session)
            self._save()

        # ensure session directory exists
        session_dir = self._sessions_dir / session_name
        session_dir.mkdir(parents=True, exist_ok=True)
        return session


def _get_sessions_dir() -> Path:
    return get_share_dir() / "sessions"
