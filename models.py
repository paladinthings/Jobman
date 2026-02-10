from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from datetime import datetime
from .database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    company = Column(String)
    location = Column(String)
    canton = Column(String, index=True)
    description = Column(Text)

    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    predicted_salary = Column(Float, nullable=True)

    source = Column(String)
    original_url = Column(String)

    posted_date = Column(DateTime, default=datetime.utcnow)
