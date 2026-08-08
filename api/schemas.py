from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class MovieResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    duration: Optional[int]
    poster_url: Optional[str]

    class Config:
        from_attributes = True

class ShowtimeResponse(BaseModel):
    id: int
    movie_id: int
    theatre_id: int
    starts_at: datetime
    price: Decimal

    class Config:
        from_attributes = True

class SeatResponse(BaseModel):
    id: int
    showtime_id: int
    row_label: str
    col_number: int
    status: str
    held_by: Optional[str]
    held_until: Optional[datetime]

    class Config:
        from_attributes = True

class HoldSeatRequest(BaseModel):
    user_id: str
    phone: str

class HoldSeatResponse(BaseModel):
    booking_ref: str
    message: str

class OtpSendRequest(BaseModel):
    phone: str
    ref: str
    callback_url: Optional[str] = None

class OtpVerifyRequest(BaseModel):
    ref: str
    code: str

class ChargeRequest(BaseModel):
    booking_ref: str

class BookingStatusResponse(BaseModel):
    booking_ref: str
    status: str
    payment_id: Optional[str]
    amount: Optional[Decimal]

    class Config:
        from_attributes = True
