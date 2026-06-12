#!/usr/bin/env python3
"""Remove optional external wrapper resources from Gradio's HTML templates.

Iris is submitted as a custom Gradio Space with a local model runtime. Gradio's
default frontend template includes optional Google preconnect tags and an
iframe-resizer CDN script for embedded-page ergonomics. The Iris app does not
need them, and removing them keeps the Space self-contained for the demo.
"""

from __future__ import annotations

from pathlib import Path

import gradio


EXTERNAL_SNIPPETS = (
    '\n\t\t<link rel="preconnect" href="https://fonts.googleapis.com" />',
    '\n\t\t<link\n'
    '\t\t\trel="preconnect"\n'
    '\t\t\thref="https://fonts.gstatic.com"\n'
    '\t\t\tcrossorigin="anonymous"\n'
    "\t\t/>",
    '\n\t\t<script\n'
    '\t\t\tsrc="https://cdnjs.cloudflare.com/ajax/libs/iframe-resizer/4.3.1/iframeResizer.contentWindow.min.js"\n'
    "\t\t\tasync\n"
    "\t\t></script>",
)

EXTERNAL_URLS = (
    "https://raw.githubusercontent.com/gradio-app/gradio/main/js/_website/src/lib/assets/img/header-image.jpg",
)


def patch_template(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    patched = text
    for snippet in EXTERNAL_SNIPPETS:
        patched = patched.replace(snippet, "")
    for url in EXTERNAL_URLS:
        patched = patched.replace(url, "")
    if patched == text:
        return False
    path.write_text(patched, encoding="utf-8")
    return True


def main() -> None:
    gradio_root = Path(gradio.__file__).resolve().parent
    targets = [
        gradio_root / "templates" / "frontend" / "index.html",
        gradio_root / "templates" / "frontend" / "share.html",
    ]
    missing = [str(path) for path in targets if not path.exists()]
    if missing:
        raise SystemExit(f"missing Gradio templates: {', '.join(missing)}")

    changed = [path for path in targets if patch_template(path)]
    print(
        "patched Gradio templates: "
        + (", ".join(path.name for path in changed) if changed else "already clean")
    )


if __name__ == "__main__":
    main()
