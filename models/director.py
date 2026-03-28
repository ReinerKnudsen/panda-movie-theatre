from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.movie import Movie


class DirectorCreate(SQLModel):
    first_name: str
    last_name: str
    birth_year: int | None = None

class Director(DirectorCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
    movies: list["Movie"] | None = Relationship(back_populates="director")

class DirectorPatch(SQLModel):
    first_name: str | None = None
    last_name: str | None = None
    birth_year: int | None = None
