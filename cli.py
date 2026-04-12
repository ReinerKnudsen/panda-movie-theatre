import json
from datetime import datetime

import click
import typer
from sqlmodel import Session, delete, select

from database import engine
from models.booking import Booking
from models.customer import Customer
from models.director import Director
from models.movie import Genre, Movie  # noqa F401
from models.screen import Floor, Screen
from models.screening import Screening

app = typer.Typer()


def get_all_directors():
    with Session(engine) as session:
        statement = select(Director)
        directors = session.exec(statement).all()
    return directors


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
    directors = get_all_directors()
    for director in directors:
        typer.echo(
            f"Id: {director.id}  Name: {director.first_name} {director.last_name}"
        )


@app.command()
def create_movie():
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
def list_movies():
    with Session(engine) as session:
        statement = select(Movie, Director).join(Director)
        results = session.exec(statement).all()
        for movie, director in results:
            typer.echo(
                f"Title: {movie.title} ({movie.id})\nContent: {movie.description}\nYear: {movie.release_year}\nDirector: {director.first_name} {director.last_name}\n\n"
            )


@app.command()
def create_screen():
    s_number = 0
    s_floor = None
    s_capa = 0
    s_avail = True
    is_avail = ""
    s_turn = 0
    with Session(engine) as session:
        statement = select(Screen)
        screens = session.exec(statement).all()
        screen_numbers = [s.number for s in screens]
        typer.echo("Neuen Saal anlegen")

        while True:
            s_number = typer.prompt("Screen Nummer", type=int)
            if s_number < 1:
                typer.echo("Die Saal-Nummer muss größer als 0 sein.")
            elif s_number in screen_numbers:
                typer.echo("Diese Saalnummer haben wir schon.")
            else:
                break
        valid_floors = [f.value for f in Floor]
        typer.echo("Stockwerk eingeben:")

        while s_floor not in valid_floors:
            for f in valid_floors:
                typer.echo(str(f))
            s_floor = typer.prompt("Auswahl", type=int)
        selected_floor = Floor(s_floor)

        while s_capa < 1:
            s_capa = typer.prompt("Kapazität", type=int)

        is_avail = typer.prompt(
            "Ist der Saal sofort verfügbar? (J/n)", type=str, default="j"
        )
        s_avail = is_avail.lower() == "j"

        # s_turn = typer.prompt("Turnaround-Zeit (Minuten)", type=int, default=15)
        s_turn = click.prompt(
            "Turnaround-Zeit in min", type=int, default=15, show_default=True
        )
        if s_turn < 1:
            raise typer.BadParameter("Muss mindestens 1 Minute sein.")

        new_screen = Screen(
            number=s_number,
            floor=selected_floor,
            capacity=s_capa,
            available=s_avail,
            turnaround_min=s_turn,
        )

        session.add(new_screen)
        session.commit()
        session.refresh(new_screen)

        typer.echo(
            f"Neuer Saal Nummer {new_screen.number} angelegt mit id {new_screen.id}."
        )


@app.command()
def create_screening():
    # with Session(engine) as session:
    #    today = datetime.today()
    pass


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
            screens = data["screens"]
            screenings = data["screenings"]
        with Session(engine) as session:
            session.exec(delete(Customer))
            session.exec(delete(Booking))
            session.exec(delete(Screening))
            session.exec(delete(Movie))
            session.exec(delete(Screen))
            session.exec(delete(Director))
            session.commit()
            # seed directors
            for d in directors:
                new_d = Director.model_validate(d)
                session.add(new_d)
            session.commit()
            # seed screens
            for s in screens:
                new_s = Screen.model_validate(s)
                session.add(new_s)
            session.commit()
            # seed movies, create relation to directors
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
            # seed screenings, create relation to movies and screens
            statement_s = select(Screen)
            screens = session.exec(statement_s).all()
            statement_m = select(Movie)
            movies = session.exec(statement_m).all()
            screens_map = {}
            for s in screens:
                screens_map[s.number] = s.id
            movies_map = {}
            for m in movies:
                movies_map[m.title] = m.id
            for sc in screenings:
                sc["movie_id"] = movies_map[sc["movie"]]
                sc["screen_id"] = screens_map[sc["screen"]]
                new_sc = Screening.model_validate(sc)
                session.add(new_sc)
            session.commit()

    else:
        exit()


if __name__ == "__main__":
    app()
