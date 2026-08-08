from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
from database import Base

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    duration = Column(Integer)
    poster_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    showtimes = relationship("Showtime", back_populates="movie", cascade="all, delete-orphan")

class Theatre(Base):
    __tablename__ = "theatres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255))
    rows = Column(Integer, nullable=False)
    cols = Column(Integer, nullable=False)

    showtimes = relationship("Showtime", back_populates="theatre", cascade="all, delete-orphan")

class Showtime(Base):
    __tablename__ = "showtimes"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"))
    theatre_id = Column(Integer, ForeignKey("theatres.id", ondelete="CASCADE"))
    starts_at = Column(DateTime(timezone=True), nullable=False)
    price = Column(Numeric(8, 2), nullable=False)

    movie = relationship("Movie", back_populates="showtimes")
    theatre = relationship("Theatre", back_populates="showtimes")
    seats = relationship("Seat", back_populates="showtime", cascade="all, delete-orphan")

class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    showtime_id = Column(Integer, ForeignKey("showtimes.id", ondelete="CASCADE"))
    row_label = Column(String(5), nullable=False)
    col_number = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="AVAILABLE")
    held_by = Column(String(255))
    held_until = Column(DateTime(timezone=True))

    showtime = relationship("Showtime", back_populates="seats")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_ref = Column(String(255), unique=True, nullable=False, index=True)
    seat_id = Column(Integer, ForeignKey("seats.id"))
    user_id = Column(String(255), nullable=False)
    phone = Column(String(20))
    payment_id = Column(String(255))
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    event_id = Column(String(255), unique=True)
    amount = Column(Numeric(8, 2))
    currency = Column(String(10), default="BDT")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
