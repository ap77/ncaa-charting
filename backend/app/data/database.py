"""Database setup and models for NCAA tournament data."""

from sqlalchemy import (
    Column,
    Float,
    Integer,
    String,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_DB_PATH = os.path.join(_PROJECT_ROOT, "data", "ncaa_tournament.db")
DATABASE_URL = f"sqlite:///{_DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    name_normalized = Column(String, nullable=False, index=True)
    conference = Column(String)

    season_stats = relationship("TeamSeasonStats", back_populates="team")

    __table_args__ = (
        UniqueConstraint("name_normalized", name="uq_team_name_normalized"),
    )


class TeamSeasonStats(Base):
    """Per-season team statistics — the features our model trains on."""

    __tablename__ = "team_season_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    season = Column(Integer, nullable=False)  # e.g. 2024

    # Record
    wins = Column(Integer)
    losses = Column(Integer)

    # Offensive stats
    points_per_game = Column(Float)
    field_goal_pct = Column(Float)
    three_point_pct = Column(Float)
    free_throw_pct = Column(Float)
    offensive_rebounds_per_game = Column(Float)
    assists_per_game = Column(Float)
    turnovers_per_game = Column(Float)

    # Defensive stats
    opp_points_per_game = Column(Float)
    steals_per_game = Column(Float)
    blocks_per_game = Column(Float)
    defensive_rebounds_per_game = Column(Float)

    # Advanced / efficiency
    adjusted_offensive_efficiency = Column(Float)
    adjusted_defensive_efficiency = Column(Float)
    tempo = Column(Float)
    strength_of_schedule = Column(Float)
    simple_rating_system = Column(Float)

    # Advanced rate stats (from Sports Reference advanced table)
    effective_fg_pct = Column(Float)       # eFG%
    true_shooting_pct = Column(Float)      # TS%
    turnover_pct = Column(Float)           # TOV% (turnovers per 100 plays)
    offensive_rebound_pct = Column(Float)  # ORB%
    total_rebound_pct = Column(Float)      # TRB%
    free_throw_rate = Column(Float)        # FTA/FGA
    three_point_rate = Column(Float)       # 3PA/FGA
    assist_pct = Column(Float)             # AST%
    steal_pct = Column(Float)              # STL%
    block_pct = Column(Float)              # BLK%

    # Tournament seeding
    seed = Column(Integer)

    team = relationship("Team", back_populates="season_stats")

    __table_args__ = (
        UniqueConstraint("team_id", "season", name="uq_team_season"),
    )


class TournamentGame(Base):
    """Historical NCAA tournament game results."""

    __tablename__ = "tournament_games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    season = Column(Integer, nullable=False)
    round_name = Column(String, nullable=False)  # R64, R32, S16, E8, F4, championship
    round_number = Column(Integer, nullable=False)  # 1-6

    team_a_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    team_b_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    team_a_seed = Column(Integer)
    team_b_seed = Column(Integer)
    team_a_score = Column(Integer)
    team_b_score = Column(Integer)
    winner_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    team_a = relationship("Team", foreign_keys=[team_a_id])
    team_b = relationship("Team", foreign_keys=[team_b_id])
    winner = relationship("Team", foreign_keys=[winner_id])

    __table_args__ = (
        UniqueConstraint(
            "season", "round_number", "team_a_id", "team_b_id",
            name="uq_tournament_game",
        ),
    )


def init_db():
    """Create all tables."""
    Base.metadata.create_all(engine)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
