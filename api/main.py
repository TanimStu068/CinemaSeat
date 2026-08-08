from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import health, movies, showtimes, seats, otp, bookings, webhooks
from services.expiry_worker import scheduler

app = FastAPI(title="CinemaSeat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(movies.router)
app.include_router(showtimes.router)
app.include_router(seats.router)
app.include_router(otp.router)
app.include_router(bookings.router)
app.include_router(webhooks.router)

@app.on_event("startup")
async def startup_event():
    scheduler.start()
