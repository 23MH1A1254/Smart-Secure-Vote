from sqlalchemy.orm import Session
from .models import Voter, Candidate

def seed_demo_data(db: Session):
    if db.query(Voter).count() == 0:
        for i in range(1, 9):
            db.add(Voter(voter_id=f"VOT100{i}", phone=f"+1555555010{i}", has_voted=False))
    if db.query(Candidate).count() == 0:
        db.add_all([Candidate(name="Candidate A", party="Demo Party"), Candidate(name="Candidate B", party="Independent")])
    db.commit()
