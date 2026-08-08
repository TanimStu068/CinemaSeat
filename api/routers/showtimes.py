from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
import models
import schemas

router = APIRouter(prefix="/showtimes", tags=["showtimes"])

@router.get("", response_model=List[schemas.ShowtimeResponse])
async def get_showtimes(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Showtime).where(models.Showtime.movie_id == movie_id))
    return result.scalars().all()

@router.get("/{showtime_id}/seats", response_model=List[schemas.SeatResponse])
async def get_seats(showtime_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Seat)
        .where(models.Seat.showtime_id == showtime_id)
        .order_by(models.Seat.row_label, models.Seat.col_number)
    )
    return result.scalars().all()
