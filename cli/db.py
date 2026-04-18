import json

import typer
from sqlalchemy import text
from sqlmodel import Session, delete, select

from database import engine
from models.booking import Booking
from models.customer import Customer
from models.director import Director
from models.movie import Genre, Movie  # noqa F401
from models.screen import Screen
from models.screening import Screening

app = typer.Typer()


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
            customers = data["customers"]
            bookings = data["bookings"]
        with Session(engine) as session:
            session.exec(delete(Booking))
            session.exec(delete(Customer))
            session.exec(delete(Screening))
            session.exec(delete(Movie))
            session.exec(delete(Screen))
            session.exec(delete(Director))
            session.commit()

            with engine.connect() as conn:
                conn.execute(text("ALTER SEQUENCE screening_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE movie_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE director_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE screen_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE booking_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE customer_id_seq RESTART WITH 1"))
                conn.commit()

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

            # seed customers
            for c in customers:
                new_c = Customer.model_validate(c)
                session.add(new_c)
            session.commit()

            # seed bookings
            for b in bookings:
                new_b = Booking.model_validate(b)
                session.add(new_b)
            session.commit()

    else:
        exit()
