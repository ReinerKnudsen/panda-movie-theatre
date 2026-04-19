import click
import typer
from rich.console import Console
from rich.table import Table
from sqlmodel import Session, select

from database import engine
from models.screen import Floor, Screen

app = typer.Typer()


@app.command()
def create():
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
def list():
    with Session(engine) as session:
        statement = select(Screen)
        screens = session.exec(statement).all()
        console = Console()
        table = Table(title="Säle")
        table.add_column("Nummer")
        table.add_column("Id")
        table.add_column("Etage")
        table.add_column("Kapazität")
        table.add_column("Turnaround-Zeit")
        table.add_column("Status")
        for s in screens:
            status = "available" if s.available else "unavailable"
            table.add_row(
                str(s.number),
                str(s.id),
                s.floor.label,
                str(s.capacity),
                str(s.turnaround_min),
                status,
            )
        console.print(table)
