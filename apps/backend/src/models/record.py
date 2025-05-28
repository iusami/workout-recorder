from datetime import date
from sqlmodel import SQLModel, Field
from typing import Optional


class WorkoutRecord(SQLModel, table=True):
    # SQLModelのテーブル定義として設定
    # __tablename__ = "workoutrecord" # (オプション) テーブル名を明示的に指定

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="Unique identifier for the workout record",
    )
    user_id: int = Field(
        ..., description="ID of the user who performed the workout", index=True
    )
    exercise_date: date = Field(..., description="Date of the workout")  # date型に変更
    exercise: str = Field(
        ..., description="Exercises performed during the workout", index=True
    )
    weight: float = Field(
        ..., description="Weight lifted during the workout, if applicable"
    )
    reps: int = Field(..., description="Number of repetitions performed")
    set_reps: int = Field(..., description="Number of sets performed")
    notes: Optional[str] = Field(
        default=None, description="Additional notes about the workout"
    )
