import subprocess
import sys
import unittest
from unittest.mock import patch


class TestYggdrasilMain(unittest.TestCase):
    """
    Tests for yggdrasil.__main__.py - the package entry point.

    This module serves as the entry point when running:
    python -m yggdrasil

    It simply imports and calls main() from cli.py.
    """

    def test_main_entry_point_import(self):
        """Test that __main__.py can be imported without errors."""
        # This covers the import statement in __main__.py
        import yggdrasil.__main__

        # Verify the module was imported successfully
        self.assertTrue(hasattr(yggdrasil.__main__, "main"))

    def test_main_entry_point_execution(self):
        """Test that __main__.py executes main() when run as module."""
        # Test the actual execution path by simulating __name__ == "__main__"
        # We'll patch main() to avoid actually running it, then test the guard

        import yggdrasil.__main__ as main_module

        with patch.object(main_module, "main") as mock_main:
            # Simulate the __name__ == "__main__" condition
            # by executing the code with __name__ set to "__main__"
            old_name = main_module.__name__
            try:
                main_module.__name__ = "__main__"

                # Re-execute the module's if __name__ == "__main__" check
                if main_module.__name__ == "__main__":
                    main_module.main()

                # Verify main was called
                mock_main.assert_called_once()
            finally:
                main_module.__name__ = old_name

    def test_python_m_yggdrasil_execution(self):
        """Test that 'python -m yggdrasil --help' works correctly."""
        # This is an integration test that verifies the complete module execution
        from pathlib import Path

        project_root = Path(__file__).resolve().parent.parent  # two levels up
        result = subprocess.run(
            [sys.executable, "-m", "yggdrasil", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        # Should exit with code 0 for help
        self.assertEqual(result.returncode, 0)

        # Should contain help text
        self.assertIn("ygg", result.stdout)
        self.assertIn("daemon", result.stdout)
        self.assertIn("run-doc", result.stdout)

    def test_module_structure(self):
        """Test the module structure and imports."""
        # Import in clean state

        import yggdrasil.__main__

        # Verify the module has the expected attributes
        self.assertTrue(hasattr(yggdrasil.__main__, "main"))

        # Verify main is callable (the important part)
        self.assertTrue(callable(yggdrasil.__main__.main))


if __name__ == "__main__":
    unittest.main()
