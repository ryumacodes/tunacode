import shutil
import uuid
from pathlib import Path

from kimi_cli.config import get_share_dir
from kimi_cli.metadata import Session, load_metadata, save_metadata


class SessionManager:
    """Manages sessions for different work directories."""

    def __init__(self):
        self._sessions_dir = get_share_dir() / "sessions"
        self._sessions_dir.mkdir(parents=True, exist_ok=True)
        self.cleanup_orphaned_sessions()

    def get_session_for_work_dir(self, work_dir: Path) -> tuple[str, Path]:
        """Get or create session for the given work directory.

        Returns:
            Tuple of (session_name, history_file_path)
        """
        work_dir_str = str(work_dir.absolute())
        metadata = load_metadata()

        # look for existing session
        for session in metadata.sessions:
            if session.work_dir == work_dir_str:
                session_dir = self._sessions_dir / session.name
                history_file = session_dir / "history.jsonl"
                return session.name, history_file

        # create new session
        session_name = str(uuid.uuid4())
        session_dir = self._sessions_dir / session_name
        session_dir.mkdir(parents=True, exist_ok=True)
        history_file = session_dir / "history.jsonl"

        # add to metadata
        new_session = Session(name=session_name, work_dir=work_dir_str)
        metadata.sessions.append(new_session)
        save_metadata(metadata)

        return session_name, history_file

    def get_session_by_name(self, session_name: str) -> tuple[str, Path]:
        """Get or create session by name.

        Returns:
            Tuple of (session_name, history_file_path)
        """
        metadata = load_metadata()

        # look for existing session
        for session in metadata.sessions:
            if session.name == session_name:
                session_dir = self._sessions_dir / session.name
                history_file = session_dir / "history.jsonl"
                return session.name, history_file

        # session name validation happens automatically when creating Session object
        new_session = Session(name=session_name, work_dir=None)

        # create new session directory
        session_dir = self._sessions_dir / session_name
        session_dir.mkdir(parents=True, exist_ok=True)
        history_file = session_dir / "history.jsonl"

        # add to metadata
        metadata.sessions.append(new_session)
        save_metadata(metadata)

        return session_name, history_file

    def list_sessions(self) -> list[Session]:
        """List all sessions."""
        metadata = load_metadata()
        return metadata.sessions

    def cleanup_orphaned_sessions(self) -> None:
        """Remove sessions for non-existent work directories."""
        metadata = load_metadata()
        valid_sessions = []

        for session in metadata.sessions:
            # skip named sessions (work_dir is None)
            if session.work_dir is None:
                valid_sessions.append(session)
                continue

            work_dir = Path(session.work_dir)
            # only clean up sessions with work directories that no longer exist
            if work_dir.exists():
                valid_sessions.append(session)
            else:
                # remove session directory
                session_dir = self._sessions_dir / session.name
                if session_dir.exists():
                    shutil.rmtree(session_dir)

        metadata.sessions = valid_sessions
        save_metadata(metadata)
