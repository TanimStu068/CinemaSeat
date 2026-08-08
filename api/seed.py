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

            movies = [
                models.Movie(title="Spider-Man: Brand New Day", description="When a new threat emerges from the multiverse, Peter Parker must face his greatest challenge yet in this midnight premiere event.", duration=150),
                models.Movie(title="The Dark Knight Returns", description="Gotham needs its hero once more. Bruce Wayne comes out of retirement to face a city overrun by a new generation of villains.", duration=165),
                models.Movie(title="Avengers: Endgame Redux", description="The epic conclusion to the Infinity Saga, re-released with 30 minutes of never-before-seen footage.", duration=210),
                models.Movie(title="Dune: Part Three", description="The holy war sweeps across the universe as Paul Atreides faces the ultimate consequences of his visions.", duration=185),
                models.Movie(title="Oppenheimer: The Director's Cut", description="An immersive look into the life of J. Robert Oppenheimer, featuring extended sequences and behind-the-scenes narration.", duration=200),
                models.Movie(title="Interstellar Reborn", description="A special 10th-anniversary IMAX re-release of the sci-fi masterpiece. Mankind's journey beyond the stars continues.", duration=175)
            ]
            
            db.add_all(movies)
            await db.flush()

            t1 = models.Theatre(name="Grand Star Cinema - Hall 1", location="Main Street, Chattogram", rows=10, cols=15)
            t2 = models.Theatre(name="Grand Star Cinema - Hall 2", location="Main Street, Chattogram", rows=8, cols=12)
            db.add_all([t1, t2])
            await db.flush()

            now = datetime.now(timezone.utc)
            d1 = now + timedelta(days=1)
            d2 = now + timedelta(days=2)
            d3 = now + timedelta(days=3)

            showtimes = [
                # Spider-Man
                models.Showtime(movie_id=movies[0].id, theatre_id=t1.id, starts_at=datetime(d1.year, d1.month, d1.day, 0, 0, tzinfo=timezone.utc), price=450),
                models.Showtime(movie_id=movies[0].id, theatre_id=t1.id, starts_at=datetime(d1.year, d1.month, d1.day, 15, 0, tzinfo=timezone.utc), price=350),
                models.Showtime(movie_id=movies[0].id, theatre_id=t2.id, starts_at=datetime(d1.year, d1.month, d1.day, 18, 30, tzinfo=timezone.utc), price=400),
                # Dark Knight
                models.Showtime(movie_id=movies[1].id, theatre_id=t1.id, starts_at=datetime(d1.year, d1.month, d1.day, 12, 0, tzinfo=timezone.utc), price=400),
                models.Showtime(movie_id=movies[1].id, theatre_id=t2.id, starts_at=datetime(d2.year, d2.month, d2.day, 20, 0, tzinfo=timezone.utc), price=500),
                # Avengers
                models.Showtime(movie_id=movies[2].id, theatre_id=t1.id, starts_at=datetime(d2.year, d2.month, d2.day, 10, 0, tzinfo=timezone.utc), price=350),
                models.Showtime(movie_id=movies[2].id, theatre_id=t2.id, starts_at=datetime(d2.year, d2.month, d2.day, 14, 0, tzinfo=timezone.utc), price=350),
                # Dune
                models.Showtime(movie_id=movies[3].id, theatre_id=t1.id, starts_at=datetime(d2.year, d2.month, d2.day, 18, 0, tzinfo=timezone.utc), price=450),
                models.Showtime(movie_id=movies[3].id, theatre_id=t2.id, starts_at=datetime(d3.year, d3.month, d3.day, 16, 0, tzinfo=timezone.utc), price=400),
                # Oppenheimer
                models.Showtime(movie_id=movies[4].id, theatre_id=t1.id, starts_at=datetime(d3.year, d3.month, d3.day, 12, 0, tzinfo=timezone.utc), price=350),
                models.Showtime(movie_id=movies[4].id, theatre_id=t2.id, starts_at=datetime(d3.year, d3.month, d3.day, 19, 0, tzinfo=timezone.utc), price=450),
                # Interstellar
                models.Showtime(movie_id=movies[5].id, theatre_id=t1.id, starts_at=datetime(d1.year, d1.month, d1.day, 21, 0, tzinfo=timezone.utc), price=500),
                models.Showtime(movie_id=movies[5].id, theatre_id=t2.id, starts_at=datetime(d2.year, d2.month, d2.day, 21, 0, tzinfo=timezone.utc), price=500),
            ]
            db.add_all(showtimes)
            await db.flush()

            row_labels = "ABCDEFGHIJ"
            seats_to_insert = []
            for st in showtimes:
                th = t1 if st.theatre_id == t1.id else t2
                for i in range(th.rows):
                    for j in range(th.cols):
                        seats_to_insert.append(models.Seat(showtime_id=st.id, row_label=row_labels[i], col_number=j+1, status="AVAILABLE"))
            db.add_all(seats_to_insert)

        print("Database seeded: 6 movies, 2 theatres, 13 showtimes")

if __name__ == "__main__":
    asyncio.run(seed_db())
