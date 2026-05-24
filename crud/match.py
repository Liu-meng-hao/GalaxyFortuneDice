from sqlalchemy.orm import Session
from models.match import Match, GameRecord, MatchScoreSheet
import uuid
from typing import List, Optional

def create_match(db: Session, room_id: int, game_mode: int = 1) -> Match:
    db_match = Match(
        room_id=room_id,
        game_mode=game_mode
    )
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match

def get_match_by_id(db: Session, match_id: int) -> Optional[Match]:
    return db.query(Match).filter(Match.id == match_id).first()

def create_game_record(
    db: Session,
    match_id: int,
    user_id: int,
    final_score: int,
    rank: int = 0,
    is_win: int = 0,
    game_mode: int = 1,
    duration: Optional[int] = None
) -> GameRecord:
    db_record = GameRecord(
        match_id=match_id,
        user_id=user_id,
        final_score=final_score,
        rank=rank,
        is_win=is_win,
        game_mode=game_mode,
        duration=duration
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

def create_match_score_sheet(
    db: Session,
    match_id: int,
    user_id: int,
    score_type: str,
    score: int
) -> MatchScoreSheet:
    db_sheet = MatchScoreSheet(
        match_id=match_id,
        user_id=user_id,
        score_type=score_type,
        score=score
    )
    db.add(db_sheet)
    db.commit()
    db.refresh(db_sheet)
    return db_sheet
