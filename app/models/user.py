from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tg_user_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    referral_link = Column(String, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, tg_user_id={self.tg_user_id}, username='{self.username}')>"