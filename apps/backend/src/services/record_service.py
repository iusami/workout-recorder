# apps/backend/src/services/record_service.py

from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.record import WorkoutRecord
from src.schemas.record import RecordCreate, RecordUpdate


async def create_record(db: AsyncSession, record_in: RecordCreate) -> WorkoutRecord:
    """
    新しいトレーニング記録を作成し、データベースに保存する。
    """
    # 1. 入力スキーマ (RecordCreate) から
    #    データベースモデル (WorkoutRecord) のインスタンスを作成します。
    #    Pydantic V2 では model_validate() を使います。
    db_record = WorkoutRecord.model_validate(record_in)

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

    # 5. 作成され、IDが採番されたレコードオブジェクトを返します。
    return db_record


async def get_record(db: AsyncSession, record_id: int) -> Optional[WorkoutRecord]:
    """
    指定されたIDのトレーニング記録をデータベースから取得する。
    存在しない場合は None を返す。
    """
    statement = select(WorkoutRecord).where(WorkoutRecord.id == record_id)
    result = await db.exec(statement)
    record = result.one_or_none()  # 1件取得、なければNone
    return record


async def get_records(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[WorkoutRecord]:
    """
    トレーニング記録の一覧をデータベースから取得する。
    skip と limit を使ってページネーションをサポートする。
    """
    statement = select(WorkoutRecord).offset(skip).limit(limit)
    result = await db.exec(statement)
    records = result.all()
    return list(records)


async def update_record(
    db: AsyncSession, record_id: int, record_update: RecordUpdate
) -> Optional[WorkoutRecord]:
    """
    指定されたIDのトレーニング記録を更新する。
    記録が存在しない場合は None を返す。
    """
    db_record = await get_record(db=db, record_id=record_id)
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


async def delete_record(db: AsyncSession, record_id: int) -> Optional[WorkoutRecord]:
    """
    指定されたIDのトレーニング記録をデータベースから削除する。
    成功した場合は削除されたレコードオブジェクトを、見つからない場合はNoneを返す。
    """
    record_object = await get_record(db=db, record_id=record_id)
    if record_object:
        await db.delete(record_object)
        await db.commit()
        return record_object
    return None
