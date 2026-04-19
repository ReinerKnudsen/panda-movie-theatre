from enum import Enum

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class Floor(int, Enum):
    GROUND = 0
    FIRST = 1
    SECOND = 2
    THIRD = 3

    @property
    def label(self) -> str:
        labels = {
            Floor.GROUND: "Erdgeschoss",
            Floor.FIRST: "1. Etage",
            Floor.SECOND: "2. Etage",
            Floor.THIRD: "3. Etage",
        }
        return labels[self]


class ScreenCreate(SQLModel):
    number: int
    floor: Floor
    capacity: int
    available: bool = True
    turnaround_min: int

    @field_validator("capacity")
    @classmethod
    def validate_capacity(cls, value):
        if value < 1:
            raise ValueError("The capacity must be larger than 0.")
        return value

    @field_validator("turnaround_min")
    @classmethod
    def validate_turnaround(cls, value):
        if value < 10 or value > 30:
            raise ValueError("Please enter a reasonable time between 10 and 30 minutes")
        return value


class ScreenPatch(SQLModel):
    number: int | None = None
    floor: Floor | None = None
    capacity: int | None = None
    available: bool | None = None
    turnaround_min: int | None = None


class Screen(ScreenCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
