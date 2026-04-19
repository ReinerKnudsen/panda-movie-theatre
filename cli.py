import typer

from cli import bookings, customers, db, directors, movies, screenings, screens

app = typer.Typer()
app.add_typer(bookings.app, name="bookings")
app.add_typer(directors.app, name="directors")
app.add_typer(movies.app, name="movies")
app.add_typer(screenings.app, name="screenings")
app.add_typer(screens.app, name="screens")
app.add_typer(db.app, name="db")
app.add_typer(customers.app, name="customers")

if __name__ == "__main__":
    app()
