from __future__ import annotations

import click
from diwire import Container
from rich.console import Console

from openmac import Chrome
from openmac.adapters.cli._internal.actions import ActionsParser
from openmac.adapters.cli._internal.display import display_object


@click.group()
def app() -> None:
    pass


@app.command(name="chrome")
@click.argument("raw_actions", nargs=-1)
def chrome_command(raw_actions: tuple[str, ...]) -> None:
    parser = ActionsParser(raw_actions)
    actions = parser.parse()

    current_object = Chrome()

    for action in actions:
        current_object = action(current_object)

    display_object(current_object)


@app.command(name="finder")
@click.argument("args")
def finder_command(args: str) -> None:
    print(args)


def main() -> None:
    container = Container()
    container.add_instance(Console())

    app()


if __name__ == "__main__":
    main()
