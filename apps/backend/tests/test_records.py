import datetime
from typing import Optional

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from src.schemas.user import UserCreate
from src.schemas.record import RecordCreate, RecordUpdate
from src.services import record_service, user_service

pytestmark = pytest.mark.asyncio

async def test_read_record_api_success(test_client: AsyncClient,
                                       db_session: AsyncSession):
    """
    GET /api/v1/records/{record_id} が成功し、
    指定されたIDの記録データを返すことをテストする。
    """
    # 1. 事前にテストデータをDBに作成 (サービス層を直接利用)
    test_user_id = 1
    record_to_create = RecordCreate(
        exercise_date=datetime.date(2025, 5, 30),
        exercise="Bench Press",
        weight=80.0,
        reps=8,
        set_reps=3,
        notes="Test record for reading",
    )
    # サービスを使って直接DBに保存
    created_record_model = await record_service.create_record(db=db_session,
                                                              record_in=record_to_create,
                                                              user_id=test_user_id)
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
    test_user_id = 1
    record_to_create = RecordCreate(
        exercise_date=datetime.date(2025, 5, 31),
        exercise="Overhead Press",
        weight=40.0,
        reps=8,
        set_reps=4
    )
    created_record = await record_service.create_record(db=db_session,
                                                        record_in=record_to_create,
                                                        user_id=test_user_id)
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
    test_user_id = 1
    record1_data = RecordCreate(
        exercise_date=datetime.date(2025, 6, 1),
        exercise="Push Up",
        weight=0,
        reps=20,
        set_reps=3,
        notes="Record 1"
    )
    record2_data = RecordCreate(
        exercise_date=datetime.date(2025, 6, 2),
        exercise="Pull Up",
        weight=0,
        reps=10,
        set_reps=3,
        notes="Record 2"
    )
    await record_service.create_record(db=db_session,
                                       record_in=record1_data,
                                       user_id=test_user_id)
    await record_service.create_record(db=db_session,
                                       record_in=record2_data,
                                       user_id=test_user_id)

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
    test_user_id = 1
    record1_data = RecordCreate(
        exercise_date=datetime.date(2025, 6, 3), exercise="Dip",
        weight=10,
        reps=15,
        set_reps=3)
    record2_data = RecordCreate(
        exercise_date=datetime.date(2025, 6, 4),
        exercise="Leg Press",
        weight=150,
        reps=12,
        set_reps=3)
    await record_service.create_record(db=db_session,
                                       record_in=record1_data,
                                       user_id=test_user_id)
    await record_service.create_record(db=db_session,
                                       record_in=record2_data,
                                       user_id=test_user_id)

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

async def test_update_record_api_success(test_client: AsyncClient,
                                         db_session: AsyncSession):
    """
    PUT /api/v1/records/{record_id} が成功し、
    更新された記録データを返すことをテストする。
    """
    # 1. 事前にテストデータをDBに作成
    test_user_id = 1
    initial_data = RecordCreate(
        exercise_date=datetime.date(2025, 7, 1),
        exercise="Squat",
        weight=100.0,
        reps=5,
        set_reps=3,
        notes="Initial Notes"
    )
    created_record = await record_service.create_record(db=db_session,
                                                        record_in=initial_data,
                                                        user_id=test_user_id)
    assert created_record.id is not None

    # 2. 更新用データを作成 (例: notes と weight を変更)
    update_payload = {
        "notes": "Updated notes after feeling stronger!",
        "weight": 102.5
    }

    # 3. APIエンドポイントを呼び出す
    response = await test_client.put(f"/api/v1/records/{created_record.id}",
                                    json=update_payload)

    # 4. アサーション
    assert response.status_code == 200 # 成功時は200 OK

    response_data = response.json()
    assert response_data["id"] == created_record.id
    assert response_data["notes"] == update_payload["notes"] # 更新されたフィールド
    assert response_data["weight"] == update_payload["weight"] # 更新されたフィールド
    assert response_data["exercise"] == initial_data.exercise

async def test_update_record_api_not_found(test_client: AsyncClient):
    """
    存在しないIDの記録を更新しようとした場合、404 Not Foundが返ることをテストする。
    """
    non_existent_id = 99997
    update_payload = {"notes": "This should fail"}
    response = await test_client.put(f"/api/v1/records/{non_existent_id}",
                                     json=update_payload)

    assert response.status_code == 404

async def test_update_record_service_success(db_session: AsyncSession):
    """
    record_service.update_record が指定されたIDの記録を
    正しく更新できることをテストする。
    """
    # 1. 初期データを作成・保存
    test_user_id = 1
    initial_record_data = RecordCreate(
        exercise_date=datetime.date(2025, 7, 2),
        exercise="Bench Press",
        weight=90.0,
        reps=6,
        set_reps=3,
        notes="Initial state"
    )
    initial_record = await record_service.create_record(db=db_session,
                                                        record_in=initial_record_data,
                                                        user_id=test_user_id)
    assert initial_record.id is not None

    # 2. 更新用データを作成 (一部のフィールドのみ)
    update_data = RecordUpdate(notes="Felt a bit tired", reps=5)

    # 3. サービス関数を呼び出す
    updated_record = await record_service.update_record(
        db=db_session, record_id=initial_record.id, record_update=update_data
    )

    # 4. アサーション
    assert updated_record is not None
    assert updated_record.id == initial_record.id
    assert updated_record.notes == "Felt a bit tired" # 更新された
    assert updated_record.reps == 5                 # 更新された
    assert updated_record.weight == 90.0            # 更新していないので元のまま
    assert updated_record.exercise == "Bench Press" # 更新していないので元のまま

async def test_update_record_service_not_found(db_session: AsyncSession):
    """
    存在しないIDの記録を record_service.update_record で更新しようとすると None が返る。
    """
    non_existent_id = 99996
    update_data = RecordUpdate(notes="This should not apply")
    updated_record = await record_service.update_record(
        db=db_session, record_id=non_existent_id, record_update=update_data
    )
    assert updated_record is None


async def test_delete_record_service_success(db_session: AsyncSession):
    """
    record_service.delete_record が指定されたIDの記録を正しく削除し、
    削除されたオブジェクトを返すことをテストする。
    その後、get_record で取得できないことも確認する。
    """
    # 1. テストデータを作成・保存
    test_user_id = 1
    record_to_create = RecordCreate(
        exercise_date=datetime.date(2025, 1, 1),
        exercise="Test Exercise for Deletion",
        weight=50.0,
        reps=10,
        set_reps=3
    )
    created_record = await record_service.create_record(db=db_session,
                                                        record_in=record_to_create,
                                                        user_id=test_user_id)
    assert created_record.id is not None
    created_record_id = created_record.id # IDを保存しておく

    # 2. サービス関数 delete_record を呼び出す
    deleted_record = await record_service.delete_record(db=db_session,
                                                        record_id=created_record_id)

    # 3. アサーション (delete_record の返り値)
    assert deleted_record is not None
    assert deleted_record.id == created_record_id
    assert deleted_record.exercise == "Test Exercise for Deletion"
    assert deleted_record.user_id == 1

    # 4. 削除されたことを確認 (get_record で取得できない)
    record_after_deletion = await record_service.get_record(db=db_session,
                                                            record_id=created_record_id)
    assert record_after_deletion is None


async def test_delete_record_service_not_found(db_session: AsyncSession):
    """
    存在しないIDで record_service.delete_record を呼び出すと None が返ることをテスト
    """
    non_existent_id = 99999
    deleted_record = await record_service.delete_record(db=db_session,
                                                        record_id=non_existent_id)

    assert deleted_record is None


async def test_delete_record_api_success(test_client: AsyncClient,
                                         db_session: AsyncSession):
    """
    DELETE /api/v1/records/{record_id} が成功し、
    削除された記録データを返し、実際にDBから削除されることをテストする。
    """
    # 1. 事前にテストデータをDBに作成 (サービス層を直接利用)
    test_user_id = 10
    record_to_create = RecordCreate(
        exercise_date=datetime.date(2025, 12, 25),
        exercise="API Delete Test Exercise",
        weight=77.7,
        reps=7,
        set_reps=1,
        notes="To be deleted via API",
    )
    created_record = await record_service.create_record(db=db_session,
                                                        record_in=record_to_create,
                                                        user_id=test_user_id)
    assert created_record.id is not None
    created_record_id = created_record.id

    # 2. APIエンドポイントを呼び出す
    response = await test_client.delete(f"/api/v1/records/{created_record_id}")

    # 3. アサーション (レスポンス)
    assert response.status_code == 200 # 成功時は200 OK (FastAPIのstatus.HTTP_200_OK)

    response_data = response.json()
    assert response_data["id"] == created_record_id
    assert response_data["exercise"] == "API Delete Test Exercise"
    assert response_data["user_id"] == 10
    assert response_data["weight"] == 77.7

    # 4. DBから実際に削除されたことを確認 (サービス層を利用)
    record_in_db = await record_service.get_record(db=db_session,
                                                   record_id=created_record_id)
    assert record_in_db is None


async def test_delete_record_api_not_found(test_client: AsyncClient):
    """
    存在しないIDの記録をDELETEしようとした場合、404 Not Foundが返ることをテストする。
    """
    non_existent_id = 99998 # 既存のテストと重複しないID
    response = await test_client.delete(f"/api/v1/records/{non_existent_id}")

    assert response.status_code == 404 # FastAPIのstatus.HTTP_404_NOT_FOUND

async def get_auth_headers(test_client: AsyncClient,
                           db_session: AsyncSession,
                           email: str,
                           password: str,
                           username: Optional[str] = None) -> dict:
    """ヘルパー関数: テストユーザーを作成・ログインし、認証ヘッダーを返す"""
    if username is None:
        username = email.split('@')[0] + "_header_user" # 適当なユーザー名

    # ユーザーが存在しない場合のみ作成
    user_check = await user_service.get_user_by_email(db=db_session, email=email)
    if not user_check:
        user_create_data = UserCreate(email=email, username=username, password=password)
        await user_service.create_user(db=db_session, user_in=user_create_data)

    login_payload = {"username": email, "password": password}
    login_response = await test_client.post("/api/v1/auth/token", data=login_payload)
    assert login_response.status_code == 200, f"Failed to login for token: {login_response.text}"
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

async def test_create_record_api_no_token(test_client: AsyncClient):
    """
    POST /api/v1/records/ にトークンなしでアクセスすると 401 Unauthorized が返る。
    """
    record_payload = {
        "date": "2025-07-03",
        "exercise": "Overhead Press",
        "weight": 50.0,
        "reps": 5,
        "set_reps": 5,
    }
    response = await test_client.post("/api/v1/records/", json=record_payload)
    assert response.status_code == 401

async def test_create_record_api_with_token_success(test_client: AsyncClient, db_session: AsyncSession):
    """
    POST /api/v1/records/ に有効なトークンでアクセスすると記録が作成され、
    作成された記録の user_id がトークンのユーザーのIDと一致する。
    """
    user_email = "record_creator@example.com"
    user_password = "password123"
    auth_headers = await get_auth_headers(test_client, db_session, user_email, user_password)

    # ログインユーザーの情報を取得して user_id を確認 (テストの正確性のため)
    me_response = await test_client.get("/api/v1/users/me", headers=auth_headers)
    assert me_response.status_code == 200
    current_user_id = me_response.json()["id"]

    record_payload = {
        "exercise_date": "2025-07-04",
        "exercise": "Barbell Row",
        "weight": 60.0,
        "reps": 8,
        "set_reps": 3,
        "notes": "Good form"
    }

    response = await test_client.post("/api/v1/records/", json=record_payload, headers=auth_headers)

    # アサーション
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["exercise"] == record_payload["exercise"]
    assert "id" in response_data
    assert response_data["user_id"] == current_user_id