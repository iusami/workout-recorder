import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

# ... (test_create_record_service はそのまま) ...

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
