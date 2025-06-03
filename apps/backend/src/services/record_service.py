# apps/backend/src/services/record_service.py

import logging
from typing import Optional

from sqlalchemy import asc, column
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.logger import APP_LOGGER_NAME
from src.models.record import WorkoutRecord
from src.schemas.record import RecordCreate, RecordUpdate

logger = logging.getLogger(APP_LOGGER_NAME)


async def create_record(db: AsyncSession, record_in: RecordCreate, user_id: int) -> WorkoutRecord:
    """
    新しいトレーニング記録を作成し、データベースに保存する。
    """

    logger.info('Creating new workout record for user_id: %s, exercise: %s', user_id, record_in.exercise)
    # 1. 入力スキーマ (RecordCreate) から
    #    データベースモデル (WorkoutRecord) のインスタンスを作成します。
    #    Pydantic V2 では model_validate() を使います。
    record_data = record_in.model_dump()
    db_record = WorkoutRecord(**record_data, user_id=user_id)

    # 2. 作成したインスタンスをデータベースセッションに追加します。
    #    この時点ではまだDBには保存されていません。
    db.add(db_record)

    # 3. データベースにコミット (永続化) します。
    #    これにより、トランザクションが実行され、データが保存されます。
    await db.commit()

    # 4. データベースから最新の状態をリフレッシュします。
    #    これにより、DBが自動的に採番した 'id' などの情報が
    #    db_record オブジェクトに反映されます。
    await db.refresh(db_record)

    logger.info('Workout record created with ID: %s for user_id: %s', db_record.id, user_id)
    # 5. 作成され、IDが採番されたレコードオブジェクトを返します。
    return db_record


async def get_record(db: AsyncSession, record_id: int, user_id: int) -> Optional[WorkoutRecord]:
    """
    指定されたIDのトレーニング記録をデータベースから取得する。
    存在しない場合は None を返す。
    """
    logger.debug('Fetching workout record with record_id: %s for user_id: %s', record_id, user_id)

    statement = select(WorkoutRecord).where(
        WorkoutRecord.id == record_id,
        WorkoutRecord.user_id == user_id,  # ユーザーIDの条件を追加
    )

    result = await db.exec(statement)
    record = result.one_or_none()

    if record:
        logger.debug(
            'Found record via get_record: ID=%s, UserID=%s, Exercise=%s',
            record.id,
            record.user_id,
            getattr(record, 'exercise', 'N/A'),  # exercise_dateをexerciseに変更
        )
    else:
        logger.warning('Record not found via get_record for record_id: %s and user_id: %s', record_id, user_id)
    return record


async def get_records(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> list[WorkoutRecord]:
    """
    トレーニング記録の一覧をデータベースから取得する。
    skip と limit を使ってページネーションをサポートする。
    """
    logger.debug('Fetching list of workout records for user_id: %s with skip: %s, limit: %s', user_id, skip, limit)

    statement = (
        select(WorkoutRecord)
        .where(WorkoutRecord.user_id == user_id)  # ユーザーIDでフィルタリング
        .offset(skip)
        .limit(limit)
        .order_by(asc(column('id')))  # IDで昇順にソート
    )

    result = await db.exec(statement)
    records = result.all()

    logger.debug('Found %s records for user_id: %s.', len(records), user_id)
    return list(records)


async def update_record(
    db: AsyncSession, record_id: int, record_update: RecordUpdate, user_id: int
) -> Optional[WorkoutRecord]:
    """
    指定されたIDのトレーニング記録を更新する。
    記録が存在しない場合は None を返す。
    """
    db_record = await get_record(db=db, record_id=record_id, user_id=user_id)
    if not db_record:
        return None

    # 更新データ (RecordUpdate) から、値がセットされているフィールドのみを取得
    # Pydantic V2 の model_dump() は exclude_unset=True で未設定フィールドを除外できる
    update_data = record_update.model_dump(exclude_unset=True)

    # 取得したDBレコードのフィールドを、更新データで上書き
    for key, value in update_data.items():
        setattr(db_record, key, value)

    db.add(db_record)  # SQLAlchemy に変更を通知
    await db.commit()
    await db.refresh(db_record)  # DBから最新情報を再読み込み

    return db_record


async def delete_record(db: AsyncSession, record_id: int, user_id: int) -> Optional[WorkoutRecord]:
    """
    Deletes a workout record if it exists and belongs to the specified user.

    This function attempts to delete a workout record by its ID, but only if the
    record belongs to the user making the request. This ensures users can only
    delete their own records.

    Args:
        db (AsyncSession): The database session.
        record_id (int): The ID of the record to delete.
        user_id (int): The ID of the user attempting to delete the record.

    Returns:
        Optional[WorkoutRecord]:
            - The deleted WorkoutRecord object if successful (for serialization).
            - None if the record doesn't exist or doesn't belong to the user.

    Raises:
        SQLAlchemyError: If there's an issue with the database operation.
    """

    logger.info('User %s attempting to delete record_id: %s', user_id, record_id)
    record_object = await get_record(db=db, record_id=record_id, user_id=user_id)
    if record_object:
        # 所有者であるかを確認
        if record_object.user_id != user_id:
            logger.warning(
                'User %s attempted to delete record_id: %s owned by user %s. Forbidden.',
                user_id,
                record_id,
                record_object.user_id,
            )
            return None  # 他人の記録なので削除しない (Noneを返す)

        # 所有者なので削除
        await db.delete(record_object)
        await db.commit()
        logger.info('Record record_id: %s deleted successfully by user %s.', record_id, user_id)
        return record_object  # 削除されたオブジェクトを返す (API層でシリアライズ用)

    logger.warning('Record record_id: %s not found for deletion by user %s.', record_id, user_id)
    return None  # 記録が見つからない
