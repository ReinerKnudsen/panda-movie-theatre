import typer
from rich.console import Console
from rich.table import Table
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
        console = Console()
        table = Table(title="Buchungen")
        table.add_column("Code")
        table.add_column("Film")
        table.add_column("Saal")
        table.add_column("Aufführung")
        table.add_column("Plätze")
        table.add_column("Kunde")
        for booking, screening, movie, screen in results:
            customer = (
                f"{booking.customer.first_name} {booking.customer.last_name}"
                if booking.customer
                else ""
            )
            table.add_row(
                booking.booking_code,
                movie.title,
                str(screen.number),
                str(screening.screen_time),
                str(booking.seats),
                customer,
            )
        console.print(table)
