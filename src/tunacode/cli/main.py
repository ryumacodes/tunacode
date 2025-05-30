"""
Module: tunacode.cli.main

Enhanced CLI entry point with better styling while staying CLI-based.
"""

import asyncio

import typer

from tunacode.cli.repl import repl
from tunacode.configuration.settings import ApplicationSettings
from tunacode.core.state import StateManager
from tunacode.setup import setup
from tunacode.ui import console as ui
from tunacode.utils.system import check_for_updates

app_settings = ApplicationSettings()
app = typer.Typer(help="🐟 TunaCode - Your AI-powered development assistant")
state_manager = StateManager()


@app.command()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit."),
    run_setup: bool = typer.Option(False, "--setup", help="Run setup process."),
    baseurl: str = typer.Option(None, "--baseurl", help="API base URL (e.g., https://openrouter.ai/api/v1)"),
    model: str = typer.Option(None, "--model", help="Default model to use (e.g., openai/gpt-4)"),
    key: str = typer.Option(None, "--key", help="API key for the provider"),
):
    """🚀 Start TunaCode - Your AI-powered development assistant"""
    
    if version:
        asyncio.run(ui.version())
        return

    asyncio.run(ui.banner())

    has_update, latest_version = check_for_updates()
    if has_update:
        asyncio.run(ui.show_update_message(latest_version))

    # Pass CLI args to setup
    cli_config = {}
    if baseurl or model or key:
        cli_config = {
            "baseurl": baseurl,
            "model": model,
            "key": key
        }

    try:
        asyncio.run(setup(run_setup, state_manager, cli_config))
        asyncio.run(repl(state_manager))
    except Exception as e:
        asyncio.run(ui.error(str(e)))


if __name__ == "__main__":
    app()
