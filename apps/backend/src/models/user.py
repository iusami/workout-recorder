from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """
    システムに登録されたユーザーを表すUserモデル。

    このSQLModelテーブルクラスは、認証詳細やアカウント状態を含むユーザー情報を
    データベースに保存するための構造を定義します。

    属性:
        id (Optional[int]): ユーザーのプライマリーキー。
        email (str): ユーザーのメールアドレス、一意である必要があります。
        username (Optional[str]): オプションのユーザー名、
                                  提供される場合は一意である必要があります。
        hashed_password (str): セキュリティのためにハッシュ形式で保存されたパスワード。
        is_active (bool): ユーザーアカウントがアクティブかどうかを示すフラグ
        is_superuser (bool): ユーザーが管理者権限を持っているかどうかを示すフラグ
    """

    id: int = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, description="User's email address")
    username: Optional[str] = Field(default=None, unique=True, index=True, description='Username')
    hashed_password: str = Field(description='Hashed password')
    is_active: bool = Field(default=True, description='Is the user account active?')
    is_superuser: bool = Field(default=False, description='Is the user a superuser?')
