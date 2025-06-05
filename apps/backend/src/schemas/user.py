from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, description='User password (min 8 characters)')


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=50, description='First name')
    last_name: Optional[str] = Field(None, max_length=50, description='Last name')
    date_of_birth: Optional[date] = Field(None, description='Date of birth')
    height: Optional[float] = Field(None, gt=0, le=300, description='Height in centimeters')
    weight: Optional[float] = Field(None, gt=0, le=1000, description='Weight in kilograms')
    fitness_level: Optional[Literal['beginner', 'intermediate', 'advanced']] = Field(None, description='Fitness level')
    fitness_goals: Optional[str] = Field(None, max_length=500, description='Fitness goals and objectives')
    preferred_units: Optional[Literal['metric', 'imperial']] = Field(None, description='Preferred units system')


class UserRead(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    fitness_level: Optional[str] = None
    fitness_goals: Optional[str] = None
    preferred_units: str = 'metric'

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    fitness_level: Optional[str] = None
    fitness_goals: Optional[str] = None
    preferred_units: str = 'metric'

    class Config:
        from_attributes = True
