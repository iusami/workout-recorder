import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.v1.auth import get_current_active_user
from src.core.database import get_session
from src.core.logger import APP_LOGGER_NAME
from src.models.user import User
from src.schemas.user import UserCreate, UserProfile, UserProfileUpdate, UserRead
from src.services import user_service

logger = logging.getLogger(APP_LOGGER_NAME)

router = APIRouter(
    prefix='/users',  # このルーターのプレフィックス
    tags=['Users'],  # APIドキュメント用のタグ
)


@router.post('/', response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_new_user_endpoint(  # 関数名を register_user_endpoint から変更してもOK
    user_in: UserCreate, db: AsyncSession = Depends(get_session)
):
    """
    新しいユーザーを作成（登録）する。
    """
    logger.info('User creation attempt for email:%s via /users endpoint', user_in.email)

    created_user = await user_service.create_user(db=db, user_in=user_in)

    if not created_user:
        logger.warning(
            'User creation failed for email %s:Email or Username already registered.',
            user_in.email,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Email or Username already registered',
        )

    logger.info('User created successfully: %s, ID: %s', created_user.email, created_user.id)
    return created_user


@router.get('/me', response_model=UserRead, status_code=status.HTTP_200_OK)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),  # 依存関係を注入
):
    """
    現在認証されているユーザーの情報を取得します。
    トークンが無効、またはユーザーがアクティブでない場合は、
    get_current_active_user 依存関係によってエラーが返されます。
    """
    logger.info('Fetching /users/me for user: %s', current_user.email)
    # get_current_active_user が User オブジェクトを返すので、それをそのまま返す
    # FastAPI が response_model=UserRead に従ってシリアライズしてくれる
    return current_user


@router.get('/me/profile', response_model=UserProfile, status_code=status.HTTP_200_OK)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    """
    現在認証されているユーザーのプロフィール情報を取得します。
    """
    logger.info('Fetching profile for user: %s', current_user.email)
    return current_user


@router.put('/me/profile', response_model=UserProfile, status_code=status.HTTP_200_OK)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
):
    """
    現在認証されているユーザーのプロフィール情報を更新します。
    """
    logger.info('Updating profile for user: %s', current_user.email)
    
    updated_user = await user_service.update_user_profile(
        db=db, user_id=current_user.id, profile_data=profile_data
    )
    
    if not updated_user:
        logger.error('Failed to update profile for user: %s', current_user.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Failed to update user profile'
        )
    
    logger.info('Profile updated successfully for user: %s', current_user.email)
    return updated_user
