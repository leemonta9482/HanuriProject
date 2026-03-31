from sqlalchemy import Boolean, Float, String, TIMESTAMP, func
from sqlalchemy.dialects.mysql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class User(Base):
    __tablename__ = "User"

    user_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    school_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    student_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    student_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    manner_score: Mapped[float] = mapped_column(Float, default=36.5)
    trust_score: Mapped[float] = mapped_column(Float, default=0.0)
    interest_major: Mapped[str | None] = mapped_column(String(100), nullable=True)
    account_status: Mapped[str] = mapped_column(
        ENUM("ACTIVE", "DORMANT", "DELETED"),
        nullable=False,
        default="ACTIVE",
    )
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    registration_status: Mapped[str] = mapped_column(
        ENUM("PENDING", "APPROVED", "REJECTED"),
        nullable=False,
        default="PENDING",
    )
    student_id_card_path: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )


class Board(Base):
    __tablename__ = "Board"

    board_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    trade_type: Mapped[str] = mapped_column(
        ENUM("DIRECT", "DELIVERY", "BOTH"),
        nullable=False,
        default="BOTH",
    )
    status: Mapped[str] = mapped_column(
        ENUM("ON_SALE", "RESERVED", "SOLD"),
        nullable=False,
        default="ON_SALE",
    )
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )
