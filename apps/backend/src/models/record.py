from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel


class WorkoutRecord(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description='Unique identifier for the workout record',
    )
    user_id: int = Field(..., description='ID of the user who performed the workout', index=True)
    exercise_date: date = Field(..., description='Date of the workout')  # date型に変更
    exercise: str = Field(..., description='Exercises performed during the workout', index=True)
    weight: float = Field(..., description='Weight lifted during the workout, if applicable')
    reps: int = Field(..., description='Number of repetitions performed')
    set_reps: int = Field(..., description='Number of sets performed')
    notes: Optional[str] = Field(default=None, description='Additional notes about the workout')
