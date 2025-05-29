import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.database import get_session
from src.main import create_app

# テスト用DB URLを確定 (SQLiteを強制使用)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """
    テストセッション全体で単一のイベントループを作成して使用する。
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine(event_loop) -> AsyncGenerator[AsyncEngine, None]:
    """
    セッションスコープで非同期テストエンジンを作成するフィクスチャ。
    引数で渡された session スコープの event_loop を使用します。
    """
    # event_loop フィクスチャがこのスコープで asyncio.set_event_loop() を
    # 呼び出していることを pytest-asyncio が期待します。
    # create_async_engine は現在のループを使用します。
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_tables(test_engine: AsyncEngine):
    """
    各テストの前にテーブルを再作成するフィクスチャ。
    """
    # drop_all と create_all を別々のトランザクションで実行
    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
    except (ProgrammingError, OperationalError) as e:
        # テーブルが存在しない場合の特定のエラーのみ無視
        # エラーの内容をログに出力することも検討
        print(f"テーブル削除中のエラーを無視します: {e}")

    # 新しいトランザクションでテーブルを作成
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    各テスト用の非同期DBセッションを提供するフィクスチャ。
    """
    session_maker = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def test_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    FastAPIのTestClientを提供するフィクスチャ。
    """
    app = create_app()

    async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session

    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
