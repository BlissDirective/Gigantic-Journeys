"""Reference validator for the v1 avatar data contracts (AUTH #044).

``avatar_params`` and ``consent_record`` are the **non-biometric** contracts for the v1
custom-avatar feature. This module validates a document against its schema and enforces the privacy
guard that an avatar parameter set carries no biometric / media field (defense in depth — the
schemas are closed, so such a field cannot occur, but the guard documents the intent). The on-device
C# runtime mirrors these checks. jsonschema + standard library only.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
KINDS = ("avatar_params", "consent_record")

# Key-name fragments that must never appear anywhere in an avatar parameter set.
FORBIDDEN = (
    "photo",
    "image",
    "video",
    "landmark",
    "embedding",
    "template",
    "descriptor",
    "mesh",
    "scan",
    "depth",
    "texture",
    "pixel",
    "biometric",
    "faceid",
    "encoding",
    "media",
)


def _schema(kind: str) -> dict:
    return json.loads((HERE / f"{kind}.schema.json").read_text(encoding="utf-8"))


def validator(kind: str) -> Draft202012Validator:
    if kind not in KINDS:
        raise ValueError(f"unknown kind {kind!r}")
    schema = _schema(kind)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate(doc: dict, kind: str) -> list[str]:
    """Schema-validate ``doc`` as ``kind``; return a sorted list of error messages ([] if valid)."""
    return sorted(e.message for e in validator(kind).iter_errors(doc))


def forbidden_keys(doc: object) -> list[str]:
    """Keys anywhere in ``doc`` whose name contains a biometric/media fragment (must be empty)."""
    found: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if any(frag in key.lower() for frag in FORBIDDEN):
                    found.append(key)
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(doc)
    return sorted(set(found))
