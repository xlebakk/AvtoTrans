from __future__ import annotations

import json
from pathlib import Path


CONFIG_PATH = Path("app/ui_config.json")

CURRENCIES: dict[str, dict] = {
    "TJS": {"code": "TJS", "symbol": "с.", "name": "Таджикский сомони", "flag": "🇹🇯"},
    "RUB": {"code": "RUB", "symbol": "₽",    "name": "Российский рубль",  "flag": "🇷🇺"},
    "USD": {"code": "USD", "symbol": "$",    "name": "Доллар США",         "flag": "🇺🇸"},
    "EUR": {"code": "EUR", "symbol": "€",    "name": "Евро",               "flag": "🇪🇺"},
    "CNY": {"code": "CNY", "symbol": "¥",    "name": "Китайский юань",    "flag": "🇨🇳"},
    "KZT": {"code": "KZT", "symbol": "₸",    "name": "Казахский тенге",   "flag": "🇰🇿"},
    "UZS": {"code": "UZS", "symbol": "сўм",  "name": "Узбекский сум",     "flag": "🇺🇿"},
    "KGS": {"code": "KGS", "symbol": "сом",   "name": "Киргизский сом",    "flag": "🇰🇬"},
}

DEFAULT_UI_CONFIG = {
    "client_badge": "Автоматизация транспортной компании",
    "client_title": "АвтоТранс",
    "client_description": "Управление грузовиками, водителями, рейсами и финансами",
    "sections_order": ["contacts", "cargo", "route"],
    "show_map": False,
    "model_mode": "dae",
    "currency": "TJS",
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


def get_currency_info(cfg: dict | None = None) -> dict:
    if cfg is None:
        cfg = load_ui_config()
    code = cfg.get("currency", "TJS")
    return CURRENCIES.get(code, CURRENCIES["TJS"])


def get_currency_symbol(cfg: dict | None = None) -> str:
    return get_currency_info(cfg)["symbol"]

