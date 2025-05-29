import datetime

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from src.schemas.record import RecordCreate
from src.services import record_service

pytestmark = pytest.mark.asyncio

async def test_create_record_api(test_client: AsyncClient):
    """
    POST /api/v1/records/ が成功し、201と記録データを返すことをテストする。
    """
    # 1. テストデータを作成
    record_data = {
        "user_id": 1,
        "exercise_date": "2025-05-29", # APIには YYYY-MM-DD 形式の文字列で送信
        "exercise": "Deadlift",
        "weight": 120.0,
        "reps": 3,
        "set_reps": 1,
        "notes": "API Test",
    }

    # 2. APIエンドポイントを呼び出す
    response = await test_client.post("/api/v1/records/", json=record_data)

    # 3. アサーション
    assert response.status_code == 201 # ステータスコードが 201 か

    response_data = response.json()
    assert response_data["user_id"] == record_data["user_id"]
    assert response_data["exercise"] == record_data["exercise"]
    assert response_data["weight"] == record_data["weight"]
    assert "id" in response_data # IDが返されているか
    assert response_data["exercise_date"] == record_data["exercise_date"]

async def test_read_record_api_success(test_client: AsyncClient,
                                       db_session: AsyncSession):
    """
    GET /api/v1/records/{record_id} が成功し、
    指定されたIDの記録データを返すことをテストする。
    """
    # 1. 事前にテストデータをDBに作成 (サービス層を直接利用)
    record_to_create = RecordCreate(
        user_id=1,
        exercise_date=datetime.date(2025, 5, 30),
        exercise="Bench Press",
        weight=80.0,
        reps=8,
        set_reps=3,
        notes="Test record for reading",
    )
    # サービスを使って直接DBに保存
    created_record_model = await record_service.create_record(db=db_session,
                                                              record_in=record_to_create)
    assert created_record_model.id is not None # IDが採番されていることを確認

    # 2. APIエンドポイントを呼び出す
    response = await test_client.get(f"/api/v1/records/{created_record_model.id}")

    # 3. アサーション
    assert response.status_code == 200 # 成功時は200 OK

    # 4. レスポンスボディのチェック
    response_data = response.json()
    assert response_data["id"] == created_record_model.id
    assert response_data["exercise"] == created_record_model.exercise
    assert response_data["user_id"] == created_record_model.user_id
    # 必要に応じて他のフィールドもチェック

async def test_read_record_api_not_found(test_client: AsyncClient):
    """
    存在しないIDの記録を読み込もうとした場合、404 Not Foundが返ることをテストする。
    """
    non_existent_id = 99999
    response = await test_client.get(f"/api/v1/records/{non_existent_id}")

    assert response.status_code == 404

async def test_get_record_by_id_service_success(db_session: AsyncSession):
    """
    record_service.get_record が指定されたIDの記録を正しく取得できることをテストする。
    """
    # 1. テストデータを作成
    record_to_create = RecordCreate(
        user_id=2,
        exercise_date=datetime.date(2025, 5, 31),
        exercise="Overhead Press",
        weight=40.0,
        reps=8,
        set_reps=4
    )
    created_record = await record_service.create_record(db=db_session,
                                                        record_in=record_to_create)
    assert created_record.id is not None

    # 2. サービス関数を呼び出す
    retrieved_record = await record_service.get_record(db=db_session,
                                                       record_id=created_record.id)

    # 3. アサーション
    assert retrieved_record is not None
    assert retrieved_record.id == created_record.id
    assert retrieved_record.exercise == "Overhead Press"

async def test_get_record_by_id_service_not_found(db_session: AsyncSession):
    """
    存在しないIDで record_service.get_record を呼び出すと None が返ることをテストする。
    """
    non_existent_id = 99998
    retrieved_record = await record_service.get_record(db=db_session,
                                                       record_id=non_existent_id)

    assert retrieved_record is None

async def test_read_records_api_success(test_client: AsyncClient,
                                        db_session: AsyncSession):
    """
    GET /api/v1/records/ が成功し、記録のリストを返すことをテストする。
    """
    # 1. 事前に複数のテストデータをDBに作成
    record1_data = RecordCreate(
        user_id=1,
        exercise_date=datetime.date(2025, 6, 1),
        exercise="Push Up",
        weight=0,
        reps=20,
        set_reps=3,
        notes="Record 1"
    )
    record2_data = RecordCreate(
        user_id=1,
        exercise_date=datetime.date(2025, 6, 2),
        exercise="Pull Up",
        weight=0,
        reps=10,
        set_reps=3,
        notes="Record 2"
    )
    await record_service.create_record(db=db_session, record_in=record1_data)
    await record_service.create_record(db=db_session, record_in=record2_data)

    # 2. APIエンドポイントを呼び出す
    response = await test_client.get("/api/v1/records/")

    # 3. アサーション
    assert response.status_code == 200 # 成功時は200 OK

    # 4. レスポンスボディのチェック
    response_data = response.json()
    assert isinstance(response_data, list) # リスト形式であること
    assert len(response_data) == 2         # 作成した2件の記録が返ってくること

    # (オプション) リストの中身も簡単にチェック
    assert response_data[0]["exercise"] == record1_data.exercise
    assert response_data[1]["exercise"] == record2_data.exercise

async def test_get_records_service(db_session: AsyncSession):
    """
    record_service.get_records が記録のリストを正しく取得できることをテストする。
    """
    # 1. 複数のテストデータを作成
    record1_data = RecordCreate(user_id=1, 
                                exercise_date=datetime.date(2025, 6, 3), exercise="Dip",
                                weight=10,
                                reps=15,
                                set_reps=3)
    record2_data = RecordCreate(user_id=1,
                                exercise_date=datetime.date(2025, 6, 4),
                                exercise="Leg Press",
                                weight=150,
                                reps=12,
                                set_reps=3)
    await record_service.create_record(db=db_session, record_in=record1_data)
    await record_service.create_record(db=db_session, record_in=record2_data)

    # 2. サービス関数を呼び出す
    retrieved_records = await record_service.get_records(db=db_session,
                                                         skip=0,
                                                         limit=10)

    # 3. アサーション
    assert retrieved_records is not None
    assert isinstance(retrieved_records, list)
    assert len(retrieved_records) == 2
    assert retrieved_records[0].exercise == "Dip"
    assert retrieved_records[1].exercise == "Leg Press"

    # (オプション) skip と limit のテストも追加するとより堅牢
    limited_records = await record_service.get_records(db=db_session,
                                                       skip=0,
                                                       limit=1)
    assert len(limited_records) == 1
    skipped_records = await record_service.get_records(db=db_session,
                                                       skip=1,
                                                       limit=1)
    assert len(skipped_records) == 1
    assert skipped_records[0].exercise == "Leg Press" # 2番目の記録のはず
