from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    store_name = Column(String(255), nullable=False, default="Whole Foods – Downtown")
    status = Column(String(50), nullable=False, default="completed")
    subtotal = Column(Numeric(10, 2), nullable=False, default=0.00)
    tax = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    item_count = Column(Integer, nullable=False, default=0)
    receipt_code = Column(String(100), unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="orders")

    def __repr__(self) -> str:
        return f"<Order id={self.id} user_id={self.user_id} total_amount={self.total_amount} status='{self.status}'>"
