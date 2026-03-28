from datetime import date
from enum import Enum

from models.director import Director
from pydantic import field_validator, model_validator
from sqlmodel import Field, Relationship, SQLModel


class Genre(str, Enum):
    ACTION = "action"
    DRAMA ="drama"
    COMEDY = "comedy"
    ROMANCE = "romance"
    THRILLER = "thriller"

class MoviePatch(SQLModel):
    title: str | None = None
    genre: Genre | None = None
    duration_min: int | None = None
    director_id: int | None = None
    description: str | None = None
    release_year: int | None = None

class MovieCreate(SQLModel):
    title: str
    genre: Genre
    duration_min: int
    director_id: int
    description: str | None = None
    release_year: int | None = None

    @field_validator("duration_min")
    @classmethod
    def validate_duration(cls, value):
        if value < 1:
            raise ValueError(f"The duration must be larger than 0. {value} is not a valid duration.")
        return value

    @field_validator("title")
    @classmethod
    def validate_title(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("The title cannot be empty.")
        return value

    @model_validator(mode='after')
    def validate_release_year(self):
        if self.release_year and self.release_year > date.today().year:
            raise ValueError('The release year cannot be in the future.')
        return self

class Movie(MovieCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
    director_id: int = Field(foreign_key="director.id")
    director: Director = Relationship(back_populates="movies")
