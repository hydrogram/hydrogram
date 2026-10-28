#!/usr/bin/env python3
# Hydrogram - Telegram MTProto API Client Library for Python
# Copyright (C) 2023-present Hydrogram <https://hydrogram.org>
#
# This file is part of Hydrogram.
#
# Hydrogram is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hydrogram is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hydrogram.  If not, see <http://www.gnu.org/licenses/>.

"""Check schema drift (0=current, 2=drift, 1=error); apply only after validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from collections.abc import Mapping

REPO_HOME = Path(__file__).resolve().parent.parent
SCHEMA_PATH = Path("compiler/api/source/main_api.tl")
PROVENANCE_PATH = Path("compiler/api/source/provenance.json")
DESKTOP_REPO = "telegramdesktop/tdesktop"
DESKTOP_PATH = "Telegram/SourceFiles/mtproto/scheme/api.tl"
TDLIB_REPO = "tdlib/td"
TDLIB_PATH = "td/generate/scheme/telegram_api.tl"
LAYER_RE = re.compile(r"^//\s*LAYER\s+(\d+)\s*$", re.MULTILINE)
DEFINITION_RE = re.compile(r"^([\w.]+)#([0-9a-f]{1,8})\s+.*?=\s*([\w.<> ]+);$")
BASIC_DECLARATIONS = {
    "boolFalse": "boolFalse#bc799737 = Bool;",
    "boolTrue": "boolTrue#997275b5 = Bool;",
    "true": "true#3fedd339 = True;",
    "vector": "vector#1cb5c415 {t:Type} # [ t ] = Vector t;",
    "error": "error#c4b9f9bb code:int text:string = Error;",
    "null": "null#56730bcc = Null;",
}
BASIC_NAMES = BASIC_DECLARATIONS.keys()
GENERATED_PATHS = (
    "hydrogram/raw/all.py",
    "hydrogram/raw/base",
    "hydrogram/raw/types",
    "hydrogram/raw/functions",
    "hydrogram/errors/exceptions",
)
SCHEMA_HEADER = """// Source and checksums: provenance.json

///////////////////////////////
///////// Main application API
///////////////////////////////

---types---

// boolFalse#bc799737 = Bool;  // Parsed manually
// boolTrue#997275b5 = Bool;  // Parsed manually
// true#3fedd339 = True;  // Not used
// vector#1cb5c415 {t:Type} # [ t ] = Vector t;  // Parsed manually
// error#c4b9f9bb code:int text:string = Error;  // Not used
// null#56730bcc = Null;  // Parsed manually
"""


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def get_layer(schema: str) -> int:
    layers = LAYER_RE.findall(schema)
    if len(layers) != 1:
        raise ValueError("Expected exactly one numeric // LAYER marker")
    return int(layers[0])


def definitions(schema: str, *, strict: bool = True) -> dict[str, str]:
    """Parse declarations without silently dropping unsupported TL syntax."""
    result = {}
    ids = set()
    for original in schema.splitlines():
        line = original.split("//", 1)[0].strip()
        if not line or line in {"---types---", "---functions---"}:
            continue
        match = DEFINITION_RE.fullmatch(line)
        if not match:
            if strict:
                raise ValueError(f"Unsupported TL declaration: {line}")
            continue  # TDLib has extra primitive/test declarations without IDs.
        name, constructor_id, _ = match.groups()
        if name in result or (strict and int(constructor_id, 16) in ids):
            raise ValueError(f"Duplicate TL name or constructor ID: {name}")
        ids.add(int(constructor_id, 16))
        result[name] = " ".join(line.split())
    if not result:
        raise ValueError("Schema contains no declarations")
    return result


def normalize_schema(schema: str) -> str:
    """Keep wire declarations verbatim; Hydrogram handles basic types itself."""
    layer = get_layer(schema)
    if schema.count("---functions---") != 1 or schema.count("---types---") > 1:
        raise ValueError("Expected one functions section and at most one types section")
    declarations = definitions(schema)
    if not declarations.keys() >= BASIC_NAMES:
        raise ValueError("Upstream schema is missing basic types")
    if any(declarations[name] != value for name, value in BASIC_DECLARATIONS.items()):
        raise ValueError("Manually handled basic types changed upstream")
    lines = []
    for original in schema.splitlines():
        line = original.strip()
        if line == "---types---" or LAYER_RE.fullmatch(line):
            continue
        if (match := DEFINITION_RE.fullmatch(line)) and match[1] in BASIC_NAMES:
            continue
        lines.append(original.rstrip())
    content = "\n".join(lines).strip()
    return f"{SCHEMA_HEADER}\n{content}\n\n// LAYER {layer}\n"


def fetch_source(repository: str, path: str, revision: str) -> tuple[str, dict]:
    """Resolve a branch once, then download only from an immutable commit."""
    response = requests.get(
        f"https://api.github.com/repos/{repository}/commits/{revision}", timeout=30
    )
    response.raise_for_status()
    commit = response.json()["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Invalid upstream commit SHA")
    url = f"https://raw.githubusercontent.com/{repository}/{commit}/{path}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.content
    return data.decode("utf-8"), {
        "repository": repository,
        "revision": commit,
        "path": path,
        "url": url,
        "sha256": sha256(data),
    }


def compare_sources(desktop: str, tdlib: str) -> dict:
    primary = definitions(desktop)
    secondary = definitions(tdlib, strict=False)
    shared = primary.keys() & secondary.keys()
    changed = sorted(name for name in shared if primary[name] != secondary[name])
    missing = sorted(primary.keys() - secondary.keys() - {"null"})
    return {"shared": len(shared), "changed": changed, "missing_from_tdlib": missing}


def schema_diff(old: str, new: str) -> dict[str, dict]:
    before, after = definitions(old), definitions(new)
    return {
        "added": {k: after[k] for k in sorted(after.keys() - before.keys())},
        "removed": {k: before[k] for k in sorted(before.keys() - after.keys())},
        "changed": {
            k: {"before": before[k], "after": after[k]}
            for k in sorted(before.keys() & after.keys())
            if before[k] != after[k]
        },
    }


def render_report(old: str, new: str, provenance: dict) -> str:
    diff = schema_diff(old, new)
    source = provenance["desktop"]
    comparison = provenance["comparison"]
    lines = [
        f"# MTProto schema: layer {get_layer(old)} → {get_layer(new)}",
        "",
        f"Source: {source['url']}",
        f"SHA-256: `{source['sha256']}`",
        f"TDLib: {provenance['tdlib']['url']}",
        f"Shared declarations: {comparison['shared']}; disagreements: {comparison['changed']}; "
        f"missing from TDLib: {comparison['missing_from_tdlib']}.",
        "",
        "Raw schema coverage does not imply high-level Client method or parser coverage.",
        "Review changed IDs, flags, argument types, return types, and handwritten callers.",
        "Review RPC errors separately against https://core.telegram.org/api/errors and affected "
        "method pages; errors are not part of TL and have no complete layer-pinned catalogue.",
        "Review compiler/api/docs.json against affected signatures; documentation may lag TL.",
        "",
    ]
    for kind, entries in diff.items():
        lines.extend([f"## {kind.title()} ({len(entries)})", ""])
        for name, value in entries.items():
            lines.extend([f"### {name}", "```tl"])
            if kind == "changed":
                lines.extend([value["before"], value["after"]])
            else:
                lines.append(value)
            lines.extend(["```", ""])
    lines.extend([
        "## Adoption",
        "",
        "Run `uv run python dev_tools/check_api_schema_updates.py --apply "
        f"--revision {source['revision']} --tdlib-revision {provenance['tdlib']['revision']}`.",
        "Application validates generation and the full offline test suite in a temporary checkout "
        "before replacing inputs. If it fails, fix the compiler/callers and add regression tests; "
        "rerun the pinned command. Add a news fragment and review the resulting diff.",
        "Generated modules are ignored; only compiler inputs and handwritten changes belong in Git.",
        "",
    ])
    return "\n".join(lines)


def generated_hashes(root: Path) -> dict[str, str]:
    result = {}
    for relative in GENERATED_PATHS:
        path = root / relative
        files = [path] if path.is_file() else sorted(path.rglob("*.py"))
        for file in files:
            result[file.relative_to(root).as_posix()] = sha256(file.read_bytes())
    return result


def validate_generation(root: Path) -> None:
    """Check repeatability both in-process and across different hash seeds."""
    generation = (
        "from compiler.api.compiler import start as api; "
        "from compiler.errors.compiler import start as errors; api(); errors()"
    )
    env = {**os.environ, "PYTHONPATH": str(root), "PYTHONHASHSEED": "1"}
    repeated = (
        generation
        + "; "
        + (
            "from dev_tools.check_api_schema_updates import generated_hashes; "
            "from pathlib import Path; before = generated_hashes(Path.cwd()); "
        )
        + generation
        + "; assert before == generated_hashes(Path.cwd()), 'In-process generation differs'"
    )
    subprocess.run([sys.executable, "-c", repeated], cwd=root, env=env, check=True, timeout=120)
    before = generated_hashes(root)
    env["PYTHONHASHSEED"] = "2"
    subprocess.run([sys.executable, "-c", generation], cwd=root, env=env, check=True, timeout=120)
    if before != generated_hashes(root):
        raise ValueError("Generated output differs across hash seeds")
    subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests"], cwd=root, env=env, check=True, timeout=300
    )


def validate_candidate(repo: Path, replacements: Mapping[Path, str]) -> None:
    """Never overwrite the working inputs with an unvalidated network response."""
    with tempfile.TemporaryDirectory(prefix="hydrogram-schema-") as directory:
        root = Path(directory)
        for name in ("compiler", "hydrogram", "tests", "dev_tools"):
            shutil.copytree(
                repo / name, root / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
            )
        for name in ("NOTICE", "pyproject.toml"):
            shutil.copy2(repo / name, root / name)
        for path, content in replacements.items():
            (root / path).write_text(content, encoding="utf-8")
        validate_generation(root)


def check_provenance(repo: Path) -> None:
    provenance = json.loads((repo / PROVENANCE_PATH).read_text(encoding="utf-8"))
    content = (repo / SCHEMA_PATH).read_bytes()
    if provenance["normalized_sha256"] != sha256(content):
        raise ValueError("Schema checksum differs from provenance.json")
    if provenance["layer"] != get_layer(content.decode("utf-8")):
        raise ValueError("Schema layer differs from provenance.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Validate and apply the candidate")
    parser.add_argument("--validate", action="store_true", help="Validate local inputs offline")
    parser.add_argument("--revision", default="dev", help="Telegram Desktop branch or commit")
    parser.add_argument("--tdlib-revision", default="master", help="TDLib branch or commit")
    parser.add_argument("--report", type=Path, help="Write a Markdown adoption report")
    parser.add_argument(
        "--json-report", type=Path, help="Write provenance and declaration changes"
    )
    args = parser.parse_args(argv)
    try:
        if args.validate:
            check_provenance(REPO_HOME)
            validate_candidate(REPO_HOME, {})
            return 0
        old = (REPO_HOME / SCHEMA_PATH).read_text(encoding="utf-8")
        desktop, source = fetch_source(DESKTOP_REPO, DESKTOP_PATH, args.revision)
        tdlib, secondary = fetch_source(TDLIB_REPO, TDLIB_PATH, args.tdlib_revision)
        new = normalize_schema(desktop)
        provenance = {
            "layer": get_layer(new),
            "desktop": source,
            "tdlib": secondary,
            "comparison": compare_sources(desktop, tdlib),
            "normalized_sha256": sha256(new.encode("utf-8")),
        }
        if args.json_report:
            args.json_report.write_text(
                json.dumps({"provenance": provenance, "diff": schema_diff(old, new)}, indent=2)
                + "\n",
                encoding="utf-8",
            )
        report = render_report(old, new, provenance)
        if args.report:
            args.report.write_text(report, encoding="utf-8")
        else:
            print(report)
        if get_layer(new) < get_layer(old):
            raise ValueError("Refusing a schema layer downgrade")
        comparison = provenance["comparison"]
        if comparison["changed"] or comparison["missing_from_tdlib"]:
            raise ValueError(
                "Telegram Desktop and TDLib disagree; review the report before adoption"
            )
        drift = old != new
        if not args.apply:
            if not drift:
                check_provenance(REPO_HOME)
            return 2 if drift else 0
        # A metadata-only upstream commit must not create endless schema updates.
        if not drift:
            check_provenance(REPO_HOME)
            validate_candidate(REPO_HOME, {})
            return 0
        replacements = {
            SCHEMA_PATH: new,
            PROVENANCE_PATH: json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        }
        validate_candidate(REPO_HOME, replacements)
        for path, content in replacements.items():
            destination = REPO_HOME / path
            temporary = destination.with_suffix(destination.suffix + ".tmp")
            temporary.write_text(content, encoding="utf-8")
            temporary.replace(destination)
        if args.report:
            with args.report.open("a", encoding="utf-8") as report_file:
                report_file.write(
                    "\nValidation: deterministic generation and all offline tests passed.\n"
                )
    except (
        requests.RequestException,
        ValueError,
        KeyError,
        OSError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ) as error:
        message = f"Schema update blocked: {error}"
        print(message, file=sys.stderr)
        if args.report:
            with args.report.open("a", encoding="utf-8") as report_file:
                report_file.write(f"\nValidation failed: {message}\nInputs were not updated.\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
