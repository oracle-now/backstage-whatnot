from __future__ import annotations

from .config import Settings
from .extract_orders import run as extract_orders
from .postprocess_orders import run as postprocess_orders


def run(settings: Settings | None = None) -> dict:
    settings = settings or Settings()
    raw = extract_orders(settings)
    processed = postprocess_orders(raw, settings)
    return {"raw": raw, "processed": processed}


if __name__ == "__main__":
    print(run())
