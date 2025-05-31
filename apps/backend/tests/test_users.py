# apps/backend/tests/test_users.py

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.security import hash_password, verify_password
from src.models.user import User
from src.schemas.user import UserCreate
from src.services import user_service

pytestmark = pytest.mark.asyncio

async def test_create_user_service_success(db_session: AsyncSession):
    """
    user_service.create_user が正しくユーザーを作成し、
    パスワードがハッシュ化されることをテストする。
    """
    user_in = UserCreate(
        email="newuser@example.com",
        username="new_username",
        password="securepassword123"
    )

    # サービス関数を呼び出す
    created_user = await user_service.create_user(db=db_session, user_in=user_in)

    # アサーション
    assert created_user is not None
    assert created_user.id is not None
    assert created_user.email == user_in.email
    assert created_user.username == user_in.username
    assert created_user.hashed_password != user_in.password # ハッシュ化されている
    assert verify_password(user_in.password, created_user.hashed_password) # 検証できる
    assert created_user.is_active is True

    # DBを直接確認
    statement = select(User).where(User.id == created_user.id)
    result = await db_session.exec(statement)
    db_user = result.one_or_none()

    assert db_user is not None
    assert db_user.email == user_in.email

async def test_create_user_service_duplicate_email(db_session: AsyncSession):
    """
    重複するメールアドレスでユーザーを作成しようとするとエラーが発生することをテストする。
    (今回は具体的なエラー型はまだ定義せず、Noneが返るか、特定の例外を期待する)
    """
    user1_in = UserCreate(email="duplicate@example.com", password="password1")
    await user_service.create_user(db=db_session, user_in=user1_in)

    user2_in = UserCreate(email="duplicate@example.com", password="password2")

    # 例: 今回はNoneが返ると期待 (サービス側でそのように実装するため)
    # または、特定のビジネス例外 (例: DuplicateEmailError) を raise することを期待
    # import pytest
    # with pytest.raises(適切な例外クラス):
    #     await user_service.create_user(db=db_session, user_in=user2_in)

    created_user_duplicate = await user_service.create_user(db=db_session,
                                                            user_in=user2_in)
    assert created_user_duplicate is None

async def test_register_user_api_success(test_client: AsyncClient):
    """
    POST /api/v1/auth/register が成功し、201とユーザー情報を返すことをテストする。
    """
    user_payload = {
        "email": "apiregister@example.com",
        "username": "api_user",
        "password": "securepasswordAPI123"
    }

    response = await test_client.post("/api/v1/auth/register", json=user_payload)

    assert response.status_code == 201
    
    response_data = response.json()
    assert response_data["email"] == user_payload["email"]
    assert response_data["username"] == user_payload["username"]
    assert "id" in response_data
    assert "password" not in response_data # UserRead にはパスワードは含まれない

async def test_register_user_api_duplicate_email(test_client: AsyncClient,
                                                 db_session: AsyncSession):
    """
    重複するメールアドレスでAPI経由でユーザー登録しようとすると 400 が返ることをテスト
    """
    # 最初にユーザーを作成しておく
    existing_user_payload = {"email": "taken@example.com",
                             "username": "taken_user",
                             "password": "password1"}
    # サービスを使って直接作成 (APIテストの独立性を保つため)
    initial_user = UserCreate(**existing_user_payload)
    await user_service.create_user(db=db_session,
                                   user_in=initial_user)

    duplicate_payload = {"email": "taken@example.com",
                         "username": "another_user",
                         "password": "password2"}
    response = await test_client.post("/api/v1/auth/register", json=duplicate_payload)

    assert response.status_code == 400
    response_data = response.json()
    assert "detail" in response_data

async def test_authenticate_user_success(db_session: AsyncSession):
    """
    正しいメールアドレスとパスワードで authenticate_user を呼び出すと、
    該当する User オブジェクトが返されることをテストする。
    """
    # 1. テスト用ユーザーを作成 (パスワードはハッシュ化されて保存される)
    email = "auth_test_user_success@example.com"
    password = "testpassword123"
    user_create_data = UserCreate(email=email,
                                  username="auth_tester_success",
                                  password=password)
    # 既にテスト済みの create_user サービスを使ってユーザーを作成
    created_user_for_auth = await user_service.create_user(db=db_session,
                                                           user_in=user_create_data)
    assert created_user_for_auth is not None # 前提条件の確認

    # 2. 認証サービスを呼び出す
    authenticated_user = await user_service.authenticate_user(
        db=db_session, email=email, password=password
    )

    # 3. アサーション
    assert authenticated_user is not None
    assert authenticated_user.email == email
    assert authenticated_user.id == created_user_for_auth.id

async def test_authenticate_user_failure_wrong_password(db_session: AsyncSession):
    """
    間違ったパスワードで authenticate_user を呼び出すと、
    None が返されることをテストする。
    """
    email = "auth_test_user_wrong_pw@example.com"
    correct_password = "correct_password"
    wrong_password = "wrong_password"
    user_create_data = UserCreate(email=email,
                                  username="auth_tester_wrong_pw",
                                  password=correct_password)
    await user_service.create_user(db=db_session, user_in=user_create_data)

    authenticated_user = await user_service.authenticate_user(
        db=db_session, email=email, password=wrong_password
    )

    assert authenticated_user is None

async def test_authenticate_user_failure_user_not_found(db_session: AsyncSession):
    """
    存在しないメールアドレスで authenticate_user を呼び出すと、
    None が返されることをテストする。
    """
    authenticated_user = await user_service.authenticate_user(
        db=db_session,
        email="nonexistentuser@example.com",
        password="anypassword"
    )

    assert authenticated_user is None # レッド！

async def test_authenticate_user_failure_inactive_user(db_session: AsyncSession):
    """
    非アクティブなユーザーで authenticate_user を呼び出すと
    None が返されることをテストする。
    """
    email = "inactive_user@example.com"
    password = "password123"
    # is_active=False でユーザーを直接作成
    # user_service.create_user は is_active=True で作成するため
    inactive_user_model = User(
        email=email,
        username="inactive_user_tester",
        hashed_password=hash_password(password), # パスワードをハッシュ化
        is_active=False # 非アクティブに設定
    )
    db_session.add(inactive_user_model)
    await db_session.commit()
    await db_session.refresh(inactive_user_model)

    authenticated_user = await user_service.authenticate_user(
        db=db_session, email=email, password=password
    )

    assert authenticated_user is None
