from passlib.context import CryptContext

# パスワードハッシュ化のコンテキストを設定 (bcrypt を使用)
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """平文パスワードとハッシュ化されたパスワードを比較検証する"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """平文パスワードをハッシュ化する"""
    return pwd_context.hash(password)
