from sqlalchemy import Column, Integer, String, Float, Date, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Price(Base):
    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    market = Column(String(100), nullable=False)
    commodity = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Float, default=0)
    recorded_at = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Price({self.market}, {self.commodity}, {self.price})>"
