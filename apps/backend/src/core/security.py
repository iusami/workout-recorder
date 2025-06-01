import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from passlib.context import CryptContext

from src.core.config import settings
from src.core.logger import APP_LOGGER_NAME

logger = logging.getLogger(APP_LOGGER_NAME)

# トークン検証失敗時のための共通例外
CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Could not validate credentials',
    headers={'WWW-Authenticate': 'Bearer'},  # OAuth2標準のレスポンスヘッダー
)

EXPIRED_TOKEN_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Token has expired',
    headers={'WWW-Authenticate': 'Bearer'},
)

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
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({'exp': expire})  # 有効期限 (exp) クレームを追加

    # JWTをエンコード
    # settings から SECRET_KEY と ALGORITHM を使用
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> str:
    """
    アクセストークンをデコードし、ペイロードから subject (ユーザー識別子) を抽出する。
    検証に失敗した場合は HTTPException を発生させる。
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # "sub" (subject) クレームを取得
        subject: Optional[str] = payload.get('sub')
        if subject is None:
            logger.warning("Token decoding failed: 'sub' claim missing in payload: %s", payload)
            # subject がペイロードに含まれない、または None の場合は不正なトークン
            raise CREDENTIALS_EXCEPTION
        logger.debug('Token decoded successfully. Subject (sub): %s', subject)
        return subject
    except ExpiredSignatureError as exc:
        logger.warning('Token decoding failed: Token has expired.')
        # トークンの有効期限切れ
        raise EXPIRED_TOKEN_EXCEPTION from exc
    except JWTError as exc:
        logger.warning('Token decoding failed: JWTError: %s.', str(exc))
        # その他のJWT関連エラー (署名不正など)
        raise CREDENTIALS_EXCEPTION from exc
