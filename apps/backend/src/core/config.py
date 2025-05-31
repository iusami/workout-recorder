import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    アプリケーションの設定を管理するクラス。
    環境変数または .env ファイルから読み込みます。
    """

    # .env ファイルから読み込む設定
    # env_file をワークスペースルートに設定
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent.parent.parent / '.env'),
        env_file_encoding='utf-8',
    )

    # データベースURL (PostgreSQL または SQLite)
    # CI環境ではSQLiteを使用
    DATABASE_URL: str = 'sqlite+aiosqlite:///./test.db' if os.environ.get('CI') else Field(...)

    # テスト用データベースURL (環境変数 TEST_DATABASE_URL がなければ None)
    # CI環境ではSQLiteを使用
    TEST_DATABASE_URL: Optional[str] = Field(default='sqlite+aiosqlite:///./test.db' if os.environ.get('CI') else None)

    LOG_LEVEL: str = Field(default='INFO')

    # トークン署名に使用する秘密鍵 (非常に重要。複雑でランダムな文字列にしてください)
    SECRET_KEY: str = Field(..., alias='SECRET_KEY')
    # トークン署名アルゴリズム
    ALGORITHM: str = Field('HS256', alias='ALGORITHM')
    # アクセストークンの有効期間 (分単位)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, alias='ACCESS_TOKEN_EXPIRE_MINUTES')

    # 非同期DB接続用のURLを生成するプロパティ
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        # Pydantic v2 では str() を使う
        url = str(self.DATABASE_URL)
        # PostgreSQLの場合のみasyncpgに変換
        if url.startswith('postgresql://'):
            return url.replace('postgresql://', 'postgresql+asyncpg://')
        return url

    @property
    def ASYNC_TEST_DATABASE_URL(self) -> Optional[str]:
        if self.TEST_DATABASE_URL:
            url = str(self.TEST_DATABASE_URL)
            # PostgreSQLの場合のみasyncpgに変換
            if url.startswith('postgresql://'):
                return url.replace('postgresql://', 'postgresql+asyncpg://')
            return url
        return None


# 設定クラスのインスタンスを作成 (アプリケーション全体で共有)
# Pydantic Settingsは環境変数から自動的に値を読み込む
settings = Settings()  # type: ignore
