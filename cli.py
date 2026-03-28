import json

from database import engine
from models.director import Director
from models.movie import Genre, Movie  # noqa F401
from sqlmodel import Session, delete, select

import typer

app = typer.Typer()


@app.command()
def create_director(first_name: str, last_name: str, birth_year=None):
    with Session(engine) as session:
        new_director = Director(
            first_name=first_name, last_name=last_name, birth_year=birth_year
        )
        session.add(new_director)
        session.commit()
        session.refresh(new_director)
        typer.echo(
            f"Director {new_director.first_name} {new_director.last_name} created with id {new_director.id}"
        )


@app.command()
def list_directors():
    with Session(engine) as session:
        statement = select(Director)
        directors = session.exec(statement).all()
        for director in directors:
            typer.echo(
                f"Id: {director.id}  Name: {director.first_name} {director.last_name}"
            )


@app.command()
def create_movie(
    title: str,
    genre: Genre,
    duration: int,
    director_id: int,
    description: str | None = None,
    release_year: int | None = None,
):
    new_movie = Movie(
        title=title,
        genre=genre,
        duration_min=duration,
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
def list_movies():
    with Session(engine) as session:
        statement = select(Movie, Director).join(Director)
        results = session.exec(statement).all()
        for movie, director in results:
            typer.echo(
                f"Title: {movie.title} ({movie.id})\nContent: {movie.description}\nYear: {movie.release_year}\nDirector: {director.first_name} {director.last_name}\n\n"
            )


@app.command()
def seed_database():
    delete_all_data = input(
        "All data in the database will be replaced with test data. Proceed? (y/N)"
    )
    if delete_all_data == "y" or delete_all_data == "Y":
        # load data
        with open("db_seed_data.json") as f:
            data = json.load(f)
            directors = data["directors"]
            movies = data["movies"]
        with Session(engine) as session:
            session.exec(delete(Movie))
            session.exec(delete(Director))
            session.commit()
            for d in directors:
                new_d = Director.model_validate(d)
                session.add(new_d)
            session.commit()
            statement = select(Director)
            directors = session.exec(statement).all()
            # Kurversion für das folgende
            # director_map = {d.last_name: d.id for d in directors}
            directors_map = {}
            for d in directors:
                directors_map[d.last_name] = d.id
            for m in movies:
                m["director_id"] = directors_map[m["director"]]
                new_m = Movie.model_validate(m)
                session.add(new_m)
            session.commit()
    else:
        exit()


if __name__ == "__main__":
    app()
