from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .database import engine, Base, SessionLocal
from . import models, schemas
from .salary import predict_salary

app = FastAPI(title="Swiss Job Aggregator API")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"status": "API running"}

@app.post("/jobs")
def create_job(job: schemas.JobCreate, db: Session = Depends(get_db)):
    predicted = predict_salary(job.title, job.canton)

    db_job = models.Job(
        **job.dict(),
        predicted_salary=predicted
    )

    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@app.get("/jobs", response_model=list[schemas.JobOut])
def search_jobs(
    keyword: str | None = None,
    canton: str | None = None,
    min_salary: float | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Job)

    if keyword:
        query = query.filter(
            or_(
                models.Job.title.ilike(f"%{keyword}%"),
                models.Job.description.ilike(f"%{keyword}%")
            )
        )

    if canton:
        query = query.filter(models.Job.canton == canton)

    if min_salary:
        query = query.filter(
            models.Job.predicted_salary >= min_salary
        )

    return query.limit(50).all()
