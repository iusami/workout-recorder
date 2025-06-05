# apps/backend/src/services/user_service.py

import logging
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.logger import APP_LOGGER_NAME
from src.core.security import hash_password, verify_password
from src.models.user import User
from src.schemas.user import UserCreate, UserProfileUpdate

logger = logging.getLogger(APP_LOGGER_NAME)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """メールアドレスでユーザーを検索する"""
    statement = select(User).where(User.email == email)
    result = await db.exec(statement)
    return result.one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """ユーザー名でユーザーを検索する"""
    if not username:  # usernameがNoneまたは空文字列の場合
        return None
    statement = select(User).where(User.username == username)
    result = await db.exec(statement)
    return result.one_or_none()


async def create_user(db: AsyncSession, user_in: UserCreate) -> Optional[User]:
    """
    新しいユーザーを作成し、データベースに保存する。
    メールアドレスまたはユーザー名が重複している場合は None を返す
    または例外を発生させる
    """
    logger.info('Attempting to create user with email: %s', user_in.email)
    # メールアドレスの重複チェック
    db_user_by_email = await get_user_by_email(db, email=user_in.email)
    if db_user_by_email:
        logger.warning('Email %s already registered.', user_in.email)
        # raise HTTPException(status_code=400, detail="Email already registered")
        return None

    # ユーザー名の重複チェック (ユーザー名が存在する場合)
    if user_in.username:
        db_user_by_username = await get_user_by_username(db, username=user_in.username)
        if db_user_by_username:
            logger.warning('Username %s already registered.', user_in.username)
            return None

    hashed_password_str = hash_password(user_in.password)

    # SQLModelインスタンスを作成
    # UserCreate スキーマには hashed_password がないので、個別に設定
    user_data = user_in.model_dump(exclude={'password'})  # パスワードを除外
    db_user = User(**user_data, hashed_password=hashed_password_str, is_active=True)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    logger.info('User created successfully with email: %s, ID: %s', user_in.email, db_user.id)
    return db_user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    メールアドレスとパスワードでユーザーを認証する。
    認証に成功すれば User オブジェクトを、失敗すれば None を返す。
    """
    logger.debug('Attempting to authenticate user with email: %s', email)

    # 1. メールアドレスでユーザーを取得 (既存の関数を再利用)
    user = await get_user_by_email(db=db, email=email)

    # 2. ユーザーが存在しないか、アクティブでないかを確認
    if not user:
        logger.info('Authentication failed: User not found for email %s', email)
        return None
    if not user.is_active:
        logger.info('Authentication failed: User %s is inactive.', email)
        return None  # 非アクティブなユーザーは認証失敗

    # 3. パスワードを検証 (core.security の verify_password を使用)
    if not verify_password(password, user.hashed_password):
        logger.info('Authentication failed: Invalid password for user %s', email)
        return None

    # 4. すべてのチェックをパスしたら、ユーザーオブジェクトを返す (認証成功)
    logger.info('User %s authenticated successfully.', email)
    return user


async def update_user_profile(
    db: AsyncSession, user_id: int, profile_data: UserProfileUpdate
) -> Optional[User]:
    """
    ユーザーのプロフィール情報を更新する。
    """
    logger.info('Updating profile for user ID: %s', user_id)
    
    # ユーザーを取得
    statement = select(User).where(User.id == user_id)
    result = await db.exec(statement)
    user = result.one_or_none()
    
    if not user:
        logger.error('User not found for ID: %s', user_id)
        return None
    
    # プロフィールデータを更新 (Noneでない値のみ)
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info('Profile updated successfully for user ID: %s', user_id)
    return user
