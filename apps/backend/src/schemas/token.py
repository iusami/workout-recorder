from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """
    クライアントに返却するアクセストークンのスキーマ。
    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    アクセストークン内にエンコードされるデータ（ペイロード）のスキーマ。
    """

    # "sub" (subject) はJWTの標準的なクレームで、
    # ユーザーの識別子 (例: メールアドレスやユーザーID) を入れる
    sub: Optional[str] = None
