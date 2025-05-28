import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

# src ディレクトリのファイルをインポートできるようにする
# (pytest.ini の pythonpath設定と合わせて確認)
from src.main import create_app  # FastAPI アプリのインスタンス
from src.core.database import (
    async_session_local,
    engine,
    get_session,
    create_db_and_tables,
    drop_db_and_tables,
)
# ↓↓↓↓↓ 重要: SQLModelのテーブル定義を読み込ませる ↓↓↓↓↓
from src import models # __init__.py などでモデルをインポートしておく

# テストエンジンが存在しない場合はスキップ (TEST_DATABASE_URL未設定時)
if not engine:
    pytest.skip("TEST_DATABASE_URL not set, skipping integration tests", allow_module_level=True)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """
    各テスト関数の前にDBテーブルを作成し、テスト後に削除するフィクスチャ。
    autouse=True で自動的に実行される。
    """
    assert engine is not None, "Test engine not initialized"
    await create_db_and_tables(engine)
    yield  # ここでテストが実行される
    await drop_db_and_tables(engine)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    テスト用の非同期DBセッションを提供するフィクスチャ。
    """
    assert async_session_local is not None, "Test session not initialized"
    async with async_session_local() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def test_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    FastAPIのTestClientを提供するフィクスチャ。
    DBセッションをテスト用にオーバーライドします。
    """

    async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
        """テスト用セッションを返す依存関係オーバーライド関数"""
        yield db_session

    # FastAPIアプリの get_session 依存関係をテスト用に差し替える
    create_app().dependency_overrides[get_session] = _override_get_session

    # httpx.AsyncClient を TestClient として使用
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    # テストが終わったらオーバーライドをクリア
    create_app().dependency_overrides.clear()

@pytest.fixture(scope="function")
def event_loop():
    """Create a new event loop for each test."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
