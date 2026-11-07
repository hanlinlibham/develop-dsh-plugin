#!/usr/bin/env python3
"""Small regression check for the bundled scaffold and audit helpers."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import audit_plugin
import scaffold_plugin


class HelperScriptsTest(unittest.TestCase):
    def test_generated_plugin_passes_and_wrong_runtime_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plugin_dir = Path(temporary) / "dsh-plugin-script-check"
            arguments = [
                str(plugin_dir),
                "--package-name", "dsh-plugin-script-check",
                "--dsh-version", "0.1.0-rc.6",
                "--cordis-version", "4.0.1",
            ]
            with redirect_stdout(io.StringIO()):
                self.assertEqual(scaffold_plugin.main(arguments), 0)
            with redirect_stderr(io.StringIO()):
                self.assertEqual(scaffold_plugin.main(arguments), 2)

            findings = audit_plugin.audit(plugin_dir, False, "0.1.0-rc.6")
            self.assertFalse([item for item in findings if item.severity == "error"])

            unbuilt = audit_plugin.audit(plugin_dir, True, "0.1.0-rc.6")
            self.assertIn("exports.unbuilt", {item.code for item in unbuilt})

            wrong_runtime = audit_plugin.audit(plugin_dir, False, "0.1.0-rc.5")
            self.assertIn("dependency.runtime", {item.code for item in wrong_runtime})


if __name__ == "__main__":
    unittest.main()
