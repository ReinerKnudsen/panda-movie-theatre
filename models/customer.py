from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.booking import Booking


class CustomerCreate(SQLModel):
    first_name: str
    last_name: str


class CustomerPatch(SQLModel):
    first_name: str | None = None
    last_name: str | None = None


class Customer(CustomerCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
    bookings: list["Booking"] | None = Relationship(back_populates="customer")
