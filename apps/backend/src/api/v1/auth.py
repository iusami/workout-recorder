import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.config import settings
from src.core.database import get_session
from src.core.logger import APP_LOGGER_NAME
from src.core.security import create_access_token
from src.schemas.token import Token
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


@router.post('/token', response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
):
    """
    ユーザーのメールアドレス（フォームではusernameとして送信）とパスワードで認証し、
    アクセストークンを発行する。
    """
    logger.info('Login attempt for username (email): %s', form_data.username)

    # 1. ユーザー認証サービスを呼び出す
    user = await user_service.authenticate_user(
        db=db, email=form_data.username, password=form_data.password
    )

    # 2. 認証失敗時のエラーハンドリング
    if not user:
        logger.warning(
            'Login failed for username (email): %s.'
            'Invalid credentials or inactive user.',
            form_data.username,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect email or password',
            headers={'WWW-Authenticate': 'Bearer'},  # OAuth2標準のレスポンスヘッダー
        )

    # 3. アクセストークンを生成
    # トークンに含めるデータ (subject はユーザーの一意な識別子)
    # 例: user.email または str(user.id)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token_data = {'sub': user.email}

    access_token = create_access_token(
        data=access_token_data, expires_delta=access_token_expires
    )

    logger.info('Token generated successfully for user: %s', user.email)

    # 4. トークンを返す
    return Token(access_token=access_token, token_type='bearer')
