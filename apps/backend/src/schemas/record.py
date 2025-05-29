import datetime
from typing import Optional

from pydantic import BaseModel


# WorkoutRecord の Config を除いた基本部分を継承
class RecordBase(BaseModel):
    user_id: int
    exercise_date: datetime.date
    exercise: str
    weight: float
    reps: int
    set_reps: int
    notes: Optional[str] = None


class RecordCreate(RecordBase):
    """記録作成時の入力スキーマ"""


class RecordRead(RecordBase):
    """記録読み取り時の出力スキーマ (IDを含む)"""

    id: int

    class Config:
        from_attributes = True  # DBモデルから変換できるようにする
