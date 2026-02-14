from achrome.core.chrome.applescript_bridge import CHROME_BRIDGE_SCRIPT


def test_open_url_uses_stable_index_for_created_tabs() -> None:
    assert CHROME_BRIDGE_SCRIPT.count("set newTabIndex to count of tabs of oneWindow") == 2
    assert (
        CHROME_BRIDGE_SCRIPT.count(
            'if activateValue is "1" then set active tab index of oneWindow to newTabIndex'
        )
        == 2
    )
    assert (
        'if activateValue is "1" then set active tab index of oneWindow to index of oneTab'
        not in CHROME_BRIDGE_SCRIPT
    )
