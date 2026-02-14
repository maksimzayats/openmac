from diwire import Container

from achrome.ioc.container import get_container


def test_get_container_returns_diwire_container() -> None:
    container = get_container()
    assert isinstance(container, Container)
