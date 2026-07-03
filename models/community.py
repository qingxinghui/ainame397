from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class NamingPoll(Base):
    __tablename__ = "naming_poll"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    options: Mapped[list["NamingPollOption"]] = relationship(
        back_populates="poll", cascade="all, delete-orphan", lazy="selectin"
    )


class NamingPollOption(Base):
    __tablename__ = "naming_poll_option"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey("naming_poll.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    moral: Mapped[str] = mapped_column(Text, default="")
    vote_count: Mapped[int] = mapped_column(Integer, default=0)

    poll: Mapped[NamingPoll] = relationship(back_populates="options")


class NamingPollVote(Base):
    __tablename__ = "naming_poll_vote"
    __table_args__ = (UniqueConstraint("poll_id", "user_id", name="uq_poll_user_vote"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey("naming_poll.id", ondelete="CASCADE"), index=True)
    option_id: Mapped[int] = mapped_column(ForeignKey("naming_poll_option.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
