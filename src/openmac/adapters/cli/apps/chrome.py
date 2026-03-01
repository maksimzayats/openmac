from __future__ import annotations

import click

from openmac import Chrome
from openmac.adapters.cli._internal.actions import ActionsParser
from openmac.adapters.cli._internal.display import display_object


@click.command(
    add_help_option=False,
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    },
)
@click.argument("raw_actions", nargs=-1)
def chrome_command(raw_actions: tuple[str, ...]) -> None:
    parser = ActionsParser(raw_actions)
    actions = parser.parse()

    current_object = Chrome()

    for action in actions:
        current_object = action(current_object)

    display_object(current_object)
