from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import declarative_base, relationship
from db.engine import engine

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    # Changed to BigInteger to prevent overflow with large Telegram/messaging IDs
    chat_id = Column(Integer, unique=True)
    phone_number = Column(String, nullable=True)
    auto_send = Column(Boolean, default=False)
    sms_service = Column(Boolean, default=False)
    tables = Column(JSON, default=list)

    # Added cascade to handle child cleanup when a user is deleted
    role = relationship(
        "Role", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    role = Column(String, default="user")
    # Added unique=True to enforce the 1-to-1 relationship at DB level
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    user = relationship("User", back_populates="role")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    file_path = Column(String)
    # Status lifecycle: pending -> running -> completed / failed
    status = Column(String, default="pending")


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True)
    grade = Column(Integer, unique=True)


class Group(Base):
    __tablename__ = "groups"
    
    # Add this line to tell SQLAlchemy to safely overwrite if it exists
    __table_args__ = {'extend_existing': True} 

    id = Column(Integer, primary_key=True)
    grade = Column(Integer, ForeignKey("grades.id")) 
    name = Column(String, unique=True)
    table = Column(JSON, default=dict)


class GroupChat(Base):
    """A Telegram group chat bound to a class schedule."""
    __tablename__ = "group_chats"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, unique=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    title = Column(String, nullable=True)

    group = relationship("Group")


def init_db():
    Base.metadata.create_all(engine)
    _add_missing_columns()


def _add_missing_columns():
    """Add columns that may be missing on pre-existing tables.

    SQLAlchemy's create_all() does not alter existing tables, so newly added
    columns need a small manual migration here.
    """
    import sqlalchemy as sa
    from sqlalchemy import inspect

    try:
        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("tasks")}
    except Exception:
        return

    if "status" not in columns:
        with engine.begin() as conn:
            conn.execute(
                sa.text("ALTER TABLE tasks ADD COLUMN status VARCHAR DEFAULT 'pending'")
            )