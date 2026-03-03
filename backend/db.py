from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from config import settings

engine = create_engine(
    f"sqlite:///{settings.db_path}",
    connect_args={"check_same_thread": False},
)


class Base(DeclarativeBase):
    pass


def get_session():
    with Session(engine) as session:
        yield session


def init_db():
    """Create tables and seed built-in profiles."""
    import models.device  # noqa: F401
    import models.profile  # noqa: F401

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        _seed_builtin_profiles(session)


def _seed_builtin_profiles(session: Session):
    from models.profile import Profile

    if session.query(Profile).filter_by(is_builtin=True).count() > 0:
        return

    builtins = [
        Profile(
            id=1,
            name="直连",
            latency_ms=0,
            jitter_ms=0,
            loss_percent=0.0,
            bandwidth_kbps=0,
            is_builtin=True,
        ),
        Profile(
            id=2,
            name="4G",
            latency_ms=30,
            jitter_ms=10,
            loss_percent=0.5,
            bandwidth_kbps=20480,
            is_builtin=True,
        ),
        Profile(
            id=3,
            name="3G",
            latency_ms=100,
            jitter_ms=20,
            loss_percent=1.0,
            bandwidth_kbps=1024,
            is_builtin=True,
        ),
        Profile(
            id=4,
            name="弱网",
            latency_ms=400,
            jitter_ms=100,
            loss_percent=8.0,
            bandwidth_kbps=256,
            is_builtin=True,
        ),
        Profile(
            id=5,
            name="断网",
            latency_ms=0,
            jitter_ms=0,
            loss_percent=100.0,
            bandwidth_kbps=0,
            is_builtin=True,
        ),
    ]
    session.add_all(builtins)
    session.commit()
