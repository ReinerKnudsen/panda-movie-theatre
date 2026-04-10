from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models.customer import Customer, CustomerCreate, CustomerPatch

router = APIRouter(prefix="/customers", tags=["customers"])


def generate_error_message(id: int):
    return f"Customer with id {id} is unknown"


@router.get("", status_code=200)
async def get_all_customers(session: Session = Depends(get_session)):
    statement = select(Customer)
    customers = session.exec(statement).all()
    return customers


@router.get("/{id}", status_code=200)
async def get_customer(
    id: int, session: Session = Depends(get_session)
) -> Customer | None:
    customer = session.get(Customer, id)
    if customer is not None:
        return customer
    else:
        raise HTTPException(status_code=404, detail=generate_error_message(id))


@router.post("", status_code=201)
async def create_customer(
    customer: CustomerCreate, session: Session = Depends(get_session)
) -> Customer:
    new_customer = Customer.model_validate(customer)
    session.add(new_customer)
    session.commit()
    session.refresh(new_customer)
    return new_customer


@router.patch("/{id}", status_code=200)
async def update_customer(
    id: int, patch: CustomerPatch, session: Session = Depends(get_session)
) -> Customer | None:
    customer = session.get(Customer, id)
    if customer is not None:
        c_data = patch.model_dump(exclude_unset=True)
        customer.sqlmodel_update(c_data)
        session.add(customer)
        session.commit()
        session.refresh(customer)
        return customer
    else:
        raise HTTPException(status_code=404, detail=generate_error_message(id))


@router.delete("/{id}", status_code=200)
async def delete_customer(id: int, session: Session = Depends(get_session)):
    customer = session.get(Customer, id)
    if customer is not None:
        session.delete(customer)
        session.commit()
        return customer
    else:
        raise HTTPException(status_code=404, detail=generate_error_message(id))
