from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, Field
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """
    アプリケーションの設定を管理するクラス。
    環境変数または .env ファイルから読み込みます。
    """

    # .env ファイルから読み込む設定
    # env_file をワークスペースルートに設定
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
    )

    # データベースURL (Pydanticが形式を検証)
    DATABASE_URL: PostgresDsn

    # テスト用データベースURL (環境変数 TEST_DATABASE_URL がなければ None)
    TEST_DATABASE_URL: Optional[PostgresDsn] = Field(None)

    # 非同期DB接続用のURLを生成するプロパティ
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        # Pydantic v2 では str() を使う
        return str(self.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://")

    @property
    def ASYNC_TEST_DATABASE_URL(self) -> Optional[str]:
        if self.TEST_DATABASE_URL:
            return str(self.TEST_DATABASE_URL).replace(
                "postgresql://", "postgresql+asyncpg://"
            )
        return None


# 設定クラスのインスタンスを作成 (アプリケーション全体で共有)
# Pydantic Settingsは環境変数から自動的に値を読み込む
settings = Settings()  # type: ignore
