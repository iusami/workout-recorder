import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.v1.auth import get_current_active_user
from src.core.database import get_session
from src.core.logger import APP_LOGGER_NAME
from src.models.user import User

# 必要なモジュールをインポート
from src.schemas.record import RecordCreate, RecordRead, RecordUpdate
from src.services import record_service

# ロガーの設定
logger = logging.getLogger(APP_LOGGER_NAME)

# ルーターの設定を /records に合わせる
router = APIRouter(
    prefix='/records',  # プレフィックスを /records に
    tags=['Records'],  # タグを Records に
)


@router.post('/', response_model=RecordRead, status_code=status.HTTP_201_CREATED)
async def create_record_endpoint(
    record_in: RecordCreate,  # リクエストボディ
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """
    新しいトレーニング記録を作成するエンドポイント。
    """
    # サービス層を呼び出して記録を作成
    created_record = await record_service.create_record(db=db, record_in=record_in, user_id=current_user.id)

    # 作成された記録を返す
    return created_record


@router.get('/', response_model=list[RecordRead], status_code=status.HTTP_200_OK)
async def read_records_endpoint(
    db: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    """
    トレーニング記録の一覧を読み取る。
    """
    records = await record_service.get_records(db=db, user_id=current_user.id, skip=skip, limit=limit)
    return records


@router.get('/{record_id}', response_model=RecordRead, status_code=status.HTTP_200_OK)
async def read_record_endpoint(
    record_id: int,
    db: AsyncSession = Depends(get_session),  # DBセッションを有効化
    current_user: User = Depends(get_current_active_user),
):
    """
    指定されたIDのトレーニング記録を読み取る。
    """
    db_record = await record_service.get_record(db=db, record_id=record_id, user_id=current_user.id)
    if db_record is None:
        raise HTTPException(status_code=404, detail='Workout record not found')
    return db_record


@router.put('/{record_id}', response_model=RecordRead, status_code=status.HTTP_200_OK)
async def update_record_endpoint(
    record_id: int,
    record_in: RecordUpdate,
    db: AsyncSession = Depends(get_session),  # DBセッションを有効化
    current_user: User = Depends(get_current_active_user),
):
    """
    指定されたIDのトレーニング記録を更新する。
    """
    updated_record = await record_service.update_record(
        db=db, record_id=record_id, record_update=record_in, user_id=current_user.id
    )
    if updated_record is None:
        raise HTTPException(status_code=404, detail='Workout record not found to update')
    return updated_record


@router.delete('/{record_id}', response_model=RecordRead, status_code=status.HTTP_200_OK)
async def delete_record_endpoint(
    record_id: int, db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_active_user)
):
    """
    指定されたIDのトレーニング記録を削除する。
    成功した場合は削除された記録オブジェクトを返す。
    記録が見つからない場合は404エラーを返す。
    """
    logger.info('User %s (ID: %d) attempting to delete record_id: %d', current_user.email, current_user.id, record_id)

    deleted_record = await record_service.delete_record(db=db, record_id=record_id, user_id=current_user.id)
    if deleted_record is None:
        logger.warning(
            'Failed to delete record_id: %d by user %s. Record not found or not owned.', record_id, current_user.email
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Workout record not found or you do not have permission to delete it',
        )
    logger.info('Record record_id: %d deleted successfully by user %s.', record_id, current_user.email)
    return deleted_record
