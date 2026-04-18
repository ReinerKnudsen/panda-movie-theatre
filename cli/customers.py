import typer
from sqlmodel import Session, select

from database import engine
from models.customer import Customer

app = typer.Typer()


@app.command()
def list():
    with Session(engine) as session:
        statement = select(Customer)
        customers = session.exec(statement)
        for c in customers:
            typer.echo(f"{c.last_name}, {c.first_name} ({c.id})")
