from __future__ import annotations

import click
from diwire import Container
from rich.console import Console

from openmac.adapters.cli.apps.chrome import chrome_command


@click.group()
def app() -> None:
    pass


app.add_command(chrome_command)


def main() -> None:
    container = Container()
    container.add_instance(Console())

    app()


if __name__ == "__main__":
    main()
