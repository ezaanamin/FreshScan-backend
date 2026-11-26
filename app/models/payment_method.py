from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    cardholder_name = Column(String(255), nullable=False)
    card_number_masked = Column(String(30), nullable=False)
    card_last4 = Column(String(4), nullable=False)
    card_brand = Column(String(50), nullable=False, default="Card")
    expiry_month = Column(String(2), nullable=False)
    expiry_year = Column(String(4), nullable=False)
    billing_zip = Column(String(20), nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", backref="payment_methods")

    def __repr__(self) -> str:
        return f"<PaymentMethod id={self.id} brand='{self.card_brand}' last4='{self.card_last4}' is_default={self.is_default}>"
