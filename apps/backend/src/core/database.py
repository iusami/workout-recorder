from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel  # SQLModel をインポート
from .config import settings

# 本番用エンジンとセッション
production_engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=True)
production_session_local = async_sessionmaker(
    bind=production_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# テスト用エンジンとセッション
test_engine = None
test_session_local = None
if settings.ASYNC_TEST_DATABASE_URL:
    test_engine = create_async_engine(settings.ASYNC_TEST_DATABASE_URL, echo=True)
    test_session_local = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

# 使用するエンジンとセッションを決定
engine = test_engine if test_engine else production_engine
async_session_local = (
    test_session_local if test_session_local else production_session_local
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI の Depends で使用する非同期DBセッションジェネレーター。
    使用後にセッションをクローズします。
    """
    async with async_session_local() as session:
        yield session


async def create_db_and_tables(engine_to_use):
    """
    データベースとテーブルを作成する関数 (主にテストや初期化用)
    Alembic を使うのが基本だが、テストでは便利。
    """
    async with engine_to_use.begin() as conn:
        # ここで SQLModel.metadata.create_all を実行する前に、
        # すべてのモデルがインポートされている必要がある。
        # (例: from src import models)
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_db_and_tables(engine_to_use):
    """
    データベースとテーブルを削除する関数 (主にテスト用)
    """
    async with engine_to_use.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
