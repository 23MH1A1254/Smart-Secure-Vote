from datetime import datetime, timedelta
import secrets
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import Base, engine, get_db
from .models import Voter, Candidate, OTPCode, Vote
from .config import CORS_ORIGINS, EXPOSE_DEMO_OTP, SEED_DEMO_DATA, ADMIN_USERNAME, ADMIN_PASSWORD
from .sms import send_otp
from .security import new_receipt
from .monitoring import record
from .seed import seed_demo_data

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Smart Secure Vote API", version="1.0.0-demo")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    if SEED_DEMO_DATA:
        db = next(get_db())
        try: seed_demo_data(db)
        finally: db.close()

class VerifyRequest(BaseModel):
    voter_id: str
class OTPRequest(BaseModel):
    voter_id: str
    otp: str
class VoteRequest(BaseModel):
    voter_id: str
    candidate_id: int
class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "demo"}

@app.get("/api/candidates")
def candidates(db: Session = Depends(get_db)):
    return [{"id": c.id, "name": c.name, "party": c.party} for c in db.query(Candidate).all()]

@app.post("/api/voter/verify")
def verify_voter(body: VerifyRequest, db: Session = Depends(get_db)):
    voter = db.query(Voter).filter_by(voter_id=body.voter_id.strip().upper()).first()
    if not voter:
        record("unknown_voter", body.voter_id)
        raise HTTPException(404, "Voter ID not found. Contact the administrator.")
    if voter.has_voted:
        raise HTTPException(409, "This voter has already voted.")
    code = f"{secrets.randbelow(1000000):06d}"
    db.add(OTPCode(voter_id=voter.voter_id, code=code, expires_at=datetime.utcnow()+timedelta(minutes=5), used=False))
    db.commit()
    send_otp(voter.phone, code)
    result = {"message": "OTP generated. Check the demo backend console."}
    if EXPOSE_DEMO_OTP:
        result["demo_otp"] = code
    return result

@app.post("/api/voter/otp")
def check_otp(body: OTPRequest, db: Session = Depends(get_db)):
    voter_id = body.voter_id.strip().upper()
    otp = db.query(OTPCode).filter_by(voter_id=voter_id, used=False).order_by(OTPCode.id.desc()).first()
    if not otp or otp.expires_at < datetime.utcnow() or otp.code != body.otp:
        record("otp_failed", voter_id)
        raise HTTPException(401, "Invalid or expired OTP.")
    otp.used = True
    db.commit()
    return {"verified": True, "voter_id": voter_id}

@app.post("/api/voter/vote")
def cast_vote(body: VoteRequest, db: Session = Depends(get_db)):
    voter = db.query(Voter).filter_by(voter_id=body.voter_id.strip().upper()).with_for_update().first()
    candidate = db.query(Candidate).filter_by(id=body.candidate_id).first()
    if not voter or not candidate:
        raise HTTPException(404, "Voter or candidate not found.")
    if voter.has_voted:
        raise HTTPException(409, "A vote has already been recorded for this voter.")
    voter.has_voted = True
    receipt = new_receipt()
    db.add(Vote(voter_pk=voter.id, candidate_id=candidate.id, receipt=receipt))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(409, "Vote could not be recorded. Please check status.")
    record("vote_cast", voter.voter_id)
    return {"message": "Vote recorded successfully.", "receipt": receipt}

@app.post("/api/admin/login")
def admin_login(body: LoginRequest):
    if body.username != ADMIN_USERNAME or body.password != ADMIN_PASSWORD:
        raise HTTPException(401, "Invalid admin credentials.")
    return {"authenticated": True, "message": "Demo admin login successful."}

@app.get("/api/admin/results")
def results(db: Session = Depends(get_db)):
    rows = db.query(Candidate.id, Candidate.name, func.count(Vote.id)).outerjoin(Vote, Vote.candidate_id == Candidate.id).group_by(Candidate.id).all()
    return [{"candidate_id": r[0], "candidate": r[1], "votes": r[2]} for r in rows]

@app.post("/api/admin/candidates")
def add_candidate(body: dict, db: Session = Depends(get_db)):
    name = str(body.get("name", "")).strip()
    if not name:
        raise HTTPException(400, "Candidate name is required.")
    candidate = Candidate(name=name, party=str(body.get("party", "Independent")))
    db.add(candidate); db.commit(); db.refresh(candidate)
    return {"id": candidate.id, "name": candidate.name, "party": candidate.party}
