from __future__ import annotations

import typer

from openmac import Chrome
from openmac.adapters.cli._internal.actions import ActionsParser
from openmac.adapters.cli._internal.display import display_object

app = typer.Typer()


@app.command(name="chrome")
def chrome_command(raw_actions: list[str]) -> None:
    parser = ActionsParser(raw_actions)
    actions = parser.parse()

    current_object = Chrome()

    for action in actions:
        current_object = action(current_object)

    display_object(current_object)


@app.command(name="finder")
def finder_command(args: str) -> None:
    print(args)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
