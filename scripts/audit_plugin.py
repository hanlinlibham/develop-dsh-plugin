#!/usr/bin/env python3
"""Audit deterministic package-shape rules for an out-of-tree DSH plugin."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str


def export_targets(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        targets: list[str] = []
        for nested in value.values():
            targets.extend(export_targets(nested))
        return targets
    return []


def file_is_packed(relative: str, patterns: list[str]) -> bool:
    relative = relative.removeprefix("./")
    for pattern in patterns:
        pattern = pattern.removeprefix("./").rstrip("/")
        if relative == pattern or relative.startswith(f"{pattern}/"):
            return True
        if fnmatch.fnmatchcase(relative, pattern):
            return True
    return False


def exact_version(value: str) -> bool:
    return re.fullmatch(
        r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?",
        value,
    ) is not None


def audit(plugin_dir: Path, require_built: bool, dsh_version: str | None) -> list[Finding]:
    findings: list[Finding] = []

    def add(severity: str, code: str, message: str) -> None:
        findings.append(Finding(severity, code, message))

    package_path = plugin_dir / "package.json"
    if not package_path.is_file():
        return [Finding("error", "package.missing", f"missing {package_path}")]
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [Finding("error", "package.invalid", str(error))]
    if not isinstance(package, dict):
        return [Finding("error", "package.invalid", "package.json root must be an object")]

    package_name = package.get("name")
    if not isinstance(package_name, str) or not package_name:
        add("error", "package.name", "package.json needs a non-empty name")
        package_name = "<unknown>"
    if package.get("type") != "module":
        add("warning", "package.esm", 'expected package.json "type": "module"')

    exports = package.get("exports")
    host_export: Any = None
    client_export: Any = None
    if isinstance(exports, str):
        host_export = exports
    elif isinstance(exports, dict):
        host_export = exports.get(".")
        client_export = exports.get("./client")
    if host_export is None:
        add("error", "exports.host", 'missing exports["."] Host entry')

    export_paths: list[str] = []
    for label, value in (("Host", host_export), ("Client", client_export)):
        javascript_targets = 0
        for target in export_targets(value):
            if target.endswith((".js", ".mjs", ".cjs")):
                javascript_targets += 1
                if not target.startswith("./") or ".." in PurePosixPath(target).parts:
                    add("error", "exports.path", f"{label} export is not a safe relative path: {target}")
                    continue
                export_paths.append(target)
                if require_built and not (plugin_dir / target).is_file():
                    add("error", "exports.unbuilt", f"missing built {label} artifact: {target}")
        if value is not None and javascript_targets == 0:
            add("error", "exports.javascript", f"{label} export has no JavaScript target")

    dsh = package.get("dsh")
    if not isinstance(dsh, dict):
        add("error", "dsh.manifest", "missing dsh manifest")
        dsh = {}
    bundle = dsh.get("bundle")
    patch = bundle.get("patch") if isinstance(bundle, dict) else None
    patches = [patch] if isinstance(patch, str) and patch else patch
    if not isinstance(patches, list) or not patches or not all(isinstance(item, str) and item for item in patches):
        add("error", "bundle.patch", "dsh.bundle.patch must be a path or a non-empty ordered list of paths")
        patches = []
    named_package = False
    for patch_name in patches:
        patch_path = (plugin_dir / patch_name).resolve()
        if Path(patch_name).is_absolute() or not patch_path.is_relative_to(plugin_dir.resolve()):
            add("error", "bundle.path", f"bundle patch must stay inside the package: {patch_name}")
            continue
        if not patch_path.is_file():
            add("error", "bundle.file", f"bundle patch does not exist: {patch_name}")
        else:
            patch_text = patch_path.read_text(encoding="utf-8")
            name_pattern = re.compile(rf"^\s*name:\s*['\"]?{re.escape(package_name)}['\"]?\s*$", re.M)
            named_package = named_package or bool(name_pattern.search(patch_text))
    if patches and package_name != "<unknown>" and not named_package:
        add("warning", "bundle.name", f"bundle patches do not name {package_name}; confirm composition intent")

    client = dsh.get("client")
    if client is not None:
        if not isinstance(client, dict) or client.get("platform") != "web":
            add("error", "client.platform", 'dsh.client.platform must be "web"')
        if client_export is None:
            add("error", "exports.client", 'dsh.client requires exports["./client"]')
    elif client_export is not None:
        add("error", "client.manifest", 'exports["./client"] requires dsh.client')

    dependencies = package.get("dependencies")
    dependencies = dependencies if isinstance(dependencies, dict) else {}
    peer_dependencies = package.get("peerDependencies")
    peer_dependencies = peer_dependencies if isinstance(peer_dependencies, dict) else {}
    dev_dependencies = package.get("devDependencies")
    dev_dependencies = dev_dependencies if isinstance(dev_dependencies, dict) else {}
    if "@deepseek-ai/cordis" in dependencies:
        add("error", "dependency.cordis", "Cordis belongs in peerDependencies, not dependencies")
    if "@deepseek-ai/cordis" not in peer_dependencies:
        add("error", "peer.cordis", "missing @deepseek-ai/cordis peerDependency")
    for section, entries in (("dependencies", dependencies), ("devDependencies", dev_dependencies)):
        for dependency, version in entries.items():
            if not (dependency == "@deepseek-ai/dsh" or dependency.startswith("@deepseek-ai/dsh-")):
                continue
            if not isinstance(version, str) or not exact_version(version):
                add("error", "dependency.floating", f"{section}: {dependency} needs an exact test/build version, got {version}")
            elif dsh_version is not None and version != dsh_version:
                add("error", "dependency.runtime", f"{section}: {dependency} is {version}, target runtime is {dsh_version}")
    for dependency in peer_dependencies:
        if dependency.startswith("@deepseek-ai/dsh-") and dependency not in dev_dependencies:
            add("warning", "peer.development", f"{dependency} has no pinned devDependency for standalone checks")

    engines = package.get("engines", {})
    if not isinstance(engines, dict):
        add("error", "engines.invalid", "engines must be an object")
    else:
        requirement = engines.get("dsh")
        if requirement is None:
            add("warning", "engines.dsh", "declare engines.dsh; otherwise the launcher uses DSH peer requirements")
        elif not isinstance(requirement, str) or not requirement.strip() or requirement.startswith("workspace:"):
            add("error", "engines.dsh", "engines.dsh must be a non-empty SemVer requirement, not workspace:")
        elif exact_version(requirement) and dsh_version is not None and requirement != dsh_version:
            add("error", "engines.runtime", f"engines.dsh is {requirement}, target runtime is {dsh_version}")
        if not engines.get("node"):
            add("warning", "engines.node", "declare the target runtime's Node.js floor")

    scripts = package.get("scripts")
    scripts = scripts if isinstance(scripts, dict) else {}
    for required_script in ("build", "typecheck", "test"):
        if not isinstance(scripts.get(required_script), str):
            add("error", "scripts.missing", f"missing {required_script} script")

    files = package.get("files")
    patterns = [entry for entry in files if isinstance(entry, str)] if isinstance(files, list) else []
    if not patterns:
        add("warning", "package.files", "package.json has no files allowlist")
    else:
        for target in [*export_paths, *patches]:
            if not file_is_packed(target, patterns):
                add("error", "package.unpacked", f"package files do not include {target}")

    source_path = plugin_dir / "src/index.ts"
    if source_path.is_file():
        source = source_path.read_text(encoding="utf-8")
        if re.search(r"export\s+default\s+(?:async\s+)?(?:function\s+)?apply\b", source):
            add("error", "source.default-apply", "function plugin must not default-export apply")
        if not re.search(r"export\s+(?:async\s+)?function\s+apply\b|export\s+const\s+apply\b", source):
            add("warning", "source.apply", "no named apply export found; confirm this is a Service class")
        for exported in ("name", "inject"):
            if not re.search(rf"export\s+const\s+{exported}\b", source):
                add("warning", f"source.{exported}", f"no named {exported} export found")

    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit Host package shape; does not evaluate SemVer ranges or replace install, Loader or unload tests."
    )
    parser.add_argument("plugin_dir", type=Path)
    parser.add_argument("--require-built", action="store_true", help="require exported JS files")
    parser.add_argument("--dsh-version", help="require runtime dependencies to match this exact version")
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dsh_version is not None and not exact_version(args.dsh_version):
        print("error: --dsh-version must be an exact semver", file=sys.stderr)
        return 2
    root = args.plugin_dir.expanduser().resolve()
    findings = audit(root, args.require_built, args.dsh_version)
    errors = sum(finding.severity == "error" for finding in findings)
    warnings = sum(finding.severity == "warning" for finding in findings)
    if args.json:
        print(json.dumps({
            "plugin": str(root),
            "ok": errors == 0,
            "errors": errors,
            "warnings": warnings,
            "findings": [asdict(finding) for finding in findings],
        }, ensure_ascii=False, indent=2))
    else:
        for finding in findings:
            print(f"{finding.severity.upper()} [{finding.code}] {finding.message}")
        status = "PASS" if errors == 0 else "FAIL"
        print(f"{status}: {root} ({errors} errors, {warnings} warnings)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
