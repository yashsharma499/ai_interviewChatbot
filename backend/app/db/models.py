from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


class Interviewer(Base):
    __tablename__ = "interviewers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)

    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    interviewer_id = Column(Integer, ForeignKey("interviewers.id"))

    scheduled_time = Column(DateTime, nullable=True)   
    status = Column(String, default="scheduled")

    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate")
    interviewer = relationship("Interviewer")
