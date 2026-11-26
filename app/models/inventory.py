from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class InventoryItem(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, default=1, index=True)
    sku = Column(String(50), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    class_label = Column(String(100), index=True, nullable=False)
    category = Column(String(100), nullable=False)
    unit_price = Column(Numeric(10, 2), default=0.00, nullable=False)
    on_hand = Column(Integer, default=0, nullable=False)
    min_stock = Column(Integer, default=20, nullable=False)
    freshness_score = Column(Integer, default=100, nullable=False)
    is_spoilage_risk = Column(Boolean, default=False, nullable=False)
    status = Column(String(50), default="In stock", nullable=False)
    shelf_location = Column(String(100), default="Aisle 1", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    store = relationship("Store", back_populates="inventory_items")

    __table_args__ = (
        UniqueConstraint("store_id", "class_label", name="uq_store_class_label"),
        UniqueConstraint("store_id", "sku", name="uq_store_sku"),
    )

    def __repr__(self) -> str:
        return f"<InventoryItem id={self.id} store_id={self.store_id} sku='{self.sku}' name='{self.name}' class_label='{self.class_label}'>"
