import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.config import settings
from src.core.database import get_session
from src.core.logger import APP_LOGGER_NAME
from src.core.security import create_access_token, decode_access_token
from src.models.user import User
from src.schemas.token import Token
from src.services import user_service

logger = logging.getLogger(APP_LOGGER_NAME)

router = APIRouter(
    prefix='/auth',  # プレフィックスを /auth に
    tags=['Authentication'],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


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


async def get_current_active_user(
    token: str = Depends(oauth2_scheme),  # ヘッダーからトークンを取得
    db: AsyncSession = Depends(get_session),
) -> User:  # 返り値の型ヒントを User モデルに
    """
    提供されたアクセストークンを検証し、
    アクティブなユーザーオブジェクトを返す依存関係関数。
    トークンが無効、ユーザーが存在しない、または非アクティブな場合は HTTPException
    """
    logger.debug('Attempting to get current active user from token.')

    # decode_access_token はトークンが無効/期限切れの場合に HTTPException を発生させる
    email_from_token = decode_access_token(token)

    user = await user_service.get_user_by_email(db, email=email_from_token)

    if user is None:
        logger.warning('User not found for email from token: %s', email_from_token)
        # CREDENTIALS_EXCEPTION は security.py で定義したものを使っても良い
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials - user not found',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    if not user.is_active:
        logger.warning('Authentication attempt for inactive user: %s', user.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Inactive user'
        )

    logger.debug('Current active user identified: %s', user.email)
    return user
