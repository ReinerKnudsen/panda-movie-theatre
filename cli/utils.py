from datetime import date

from sqlmodel import Session, func, select

from database import engine
from models.booking import Booking
from models.customer import Customer
from models.movie import Movie
from models.screen import Screen
from models.screening import Screening


def load_movies():
    with Session(engine) as session:
        statement = select(Movie)
        movies = session.exec(statement).all()
    return movies


def find_movie(id: int):
    with Session(engine) as session:
        movie = session.get(Movie, id)
    if movie is None:
        raise ValueError("Movie not found")
    return movie


def load_screens():
    with Session(engine) as session:
        statement = select(Screen)
        screens = session.exec(statement).all()
    return screens


def find_screen(id: int) -> Screen:
    with Session(engine) as session:
        screen = session.get(Screen, id)
    if screen is None:
        raise ValueError("Screen not found")
    return screen


def load_screenings():
    with Session(engine) as session:
        statement = select(Screening)
        screenings = session.exec(statement).all()
    return screenings


def find_screening(id: int) -> Screening:
    with Session(engine) as session:
        screening = session.get(Screening, id)
    if screening is None:
        raise ValueError("Screening not found")
    return screening


def load_customers():
    with Session(engine) as session:
        statement = select(Customer)
        customers = session.exec(statement).all()
    return customers


def find_customer(id: int) -> Customer:
    with Session(engine) as session:
        customer = session.get(Customer, id)
    if customer is None:
        raise ValueError("Customer not found")
    return customer


def generate_booking_code() -> str:
    today = date.today()
    with Session(engine) as session:
        count = session.exec(
            select(func.count()).where(
                Booking.booking_code.startswith(f"PMT-{today.strftime('%Y%m%d')}")
            )
        ).one()
        code = f"PMT-{today.strftime('%Y%m%d')}-{count + 1:04d}"
    return code
