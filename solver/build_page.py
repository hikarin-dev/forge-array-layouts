"""Build index.html from template.html and the data in data/.

Usage: python solver/build_page.py [fragment_out.html]   (from the repo root)

The optional argument also writes the page as a bare fragment (no <html>,
<head> or <body>), the form the Claude artifact copy is published from.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(*parts):
    return open(os.path.join(ROOT, *parts), encoding="utf-8").read()


def main():
    page = (read("template.html")
            .replace("__DATA__", read("data", "layouts.json"))
            .replace("__SMALL__", read("data", "small.json")))
    if len(sys.argv) > 1:
        open(sys.argv[1], "w", encoding="utf-8").write(page)

    head_end = page.index("</style>") + len("</style>")
    head, body = page[:head_end], page[head_end:]
    head = head.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    head = head.replace("body {\n", "body {\n  margin: 0;\n", 1)
    full = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + head + "\n</head>\n<body>" + body + "</body>\n</html>\n")
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8", newline="\n").write(full)
    print(f"index.html: {len(full):,} bytes")


if __name__ == "__main__":
    main()
