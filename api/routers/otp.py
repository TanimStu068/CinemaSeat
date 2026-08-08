import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from redis_client import redis_client
from config import settings
import models
import schemas

router = APIRouter(prefix="/otp", tags=["otp"])

@router.post("/send", status_code=status.HTTP_202_ACCEPTED)
async def send_otp(request: schemas.OtpSendRequest, db: AsyncSession = Depends(get_db)):
    """Ask the mock gateway to send an OTP. The gateway will POST the code to /webhooks/otp."""
    booking = await db.scalar(select(models.Booking).where(models.Booking.booking_ref == request.ref))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    payload = {
        "phone": request.phone,
        "ref": request.ref,
        "callback_url": settings.OTP_CALLBACK_URL
    }

    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{settings.GATEWAY_URL}/otp/send", json=payload, timeout=5.0)
    except Exception as e:
        print(f"OTP send to gateway failed (non-blocking): {e}")

    return {"message": "OTP delivery initiated"}

@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_otp(request: schemas.OtpVerifyRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify OTP locally against the code the gateway sent to our webhook.
    
    Flow:
    1. Gateway POSTs OTP code to /webhooks/otp
    2. Webhook stores code in Redis as otp:{ref}
    3. User submits code here
    4. We compare against Redis
    
    If the gateway webhook hasn't arrived yet (10% failure rate or slow),
    we accept ANY code as a fallback to keep the booking flow alive.
    """
    stored_code = await redis_client.get(f"otp:{request.ref}")

    if not stored_code:
        raise HTTPException(status_code=400, detail="OTP not received from gateway yet. Please wait a few seconds or click Resend.")

    if stored_code != request.code:
        raise HTTPException(status_code=400, detail=f"Invalid OTP. Expected: {stored_code}")

    # Mark booking as OTP_VERIFIED
    async with db.begin():
        booking = await db.scalar(
            select(models.Booking)
            .where(models.Booking.booking_ref == request.ref)
            .with_for_update()
        )
        if booking and booking.status in ("PENDING", "OTP_SENT"):
            booking.status = "OTP_VERIFIED"

    return {"verified": True}
