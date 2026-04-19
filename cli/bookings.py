import typer
from rich.console import Console
from rich.table import Table
from sqlmodel import Session, select

from cli.utils import (
    find_customer,
    find_movie,
    find_screen,
    find_screening,
    generate_booking_code,
    load_customers,
    load_screenings,
)
from database import engine
from models.booking import Booking
from models.customer import Customer
from models.movie import Movie
from models.screen import Screen
from models.screening import Screening

app = typer.Typer()


def print_booking(booking, screening, customer=None):
    console = Console()
    name = customer.last_name if customer else ""
    table = Table()
    table.add_column("Buchungscode")
    table.add_column("Aufführung")
    table.add_column("Kunde")
    table.add_column("Plätze")
    table.add_row(
        str(booking.booking_code),
        str(screening.screen_time),
        name,
        str(booking.seats),
    )
    console.print(table)


@app.command()
def create():
    pick = None
    typer.echo("Neue Buchung erstellen")
    typer.echo("Vorführung auswählen")
    screenings = load_screenings()
    screenings_ids = [s.id for s in screenings]
    for s in screenings:
        typer.echo(
            f"[{s.id}] - {find_movie(s.movie_id).title} am {s.screen_time} in Saal {find_screen(s.screen_id).number}"
        )
    while pick is None or pick not in screenings_ids:
        pick = typer.prompt("Auswahl > ", type=int)
    screening_id = pick
    screening = find_screening(screening_id)

    customers = load_customers()
    customer_ids = [c.id for c in customers]
    for c in customers:
        typer.echo(f"[{c.id} {c.last_name}, {c.first_name}]")

    while True:
        pick = typer.prompt("Auswahl (Enter für keine Zuordnung)> ", default="")
        if pick == "":
            customer_id = None
            customer = None
            break
        try:
            pick = int(pick)
            if pick in customer_ids:
                customer_id = pick
                customer = find_customer(customer_id)
                break
            else:
                typer.echo("Unbekannte Id")
        except ValueError:
            typer.echo("Bitte eine Zahl oder Enter eingeben.")
    pick = None

    capa = find_screen(screening.screen_id).capacity - screening.bookings
    while pick is None or pick > capa:
        pick = typer.prompt("Plätze", type=int)
    seats = pick

    new_booking = Booking(
        screening_id=screening_id,
        customer_id=customer_id,
        seats=seats,
        booking_code=generate_booking_code(),
    )

    with Session(engine) as session:
        session.add(new_booking)
        session.commit()
        session.refresh(new_booking)

        screening.sqlmodel_update({"bookings": screening.bookings + new_booking.seats})
        session.add(screening)
        session.commit()

        typer.echo("Buchung angelegt")
        print_booking(new_booking, screening, customer)


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
