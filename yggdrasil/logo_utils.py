"""
ASCII logo display utilities for Yggdrasil CLI.
"""

from pathlib import Path


def get_ascii_logo() -> str:
    """
    Load the ASCII logo from the assets directory.

    Returns:
        str: The ASCII logo content, or a fallback if file not found.
    """
    try:
        # Try to load from package assets using modern importlib.resources
        try:
            from importlib.resources import files

            logo_content = (files("yggdrasil") / "assets" / "ascii-logo.txt").read_text(
                encoding="utf-8"
            )
            return logo_content
        except ImportError:
            # Fallback for Python < 3.9
            from importlib import resources

            with resources.open_text("yggdrasil.assets", "ascii-logo.txt") as f:
                return f.read()
    except (ImportError, FileNotFoundError, ModuleNotFoundError):
        # Fallback for development or if importlib.resources isn't available
        try:
            logo_path = Path(__file__).parent / "assets" / "ascii-logo.txt"
            return logo_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            # Ultimate fallback - simple text logo
            return """
    ╭─────────────────────────────────╮
    │                                 │
    │    ┬ ┬┌─┐┌─┐┌┬┐┬─┐┌─┐┌─┐┬┬      │
    │    └┬┘│ ┬│ ┬ ││├┬┘├─┤└─┐││      │
    │     ┴ └─┘└─┘─┴┘┴└─┴ ┴└─┘┴└─┘    │
    │                                 │
    ╰─────────────────────────────────╯
"""


def print_logo(version: str | None = None) -> None:
    """
    Print the ASCII logo to stdout.

    Args:
        version: Optional version string to display below logo
    """
    logo = get_ascii_logo()
    print(logo)

    if version:
        version_text = f"    v{version}"
        print(version_text)

    print()  # Add spacing after logo


if __name__ == "__main__":
    # Simple demo
    print("Basic logo:")
    print_logo()

    print("Logo with version:")
    print_logo(version="1.0.0")
