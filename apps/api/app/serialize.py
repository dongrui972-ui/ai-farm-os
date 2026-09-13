from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models import Zone


def row(obj: Any, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    data = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    if extra:
        data.update(extra)
    return data


def zone_map(db: Session) -> dict[str, Zone]:
    return {z.id: z for z in db.query(Zone).all()}


def zone_code(zones: dict[str, Zone], zone_id: str | None) -> str | None:
    if not zone_id:
        return None
    zone = zones.get(zone_id)
    return zone.code if zone else None


def parse_polygon(raw: str) -> list[dict[str, float]]:
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    return []
