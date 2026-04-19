from typing import TYPE_CHECKING, Optional

from pydantic import field_validator
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.customer import Customer


class BookingCreate(SQLModel):
    screening_id: int
    customer_id: int | None = None
    seats: int

    @field_validator("seats")
    @classmethod
    def validate_seats(cls, value):
        if value < 1:
            raise ValueError("A booking must be for at least one seat.")
        return value


class BookingPatch(SQLModel):
    seats: int


class Booking(BookingCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
    booking_code: str | None = None
    screening_id: int = Field(foreign_key="screening.id")
    customer_id: int | None = Field(default=None, foreign_key="customer.id")
    customer: Optional["Customer"] = Relationship(back_populates="bookings")
