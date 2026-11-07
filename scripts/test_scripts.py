#!/usr/bin/env python3
"""Small regression check for the bundled scaffold and audit helpers."""

from __future__ import annotations

import io
import json
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
                "--dsh-version", "0.2.2-rc.1",
                "--cordis-version", "4.1.0",
            ]
            with redirect_stdout(io.StringIO()):
                self.assertEqual(scaffold_plugin.main(arguments), 0)
            with redirect_stderr(io.StringIO()):
                self.assertEqual(scaffold_plugin.main(arguments), 2)

            findings = audit_plugin.audit(plugin_dir, False, "0.2.2-rc.1")
            self.assertFalse([item for item in findings if item.severity == "error"])

            unbuilt = audit_plugin.audit(plugin_dir, True, "0.2.2-rc.1")
            self.assertIn("exports.unbuilt", {item.code for item in unbuilt})

            wrong_runtime = audit_plugin.audit(plugin_dir, False, "0.2.1-rc.5")
            self.assertIn("dependency.runtime", {item.code for item in wrong_runtime})

    def test_ordered_bundle_paths_and_peer_ranges(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(scaffold_plugin.main([
                    str(root), "--package-name", "dsh-plugin-test",
                    "--dsh-version", "0.2.2-rc.1", "--cordis-version", "4.1.0",
                ]), 0)
            package_path = root / "package.json"
            package = json.loads(package_path.read_text())
            package["dsh"]["bundle"]["patch"] = ["./cordis.patch.yml", "./extra.yml"]
            package["files"].append("extra.yml")
            package["peerDependencies"]["@deepseek-ai/dsh-tools"] = ">=0.2.2-rc.1 <0.3.0"
            (root / "extra.yml").write_text("[]\n")
            package_path.write_text(json.dumps(package))
            self.assertFalse([f for f in audit_plugin.audit(root, False, "0.2.2-rc.1") if f.severity == "error"])

            package["files"].remove("extra.yml")
            package_path.write_text(json.dumps(package))
            self.assertIn("package.unpacked", {f.code for f in audit_plugin.audit(root, False, None)})

            package["dsh"]["bundle"]["patch"] = ["../outside.yml"]
            package_path.write_text(json.dumps(package))
            self.assertIn("bundle.path", {f.code for f in audit_plugin.audit(root, False, None)})

    def test_runtime_requirement_and_pinned_development_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with redirect_stdout(io.StringIO()):
                scaffold_plugin.main([str(root), "--package-name", "dsh-plugin-test",
                                      "--dsh-version", "0.2.2-rc.1", "--cordis-version", "4.1.0"])
            path = root / "package.json"
            package = json.loads(path.read_text())
            package["engines"]["dsh"] = "workspace:*"
            package["devDependencies"]["@deepseek-ai/dsh-tools"] = "^0.2.2-rc.1"
            path.write_text(json.dumps(package))
            codes = {f.code for f in audit_plugin.audit(root, False, "0.2.2-rc.1")}
            self.assertIn("engines.dsh", codes)
            self.assertIn("dependency.floating", codes)


if __name__ == "__main__":
    unittest.main()
