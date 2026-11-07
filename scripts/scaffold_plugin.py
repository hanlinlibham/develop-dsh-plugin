#!/usr/bin/env python3
"""Create a minimal, buildable Host-only DSH plugin from the bundled template."""

from __future__ import annotations

import argparse
import re
import shlex
import sys
from pathlib import Path
from typing import NoReturn


PACKAGE_RE = re.compile(r"(?:@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*\Z")
PLUGIN_ID_RE = re.compile(r"[a-z][a-z0-9-]*\Z")
TOOL_NAME_RE = re.compile(r"[a-z][a-z0-9_]*\Z")
EXACT_VERSION_RE = re.compile(
    r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?\Z"
)
TOKEN_RE = re.compile(r"__[A-Z0-9_]+__")


def fail(message: str) -> NoReturn:
    raise ValueError(message)


def infer_plugin_id(package_name: str) -> str:
    leaf = package_name.rsplit("/", 1)[-1]
    for prefix in ("dsh-plugin-", "dsh-"):
        if leaf.startswith(prefix):
            leaf = leaf[len(prefix) :]
            break
    value = re.sub(r"[^a-z0-9]+", "-", leaf).strip("-")
    if not PLUGIN_ID_RE.fullmatch(value):
        fail("cannot infer a valid plugin id; pass --plugin-id")
    return value


def validate_exact_version(label: str, value: str) -> None:
    if not EXACT_VERSION_RE.fullmatch(value):
        fail(f"{label} must be an exact semver, for example 0.1.0-rc.6")


def render_template(template_dir: Path, substitutions: dict[str, str]) -> dict[Path, str]:
    rendered: dict[Path, str] = {}
    for source in sorted(path for path in template_dir.rglob("*") if path.is_file()):
        relative = source.relative_to(template_dir)
        if relative.name.endswith(".tmpl"):
            relative = relative.with_name(relative.name.removesuffix(".tmpl"))
        content = source.read_text(encoding="utf-8")
        for token, value in substitutions.items():
            content = content.replace(token, value)
        unresolved = sorted(set(TOKEN_RE.findall(content)))
        if unresolved:
            fail(f"unresolved template tokens in {source}: {', '.join(unresolved)}")
        rendered[relative] = content
    if not rendered:
        fail(f"template is empty: {template_dir}")
    return rendered


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a minimal Host-only DSH tool plugin without overwriting files."
    )
    parser.add_argument("destination", type=Path, help="new or empty output directory")
    parser.add_argument("--package-name", required=True, help="npm package name")
    parser.add_argument("--dsh-version", required=True, help="exact target DSH version")
    parser.add_argument("--cordis-version", required=True, help="exact target Cordis version")
    parser.add_argument("--plugin-id", help="Cordis row id; inferred from package name")
    parser.add_argument("--tool-name", help="model tool name; defaults to <plugin-id>_status")
    parser.add_argument(
        "--package-manager", choices=("npm", "pnpm"), default="npm"
    )
    parser.add_argument("--dry-run", action="store_true", help="show files without writing")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if not PACKAGE_RE.fullmatch(args.package_name):
            fail("--package-name must be a lowercase npm package name")
        validate_exact_version("--dsh-version", args.dsh_version)
        validate_exact_version("--cordis-version", args.cordis_version)

        plugin_id = args.plugin_id or infer_plugin_id(args.package_name)
        if not PLUGIN_ID_RE.fullmatch(plugin_id):
            fail("--plugin-id must match [a-z][a-z0-9-]*")
        tool_name = args.tool_name or f"{plugin_id.replace('-', '_')}_status"
        if len(tool_name) > 64 or not TOOL_NAME_RE.fullmatch(tool_name):
            fail("--tool-name must be at most 64 chars and match [a-z][a-z0-9_]*")

        destination = args.destination.expanduser()
        if destination.is_symlink():
            fail(f"destination must not be a symlink: {destination}")
        if destination.exists() and (
            not destination.is_dir() or any(destination.iterdir())
        ):
            fail(f"destination must be new or empty: {destination}")

        if args.package_manager == "npm":
            install, check, pack = (
                "npm install",
                "npm run check",
                "npm pack --dry-run",
            )
        else:
            install, check, pack = (
                "pnpm install",
                "pnpm run check",
                "pnpm pack --dry-run",
            )

        template_dir = Path(__file__).resolve().parents[1] / "assets/minimal-host-plugin"
        files = render_template(
            template_dir,
            {
                "__PACKAGE_NAME__": args.package_name,
                "__PLUGIN_ID__": plugin_id,
                "__TOOL_NAME__": tool_name,
                "__DSH_VERSION__": args.dsh_version,
                "__CORDIS_VERSION__": args.cordis_version,
                "__PM_INSTALL__": install,
                "__PM_CHECK__": check,
                "__PM_PACK__": pack,
            },
        )

        if args.dry_run:
            print(f"Would create {len(files)} files in {destination}:")
            for relative in files:
                print(f"  {relative}")
            return 0

        destination.mkdir(parents=True, exist_ok=True)
        for relative, content in files.items():
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        print(f"Created {args.package_name} in {destination} ({len(files)} files).")
        print(f"Next: cd {shlex.quote(str(destination))} && {install} && {check}")
        return 0
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
