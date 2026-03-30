from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from schemas.auth import LoginRequest, RegisterRequest, Token
from schemas.user import UserRead
from services import auth_service
from utils.jwt import create_access_token
from utils.service_errors import raise_service_exception

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = auth_service.authenticate_user(db, payload)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, token_type="bearer")


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserRead:
    try:
        user = auth_service.register_user(db, payload)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)
    return UserRead.model_validate(user)
