"""Template loader for managing TunaCode templates.

This module provides the Template dataclass and TemplateLoader class for
managing templates that pre-approve specific tools for different workflows.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
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


class TemplateLoader:
    """Loads and manages templates from the filesystem."""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize the template loader.

        Args:
            template_dir: Optional custom template directory. If not provided,
                         uses the default ~/.config/tunacode/templates
        """
        if template_dir is None:
            self.template_dir = Path.home() / ".config" / "tunacode" / "templates"
        else:
            self.template_dir = Path(template_dir)

        # Ensure template directory exists
        self.template_dir.mkdir(parents=True, exist_ok=True)

    def load_template(self, name: str) -> Optional[Template]:
        """Load a template by name from disk.

        Args:
            name: The name of the template (without .json extension)

        Returns:
            Template instance if found and valid, None otherwise
        """
        template_path = self.get_template_path(name)

        if not template_path.exists():
            return None

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate required fields
            required_fields = ["name", "description", "prompt", "allowed_tools"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Template missing required field: {field}")

            # Ensure allowed_tools is a list
            if not isinstance(data["allowed_tools"], list):
                raise ValueError("allowed_tools must be a list")

            return Template(
                name=data["name"],
                description=data["description"],
                prompt=data["prompt"],
                allowed_tools=data["allowed_tools"],
                parameters=data.get("parameters", {}),
                shortcut=data.get("shortcut"),
            )

        except (json.JSONDecodeError, ValueError) as e:
            # Log error but don't raise - return None for invalid templates
            print(f"Error loading template '{name}': {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error loading template '{name}': {str(e)}")
            return None

    def list_templates(self) -> List[str]:
        """List all available template names.

        Returns:
            List of template names (without .json extension)
        """
        templates = []

        try:
            # Look for JSON files in template directory
            for path in self.template_dir.glob("*.json"):
                if path.is_file():
                    templates.append(path.stem)

            # Also check subdirectories
            for subdir in ["project", "tool", "config"]:
                subdir_path = self.template_dir / subdir
                if subdir_path.exists():
                    for path in subdir_path.glob("*.json"):
                        if path.is_file():
                            templates.append(f"{subdir}/{path.stem}")

            return sorted(templates)

        except Exception as e:
            print(f"Error listing templates: {str(e)}")
            return []

    def save_template(self, template: Template) -> bool:
        """Save a template to disk.

        Args:
            template: The template to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            template_path = self.get_template_path(template.name)

            # Create parent directory if needed
            template_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare data for JSON serialization
            data = {
                "name": template.name,
                "description": template.description,
                "prompt": template.prompt,
                "allowed_tools": template.allowed_tools,
                "parameters": template.parameters,
            }

            # Only include shortcut if it's set
            if template.shortcut:
                data["shortcut"] = template.shortcut

            # Write to disk
            with open(template_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error saving template '{template.name}': {str(e)}")
            return False

    def delete_template(self, name: str) -> bool:
        """Delete a template from disk.

        Args:
            name: The name of the template to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            template_path = self.get_template_path(name)

            if template_path.exists():
                template_path.unlink()
                return True
            else:
                return False

        except Exception as e:
            print(f"Error deleting template '{name}': {str(e)}")
            return False

    def get_template_path(self, name: str) -> Path:
        """Get the file path for a template.

        Args:
            name: The template name (can include subdirectory like "project/web")

        Returns:
            Path to the template file
        """
        # Handle subdirectory in name
        if "/" in name:
            parts = name.split("/", 1)
            return self.template_dir / parts[0] / f"{parts[1]}.json"
        else:
            return self.template_dir / f"{name}.json"

    def get_templates_with_shortcuts(self) -> Dict[str, Template]:
        """Get all templates that have shortcuts defined.

        Returns:
            Dictionary mapping shortcut to Template instance
        """
        shortcuts = {}

        try:
            for template_name in self.list_templates():
                template = self.load_template(template_name)
                if template and template.shortcut:
                    shortcuts[template.shortcut] = template

            return shortcuts

        except Exception as e:
            print(f"Error loading template shortcuts: {str(e)}")
            return {}
