#!/usr/bin/env python
import typer

from dumbo_esse3.cli import app, app_options, is_debug_on
from utils.console import console

if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        if is_debug_on():
            raise e
        else:
            console.print(f"[red bold]Error:[/red bold] {e}")
