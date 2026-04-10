from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models.screen import Screen, ScreenCreate, ScreenPatch

router = APIRouter(prefix="/screens", tags=["screens"])


def create_error_message(id: int):
    return f"Screen with id {id} is unknown"


@router.get("", status_code=200)
async def get_all_screens(session: Session = Depends(get_session)):
    statement = select(Screen)
    screens = session.exec(statement).all()
    return screens


@router.get("/{id}", status_code=200)
async def get_screen_by_id(id: int, session: Session = Depends(get_session)) -> Screen:
    screen = session.get(Screen, id)
    if screen is not None:
        return screen
    else:
        raise HTTPException(status_code=404, detail=create_error_message(id))


@router.post("", status_code=201)
async def create_screen(
    screen: ScreenCreate, session: Session = Depends(get_session)
) -> Screen:
    new_screen = Screen.model_validate(screen)
    session.add(new_screen)
    session.commit()
    session.refresh(new_screen)
    return new_screen


@router.patch("/{id}", status_code=200)
async def update_screen(
    id: int, screen: ScreenPatch, session: Session = Depends(get_session)
) -> Screen | None:
    existing_screen = session.get(Screen, id)
    if existing_screen is not None:
        screen_data = screen.model_dump(exclude_unset=True)
        existing_screen.sqlmodel_update(screen_data)
        session.add(existing_screen)
        session.commit()
        session.refresh(existing_screen)
        return existing_screen
    else:
        raise HTTPException(status_code=404, detail=create_error_message(id))


@router.delete("/{id}", status_code=200)
async def delete_screen(id: int, session: Session = Depends(get_session)) -> Screen:
    existing_screen = session.get(Screen, id)
    if existing_screen is not None:
        session.delete(existing_screen)
        session.commit()
        return existing_screen
    else:
        raise HTTPException(status_code=404, detail=create_error_message(id))
