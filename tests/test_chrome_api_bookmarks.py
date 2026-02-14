from achrome.core.chrome.api import ChromeAPI
from tests.fakes import FakeAppleScriptExecutor, ok_envelope


def test_bookmarks_tree_returns_nested_structure() -> None:
    executor = FakeAppleScriptExecutor(
        responses={
            "bookmarks_tree": ok_envelope(
                {
                    "bookmarks_bar": {
                        "id": "1",
                        "title": "Bookmarks Bar",
                        "index": 1,
                        "folders": [
                            {
                                "id": "2",
                                "title": "News",
                                "index": 1,
                                "folders": [],
                                "items": [
                                    {
                                        "id": "3",
                                        "title": "Site",
                                        "url": "https://example.com",
                                        "index": 1,
                                    }
                                ],
                            }
                        ],
                        "items": [],
                    },
                    "other_bookmarks": {
                        "id": "10",
                        "title": "Other",
                        "index": 2,
                        "folders": [],
                        "items": [],
                    },
                }
            ),
        }
    )
    api = ChromeAPI(apple_script_executor=executor)

    tree = api.bookmarks_tree()

    assert tree.bookmarks_bar.title == "Bookmarks Bar"
    assert tree.bookmarks_bar.folders[0].items[0].url == "https://example.com"
    assert tree.other_bookmarks.id == "10"
