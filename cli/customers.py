import typer
from rich.console import Console
from rich.table import Table
from sqlmodel import Session, select

from cli.utils import find_customer, load_customers
from database import engine
from models.customer import Customer

app = typer.Typer()


def print_customer(c: Customer, title=None):
    console = Console()
    table = Table(title=title)
    table.add_column("Id")
    table.add_column("Vorname")
    table.add_column("Nachname")
    table.add_row(str(c.id), c.first_name, c.last_name)
    console.print(table)


def print_customers(customers, title=None):
    console = Console()
    table = Table(title=title)
    table.add_column("Id")
    table.add_column("Vorname")
    table.add_column("Nachname")
    for c in customers:
        table.add_row(str(c.id), c.first_name, c.last_name)
    console.print(table)


@app.command()
def create():
    f_name = ""
    l_name = ""
    typer.echo("Neuen Kunden anlegen")

    while f_name == "":
        f_name = typer.prompt("Vorname").strip()

    while l_name == "":
        l_name = typer.prompt("Nachname").strip()

    new_customer = Customer(first_name=f_name, last_name=l_name)
    with Session(engine) as session:
        session.add(new_customer)
        session.commit()
        session.refresh(new_customer)

        print_customer(new_customer, "Kunde angelegt")


@app.command()
def delete():
    pick = None
    customer = None
    customers = load_customers()
    customer_ids = [c.id for c in customers]
    print_customers(customers, "Kunde löschen")
    while pick is None or pick not in customer_ids:
        pick = typer.prompt("Auswahl >", type=int)
    if pick:
        customer = find_customer(pick)
    confirm = typer.confirm(
        "Diesen Kunden wirklich löschen? (y/N)", default=False, show_default=True
    )
    if confirm:
        with Session(engine) as session:
            print_customer(customer, "Kunde erfolgreich gelöscht")
            session.delete(customer)
            session.commit()


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
