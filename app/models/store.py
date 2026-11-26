from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    store_type = Column(String(50), default="Supermarket", nullable=False)
    status = Column(String(50), default="Online / Active", nullable=False)
    camera_nodes = Column(Integer, default=4, nullable=False)
    aisles = Column(Integer, default=12, nullable=False)
    manager = Column(String(100), nullable=False)
    contact_phone = Column(String(50), nullable=True)
    logo_url = Column(String(500), nullable=True)
    currency = Column(String(10), default="USD", nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    inventory_items = relationship("InventoryItem", back_populates="store", cascade="all, delete-orphan")
    admin_users = relationship("User", back_populates="store")

    def __repr__(self) -> str:
        return f"<Store id={self.id} code='{self.code}' name='{self.name}'>"
