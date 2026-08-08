import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select

from database import AsyncSessionLocal
import models

async def seed_db():
    async with AsyncSessionLocal() as db:
        async with db.begin():
            result = await db.execute(select(models.Movie).limit(1))
            if result.scalar_one_or_none():
                print("Database already seeded")
                return

            m1 = models.Movie(title="Spider-Man: Brand New Day", description="When a new threat emerges from the multiverse, Peter Parker must face his greatest challenge yet in this midnight premiere event.", duration=150)
            m2 = models.Movie(title="The Dark Knight Returns", description="Gotham needs its hero once more. Bruce Wayne comes out of retirement to face a city overrun by a new generation of villains.", duration=165)
            m3 = models.Movie(title="Avengers: Endgame Redux", description="The epic conclusion to the Infinity Saga, re-released with 30 minutes of never-before-seen footage.", duration=210)
            db.add_all([m1, m2, m3])
            await db.flush()

            t1 = models.Theatre(name="Grand Star Cinema - Hall 1", location="Main Street, Chattogram", rows=10, cols=15)
            t2 = models.Theatre(name="Grand Star Cinema - Hall 2", location="Main Street, Chattogram", rows=8, cols=12)
            db.add_all([t1, t2])
            await db.flush()

            now = datetime.now(timezone.utc)
            d1 = now + timedelta(days=1)
            d2 = now + timedelta(days=2)

            showtimes = [
                models.Showtime(movie_id=m1.id, theatre_id=t1.id, starts_at=datetime(d1.year, d1.month, d1.day, 0, 0, tzinfo=timezone.utc), price=450),
                models.Showtime(movie_id=m1.id, theatre_id=t1.id, starts_at=datetime(d1.year, d1.month, d1.day, 15, 0, tzinfo=timezone.utc), price=350),
                models.Showtime(movie_id=m1.id, theatre_id=t2.id, starts_at=datetime(d1.year, d1.month, d1.day, 18, 30, tzinfo=timezone.utc), price=400),
                models.Showtime(movie_id=m2.id, theatre_id=t1.id, starts_at=datetime(d1.year, d1.month, d1.day, 12, 0, tzinfo=timezone.utc), price=400),
                models.Showtime(movie_id=m2.id, theatre_id=t2.id, starts_at=datetime(d2.year, d2.month, d2.day, 20, 0, tzinfo=timezone.utc), price=500),
                models.Showtime(movie_id=m3.id, theatre_id=t1.id, starts_at=datetime(d2.year, d2.month, d2.day, 10, 0, tzinfo=timezone.utc), price=350),
                models.Showtime(movie_id=m3.id, theatre_id=t2.id, starts_at=datetime(d2.year, d2.month, d2.day, 14, 0, tzinfo=timezone.utc), price=350),
            ]
            db.add_all(showtimes)
            await db.flush()

            row_labels = "ABCDEFGHIJ"
            for st in showtimes:
                th = t1 if st.theatre_id == t1.id else t2
                for i in range(th.rows):
                    for j in range(th.cols):
                        db.add(models.Seat(showtime_id=st.id, row_label=row_labels[i], col_number=j+1, status="AVAILABLE"))

        print("Database seeded: 3 movies, 2 theatres, 7 showtimes")

if __name__ == "__main__":
    asyncio.run(seed_db())
