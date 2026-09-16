from __future__ import annotations

import json
from pathlib import Path


CONFIG_PATH = Path("app/ui_config.json")

DEFAULT_UI_CONFIG = {
    "client_badge": "Автоматизация транспортной компании",
    "client_title": "АвтоТранс",
    "client_description": "Управление грузовиками, водителями, рейсами и финансами",
    "sections_order": ["contacts", "cargo", "route"],
    "show_map": False,
    "model_mode": "dae",
}


def load_ui_config() -> dict:
    if not CONFIG_PATH.exists():
        save_ui_config(DEFAULT_UI_CONFIG)
        return DEFAULT_UI_CONFIG.copy()

    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return {**DEFAULT_UI_CONFIG, **data}


def save_ui_config(data: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_sections_order(values: list[str]) -> list[str]:
    allowed = ["contacts", "cargo", "route"]
    normalized = []
    for value in values:
        if value in allowed and value not in normalized:
            normalized.append(value)
    for value in allowed:
        if value not in normalized:
            normalized.append(value)
    return normalized

