from datetime import datetime

import typer
from sqlmodel import Session, select

from database import engine
from models.director import Director
from models.movie import Genre, Movie  # noqa F401

app = typer.Typer()


def get_all_directors():
    with Session(engine) as session:
        statement = select(Director)
        directors = session.exec(statement).all()
    return directors


@app.command()
def create():
    valid_genres = [g.value for g in Genre]
    title = None
    genre = 0
    duration_min = 0
    director_id = 0
    release_year = 0

    typer.echo("Neuen Film anlegen")
    while not title:
        title = typer.prompt("Titel")
    while genre < 1 or genre > len(valid_genres):
        typer.echo("Genre:")
        for i, g in enumerate(valid_genres):
            typer.echo(f"[{i + 1}] {g}")
        genre = typer.prompt("Genre", type=int)
    typer.echo(f"Genre: {valid_genres[genre - 1]}")
    while not duration_min or duration_min == 0:
        duration_min = typer.prompt("Dauer in min", type=int)
    typer.echo("Wähle den Regisseur:")
    directors = get_all_directors()
    for director in directors:
        typer.echo(f"[{director.id}]  Name: {director.first_name} {director.last_name}")
    director_ids = [d.id for d in directors]
    while director_id not in director_ids:
        director_id = typer.prompt("Director Id", type=int)
    selected_director: Director = [d for d in directors if d.id == director_id][0]
    typer.echo(
        f"Regisseur: {selected_director.first_name} {selected_director.last_name}"
    )
    description = typer.prompt("Kurzbeschreibung")
    today = datetime.today().year
    while release_year < 1800 or release_year > today:
        release_year = typer.prompt("Jahr", type=int)
    selected_genre: Genre = Genre(valid_genres[genre - 1])

    new_movie = Movie(
        title=title,
        genre=selected_genre,
        duration_min=duration_min,
        director_id=director_id,
        description=description,
        release_year=release_year,
    )
    with Session(engine) as session:
        session.add(new_movie)
        session.commit()
        session.refresh(new_movie)
        typer.echo(f"Created new movie {new_movie.title} with id {new_movie.id}")


@app.command()
def list():
    with Session(engine) as session:
        statement = select(Movie, Director).join(Director)
        results = session.exec(statement).all()
        for movie, director in results:
            typer.echo(
                f"Title: {movie.title} ({movie.id})\nContent: {movie.description}\nYear: {movie.release_year}\nDirector: {director.first_name} {director.last_name}\n\n"
            )
