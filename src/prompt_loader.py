from pathlib import Path
from string import Template

import yaml


def load_prompts(path="prompts/prompts.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def render(template: str, **values) -> str:
    """Fill $placeholders. Braces in JSON examples are left untouched."""
    return Template(template).safe_substitute(**values)


def load_config(path="config.yaml"):
    with open(Path(path), encoding="utf-8") as f:
        return yaml.safe_load(f)
