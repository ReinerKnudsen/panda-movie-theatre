from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import create_db_and_tables
from models.booking import Booking  # noqa F401
from models.customer import Customer  # noqa F401
from models.director import Director  # noqa F401
from models.movie import Movie  # noqa F401
from models.screen import Screen  # noqa F401
from models.screening import Screening  # noqa F401
from routers import bookings, customers, directors, movies, screenings, screens


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(">>> create_db_and_tables wird aufgerufen")
    create_db_and_tables()
    print(">>> fertig")
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(movies.router)
app.include_router(directors.router)
app.include_router(screens.router)
app.include_router(screenings.router)
app.include_router(bookings.router)
app.include_router(customers.router)
