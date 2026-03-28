from contextlib import asynccontextmanager

from database import create_db_and_tables
from models.director import Director  # noqa F401
from models.movie import Movie  # noqa F401
from routers import directors, movies

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(">>> create_db_and_tables wird aufgerufen")
    create_db_and_tables()
    print(">>> fertig")
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(movies.router)
app.include_router(directors.router)

