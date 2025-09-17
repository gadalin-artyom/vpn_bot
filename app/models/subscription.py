from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, Float
from sqlalchemy.sql import func
from app.database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.tg_user_id"), nullable=False)
    vpn_key = Column(String, unique=False, index=False, nullable=False)
    vpn_id = Column(String, nullable=True)
    subscription_date = Column(DateTime(timezone=True), nullable=False)
    traffic_limit = Column(Float, nullable=True)
    creation_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    traffic_used = Column(Float, default=0.0, nullable=True)

    def __repr__(self):
        return (
            f"<Subscription(id={self.id}, user_id={self.user_id}, "
            f"vpn_key='{self.vpn_key}', subscription_date={self.subscription_date})>"
        )