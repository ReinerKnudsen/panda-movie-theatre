from datetime import datetime

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class ScreeningCreate(SQLModel):
    movie_id: int
    screen_id: int
    screen_time: datetime
    bookings: int | None = None

    @field_validator("screen_time")
    @classmethod
    def validate_screen_time(cls, value):
        if value < datetime.now():
            raise ValueError("The screening date can't be in the past")
        return value


class ScreeningPatch(SQLModel):
    movie_id: int | None = None
    screen_id: int | None = None
    screen_time: datetime | None = None
    bookings: int | None = None


class Screening(ScreeningCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
    movie_id: int = Field(foreign_key="movie.id")
    screen_id: int = Field(foreign_key="screen.id")
