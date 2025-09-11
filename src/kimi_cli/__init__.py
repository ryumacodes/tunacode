import asyncio
import os
from pathlib import Path

import click
from kosong.context.linear import JsonlLinearStorage
from kosong.tooling import SimpleToolset
from pydantic import SecretStr

from kimi_cli.agent import load_agent, load_system_prompt
from kimi_cli.app import App
from kimi_cli.config import (
    DEFAULT_KIMI_BASE_URL,
    DEFAULT_KIMI_MODEL,
    ConfigError,
    LLMModel,
    LLMProvider,
    get_share_dir,
    load_config,
)
from kimi_cli.soul import Soul
from kimi_cli.tool import load_tool
from kimi_cli.utils.provider import augment_provider_with_env_vars, create_chat_provider


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Print verbose information (default: no)",
)
@click.option(
    "--agent",
    "agent_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=Path(__file__).parent / "koder" / "agent.yaml",
    help="Custom agent definition file (default: builtin Kimi Koder)",
)
@click.option(
    "--model",
    "-m",
    "model_name",
    type=str,
    default=None,
    help="LLM model to use (default: default model set in config file)",
)
@click.option(
    "--work-dir",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help="Working directory for the agent (default: current directory)",
)
@click.option(
    "--command",
    "-c",
    "--query",
    "-q",
    "command",
    type=str,
    default=None,
    help="User query to the agent (default: interactive mode)",
)
def kimi(
    verbose: bool,
    agent_path: Path,
    model_name: str | None,
    work_dir: Path,
    command: str | None,
):
    """Kimi, your next CLI agent."""
    echo = click.echo if verbose else lambda *args, **kwargs: None

    agent_path = agent_path.absolute()
    work_dir = work_dir.absolute()

    try:
        config = load_config()
    except ConfigError as e:
        raise click.ClickException(f"Failed to load config: {e}") from e
    echo(f"✓ Loaded config: {config}")

    model: LLMModel | None = None
    provider: LLMProvider | None = None

    # try to use config file
    if not model_name and config.default_model:
        # no --model specified && default model is set in config
        model = config.models[config.default_model]
        provider = config.providers[model.provider]
    if model_name and model_name in config.models:
        # --model specified && model is set in config
        model = config.models[model_name]
        provider = config.providers[model.provider]

    if not model:
        model = LLMModel(provider="", model=DEFAULT_KIMI_MODEL)
        provider = LLMProvider(type="kimi", base_url=DEFAULT_KIMI_BASE_URL, api_key=SecretStr(""))

    # try overwrite with environment variables
    assert provider is not None
    augment_provider_with_env_vars(provider)

    if not provider.api_key:
        raise click.ClickException("API key is not set")

    echo(f"✓ Using LLM provider: {provider}")
    echo(f"✓ Using LLM model: {model.model}")

    agent = load_agent(agent_path)
    echo(f"✓ Loaded agent: {agent.name}")

    system_prompt = load_system_prompt(
        agent,
        builtin_args={
            "ENSOUL_WORK_DIR": work_dir,
        },
    )
    preview = system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt
    echo(f"✓ Loaded system prompt: {preview} ({len(system_prompt)} characters)")

    toolset = SimpleToolset()
    bad_tools = []
    for tool_path in agent.tools:
        tool = load_tool(tool_path)
        if tool:
            toolset += tool
        else:
            bad_tools.append(tool_path)

    if bad_tools:
        raise click.ClickException(f"Failed to load tools: {bad_tools}")

    echo(f"✓ Loaded tools: {[tool.name for tool in toolset.tools]}")

    if command is not None:
        command = command.strip()
        if not command:
            raise click.BadArgumentUsage("Command cannot be empty")

    context_storage = JsonlLinearStorage(get_share_dir() / "history.jsonl")
    soul = Soul(
        agent.name,
        chat_provider=create_chat_provider(provider, model),
        system_prompt=system_prompt,
        toolset=toolset,
        context_storage=context_storage,
    )
    app = App(soul)

    # switch to workspace directory
    original_cwd = Path.cwd()
    os.chdir(work_dir)

    try:
        asyncio.run(app.run(command))
    finally:
        # restore original working directory
        os.chdir(original_cwd)


def main():
    kimi()
