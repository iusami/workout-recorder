from fastapi import APIRouter, status
from src.models import WorkoutRecord

# APIRouterインスタンスを作成
router = APIRouter(
    prefix="/records",  # このルーター内のエンドポイントはすべて /records で始まる
    tags=["Records"],  # FastAPIドキュメントでのグループ化タグ
)


@router.post("/", response_model=WorkoutRecord, status_code=status.HTTP_201_CREATED)
async def create_record_endpoint(
    record_in: WorkoutRecord,  # リクエストボディを WorkoutRecord スキーマで受け取る
    # db: AsyncSession = Depends(get_session) # <-- DBセッションはまだ使わない
):
    """
    新しいワークアウト記録を作成するエンドポイント（最小限の実装）。
    """
    print(f"Received workout record creation request for: {record_in.user_id}")

    # --- TDD フェーズ 2: 最小限の実装 ---
    # ここでは、まだデータベース保存やサービス呼び出しは行いません。
    # テストが 404 ではなくなるように、
    # 期待されるレスポンスモデルに合わせたダミーデータを返します。

    # 本来はサービス層を呼び出し、DBに保存されたrecord情報を返す
    # record_created = await record_service.create_record(db=db, record_create=record_in)

    # 今はダミーデータを返す
    dummy_created_record = WorkoutRecord(
        id=1,  # 仮のID
        user_id=123,  # リクエストから受け取ったユーザーIDをそのまま返す
        exercise_date=record_in.exercise_date,  # リクエストから受け取った日付をそのまま返す
        exercise=record_in.exercise,
        weight=record_in.weight,
        reps=record_in.reps,
        set_reps=record_in.set_reps,
        notes=record_in.notes or "",  # notesはオプションなので、Noneなら空文字にする
    )
    return dummy_created_record
