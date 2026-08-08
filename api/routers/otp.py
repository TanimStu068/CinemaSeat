import os
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db, AsyncSessionLocal
from config import settings
import models
import schemas

router = APIRouter(prefix="/otp", tags=["otp"])

@router.post("/send", status_code=status.HTTP_202_ACCEPTED)
async def send_otp(request: schemas.OtpSendRequest, db: AsyncSession = Depends(get_db)):
    booking = await db.scalar(select(models.Booking).where(models.Booking.booking_ref == request.ref))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # We shouldn't block the frontend, fire-and-forget or just await if it's fast
    # The gateway usually accepts instantly for OTP send
    payload = {
        "phone": request.phone,
        "ref": request.ref,
        "callback_url": settings.OTP_CALLBACK_URL
    }
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.GATEWAY_URL}/otp/send",
                json=payload,
                timeout=5.0
            )
    except Exception:
        pass # Ignore failure to send to mock gateway

    return {"message": "OTP delivery initiated"}

@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_otp(request: schemas.OtpVerifyRequest, db: AsyncSession = Depends(get_db)):
    # Contact mock gateway to verify
    payload = {
        "ref": request.ref,
        "code": request.code
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.GATEWAY_URL}/otp/verify",
                json=payload,
                timeout=5.0
            )
            
            if resp.status_code == 200:
                # Update booking status
                async with db.begin():
                    booking = await db.scalar(
                        select(models.Booking)
                        .where(models.Booking.booking_ref == request.ref)
                        .with_for_update()
                    )
                    if booking and booking.status in ("PENDING", "OTP_SENT"):
                        booking.status = "OTP_VERIFIED"
                return {"verified": True}
            else:
                raise HTTPException(status_code=400, detail="Invalid OTP code")
    except httpx.RequestError:
        raise HTTPException(status_code=500, detail="Failed to contact OTP gateway")
