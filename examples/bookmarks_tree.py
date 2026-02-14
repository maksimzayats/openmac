from achrome import ChromeAPI, ChromeBookmarkFolder


def print_folder(folder: ChromeBookmarkFolder, indent: int = 0) -> None:
    prefix = " " * indent
    print(f"{prefix}- {folder.title} ({folder.id})")

    for item in folder.items:
        print(f"{prefix}  * {item.title} -> {item.url}")

    for subfolder in folder.folders:
        print_folder(subfolder, indent + 2)


def main() -> None:
    chrome = ChromeAPI()
    tree = chrome.bookmarks_tree()

    print("Bookmarks Bar")
    print_folder(tree.bookmarks_bar, indent=2)
    print("Other Bookmarks")
    print_folder(tree.other_bookmarks, indent=2)


if __name__ == "__main__":
    main()
