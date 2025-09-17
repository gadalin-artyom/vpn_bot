from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vpn_key = Column(String, nullable=False)
    vpn_id = Column(String, nullable=False, unique=True)
    subscription_date = Column(DateTime, nullable=False)
    traffic_limit = Column(BigInteger, default=0)
    creation_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    traffic_used = Column(BigInteger, default=0)

    user = relationship("User", back_populates="subscriptions")

    def __repr__(self) -> str:
        return (
            f"<Subscription(id={self.id}, user_id={self.user_id}, "
            f"vpn_id='{self.vpn_id}')>"
        )
