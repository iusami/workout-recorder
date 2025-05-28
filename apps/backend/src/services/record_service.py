# apps/backend/src/services/record_service.py

from sqlmodel.ext.asyncio.session import AsyncSession
from src.schemas.record import RecordCreate
from src.models.record import WorkoutRecord


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
