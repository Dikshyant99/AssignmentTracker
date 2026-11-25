from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Session, select

from database import create_db_and_tables, get_session
from models import Assignment, AssignmentCreate, AssignmentPublic, AssignmentUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Assignment Tracker API", lifespan=lifespan)

# Reusable shortcut: "this endpoint needs a database session"
SessionDep = Annotated[Session, Depends(get_session)]


@app.get("/")
def home():
    return {"message": "Assignment Tracker API is running!"}


# ---------- CREATE ----------
@app.post("/assignments", response_model=AssignmentPublic, status_code=201)
def create_assignment(assignment: AssignmentCreate, session: SessionDep):
    db_assignment = Assignment.model_validate(assignment)
    session.add(db_assignment)
    session.commit()
    session.refresh(db_assignment)
    return db_assignment


# ---------- READ (all) ----------
@app.get("/assignments", response_model=list[AssignmentPublic])
def list_assignments(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    assignments = session.exec(select(Assignment).offset(offset).limit(limit)).all()
    return assignments


# ---------- READ (one) ----------
@app.get("/assignments/{assignment_id}", response_model=AssignmentPublic)
def get_assignment(assignment_id: int, session: SessionDep):
    assignment = session.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


# ---------- UPDATE ----------
@app.patch("/assignments/{assignment_id}", response_model=AssignmentPublic)
def update_assignment(assignment_id: int, assignment: AssignmentUpdate, session: SessionDep):
    db_assignment = session.get(Assignment, assignment_id)
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    update_data = assignment.model_dump(exclude_unset=True)
    db_assignment.sqlmodel_update(update_data)

    session.add(db_assignment)
    session.commit()
    session.refresh(db_assignment)
    return db_assignment


# ---------- DELETE ----------
@app.delete("/assignments/{assignment_id}", status_code=204)
def delete_assignment(assignment_id: int, session: SessionDep):
    assignment = session.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    session.delete(assignment)
    session.commit()