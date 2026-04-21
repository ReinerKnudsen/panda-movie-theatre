from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table
from sqlmodel import Session, select

from database import engine
from models.movie import Movie
from models.screen import Screen
from models.screening import Screening
from utils import find_movie, find_screen, load_movies, load_screens

app = typer.Typer()


def print_screening(screening: Screening):
    movie = find_movie(screening.movie_id)
    screen = find_screen(screening.screen_id)
    console = Console()
    table = Table()
    table.add_column("Id")
    table.add_column("Datum")
    table.add_column("Film")
    table.add_column("Saal")
    table.add_row(
        str(screening.id), str(screening.screen_time), movie.title, str(screen.number)
    )
    console.print(table)


@app.command()
def create():
    movie_id = None
    screen_no = None
    s_datetime = datetime.now()
    typer.echo("Aufführung anlegen")
    typer.echo("Film auswählen")
    movies = load_movies()
    for m in movies:
        typer.echo(f"[{m.id}] - {m.title}")
    movie_ids = [m.id for m in movies]
    while movie_id is None or movie_id not in movie_ids:
        movie_id = typer.prompt("? ", type=int)

    screens = load_screens()
    typer.echo("Saal auswählen")
    for s in screens:
        typer.echo(f"[{s.number}] ({s.floor.label})")
    screens_nums = [s.number for s in screens]
    while screen_no is None or screen_no not in screens_nums:
        screen_no = typer.prompt("Saal", type=int)

    while s_datetime <= datetime.now():
        input = typer.prompt("Datum (yyyy-mm-dd hh:mm)")
        s_datetime = datetime.strptime(input, "%Y-%m-%d %H:%M")

    new_screening = Screening(
        movie_id=movie_id, screen_id=screen_no, screen_time=s_datetime, bookings=0
    )
    with Session(engine) as session:
        session.add(new_screening)
        session.commit()
        session.refresh(new_screening)
    print_screening(new_screening)


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
