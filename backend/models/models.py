from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    TIMESTAMP,
    Boolean,
    Text,
    Interval,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, declarative_base
import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from backend.database.base import Base


class Website(Base):
    __tablename__ = "websites"

    site_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), unique=True)
    avatar_id = Column(String(255))
    voice_id = Column(String(255))
    prompt_template = Column(Text)
    knowledge_base = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    users = relationship("User", back_populates="website", cascade="all, delete-orphan")
    sessions = relationship(
        "Session", back_populates="website", cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(255), unique=True, nullable=False)
    site_id = Column(Integer, ForeignKey("websites.site_id", ondelete="CASCADE"))
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    website = relationship("Website", back_populates="users")
    sessions = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )


class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # conversation_id = Column(String(255), nullable=True)
    site_id = Column(Integer, ForeignKey("websites.site_id", ondelete="CASCADE"))
    user_id = Column(
        Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    started_at = Column(TIMESTAMP, default=datetime.utcnow)
    last_activity_at = Column(TIMESTAMP, default=datetime.utcnow)
    ended_at = Column(TIMESTAMP, nullable=True)
    total_talk_time = Column(Interval, default="0")
    meeting_status = Column(String(50), default="OnlyChat")
    went_to_pricing = Column(Boolean, default=False)

    website = relationship("Website", back_populates="sessions")
    user = relationship("User", back_populates="sessions")
    messages = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )
    tool_usage = relationship(
        "ToolUsage", back_populates="session", cascade="all, delete-orphan"
    )
    meetings = relationship(
        "Meeting", back_populates="session", cascade="all, delete-orphan"
    )
    summaries = relationship(
        "Summary", back_populates="session", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    message_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="CASCADE")
    )
    sender = Column(String(50))  # 'User' or 'AI'
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    content = Column(Text)

    session = relationship("Session", back_populates="messages")


class ToolUsage(Base):
    __tablename__ = "tool_usage"

    event_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="CASCADE")
    )
    tool_type = Column(String(50))  # e.g., 'CAPTURE_INFO', 'SCHEDULE_MEETING'
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    details = Column(JSON, nullable=True)

    session = relationship("Session", back_populates="tool_usage")


class Meeting(Base):
    __tablename__ = "meetings"

    meeting_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="CASCADE")
    )
    scheduled_for = Column(TIMESTAMP)
    meeting_link = Column(String(255))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    session = relationship("Session", back_populates="meetings")


class Summary(Base):
    __tablename__ = "summaries"

    summary_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="CASCADE")
    )
    summary_text = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    emailed_to = Column(String(255), nullable=True)
    emailed_at = Column(TIMESTAMP, nullable=True)

    session = relationship("Session", back_populates="summaries")


class PresentationURL(Base):
    __tablename__ = "presentation_urls"

    url_id = Column(Integer, primary_key=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey("websites.site_id", ondelete="CASCADE"))
    url = Column(String(255), nullable=False)
    url_type = Column(String(50))  # e.g., 'AI', 'User'
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # session = relationship("Session", back_populates="presentation_urls")
