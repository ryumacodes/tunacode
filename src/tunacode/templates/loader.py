"""Template metadata for TunaCode templates."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Template:
    """Represents a template with metadata and allowed tools."""

    name: str
    description: str
    prompt: str
    allowed_tools: List[str]
    parameters: Dict[str, str] = field(default_factory=dict)
    shortcut: Optional[str] = None
