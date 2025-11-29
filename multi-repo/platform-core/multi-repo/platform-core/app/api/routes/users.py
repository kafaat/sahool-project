from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app import schemas, models
from app.services.user_service import create_user

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=schemas.User)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.post("", response_model=schemas.User, status_code=201)
def create_user_endpoint(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Here you can add RBAC checks (only tenant admins / superusers)
    user = create_user(db, user_in)
    return user