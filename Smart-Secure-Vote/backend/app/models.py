from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from .database import Base

class Voter(Base):
    __tablename__ = "voters"
    id = Column(Integer, primary_key=True)
    voter_id = Column(String(40), unique=True, nullable=False, index=True)
    phone = Column(String(30), nullable=False)
    has_voted = Column(Boolean, default=False, nullable=False)

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    party = Column(String(100), default="Independent")

class OTPCode(Base):
    __tablename__ = "otp_codes"
    id = Column(Integer, primary_key=True)
    voter_id = Column(String(40), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)

class Vote(Base):
    __tablename__ = "votes"
    id = Column(Integer, primary_key=True)
    voter_pk = Column(Integer, ForeignKey("voters.id"), nullable=False, unique=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    receipt = Column(String(32), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("voter_pk", name="uq_one_vote_per_voter"),)
