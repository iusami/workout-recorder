# apps/backend/tests/test_records.py

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select # select をインポート
import datetime

# サービスとスキーマ/モデルをインポート
from src.services import record_service
from src.schemas.record import RecordCreate
from src.models.record import WorkoutRecord

pytestmark = pytest.mark.asyncio

async def test_create_record_service(db_session: AsyncSession):
    """
    record_service.create_record が正しくDBに記録を作成できることをテストする。
    """
    # 1. テストデータを作成
    record_to_create = RecordCreate(
        user_id=1,
        exercise_date=datetime.date(2025, 5, 28),
        exercise="Squat",
        weight=100.0,
        reps=5,
        set_reps=3,
        notes="Felt good",
    )

    # 2. サービス関数を呼び出す（まだ実装されていないので失敗するはず）
    created_record = await record_service.create_record(
        db=db_session, record_in=record_to_create
    )

    # 3. アサーション (レッド！)
    #    (create_record が pass だと created_record は None なので失敗する)
    assert created_record is not None
    assert created_record.id is not None # IDが割り振られているか
    assert created_record.user_id == record_to_create.user_id
    assert created_record.exercise == record_to_create.exercise

    # 4. データベースを直接確認 (レッド！)
    #    (何も保存されていないので失敗する)
    statement = select(WorkoutRecord).where(WorkoutRecord.id == created_record.id)
    result = await db_session.execute(statement)
    db_record = result.scalar_one_or_none() # 1件だけ取得、なければ None

    assert db_record is not None
    assert db_record.exercise == "Squat"