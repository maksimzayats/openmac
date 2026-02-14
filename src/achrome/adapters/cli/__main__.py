from typer import Typer

typer = Typer()


@typer.command("browser")
def browser() -> None:
    print("Browser command")


@typer.command("browser2")
def browser2() -> None:
    print("Browser command")


def main() -> None:
    typer()


if __name__ == "__main__":
    main()
