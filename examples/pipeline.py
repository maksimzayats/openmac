from achrome import ChromeAPI
from achrome.core.apple_script import AppleScriptExecutor


def main() -> None:
    chrome = ChromeAPI(apple_script_executor=AppleScriptExecutor())
    tab = chrome.open_url("https://www.example.com", activate=False)
    snapshot = chrome.snapshot(tab=tab.composite_id)
    print(f"Snapshot of tab {tab.composite_id} ({tab.title}):")
    print(snapshot.tree)


if __name__ == "__main__":
    main()
