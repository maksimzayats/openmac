from __future__ import annotations

import typer
from diwire import Container
from rich.console import Console

from openmac.adapters.cli.apps.chrome.application import chrome_app_cli

app = typer.Typer()
app.add_typer(chrome_app_cli)


@app.command(name="finder")
def finder_command(args: str) -> None:
    print(args)


def main() -> None:
    container = Container()
    container.add_instance(Console())

    app()


if __name__ == "__main__":
    main()
