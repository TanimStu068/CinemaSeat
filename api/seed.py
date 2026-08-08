import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import engine, AsyncSessionLocal
import models

async def seed_db():
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(models.Movie).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded")
            return

        async with db.begin():
            # Create movie
            movie = models.Movie(
                title="Spider-Man: Brand New Day",
                description="The much anticipated midnight premiere",
                duration=150,
                poster_url="https://example.com/poster.jpg"
            )
            db.add(movie)
            await db.flush()

            # Create theatre
            theatre = models.Theatre(
                name="Grand Star Cinema",
                location="Main Street",
                rows=10,
                cols=15
            )
            db.add(theatre)
            await db.flush()

            # Create showtime (tomorrow midnight)
            now = datetime.now(timezone.utc)
            tomorrow = now + timedelta(days=1)
            starts_at = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, tzinfo=timezone.utc)
            
            showtime = models.Showtime(
                movie_id=movie.id,
                theatre_id=theatre.id,
                starts_at=starts_at,
                price=450.00
            )
            db.add(showtime)
            await db.flush()

            # Generate seats
            row_labels = "ABCDEFGHIJ"
            seats = []
            for i in range(theatre.rows):
                for j in range(theatre.cols):
                    seats.append(
                        models.Seat(
                            showtime_id=showtime.id,
                            row_label=row_labels[i],
                            col_number=j + 1,
                            status="AVAILABLE"
                        )
                    )
            db.add_all(seats)

        print("Database seeding completed")

if __name__ == "__main__":
    asyncio.run(seed_db())
