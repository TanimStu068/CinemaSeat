import os
import asyncio
from uuid import uuid4
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import DBAPIError
from database import get_db
import models
import schemas

router = APIRouter(prefix="/seats", tags=["seats"])

# Helper to release a hold after TTL expires
async def _release_hold(booking_ref: str, ttl: int):
    await asyncio.sleep(ttl)
    async with asyncio.Lock():  # ensure atomic release
        async with get_db() as db:  # get a fresh session
            result = await db.execute(select(models.Booking).where(models.Booking.booking_ref == booking_ref))
            booking = result.scalar_one_or_none()
            if booking and booking.status in ("PENDING", "OTP_SENT"):
                # free seat
                seat = await db.get(models.Seat, booking.seat_id)
                if seat:
                    seat.status = "AVAILABLE"
                    seat.held_by = None
                    seat.held_until = None
                # delete the booking – optional, keep for audit
                await db.delete(booking)
                await db.commit()

@router.post("/{seat_id}/hold", response_model=schemas.HoldSeatResponse)
async def hold_seat(seat_id: int, request: schemas.HoldSeatRequest, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        # Enforce max 3 held seats per user for this showtime
        result = await db.execute(
            select(models.Booking)
            .join(models.Seat, models.Booking.seat_id == models.Seat.id)
            .where(models.Booking.user_id == request.user_id)
            .where(models.Booking.status.in_(["PENDING", "OTP_SENT"]))
        )
        current_holds = result.scalars().all()
        if len(current_holds) >= 3:
            raise HTTPException(status_code=400, detail="Maximum of 3 seats can be held at a time.")

        try:
            # Pessimistic locking with NOWAIT
            result = await db.execute(
                select(models.Seat)
                .where(models.Seat.id == seat_id)
                .with_for_update(nowait=True)
            )
            seat = result.scalar_one_or_none()
        except DBAPIError:
            # Handle LockNotAvailable gracefully
            raise HTTPException(status_code=409, detail="Seat is currently being processed by another user")

        if not seat:
            raise HTTPException(status_code=404, detail="Seat not found")
        if seat.status != "AVAILABLE":
            raise HTTPException(status_code=409, detail="Seat not available")

        # Load the associated showtime to get the price
        showtime = await db.get(models.Showtime, seat.showtime_id)
        if not showtime:
            raise HTTPException(status_code=500, detail="Seat data corrupted: No showtime found")

        booking_ref = f"bk_{uuid4().hex[:12]}"
        ttl = int(os.getenv("HOLD_TTL_SECONDS", "60"))

        seat.status = "HELD"
        seat.held_by = request.user_id
        seat.held_until = datetime.utcnow() + timedelta(seconds=ttl)

        booking = models.Booking(
            booking_ref=booking_ref,
            seat_id=seat.id,
            user_id=request.user_id,
            phone=request.phone,
            amount=showtime.price,
            status="PENDING",
        )
        db.add(booking)
        await db.flush()  # ensure booking gets an ID before committing
        # Schedule automatic release after TTL
        asyncio.create_task(_release_hold(booking_ref, ttl))

    return {"booking_ref": booking_ref, "message": "Seat held successfully"}

@router.post("/{seat_id}/release")
async def release_seat(seat_id: int, request: schemas.ReleaseSeatRequest, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        seat = await db.get(models.Seat, seat_id)
        if not seat:
            raise HTTPException(status_code=404, detail="Seat not found")
        if seat.status != "HELD" or seat.held_by != request.user_id:
            raise HTTPException(status_code=400, detail="Seat is not held by this user")
        # Find associated booking
        result = await db.execute(select(models.Booking).where(models.Booking.seat_id == seat_id, models.Booking.user_id == request.user_id))
        booking = result.scalar_one_or_none()
        if booking:
            await db.delete(booking)
        seat.status = "AVAILABLE"
        seat.held_by = None
        seat.held_until = None
    return {"message": "Seat released"}
