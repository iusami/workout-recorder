from fastapi import APIRouter, status, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException

# 必要なモジュールをインポート
from src.schemas.record import RecordCreate, RecordRead
from src.services import record_service
from src.core.database import get_session

# ルーターの設定を /records に合わせる
router = APIRouter(
    prefix="/records",  # プレフィックスを /records に
    tags=["Records"],  # タグを Records に
)


@router.post("/", response_model=RecordRead, status_code=status.HTTP_201_CREATED)
async def create_record_endpoint(
    record_in: RecordCreate,  # リクエストボディ
    db: AsyncSession = Depends(get_session),  # DBセッションをDIで取得
):
    """
    新しいトレーニング記録を作成するエンドポイント。
    """
    # サービス層を呼び出して記録を作成
    created_record = await record_service.create_record(db=db, record_in=record_in)

    # 作成された記録を返す
    return created_record


@router.get("/{record_id}", response_model=RecordRead, status_code=status.HTTP_200_OK)
async def read_record_endpoint(
    record_id: int,
    db: AsyncSession = Depends(get_session),  # DBセッションを有効化
):
    """
    指定されたIDのトレーニング記録を読み取る。
    """
    db_record = await record_service.get_record(db=db, record_id=record_id)
    if db_record is None:
        raise HTTPException(status_code=404, detail="Workout record not found")
    return db_record
