"""Inventory Service: owns stock levels and answers availability queries."""

from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="Inventory Service")

# In-memory stock levels. This service is the only owner of this data.
STOCK: dict[str, int] = {"widget": 10, "gadget": 0, "gizmo": 3}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/items/{item_id}/availability")
def check_availability(item_id: str, qty: int = Query(1, ge=1)) -> dict:
    """Query: report whether `qty` units are in stock.

    Read-only; never changes stock.
    """
    if item_id not in STOCK:
        raise HTTPException(status_code=404, detail="unknown item")
    return {
        "item_id": item_id,
        "requested": qty,
        "available": STOCK[item_id] >= qty,
    }
