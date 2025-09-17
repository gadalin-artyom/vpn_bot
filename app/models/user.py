from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tg_user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    created = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    referral_link = Column(String, nullable=True)

    subscriptions = relationship("Subscription", back_populates="user")

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, tg_user_id={self.tg_user_id}, "
            f"username='{self.username}')>"
        )
