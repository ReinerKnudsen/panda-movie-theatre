import typer
from rich.console import Console
from rich.table import Table
from sqlmodel import Session, select

from database import engine
from models.customer import Customer

app = typer.Typer()


@app.command()
def list():
    with Session(engine) as session:
        statement = select(Customer)
        customers = session.exec(statement)
        console = Console()
        table = Table(title="Kunden")
        table.add_column("Id")
        table.add_column("Vorname")
        table.add_column("Nachname")
        for c in customers:
            table.add_row(str(c.id), c.first_name, c.last_name)
        console.print(table)
