import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.database import get_session
from src.core.logger import APP_LOGGER_NAME
from src.schemas.user import UserCreate, UserRead
from src.services import user_service

logger = logging.getLogger(APP_LOGGER_NAME)

router = APIRouter(
    prefix='/auth',  # プレフィックスを /auth に
    tags=['Authentication'],
)


@router.post('/register', response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user_endpoint(
    user_in: UserCreate, db: AsyncSession = Depends(get_session)
):
    logger.info('Registration attempt for email: %s', user_in.email)
    created_user = await user_service.create_user(db=db, user_in=user_in)
    if not created_user:
        logger.warning(
            'Registration failed for email %s: Email or Username already registered.',
            user_in.email,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Email or Username already registered',
        )
    logger.info('User registered successfully: %s', created_user.email)
    return created_user
