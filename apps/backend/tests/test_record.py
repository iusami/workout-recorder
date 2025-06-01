import datetime

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.record import WorkoutRecord
from src.schemas.record import RecordCreate

# サービスとスキーマ/モデルをインポート
from src.services import record_service

pytestmark = pytest.mark.asyncio


async def test_create_record_service(db_session: AsyncSession):
    """
    record_service.create_record が正しくDBに記録を作成できることをテストする。
    """
    # 1. テストデータを作成
    test_user_id = 1  # 仮のユーザーID
    record_to_create = RecordCreate(
        exercise_date=datetime.date(2025, 5, 28),
        exercise='Squat',
        weight=100.0,
        reps=5,
        set_reps=3,
        notes='Felt good',
    )

    # 2. サービス関数を呼び出す
    created_record = await record_service.create_record(db=db_session, record_in=record_to_create, user_id=test_user_id)

    # 3. アサーション
    assert created_record is not None
    assert created_record.id is not None  # IDが割り振られているか
    assert created_record.user_id == test_user_id
    assert created_record.exercise == record_to_create.exercise

    # 4. データベースを直接確認
    statement = select(WorkoutRecord).where(WorkoutRecord.id == created_record.id)
    result = await db_session.exec(statement)
    db_record = result.one_or_none()  # 1件だけ取得、なければ None

    assert db_record is not None
    assert db_record.exercise == 'Squat'
