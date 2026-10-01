from __future__ import annotations

import json
import os
from pathlib import Path

from domain import ProductTarget


TARGET_SITES = (
    {
        "store": "Flora y Fauna",
        "url": "https://www.florayfauna.pe/cuidado-personal/cuidado-corporal",
    },
    {"store": "Dermashop", "url": "https://dermashop.pe/"},
    {
        "store": "Inkafarma",
        "url": "https://inkafarma.pe/categoria/dermatologia-cosmetica",
    },
)

GOOGLE_SCOPES = (
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.send",
)


def load_product_targets() -> tuple[ProductTarget, ...]:
    path = Path(__file__).with_name("product_targets.json")
    raw_targets = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        ProductTarget(
            product_key=target["product_key"],
            display_name=target["display_name"],
            match_terms=tuple(target["match_terms"]),
        )
        for target in raw_targets
    )


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
