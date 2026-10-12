"""Every source directory that holds Python modules is a regular package."""

import unittest
from pathlib import Path

# Located from this file, not from the imported package: an installed copy
# would not show a directory that was left out of the distribution.
_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "yggdrasil"


def _module_directories(root: Path) -> list[Path]:
    """Return every directory at or below ``root`` that directly holds a ``.py`` file."""
    return sorted({path.parent for path in root.rglob("*.py")})


class TestPackageLayout(unittest.TestCase):
    """Package discovery only finds directories that have an ``__init__.py``.

    This checks the source tree. What a built wheel contains is a separate
    question that this test does not answer.
    """

    def test_source_tree_is_found(self):
        self.assertIn(_SOURCE_ROOT, _module_directories(_SOURCE_ROOT))

    def test_every_module_directory_has_an_initializer(self):
        missing = [
            directory.relative_to(_SOURCE_ROOT.parent).as_posix()
            for directory in _module_directories(_SOURCE_ROOT)
            if not (directory / "__init__.py").is_file()
        ]
        self.assertEqual(missing, [])
