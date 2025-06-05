from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """
    システムに登録されたユーザーを表すUserモデル。

    このSQLModelテーブルクラスは、認証詳細やアカウント状態、プロフィール情報を含む
    ユーザー情報をデータベースに保存するための構造を定義します。

    属性:
        id (Optional[int]): ユーザーのプライマリーキー。
        email (str): ユーザーのメールアドレス、一意である必要があります。
        username (Optional[str]): オプションのユーザー名、
                                  提供される場合は一意である必要があります。
        hashed_password (str): セキュリティのためにハッシュ形式で保存されたパスワード。
        is_active (bool): ユーザーアカウントがアクティブかどうかを示すフラグ
        is_superuser (bool): ユーザーが管理者権限を持っているかどうかを示すフラグ
        first_name (Optional[str]): ユーザーの名前
        last_name (Optional[str]): ユーザーの姓
        date_of_birth (Optional[date]): ユーザーの生年月日
        height (Optional[float]): ユーザーの身長（cm）
        weight (Optional[float]): ユーザーの体重（kg）
        fitness_level (Optional[str]): フィットネスレベル（beginner, intermediate, advanced）
        fitness_goals (Optional[str]): フィットネス目標の説明
        preferred_units (str): 単位の設定（metric, imperial）
    """

    id: int = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, description="User's email address")
    username: Optional[str] = Field(default=None, unique=True, index=True, description='Username')
    hashed_password: str = Field(description='Hashed password')
    is_active: bool = Field(default=True, description='Is the user account active?')
    is_superuser: bool = Field(default=False, description='Is the user a superuser?')
    
    first_name: Optional[str] = Field(default=None, description='First name')
    last_name: Optional[str] = Field(default=None, description='Last name')
    date_of_birth: Optional[date] = Field(default=None, description='Date of birth')
    height: Optional[float] = Field(default=None, description='Height in centimeters')
    weight: Optional[float] = Field(default=None, description='Weight in kilograms')
    fitness_level: Optional[str] = Field(default=None, description='Fitness level: beginner, intermediate, advanced')
    fitness_goals: Optional[str] = Field(default=None, description='User fitness goals and objectives')
    preferred_units: str = Field(default='metric', description='Preferred units: metric or imperial')
