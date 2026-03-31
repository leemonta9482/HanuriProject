from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.dialects.mysql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    # 로그인할 때마다 증가. JWT tv와 일치해야 하며, 새 로그인 시 이전 세션 토큰은 무효화됩니다.
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
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
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    images: Mapped[list["BoardImage"]] = relationship(
        "BoardImage",
        back_populates="board",
        cascade="all, delete-orphan",
        order_by="BoardImage.sort_order",
    )


class BoardImage(Base):
    __tablename__ = "BoardImage"

    image_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("Board.board_id", ondelete="CASCADE"), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    board: Mapped["Board"] = relationship("Board", back_populates="images")


class Favorite(Base):
    __tablename__ = "Favorite"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    board_id: Mapped[int] = mapped_column(ForeignKey("Board.board_id", ondelete="CASCADE"), nullable=False)


class PurchaseRequest(Base):
    __tablename__ = "PurchaseRequest"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("Board.board_id", ondelete="CASCADE"), nullable=False)
    buyer_id: Mapped[str] = mapped_column(String(50), ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(
        ENUM("REQUESTED", "ACCEPTED", "REJECTED"),
        nullable=False,
        default="REQUESTED",
    )
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class Report(Base):
    __tablename__ = "Report"

    report_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("Board.board_id", ondelete="CASCADE"), nullable=False)
    reporter_id: Mapped[str] = mapped_column(String(50), ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(String(2000), nullable=False)
    status: Mapped[str] = mapped_column(
        ENUM("PENDING", "REVIEWED", "DISMISSED", "ACTION_TAKEN"),
        nullable=False,
        default="PENDING",
    )
    reviewed_at: Mapped[object | None] = mapped_column(TIMESTAMP, nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("User.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    admin_note: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class WantedPost(Base):
    __tablename__ = "WantedPost"

    wanted_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )


class ChatRoom(Base):
    __tablename__ = "ChatRoom"

    room_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    listing_kind: Mapped[str] = mapped_column(ENUM("BOARD", "WANTED"), nullable=False)
    listing_id: Mapped[int] = mapped_column(Integer, nullable=False)
    initiator_id: Mapped[str] = mapped_column(String(50), ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    peer_id: Mapped[str] = mapped_column(String(50), ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    last_message_at: Mapped[object | None] = mapped_column(TIMESTAMP, nullable=True)
    closed_at: Mapped[object | None] = mapped_column(TIMESTAMP, nullable=True)
    deleted_at_initiator: Mapped[object | None] = mapped_column(TIMESTAMP, nullable=True)
    deleted_at_peer: Mapped[object | None] = mapped_column(TIMESTAMP, nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )


class ChatMessage(Base):
    __tablename__ = "ChatMessage"

    message_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("ChatRoom.room_id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[str] = mapped_column(String(50), ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())
