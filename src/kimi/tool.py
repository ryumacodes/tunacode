import importlib

from kosong.tooling import CallableTool


def load_tool(tool_path: str, **tool_kwargs) -> CallableTool | None:
    module_name, class_name = tool_path.rsplit(":", 1)
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return None
    cls = getattr(module, class_name, None)
    if cls is None:
        return None
    return cls(**tool_kwargs)
