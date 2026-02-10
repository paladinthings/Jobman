from pydantic import BaseModel
from datetime import datetime

class JobCreate(BaseModel):
    title: str
    company: str
    location: str
    canton: str
    description: str
    salary_min: float | None = None
    salary_max: float | None = None
    source: str
    original_url: str

class JobOut(BaseModel):
    id: int
    title: str
    company: str
    location: str
    canton: str
    predicted_salary: float | None

    class Config:
        from_attributes = True
