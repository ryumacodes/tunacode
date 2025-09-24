from pathlib import Path
from typing import override

from kosong.tooling import CallableTool2, ToolOk, ToolReturnType
from pydantic import BaseModel, Field

from kimi_cli.denwarenji import DenwaRenji


class Params(BaseModel):
    message: str = Field(description="The message to send")
    step: int = Field(description="The step to send the message before")


class DMail(CallableTool2):
    name: str = "DMail"
    description: str = (Path(__file__).parent / "dmail.md").read_text()
    params: type[Params] = Params

    def __init__(self, denwa_renji: DenwaRenji, **kwargs):
        super().__init__(**kwargs)
        self._denwa_renji = denwa_renji

    @override
    async def __call__(self, params) -> ToolReturnType:
        await self._denwa_renji.send_dmail(params.message, params.step)
        return ToolOk(output="El Psy Congroo")
