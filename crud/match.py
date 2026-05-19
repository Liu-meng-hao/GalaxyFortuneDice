from sqlalchemy.orm import Session
from models.match import Match, GameRecord
import uuid
from typing import List, Optional

def create_match(db: Session, room_id: int) -> Match:
    db_match = Match(
        room_id=room_id
    )
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match

def get_match_by_id(db: Session, match_id: int) -> Optional[Match]:
    return db.query(Match).filter(Match.id == match_id).first()

def create_game_record(
    db: Session,
    match_id: str,
    user_id: int,
    round: int,
    score_type: str,
    round_score: int,
    total_score: int
) -> GameRecord:
    db_record = GameRecord(
        match_id=match_id,
        user_id=user_id,
        round=round,
        score_type=score_type,
        round_score=round_score,
        total_score=total_score
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_game_records_by_match(db: Session, match_id: str) -> List[GameRecord]:
    return db.query(GameRecord).filter(GameRecord.match_id == match_id).all()

def update_match(db: Session, match_id: int, **kwargs):
    match = db.query(Match).filter(Match.id == match_id).first()
    if match:
        for key, value in kwargs.items():
            if hasattr(match, key):
                setattr(match, key, value)
        db.commit()
        db.refresh(match)
    return match
