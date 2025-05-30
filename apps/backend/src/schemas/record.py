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


class RecordUpdate(BaseModel):
	"""記録更新時の入力スキーマ (全てのフィールドがオプショナル)"""

	# user_id は通常更新させないことが多いですが、要件によります。
	# ここでは一旦更新可能としておきます。
	user_id: Optional[int] = None
	exercise_date: Optional[datetime.date] = None
	exercise: Optional[str] = None
	weight: Optional[float] = None
	reps: Optional[int] = None
	set_reps: Optional[int] = None
	notes: Optional[str] = None
