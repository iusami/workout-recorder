from fastapi import APIRouter, status, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

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
