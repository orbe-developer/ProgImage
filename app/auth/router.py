"""Authentication endpoints: register, login, me."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import Token, UserCreate, UserRead
from app.auth.security import create_access_token, hash_password, verify_password
from app.database import get_session
from app.models.user import User
from app.schemas import ErrorResponse


router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
    },
)
async def register(
    payload: UserCreate,
    session: AsyncSession = Depends(get_session),
) -> User:
    """Create a new user account."""
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    await session.refresh(user)
    return user


@router.post(
    "/login",
    response_model=Token,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    },
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> Token:
    """Exchange email + password for a bearer token.

    OAuth2PasswordRequestForm uses ``username`` as the identifier field;
    this endpoint treats it as the user's email.
    """
    result = await session.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user.id)
    return Token(access_token=token)


@router.get(
    "/me",
    response_model=UserRead,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    },
)
async def me(current_user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user."""
    return current_user
