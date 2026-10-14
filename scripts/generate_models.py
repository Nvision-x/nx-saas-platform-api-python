from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "openapi" / "openapi.yaml"
OUT = ROOT / "src" / "nvisionx" / "_models.py"
TYPES = ROOT / "src" / "nvisionx" / "types.py"

SKIP_PATHS = {"/mcp"}
RENAMES = {"Error1": "ErrorDetail"}
INFO_KEYS = ("title", "version", "summary")


def refs(node: object) -> set[str]:
    found: set[str] = set()
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/"):
            found.add(ref)
        for value in node.values():
            found |= refs(value)
    elif isinstance(node, list):
        for value in node:
            found |= refs(value)
    return found


def resolve(spec: dict[str, Any], ref: str) -> Any:
    node: Any = spec
    for part in ref.removeprefix("#/").split("/"):
        node = node[part]
    return node


def prune(spec: dict) -> dict:
    paths: dict = {}
    for path, item in spec["paths"].items():
        if path in SKIP_PATHS:
            continue
        ops = {method: op for method, op in item.items() if isinstance(op, dict) and "x-required-scope" in op}
        if ops:
            shared = {k: v for k, v in item.items() if k == "parameters"}
            paths[path] = {**shared, **ops}

    seen: set[str] = set()
    todo = refs(paths) | {"#/components/schemas/ErrorType", "#/components/securitySchemes/bearerAuth"}
    while todo:
        ref = todo.pop()
        if ref in seen:
            continue
        seen.add(ref)
        todo |= refs(resolve(spec, ref)) - seen

    components: dict = {}
    for ref in sorted(seen):
        _, _, kind, name = ref.split("/")
        components.setdefault(kind, {})[name] = spec["components"][kind][name]

    return {
        "openapi": spec["openapi"],
        "info": {k: spec["info"][k] for k in INFO_KEYS if k in spec["info"]},
        "servers": spec.get("servers", []),
        "security": [{"bearerAuth": []}],
        "paths": paths,
        "components": components,
    }


def generate() -> None:
    cmd = [
        sys.executable,
        "-m",
        "datamodel_code_generator",
        "--input",
        str(SPEC),
        "--input-file-type",
        "openapi",
        "--output",
        str(OUT),
        "--output-model-type",
        "pydantic_v2.BaseModel",
        "--target-python-version",
        "3.10",
        "--use-annotated",
        "--use-standard-collections",
        "--use-union-operator",
        "--use-type-alias",
        "--use-schema-description",
        "--use-field-description",
        "--field-constraints",
        "--enum-field-as-literal",
        "all",
        "--use-double-quotes",
        "--disable-timestamp",
        "--formatters",
        "builtin",
        "--type-mappings",
        "string+uri=string",
        "string+email=string",
        "--base-class",
        "nvisionx._base.NxModel",
    ]
    subprocess.run(cmd, check=True)
    lines = OUT.read_text().splitlines()
    while lines and (lines[0].startswith("#") or not lines[0].strip()):
        lines.pop(0)
    source = "\n".join(lines) + "\n"
    for old, new in RENAMES.items():
        source = re.sub(rf"\b{old}\b", new, source)
    source = re.sub(r"Literal\[[^\[\]]*\]", lambda m: f"Annotated[{m.group(0)}, Open]", source)
    source = source.replace("from nvisionx._base import NxModel", "from nvisionx._base import NxModel, Open")
    OUT.write_text(source)
    subprocess.run([sys.executable, "-m", "ruff", "format", "-q", str(OUT)], check=True)
    subprocess.run([sys.executable, "-m", "ruff", "check", "-q", "--fix", "--select", "I,F401", str(OUT)], check=True)
    write_types(OUT.read_text())


def write_types(models: str) -> None:
    matches = re.findall(r"^(?:class (\w+)\(|(\w+) = TypeAliasType\()", models, re.M)
    exported = sorted({cls or alias for cls, alias in matches})
    lines = ["from nvisionx._models import ("]
    lines += [f"    {name}," for name in exported]
    lines += [")", "", "SearchFilters = Filters", "", "__all__ = ["]
    lines += [f'    "{name}",' for name in [*exported, "SearchFilters"]]
    lines += ["]", ""]
    TYPES.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate the SDK models.")
    parser.add_argument(
        "--from-spec", type=Path, help="Full Nx Platform OpenAPI document to prune into openapi/openapi.yaml first."
    )
    args = parser.parse_args()

    if args.from_spec:
        pruned = prune(yaml.safe_load(args.from_spec.read_text()))
        SPEC.parent.mkdir(exist_ok=True)
        SPEC.write_text(yaml.safe_dump(pruned, sort_keys=False, allow_unicode=True, width=120))
    generate()
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
