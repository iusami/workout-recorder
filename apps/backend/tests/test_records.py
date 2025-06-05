import datetime
import logging
from typing import Optional

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.logger import APP_LOGGER_NAME
from src.schemas.record import RecordCreate, RecordUpdate
from src.schemas.user import UserCreate
from src.services import record_service, user_service

logger = logging.getLogger(APP_LOGGER_NAME)

pytestmark = pytest.mark.asyncio


async def test_get_record_by_id_service_success(db_session: AsyncSession):
    """
    record_service.get_record が指定されたIDの記録を正しく取得できることをテストする。
    """
    # 1. テストデータを作成
    test_user_id = 1
    record_to_create = RecordCreate(
        exercise_date=datetime.date(2025, 5, 31), exercise='Overhead Press', weight=40.0, reps=8, set_reps=4
    )
    created_record = await record_service.create_record(db=db_session, record_in=record_to_create, user_id=test_user_id)
    assert created_record.id is not None

    # 2. サービス関数を呼び出す
    retrieved_record = await record_service.get_record(db=db_session, record_id=created_record.id, user_id=test_user_id)

    # 3. アサーション
    assert retrieved_record is not None
    assert retrieved_record.id == created_record.id
    assert retrieved_record.exercise == 'Overhead Press'


async def test_get_record_by_id_service_not_found(db_session: AsyncSession):
    """
    存在しないIDで record_service.get_record を呼び出すと None が返ることをテストする。
    """
    non_existent_id = 99998
    retrieved_record = await record_service.get_record(db=db_session, record_id=non_existent_id, user_id=1)

    assert retrieved_record is None


async def test_get_records_service(db_session: AsyncSession):
    """
    record_service.get_records が記録のリストを正しく取得できることをテストする。
    """
    # 1. 複数のテストデータを作成
    test_user_id = 1
    record1_data = RecordCreate(exercise_date=datetime.date(2025, 6, 3), exercise='Dip', weight=10, reps=15, set_reps=3)
    record2_data = RecordCreate(
        exercise_date=datetime.date(2025, 6, 4), exercise='Leg Press', weight=150, reps=12, set_reps=3
    )
    await record_service.create_record(db=db_session, record_in=record1_data, user_id=test_user_id)
    await record_service.create_record(db=db_session, record_in=record2_data, user_id=test_user_id)

    # 2. サービス関数を呼び出す
    retrieved_records = await record_service.get_records(db=db_session, skip=0, limit=10, user_id=test_user_id)

    # 3. アサーション
    assert retrieved_records is not None
    assert isinstance(retrieved_records, list)
    assert len(retrieved_records) == 2
    assert retrieved_records[0].exercise == 'Dip'
    assert retrieved_records[1].exercise == 'Leg Press'

    # (オプション) skip と limit のテストも追加するとより堅牢
    limited_records = await record_service.get_records(db=db_session, skip=0, limit=1, user_id=test_user_id)
    assert len(limited_records) == 1
    skipped_records = await record_service.get_records(db=db_session, skip=1, limit=1, user_id=test_user_id)
    assert len(skipped_records) == 1
    assert skipped_records[0].exercise == 'Leg Press'  # 2番目の記録のはず


async def test_update_record_service_success(db_session: AsyncSession):
    """
    record_service.update_record が指定されたIDの記録を
    正しく更新できることをテストする。
    """
    # 1. 初期データを作成・保存
    test_user_id = 1
    initial_record_data = RecordCreate(
        exercise_date=datetime.date(2025, 7, 2),
        exercise='Bench Press',
        weight=90.0,
        reps=6,
        set_reps=3,
        notes='Initial state',
    )
    initial_record = await record_service.create_record(
        db=db_session, record_in=initial_record_data, user_id=test_user_id
    )
    assert initial_record.id is not None

    # 2. 更新用データを作成 (一部のフィールドのみ)
    update_data = RecordUpdate(notes='Felt a bit tired', reps=5)

    # 3. サービス関数を呼び出す
    updated_record = await record_service.update_record(
        db=db_session, record_id=initial_record.id, record_update=update_data, user_id=test_user_id
    )

    # 4. アサーション
    assert updated_record is not None
    assert updated_record.id == initial_record.id
    assert updated_record.notes == 'Felt a bit tired'  # 更新された
    assert updated_record.reps == 5  # 更新された
    assert updated_record.weight == 90.0  # 更新していないので元のまま
    assert updated_record.exercise == 'Bench Press'  # 更新していないので元のまま


async def test_update_record_service_not_found(db_session: AsyncSession):
    """
    存在しないIDの記録を record_service.update_record で更新しようとすると None が返る。
    """
    non_existent_id = 99996
    update_data = RecordUpdate(notes='This should not apply')
    updated_record = await record_service.update_record(
        db=db_session, record_id=non_existent_id, record_update=update_data, user_id=1
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
        exercise_date=datetime.date(2025, 1, 1), exercise='Test Exercise for Deletion', weight=50.0, reps=10, set_reps=3
    )
    created_record = await record_service.create_record(db=db_session, record_in=record_to_create, user_id=test_user_id)
    assert created_record.id is not None
    created_record_id = created_record.id  # IDを保存しておく

    # 2. サービス関数 delete_record を呼び出す
    deleted_record = await record_service.delete_record(
        db=db_session, record_id=created_record_id, user_id=test_user_id
    )

    # 3. アサーション (delete_record の返り値)
    assert deleted_record is not None
    assert deleted_record.id == created_record_id
    assert deleted_record.exercise == 'Test Exercise for Deletion'
    assert deleted_record.user_id == 1

    # 4. 削除されたことを確認 (get_record で取得できない)
    record_after_deletion = await record_service.get_record(
        db=db_session, record_id=created_record_id, user_id=test_user_id
    )
    assert record_after_deletion is None


async def get_auth_headers(
    test_client: AsyncClient, db_session: AsyncSession, email: str, password: str, username: Optional[str] = None
) -> dict:
    """ヘルパー関数: テストユーザーを作成・ログインし、認証ヘッダーを返す"""
    if username is None:
        username = email.split('@')[0] + '_header_user'  # 適当なユーザー名

    logger.debug('get_auth_headers: Checking if user %s exists...', email)

    # ユーザーが存在しない場合のみ作成
    user_check = await user_service.get_user_by_email(db=db_session, email=email)
    if not user_check:
        logger.debug('get_auth_headers: User %s not found, creating...', email)
        user_create_data = UserCreate(email=email, username=username, password=password)
        created_user = await user_service.create_user(db=db_session, user_in=user_create_data)
        assert created_user is not None, f'Failed to create user {email}: {created_user}'
        logger.debug('get_auth_headers: User %s created with ID %s', email, created_user.id)

    login_payload = {'username': email, 'password': password}
    login_response = await test_client.post('/api/v1/auth/token', data=login_payload)
    assert login_response.status_code == 200, f'Failed to login for token: {login_response.text}'
    token = login_response.json()['access_token']
    logger.debug('get_auth_headers: Token obtained for user %s', email)
    return {'Authorization': f'Bearer {token}'}


async def test_create_record_api_no_token(test_client: AsyncClient):
    """
    POST /api/v1/records/ にトークンなしでアクセスすると 401 Unauthorized が返る。
    """
    record_payload = {
        'exercise_date': '2025-07-03',
        'exercise': 'Overhead Press',
        'weight': 50.0,
        'reps': 5,
        'set_reps': 5,
    }
    response = await test_client.post('/api/v1/records/', json=record_payload)
    assert response.status_code == 401


async def test_create_record_api_with_token_success(test_client: AsyncClient, db_session: AsyncSession):
    """
    POST /api/v1/records/ に有効なトークンでアクセスすると記録が作成され、
    作成された記録の user_id がトークンのユーザーのIDと一致する。
    """
    user_email = 'record_creator@example.com'
    user_password = 'password123'
    auth_headers = await get_auth_headers(test_client, db_session, user_email, user_password)

    # ログインユーザーの情報を取得して user_id を確認 (テストの正確性のため)
    me_response = await test_client.get('/api/v1/users/me', headers=auth_headers)
    assert me_response.status_code == 200
    current_user_id = me_response.json()['id']

    record_payload = {
        'exercise_date': '2025-07-04',
        'exercise': 'Barbell Row',
        'weight': 60.0,
        'reps': 8,
        'set_reps': 3,
        'notes': 'Good form',
    }

    response = await test_client.post('/api/v1/records/', json=record_payload, headers=auth_headers)

    # アサーション
    assert response.status_code == 201
    response_data = response.json()
    assert response_data['exercise'] == record_payload['exercise']
    assert 'id' in response_data
    assert response_data['user_id'] == current_user_id


async def test_delete_record_api_no_token(test_client: AsyncClient, db_session: AsyncSession):
    """
    DELETE /api/v1/records/{record_id} にトークンなしでアクセスすると 401 Unauthorized が返る。
    """
    # ダミーの記録を作成しておく (削除対象の存在は問わないが、パスが存在することを示すため)
    record_data = RecordCreate(
        exercise_date=datetime.date(2025, 7, 10), exercise='Test Delete No Token', weight=10, reps=1, set_reps=1
    )
    # サービスを使って記録を作成
    created_record = await record_service.create_record(db=db_session, record_in=record_data, user_id=1)

    response = await test_client.delete(f'/api/v1/records/{created_record.id}')
    assert response.status_code == 401


async def test_delete_record_api_another_users_record(test_client: AsyncClient, db_session: AsyncSession):
    """
    他人の記録を削除しようとすると 404 Not Found (または 403 Forbidden) が返る。
    (サービス層で見つからない扱いにするか、権限エラーにするかで変わる)
    """
    # ユーザーA (記録の所有者) を作成しログイン
    user_a_email = 'user_a_delete@example.com'
    user_a_password = 'password_a'
    headers_a = await get_auth_headers(test_client, db_session, user_a_email, user_a_password, 'userAdelete')
    me_response_a = await test_client.get('/api/v1/users/me', headers=headers_a)
    user_a_id = me_response_a.json()['id']

    # ユーザーB (削除を試みるユーザー) を作成しログイン
    user_b_email = 'user_b_delete@example.com'
    user_b_password = 'password_b'
    headers_b = await get_auth_headers(test_client, db_session, user_b_email, user_b_password, 'userBdelete')

    # ユーザーAの記録を作成
    record_data_a = RecordCreate(
        exercise_date=datetime.date(2025, 7, 11), exercise="User A's Record", weight=10, reps=1, set_reps=1
    )
    created_record_a = await record_service.create_record(db=db_session, record_in=record_data_a, user_id=user_a_id)

    # ユーザーBがユーザーAの記録を削除しようとする
    response = await test_client.delete(f'/api/v1/records/{created_record_a.id}', headers=headers_b)

    # 404 (見つからない) または 403 (権限なし) を期待。サービスの実装による。
    assert response.status_code == 404

    # idが存在することを確認
    assert created_record_a.id is not None

    # 実際に削除されていないことも確認
    record_still_exists = await record_service.get_record(
        db=db_session, record_id=created_record_a.id, user_id=user_a_id
    )
    assert record_still_exists is not None


async def test_delete_record_api_own_record_success(test_client: AsyncClient, db_session: AsyncSession):
    """
    自分の記録を削除すると成功し、削除された記録が返り、DBからも削除される。
    """
    # ユーザーを作成しログイン
    user_email = 'owner_deleter@example.com'
    user_password = 'password_owner'
    auth_headers = await get_auth_headers(test_client, db_session, user_email, user_password, 'ownerDeleter')
    me_response = await test_client.get('/api/v1/users/me', headers=auth_headers)
    user_id = me_response.json()['id']

    # 自分の記録を作成
    record_data = RecordCreate(
        exercise_date=datetime.date(2025, 7, 12), exercise='Record to Delete', weight=10, reps=1, set_reps=1
    )
    created_record = await record_service.create_record(db=db_session, record_in=record_data, user_id=user_id)
    record_id_to_delete = created_record.id

    assert record_id_to_delete is not None  # IDが採番されていることを確認

    # 自分の記録を削除
    response = await test_client.delete(f'/api/v1/records/{record_id_to_delete}', headers=auth_headers)

    # アサーション
    assert response.status_code == 200
    deleted_data = response.json()
    assert deleted_data['id'] == record_id_to_delete
    assert deleted_data['exercise'] == 'Record to Delete'

    # DBから実際に削除されたことを確認
    record_should_be_gone = await record_service.get_record(
        db=db_session, record_id=record_id_to_delete, user_id=user_id
    )
    assert record_should_be_gone is None


async def test_delete_record_service_own_record(db_session: AsyncSession):
    """自分の記録を削除できることをテストする"""
    user_id = 10
    record_data = RecordCreate(
        exercise_date=datetime.date(2025, 7, 13), exercise='Service Delete Own', weight=1, reps=1, set_reps=1
    )
    created_record = await record_service.create_record(db=db_session, record_in=record_data, user_id=user_id)
    record_id_to_delete = created_record.id

    assert record_id_to_delete is not None  # IDが採番されていることを確認

    deleted_record = await record_service.delete_record(db=db_session, record_id=record_id_to_delete, user_id=user_id)

    assert deleted_record is not None
    assert deleted_record.id == record_id_to_delete

    # DBから削除されたか確認
    record_in_db = await record_service.get_record(db=db_session, record_id=record_id_to_delete, user_id=user_id)
    assert record_in_db is None


async def test_delete_record_service_another_users_record(db_session: AsyncSession):
    """他人の記録は削除できず、Noneが返ることをテストする"""
    owner_user_id = 11
    attacker_user_id = 12
    record_data = RecordCreate(
        exercise_date=datetime.date(2025, 7, 14), exercise="Service Delete Other's", weight=1, reps=1, set_reps=1
    )
    created_record = await record_service.create_record(db=db_session, record_in=record_data, user_id=owner_user_id)
    record_id_to_delete = created_record.id

    assert record_id_to_delete is not None  # IDが採番されていることを確認

    # 他のユーザーIDで削除を試みる
    deleted_record = await record_service.delete_record(
        db=db_session, record_id=record_id_to_delete, user_id=attacker_user_id
    )

    assert deleted_record is None  # 削除されずNoneが返る

    # DBに記録が残っているか確認
    record_in_db = await record_service.get_record(db=db_session, record_id=record_id_to_delete, user_id=owner_user_id)
    assert record_in_db is not None  # 記録は削除されていない


async def test_delete_record_service_not_found(db_session: AsyncSession):
    """存在しない記録を削除しようとするとNoneが返る"""
    user_id = 13
    non_existent_record_id = 99995
    deleted_record = await record_service.delete_record(
        db=db_session, record_id=non_existent_record_id, user_id=user_id
    )
    assert deleted_record is None


async def test_read_single_record_api_no_token(test_client: AsyncClient, db_session: AsyncSession):
    """
    GET /api/v1/records/{record_id} にトークンなしでアクセスすると 401 Unauthorized が返る。
    """
    # ダミーの記録を作成 (削除テストのものを参考に、user_idはサービスに任せるので不要)
    record_data = RecordCreate(
        exercise_date=datetime.date(2025, 7, 15), exercise='Test Read No Token', weight=10, reps=1, set_reps=1
    )
    # サービスを使って記録を作成 (user_idは仮で1とするが、このテストの本質ではない)
    # ただし、この記録IDは実際には使わないが、エンドポイントが存在することを示すために何かIDが必要
    created_record = await record_service.create_record(db=db_session, record_in=record_data, user_id=1)

    response = await test_client.get(f'/api/v1/records/{created_record.id}')  # 存在しうるIDで試す
    assert response.status_code == 401


async def test_read_single_record_api_another_users_record(test_client: AsyncClient, db_session: AsyncSession):
    """
    認証済みユーザーが他人の記録を読み取ろうとすると 404 Not Found が返る。
    """
    # ユーザーA (記録の所有者)
    user_a_email = 'user_a_read_single@example.com'
    user_a_password = 'password_a'
    # get_auth_headers内でユーザーが作成される
    headers_a = await get_auth_headers(test_client, db_session, user_a_email, user_a_password, 'userAReadSingle')
    me_response_a = await test_client.get('/api/v1/users/me', headers=headers_a)
    user_a_id = me_response_a.json()['id']

    # ユーザーB (記録の読み取りを試みるユーザー)
    user_b_email = 'user_b_read_single@example.com'
    user_b_password = 'password_b'
    headers_b = await get_auth_headers(test_client, db_session, user_b_email, user_b_password, 'userBReadSingle')

    # ユーザーAの記録を作成
    record_data_a = RecordCreate(
        exercise_date=datetime.date(2025, 7, 16), exercise="User A's Private Record", weight=20, reps=1, set_reps=1
    )
    created_record_a = await record_service.create_record(db=db_session, record_in=record_data_a, user_id=user_a_id)

    # ユーザーBがユーザーAの記録を読み取ろうとする
    response = await test_client.get(f'/api/v1/records/{created_record_a.id}', headers=headers_b)

    assert response.status_code == 404


async def test_read_single_record_api_own_record_success(test_client: AsyncClient, db_session: AsyncSession):
    """
    認証済みユーザーが自分の記録を読み取ると成功し、正しいデータが返る。
    """
    user_email = 'owner_reader@example.com'
    user_password = 'password_owner_read'
    auth_headers = await get_auth_headers(test_client, db_session, user_email, user_password, 'ownerReader')
    me_response = await test_client.get('/api/v1/users/me', headers=auth_headers)
    user_id = me_response.json()['id']

    # 自分の記録を作成
    record_data = RecordCreate(
        exercise_date=datetime.date(2025, 7, 17),
        exercise='My Readable Record',
        weight=30,
        reps=1,
        set_reps=1,
        notes='Test this read',
    )

    created_record = await record_service.create_record(db=db_session, record_in=record_data, user_id=user_id)
    record_id_to_read = created_record.id

    # 自分の記録を読み取る
    response = await test_client.get(f'/api/v1/records/{record_id_to_read}', headers=auth_headers)

    # アサーション
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['id'] == record_id_to_read
    assert response_data['exercise'] == 'My Readable Record'
    assert response_data['user_id'] == user_id
    assert response_data['notes'] == 'Test this read'


async def test_read_single_record_api_record_not_found_for_owner(test_client: AsyncClient, db_session: AsyncSession):
    """
    認証済みユーザーが存在しない自分の記録IDで読み取ろうとすると 404 Not Found が返る。
    """
    user_email = 'owner_reader_404@example.com'
    user_password = 'password_owner_404'
    auth_headers = await get_auth_headers(test_client, db_session, user_email, user_password, 'ownerReader404')

    non_existent_record_id = 99990
    response = await test_client.get(f'/api/v1/records/{non_existent_record_id}', headers=auth_headers)

    assert response.status_code == 404


async def test_read_records_list_api_no_token(test_client: AsyncClient):
    """
    GET /api/v1/records/ にトークンなしでアクセスすると 401 Unauthorized が返る。
    """
    response = await test_client.get('/api/v1/records/')
    assert response.status_code == 401

async def test_read_records_list_api_own_records_only(test_client: AsyncClient, db_session: AsyncSession):
    """
    認証済みユーザーが記録一覧を取得すると、自分の記録のみが返され、他人の記録は含まれない。
    """
    # ユーザーA を作成しログイン、記録も作成
    user_a_email = 'user_a_list@example.com'
    user_a_password = 'password_a_list'
    headers_a = await get_auth_headers(test_client, db_session, user_a_email, user_a_password, 'userAList')
    me_response_a = await test_client.get('/api/v1/users/me', headers=headers_a)
    user_a_id = me_response_a.json()['id']

    record_a1_data = RecordCreate(
        exercise_date=datetime.date(2025, 7, 20), exercise='Record A1', weight=10, reps=1, set_reps=1
    )
    record_a2_data = RecordCreate(
        exercise_date=datetime.date(2025, 7, 21), exercise='Record A2', weight=20, reps=1, set_reps=1
    )
    await record_service.create_record(db=db_session, record_in=record_a1_data, user_id=user_a_id)
    await record_service.create_record(db=db_session, record_in=record_a2_data, user_id=user_a_id)

    # ユーザーB を作成 (ログインは不要、記録作成用)
    user_b_email = 'user_b_list@example.com'
    user_b_password = 'password_b_list'
    # ユーザーBも作成しておく (get_auth_headers内で作成されるか、別途作成)
    user_b_create_data = UserCreate(email=user_b_email, username='userBList', password=user_b_password)
    user_b = await user_service.create_user(db=db_session, user_in=user_b_create_data)
    assert user_b is not None
    user_b_id = user_b.id

    record_b1_data = RecordCreate(
        exercise_date=datetime.date(2025, 7, 22), exercise='Record B1 (Other user)', weight=30, reps=1, set_reps=1
    )
    await record_service.create_record(db=db_session, record_in=record_b1_data, user_id=user_b_id)

    # ユーザーAとして記録一覧を取得
    response_a = await test_client.get('/api/v1/records/', headers=headers_a)

    # アサーション
    assert response_a.status_code == 200
    records_for_a = response_a.json()
    assert isinstance(records_for_a, list)
    assert len(records_for_a) == 2  # ユーザーAの記録のみ2件のはず
    for record in records_for_a:
        assert record['user_id'] == user_a_id  # 返された記録のuser_idがユーザーAのものであること
        assert record['exercise'] != 'Record B1 (Other user)'  # ユーザーBの記録が含まれていないこと


async def test_read_records_list_api_pagination(test_client: AsyncClient, db_session: AsyncSession):
    """
    記録一覧取得時のページネーション (skip, limit) が機能することをテストする。
    (このテストは、所有権が実装された後に、自分の記録に対して行う)
    """
    user_email = 'pager_user@example.com'
    user_password = 'password_pager'
    auth_headers = await get_auth_headers(test_client, db_session, user_email, user_password, 'pagerUser')
    me_response = await test_client.get('/api/v1/users/me', headers=auth_headers)
    user_id = me_response.json()['id']

    # 3件の記録を作成
    for i in range(3):
        await record_service.create_record(
            db=db_session,
            record_in=RecordCreate(
                exercise_date=datetime.date(2025, 7, 23 + i),
                exercise=f'Paged Record {i + 1}',
                weight=10 + i,
                reps=1,
                set_reps=1,
            ),
            user_id=user_id,
        )

    # skip=0, limit=1 (最初の1件)
    response1 = await test_client.get('/api/v1/records/?skip=0&limit=1', headers=auth_headers)
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1) == 1
    assert data1[0]['exercise'] == 'Paged Record 1'

    # skip=1, limit=1 (2番目の1件)
    response2 = await test_client.get('/api/v1/records/?skip=1&limit=1', headers=auth_headers)
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2) == 1
    assert data2[0]['exercise'] == 'Paged Record 2'

    # skip=0, limit=5 (全件取得できる十分なlimit)
    response_all = await test_client.get('/api/v1/records/?skip=0&limit=5', headers=auth_headers)
    assert response_all.status_code == 200
    data_all = response_all.json()
    assert len(data_all) == 3


async def test_get_records_service_own_records_only(db_session: AsyncSession):
    """
    record_service.get_records が、指定されたユーザーの記録のみを返し、
    他人の記録は返さないことをテストする。
    """
    user1_id = 101
    user2_id = 102

    # ユーザー1の記録を作成
    await record_service.create_record(
        db=db_session,
        record_in=RecordCreate(
            exercise_date=datetime.date(2025, 7, 25), exercise='User1 Record1', weight=10, reps=1, set_reps=1
        ),
        user_id=user1_id,
    )
    await record_service.create_record(
        db=db_session,
        record_in=RecordCreate(
            exercise_date=datetime.date(2025, 7, 26), exercise='User1 Record2', weight=10, reps=1, set_reps=1
        ),
        user_id=user1_id,
    )

    # ユーザー2の記録を作成
    await record_service.create_record(
        db=db_session,
        record_in=RecordCreate(
            exercise_date=datetime.date(2025, 7, 27), exercise='User2 Record1', weight=10, reps=1, set_reps=1
        ),
        user_id=user2_id,
    )

    # ユーザー1の記録を取得
    records_user1 = await record_service.get_records(db=db_session, user_id=user1_id, skip=0, limit=10)
    assert len(records_user1) == 2
    for record in records_user1:
        assert record.user_id == user1_id

    # ユーザー2の記録を取得
    records_user2 = await record_service.get_records(db=db_session, user_id=user2_id, skip=0, limit=10)
    assert len(records_user2) == 1
    assert records_user2[0].user_id == user2_id
    assert records_user2[0].exercise == 'User2 Record1'


async def test_get_records_service_pagination(db_session: AsyncSession):
    """
    record_service.get_records のページネーションが正しく機能することをテストする。
    (特定のユーザーの記録に対して)
    """
    user_id_pager = 103
    # 5件の記録を作成
    for i in range(5):
        await record_service.create_record(
            db=db_session,
            record_in=RecordCreate(
                exercise_date=datetime.date(2025, 7, 25 + i),
                exercise=f'Pager Record {i + 1} for user {user_id_pager}',
                weight=10 + i,
                reps=1,
                set_reps=1,
            ),
            user_id=user_id_pager,
        )
    # 他のユーザーの記録も混ぜておく (フィルタリングされるはず)
    await record_service.create_record(
        db=db_session,
        record_in=RecordCreate(
            exercise_date=datetime.date(2025, 8, 1), exercise='Other User Pager Record', weight=10, reps=1, set_reps=1
        ),
        user_id=user_id_pager + 1,
    )

    # 最初の2件を取得
    records_page1 = await record_service.get_records(db=db_session, user_id=user_id_pager, skip=0, limit=2)
    assert len(records_page1) == 2
    assert records_page1[0].exercise == f'Pager Record 1 for user {user_id_pager}'
    assert records_page1[1].exercise == f'Pager Record 2 for user {user_id_pager}'

    # 次の2件を取得
    records_page2 = await record_service.get_records(db=db_session, user_id=user_id_pager, skip=2, limit=2)
    assert len(records_page2) == 2
    assert records_page2[0].exercise == f'Pager Record 3 for user {user_id_pager}'
    assert records_page2[1].exercise == f'Pager Record 4 for user {user_id_pager}'

    # 最後の1件を取得
    records_page3 = await record_service.get_records(db=db_session, user_id=user_id_pager, skip=4, limit=2)
    assert len(records_page3) == 1
    assert records_page3[0].exercise == f'Pager Record 5 for user {user_id_pager}'

    # 存在しないページ
    records_empty_page = await record_service.get_records(db=db_session, user_id=user_id_pager, skip=10, limit=2)
    assert len(records_empty_page) == 0

async def test_update_record_api_no_token(test_client: AsyncClient, db_session: AsyncSession):
    """
    PUT /api/v1/records/{record_id} にトークンなしでアクセスすると 401 Unauthorized が返る。
    """
    # ダミーの記録を作成
    record_data = RecordCreate(
        exercise_date=datetime.date(2025, 8, 1), exercise="Test Update No Token", weight=10, reps=1, set_reps=1)
    created_record = await record_service.create_record(db=db_session, record_in=record_data, user_id=1) # user_idは仮
    
    update_payload = {"notes": "Updated without token"}
    response = await test_client.put(f"/api/v1/records/{created_record.id}", json=update_payload)
    assert response.status_code == 401

async def test_update_record_api_another_users_record(test_client: AsyncClient, db_session: AsyncSession):
    """
    認証済みユーザーが他人の記録を更新しようとすると 404 Not Found (または 403) が返る。
    """
    # ユーザーA (記録の所有者)
    user_a_email = "user_a_update@example.com"
    user_a_password = "password_a"
    headers_a = await get_auth_headers(test_client, db_session, user_a_email, user_a_password, "userAUpdate")
    me_response_a = await test_client.get("/api/v1/users/me", headers=headers_a)
    user_a_id = me_response_a.json()["id"]

    # ユーザーB (更新を試みるユーザー)
    user_b_email = "user_b_update@example.com"
    user_b_password = "password_b"
    headers_b = await get_auth_headers(test_client, db_session, user_b_email, user_b_password, "userBUpdate")

    # ユーザーAの記録を作成
    record_data_a = RecordCreate(
        exercise_date=datetime.date(2025, 8, 2), exercise="User A's Record to Update", weight=20, reps=1, set_reps=1)
    created_record_a = await record_service.create_record(db=db_session, record_in=record_data_a, user_id=user_a_id)

    update_payload_by_b = {"notes": "User B trying to update User A's record"}
    # ユーザーBがユーザーAの記録を更新しようとする
    response = await test_client.put(
        f"/api/v1/records/{created_record_a.id}", json=update_payload_by_b, headers=headers_b)
    
    assert response.status_code == 404

async def test_update_record_api_own_record_success(test_client: AsyncClient, db_session: AsyncSession):
    """
    認証済みユーザーが自分の記録を更新すると成功し、更新されたデータが返る。
    """
    user_email = "owner_updater@example.com"
    user_password = "password_owner_update"
    auth_headers = await get_auth_headers(test_client, db_session, user_email, user_password, "ownerUpdater")
    me_response = await test_client.get("/api/v1/users/me", headers=auth_headers)
    user_id = me_response.json()["id"]

    # 自分の記録を作成
    initial_exercise_name = "My Record Before Update"
    record_data = RecordCreate(
        exercise_date=datetime.date(2025, 8, 3), exercise=initial_exercise_name,
        weight=30, reps=1, set_reps=1, notes="Initial notes"
    )
    created_record = await record_service.create_record(db=db_session, record_in=record_data, user_id=user_id)
    record_id_to_update = created_record.id

    # 更新用データ (一部のフィールドのみ)
    update_payload = {
        "notes": "Successfully updated notes!",
        "reps": 12
    }

    # 自分の記録を更新
    response = await test_client.put(
        f"/api/v1/records/{record_id_to_update}", json=update_payload, headers=auth_headers)

    # アサーション
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == record_id_to_update
    assert response_data["notes"] == update_payload["notes"] # 更新された
    assert response_data["reps"] == update_payload["reps"]   # 更新された
    assert response_data["exercise"] == initial_exercise_name # 更新していないフィールドは元のまま
    assert response_data["user_id"] == user_id

async def test_update_record_api_record_not_found_for_owner(test_client: AsyncClient, db_session: AsyncSession):
    """
    認証済みユーザーが存在しない自分の記録IDで更新しようとすると 404 Not Found が返る。
    """
    user_email = "owner_updater_404@example.com"
    user_password = "password_owner_update_404"
    auth_headers = await get_auth_headers(test_client, db_session, user_email, user_password, "ownerUpdater404")
    
    non_existent_record_id = 99980
    update_payload = {"notes": "Trying to update non-existent record"}
    response = await test_client.put(
        f"/api/v1/records/{non_existent_record_id}", json=update_payload, headers=auth_headers)

    assert response.status_code == 404