"""UGC template loader — reads YAML templates from disk."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_template(template_path: Path) -> dict[str, Any]:
    with open(template_path) as f:
        return yaml.safe_load(f)


def load_all_templates(templates_dir: Path) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    if not templates_dir.exists():
        return templates
    for yaml_file in sorted(templates_dir.glob("*.yaml")):
        try:
            templates.append(load_template(yaml_file))
        except Exception:
            continue
    return templates


def find_template(templates_dir: Path, slug: str) -> dict[str, Any] | None:
    path = templates_dir / f"{slug}.yaml"
    if path.exists():
        return load_template(path)
    return None
