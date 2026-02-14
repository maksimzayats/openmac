from achrome import ChromeAPI
from achrome.core.apple_script import AppleScriptExecutor


def main() -> None:
    # container = Container()
    chrome = ChromeAPI(apple_script_executor=AppleScriptExecutor())

    app = chrome.application_info()
    print(f"{app.name} {app.version} (frontmost={app.frontmost})")

    windows = chrome.list_windows()
    print(f"Windows: {len(windows)}")
    for window in windows:
        print(
            f"window={window.id} index={window.index} tabs={window.tab_count} "
            f"mode={window.mode} bounds={window.bounds.left},{window.bounds.top},"
            f"{window.bounds.right},{window.bounds.bottom}"
        )

    tabs = chrome.list_tabs()
    print(f"Tabs: {len(tabs)}")
    for tab in tabs:
        marker = "*" if tab.is_active else " "
        print(f"{marker} {tab.composite_id} {tab.title} -> {tab.url}")


if __name__ == "__main__":
    main()
