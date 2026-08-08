from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select

from database import AsyncSessionLocal
import models

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job("interval", seconds=30)
async def expire_held_seats():
    async with AsyncSessionLocal() as db:
        async with db.begin():
            expired_seats = (await db.execute(
                select(models.Seat).where(
                    models.Seat.status == "HELD",
                    models.Seat.held_until < datetime.utcnow()
                ).with_for_update()
            )).scalars().all()

            for seat in expired_seats:
                seat.status = "AVAILABLE"
                seat.held_by = None
                seat.held_until = None
                
                booking = await db.scalar(
                    select(models.Booking).where(
                        models.Booking.seat_id == seat.id,
                        models.Booking.status.in_(["PENDING", "OTP_SENT", "OTP_VERIFIED", "CHARGING"])
                    )
                )
                if booking:
                    booking.status = "FAILED"
