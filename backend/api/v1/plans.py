from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_role
from core.models import Plan, User
from core.schemas_completos import PlanCreate, PlanResponse, PlanUpdate

router = APIRouter(prefix="/plans", tags=["plans"])


def require_playwave_admin(
    current_user: User = Depends(require_role("admin")),
) -> User:
    return current_user


@router.get("/", response_model=List[PlanResponse])
def list_plans(
    db: Session = Depends(get_db),
    _: User = Depends(require_playwave_admin),
):
    return db.query(Plan).order_by(Plan.price_brl.asc(), Plan.name.asc()).all()


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_playwave_admin),
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    return plan


@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    plan_in: PlanCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_playwave_admin),
):
    if db.query(Plan).filter(Plan.id == plan_in.id).first():
        raise HTTPException(status_code=409, detail="Já existe um plano com este id")

    plan = Plan(**plan_in.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.put("/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: str,
    plan_in: PlanUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_playwave_admin),
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    for field, value in plan_in.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)

    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_playwave_admin),
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    db.delete(plan)
    db.commit()
    return None
