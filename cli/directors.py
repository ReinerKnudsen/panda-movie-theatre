import typer
from sqlmodel import Session, select

from database import engine
from models.director import Director

app = typer.Typer()


def get_all_directors():
    with Session(engine) as session:
        statement = select(Director)
        directors = session.exec(statement).all()
    return directors


@app.command()
def create(first_name: str, last_name: str, birth_year=None):
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
def list():
    directors = get_all_directors()
    for director in directors:
        typer.echo(
            f"Id: {director.id}  Name: {director.first_name} {director.last_name}"
        )
