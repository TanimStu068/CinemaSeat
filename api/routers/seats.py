import os
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

@router.post("/{seat_id}/hold", response_model=schemas.HoldSeatResponse)
async def hold_seat(seat_id: int, request: schemas.HoldSeatRequest, db: AsyncSession = Depends(get_db)):
    async with db.begin():
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
        ttl = int(os.getenv("HOLD_TTL_SECONDS", "300"))

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
        
    return {"booking_ref": booking_ref, "message": "Seat held successfully"}
