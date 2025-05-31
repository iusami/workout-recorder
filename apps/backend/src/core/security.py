from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from src.core.config import settings

# パスワードハッシュ化のコンテキストを設定 (bcrypt を使用)
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """平文パスワードとハッシュ化されたパスワードを比較検証する"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """平文パスワードをハッシュ化する"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    与えられたデータと有効期限からアクセストークン (JWT) を生成します。
    """
    to_encode = data.copy()

    # 有効期限を設定
    if expires_delta:
        # expires_delta が指定されていれば、それを使用
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # 指定されていなければ、設定ファイルからデフォルトの有効期限（分）を取得
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({'exp': expire})  # 有効期限 (exp) クレームを追加

    # JWTをエンコード
    # settings から SECRET_KEY と ALGORITHM を使用
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt
