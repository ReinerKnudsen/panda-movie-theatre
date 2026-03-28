from database import get_session
from models.director import Director, DirectorCreate, DirectorPatch
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/directors", tags=["directors"])


@router.get("", status_code=200)
async def get_all_directors(session: Session = Depends(get_session)):
    statement = select(Director)
    directors = session.exec(statement).all()
    return directors


@router.get("/{id}", status_code=200)
async def get_director_by_id(id: int, session: Session = Depends(get_session)):
    director = session.get(Director, id)
    if director is not None:
        return director
    else:
        raise HTTPException(status_code=404, detail=f"Director with id {id} is unknown")


@router.post("", status_code=201)
async def create_director(
    director: DirectorCreate, session: Session = Depends(get_session)
):
    new_director = Director.model_validate(director)
    session.add(new_director)
    session.commit()
    session.refresh(new_director)
    return new_director


@router.delete("/{id}", status_code=200)
async def delete_director(id: int, session: Session = Depends(get_session)):
    director_to_delete = session.get(Director, id)
    if director_to_delete is not None:
        try:
            session.delete(director_to_delete)
            session.commit()
            return director_to_delete
        except IntegrityError:
            raise HTTPException(
                status_code=409,
                detail=f"Director {director_to_delete.last_name} is still connected to Movies",
            )
    else:
        raise HTTPException(status_code=404, detail=f"Director with id {id} is unknown")


@router.patch("/{id}", status_code=200)
async def update_director(
    id: int, director: DirectorPatch, session: Session = Depends(get_session)
):
    director_to_update = session.get(Director, id)
    if director_to_update is not None:
        director_data = director.model_dump(exclude_unset=True)
        director_to_update.sqlmodel_update(director_data)
        session.add(director_to_update)
        session.commit()
        session.refresh(director_to_update)
        return director_to_update
    else:
        raise HTTPException(status_code=404, detail=f"Director with id {id} is unknown")
