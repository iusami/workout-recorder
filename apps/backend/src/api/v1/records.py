from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.database import get_session

# 必要なモジュールをインポート
from src.schemas.record import RecordCreate, RecordRead, RecordUpdate
from src.services import record_service

# ルーターの設定を /records に合わせる
router = APIRouter(
    prefix='/records',  # プレフィックスを /records に
    tags=['Records'],  # タグを Records に
)


@router.post('/', response_model=RecordRead, status_code=status.HTTP_201_CREATED)
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


@router.get('/', response_model=list[RecordRead], status_code=status.HTTP_200_OK)
async def read_records_endpoint(
    db: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
):
    """
    トレーニング記録の一覧を読み取る。
    """
    records = await record_service.get_records(db=db, skip=skip, limit=limit)
    return records


@router.get('/{record_id}', response_model=RecordRead, status_code=status.HTTP_200_OK)
async def read_record_endpoint(
    record_id: int,
    db: AsyncSession = Depends(get_session),  # DBセッションを有効化
):
    """
    指定されたIDのトレーニング記録を読み取る。
    """
    db_record = await record_service.get_record(db=db, record_id=record_id)
    if db_record is None:
        raise HTTPException(status_code=404, detail='Workout record not found')
    return db_record


@router.put('/{record_id}', response_model=RecordRead, status_code=status.HTTP_200_OK)
async def update_record_endpoint(
    record_id: int,
    record_in: RecordUpdate,
    db: AsyncSession = Depends(get_session),  # DBセッションを有効化
):
    """
    指定されたIDのトレーニング記録を更新する。
    """
    updated_record = await record_service.update_record(
        db=db, record_id=record_id, record_update=record_in
    )
    if updated_record is None:
        raise HTTPException(
            status_code=404, detail='Workout record not found to update'
        )
    return updated_record
