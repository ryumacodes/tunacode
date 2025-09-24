from pathlib import Path
from typing import override

from kosong.base.tool import ParametersType
from kosong.tooling import CallableTool, ToolOk, ToolReturnType

from kimi_cli.denwarenji import DenwaRenji


class DMail(CallableTool):
    name: str = "DMail"
    description: str = (Path(__file__).parent / "dmail.md").read_text()
    parameters: ParametersType = {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "The message to send"},
            "step": {"type": "number", "description": "The step to send the message before"},
        },
    }

    def __init__(self, denwa_renji: DenwaRenji, **kwargs):
        super().__init__(**kwargs)
        self._denwa_renji = denwa_renji

    @override
    async def __call__(self, message: str, step: int) -> ToolReturnType:
        await self._denwa_renji.send_dmail(message, step)
        return ToolOk(output="El Psy Congroo")
