"""Hugging Face Spaces entrypoint for Iris."""

from iris.ui import create_app


demo = create_app()


if __name__ == "__main__":
    demo.queue().launch()
