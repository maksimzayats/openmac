import json

from achrome import ChromeAPI


def main() -> None:
    chrome = ChromeAPI()

    tab = chrome.open_url("https://example.com", activate=True)
    print(f"Opened: {tab.composite_id} {tab.url}")

    title = chrome.execute_javascript("document.title", tab=tab.composite_id)
    print(f"Title via JS: {title}")

    payload = chrome.execute_javascript_json(
        "{ title: document.title, href: window.location.href }",
        tab=tab.composite_id,
    )
    print("Structured payload:")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
