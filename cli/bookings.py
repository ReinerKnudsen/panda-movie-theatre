import typer
from sqlmodel import Session, select

from database import engine
from models.booking import Booking
from models.customer import Customer
from models.movie import Movie
from models.screen import Screen
from models.screening import Screening

app = typer.Typer()


@app.command()
def list():
    with Session(engine) as session:
        statement = (
            select(Booking, Screening, Movie, Screen)
            .join(Screening, Booking.screening_id == Screening.id)  # type: ignore
            .join(Movie, Screening.movie_id == Movie.id)  # type: ignore
            .join(Screen, Screening.screen_id == Screen.id)  # type: ignore
            .outerjoin(Customer, Booking.customer_id == Customer.id)  # type: ignore
        )
        results = session.exec(statement)
        for booking, screening, movie, screen in results:
            customer = (
                f"Customer: {booking.customer.first_name} {booking.customer.last_name}"
                if booking.customer
                else ""
            )
            typer.echo(
                f'Booking {booking.booking_code}, Id {booking.id}\nFilm: "{movie.title}" in Kino {screen.number}\nAufführung: {screening.screen_time}\n{customer} \n'
            )
