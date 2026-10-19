"""Order Service: owns orders and asks Inventory whether stock is available."""

import logging
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import quote

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")
logger = logging.getLogger("order_service")

INVENTORY_URL = os.environ.get("INVENTORY_URL", "http://localhost:8081")
INVENTORY_TIMEOUT_SECONDS = 2.0

app = FastAPI(title="Order Service")

# In-memory orders. This service is the only owner of this data.
ORDERS: dict[str, "Order"] = {}


class OrderRequest(BaseModel):
    item_id: str
    quantity: int = Field(ge=1)


class Order(BaseModel):
    id: str
    item_id: str
    quantity: int
    status: str
    created_at: datetime



@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/orders", status_code=201, response_model=Order)
async def create_order(request: OrderRequest) -> Order:
    """Command: create an order if Inventory reports the stock available."""
    if not await check_availability(request.item_id, request.quantity):
        logger.info("rejected order for %r: item unavailable",
                    request.item_id)
        raise HTTPException(409, "item unavailable")

    order = Order(
        id=str(uuid.uuid4()),
        item_id=request.item_id,
        quantity=request.quantity,
        status="CREATED",
        created_at=datetime.now(timezone.utc),
    )
    ORDERS[order.id] = order
    logger.info(
        "[event] OrderCreated order_id=%s item_id=%s "
        "(would publish to broker)", order.id, order.item_id)
    return order


@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: str) -> Order:
    order = ORDERS.get(order_id)
    if order is None:
        raise HTTPException(404, "order not found")
    return order
