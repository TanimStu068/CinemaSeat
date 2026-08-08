import json
import hmac
import hashlib
import asyncio
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import AsyncSessionLocal
from redis_client import redis_client
from config import settings
import models

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/payment")
async def payment_webhook(request: Request):
    raw_body = await request.body()
    
    # HMAC verification
    sig = request.headers.get("X-Signature", "")
    secret = settings.GATEWAY_SECRET.encode()
    expected = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(expected, sig):
        # Always return 200 to prevent retries even if signature fails
        return {"status": "ok"}

    try:
        payload = json.loads(raw_body)
    except Exception:
        return {"status": "ok"}

    event_id = payload.get("event_id")
    booking_ref = payload.get("booking_ref")
    gw_status = payload.get("status")

    if not event_id or not booking_ref:
        return {"status": "ok"}

    # Idempotency
    if not await redis_client.setnx(f"event:{event_id}", "1"):
        return {"status": "ok"}
    await redis_client.expire(f"event:{event_id}", 86400)

    # Handle race condition
    booking = None
    for _ in range(6):
        async with AsyncSessionLocal() as db:
            booking = await db.scalar(
                select(models.Booking).where(models.Booking.booking_ref == booking_ref)
            )
        if booking:
            break
        await asyncio.sleep(0.5)

    if not booking:
        return {"status": "ok"}

    async with AsyncSessionLocal() as db:
        async with db.begin():
            b = await db.scalar(
                select(models.Booking)
                .where(models.Booking.booking_ref == booking_ref)
                .with_for_update()
            )
            if not b or b.status in ("SUCCEEDED", "FAILED", "REFUNDED"):
                return {"status": "ok"}

            b.event_id = event_id
            seat = await db.get(models.Seat, b.seat_id)

            if gw_status == "SUCCEEDED":
                b.status = "SUCCEEDED"
                seat.status = "BOOKED"
            elif gw_status == "FAILED":
                b.status = "FAILED"
                seat.status = "AVAILABLE"
                seat.held_by = None
                seat.held_until = None
            elif gw_status == "REFUNDED":
                b.status = "REFUNDED"
                seat.status = "AVAILABLE"
                seat.held_by = None
                seat.held_until = None

    return {"status": "ok"}

@router.post("/otp")
async def otp_webhook(request: Request):
    try:
        payload = await request.json()
        ref = payload.get("ref")
        code = payload.get("code")
        if ref and code:
            await redis_client.setex(f"otp:{ref}", 600, code)
            
            async with AsyncSessionLocal() as db:
                async with db.begin():
                    b = await db.scalar(
                        select(models.Booking).where(models.Booking.booking_ref == ref)
                    )
                    if b and b.status == "PENDING":
                        b.status = "OTP_SENT"
    except Exception:
        pass
    return {"status": "ok"}
