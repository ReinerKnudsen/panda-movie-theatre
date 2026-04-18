import typer
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
        for screening, movie, screen in screenings:
            typer.echo(
                f"Film: {movie.title} \nDatum: {screening.screen_time} in Saal {screen.number}"
            )
