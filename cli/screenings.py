import typer
from rich.console import Console
from rich.table import Table
from sqlmodel import Session, select

from database import engine
from models.movie import Movie
from models.screen import Screen
from models.screening import Screening

app = typer.Typer()


@app.command()
def create():
    # with Session(engine) as session:
    #    today = datetime.today()
    pass


@app.command()
def list():
    with Session(engine) as session:
        statement = (
            select(Screening, Movie, Screen)
            .join(Movie, Screening.movie_id == Movie.id)  # type: ignore
            .join(Screen, Screening.screen_id == Screen.id)  # type: ignore
        )
        screenings = session.exec(statement)
        console = Console()
        table = Table(title="Aufführungen")
        table.add_column("Film")
        table.add_column("Datum")
        table.add_column("Saal")
        table.add_column("Kapazität")
        table.add_column("Buchungen")
        for screening, movie, screen in screenings:
            table.add_row(
                movie.title,
                str(screening.screen_time),
                str(screen.number),
                str(screen.capacity),
                str(screening.bookings),
            )
        console.print(table)
