from __future__ import annotations

from fastapi import HTTPException


KNOWN_ROUTES_KM: dict[tuple[str, str], float] = {
    ("москва", "санкт-петербург"): 710,
    ("москва", "казань"): 820,
    ("москва", "екатеринбург"): 1780,
    ("москва", "новосибирск"): 3360,
    ("москва", "ростов-на-дону"): 1080,
    ("санкт-петербург", "казань"): 1510,
    ("санкт-петербург", "екатеринбург"): 2310,
    ("казань", "екатеринбург"): 950,
    ("екатеринбург", "новосибирск"): 1560,
    ("ташкент", "самарканд"): 305,
    ("ташкент", "бухара"): 575,
    ("ташкент", "алматы"): 815,
}


def normalize_location(value: str) -> str:
    return " ".join(value.strip().lower().split())


def route_key(origin: str, destination: str) -> tuple[str, str]:
    return normalize_location(origin), normalize_location(destination)


def get_known_distance(origin: str, destination: str) -> float | None:
    key = route_key(origin, destination)
    reverse_key = key[1], key[0]
    return KNOWN_ROUTES_KM.get(key) or KNOWN_ROUTES_KM.get(reverse_key)


def require_distance(origin: str, destination: str, provided_distance: float | None = None) -> float:
    if provided_distance is not None:
        return provided_distance
    if not destination:
        raise HTTPException(status_code=422, detail="Укажите расстояние вручную, если точка доставки ещё не определена.")
    distance = get_known_distance(origin, destination)
    if distance is None:
        raise HTTPException(
            status_code=422,
            detail="Расстояние для маршрута неизвестно. Передайте distance_km или добавьте маршрут в таблицу.",
        )
    return distance
