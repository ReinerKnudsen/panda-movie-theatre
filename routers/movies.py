from database import get_session
from models.director import Director  # noqa F401
from models.movie import Movie, MovieCreate, MoviePatch
from sqlmodel import Session, select

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("", status_code=200)
async def get_all_movies(session: Session = Depends(get_session)):
    statement = select(Movie)
    movies = session.exec(statement).all()
    return movies


@router.get("/{id}", status_code=200)
async def get_movie_by_id(id: int, session: Session = Depends(get_session)) -> Movie | None:
    movie = session.get(Movie, id)
    if movie is not None:
        return movie
    else:
        raise HTTPException(status_code=404, detail=f"Movie with id {id} is unknown.")

@router.post("", status_code=201)
async def create_movie(movie: MovieCreate, session: Session = Depends(get_session)) -> Movie:
    new_movie=Movie.model_validate(movie)
    session.add(new_movie)
    session.commit()
    session.refresh(new_movie)
    return new_movie


@router.patch("/{id}", status_code=200)
async def update_movie(id: int, movie: MoviePatch, session: Session = Depends(get_session)) -> Movie:
    existing_movie = session.get(Movie, id)
    if existing_movie:
        movie_data = movie.model_dump(exclude_unset=True)
        existing_movie.sqlmodel_update(movie_data)
        session.add(existing_movie)
        session.commit()
        session.refresh(existing_movie)
        return existing_movie
    else:
        raise HTTPException(status_code=404, detail=f"Movie with id {id} is unkown.")


@router.delete("/{id}", status_code=200)
async def delete_movie(id: int, session: Session = Depends(get_session)) -> Movie:
    movie_to_delete = session.get(Movie, id)
    if movie_to_delete:
        session.delete(movie_to_delete)
        session.commit()
        return movie_to_delete
    else:
        raise HTTPException(status_code=404, detail=f"Movie with id {id} is unknown.")
