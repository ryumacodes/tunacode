"""Tool-specific panel renderers following NeXTSTEP UI principles.

All renderers implement a 4-zone layout with syntax highlighting:
- Zone 1: Header (tool name, key stats)
- Zone 2: Params (key-value parameter display)
- Zone 3: Viewport (main content with syntax highlighting)
- Zone 4: Status (truncation info, timing)
"""

from tunacode.ui.renderers.tools.base import (  # noqa: F401
    BOX_HORIZONTAL,
    SEPARATOR_WIDTH,
    BaseToolRenderer,
    RendererConfig,
    RenderFunc,
    ToolRendererProtocol,
    get_renderer,
    list_renderers,
    pad_lines,
    tool_renderer,
    truncate_content,
    truncate_line,
)
from tunacode.ui.renderers.tools.bash import render_bash  # noqa: F401
from tunacode.ui.renderers.tools.discover import render_discover  # noqa: F401
from tunacode.ui.renderers.tools.hashline_edit import render_hashline_edit  # noqa: F401
from tunacode.ui.renderers.tools.read_file import render_read_file  # noqa: F401
from tunacode.ui.renderers.tools.syntax_utils import (  # noqa: F401
    EXTENSION_LEXERS,
    SYNTAX_THEME,
    detect_code_lexer,
    get_color,
    get_lexer,
    syntax_or_text,
)
from tunacode.ui.renderers.tools.web_fetch import render_web_fetch  # noqa: F401
from tunacode.ui.renderers.tools.write_file import render_write_file  # noqa: F401
