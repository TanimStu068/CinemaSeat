from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
import models
import schemas

router = APIRouter(prefix="/movies", tags=["movies"])

@router.get("", response_model=List[schemas.MovieResponse])
async def get_movies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Movie))
    return result.scalars().all()

@router.get("/{movie_id}", response_model=schemas.MovieResponse)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(models.Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie
