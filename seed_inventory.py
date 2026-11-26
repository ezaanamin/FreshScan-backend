import sys
from decimal import Decimal
from app.database import engine, SessionLocal, Base
from app.models.inventory import InventoryItem

INVENTORY_DATA = [
    {
        "class_label": "apple",
        "name": "Apple · Gala / Fuji",
        "sku": "PRD-APP-001",
        "category": "Produce",
        "unit_price": Decimal("1.20"),
        "on_hand": 180,
        "min_stock": 50,
        "freshness_score": 98,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Aisle 1 · Produce Bay A"
    },
    {
        "class_label": "apple_rotten",
        "name": "Apple · Rotten / Bruised",
        "sku": "PRD-APP-001-R",
        "category": "Spoilage Risk",
        "unit_price": Decimal("0.00"),
        "on_hand": 12,
        "min_stock": 0,
        "freshness_score": 18,
        "is_spoilage_risk": True,
        "status": "Spoiled / Flagged",
        "shelf_location": "Write-off Bin · Compost"
    },
    {
        "class_label": "banana",
        "name": "Banana · Cavendish",
        "sku": "PRD-BAN-002",
        "category": "Produce",
        "unit_price": Decimal("0.50"),
        "on_hand": 240,
        "min_stock": 60,
        "freshness_score": 95,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Aisle 1 · Produce Bay B"
    },
    {
        "class_label": "banana_rotten",
        "name": "Banana · Overripe / Rotten",
        "sku": "PRD-BAN-002-R",
        "category": "Spoilage Risk",
        "unit_price": Decimal("0.00"),
        "on_hand": 8,
        "min_stock": 0,
        "freshness_score": 22,
        "is_spoilage_risk": True,
        "status": "Spoiled / Flagged",
        "shelf_location": "Write-off Bin · Compost"
    },
    {
        "class_label": "bolt",
        "name": "Hex Bolt & Fastener",
        "sku": "HRD-BLT-003",
        "category": "Hardware & Non-Food",
        "unit_price": Decimal("0.85"),
        "on_hand": 95,
        "min_stock": 30,
        "freshness_score": 100,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Aisle 7 · Hardware Bay C"
    },
    {
        "class_label": "butter",
        "name": "Butter · Pure Salted 250g",
        "sku": "DRY-BUT-004",
        "category": "Dairy & Eggs",
        "unit_price": Decimal("3.49"),
        "on_hand": 45,
        "min_stock": 25,
        "freshness_score": 100,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Aisle 3 · Chiller 2"
    },
    {
        "class_label": "capsicum",
        "name": "Capsicum / Bell Pepper · Green",
        "sku": "PRD-CAP-005",
        "category": "Produce",
        "unit_price": Decimal("1.80"),
        "on_hand": 78,
        "min_stock": 35,
        "freshness_score": 94,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Aisle 1 · Produce Bay C"
    },
    {
        "class_label": "capsicum_rotten",
        "name": "Capsicum · Rotten / Shriveled",
        "sku": "PRD-CAP-005-R",
        "category": "Spoilage Risk",
        "unit_price": Decimal("0.00"),
        "on_hand": 6,
        "min_stock": 0,
        "freshness_score": 15,
        "is_spoilage_risk": True,
        "status": "Spoiled / Flagged",
        "shelf_location": "Write-off Bin · Compost"
    },
    {
        "class_label": "eggs",
        "name": "Eggs · Farm Fresh",
        "sku": "DRY-EGG-006",
        "category": "Dairy & Eggs",
        "unit_price": Decimal("4.29"),
        "on_hand": 110,
        "min_stock": 40,
        "freshness_score": 100,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Aisle 3 · Chiller 1"
    },
    {
        "class_label": "garlic",
        "name": "Garlic Bulbs · Mesh 3-Pack",
        "sku": "PRD-GAR-007",
        "category": "Produce",
        "unit_price": Decimal("1.49"),
        "on_hand": 130,
        "min_stock": 45,
        "freshness_score": 96,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Aisle 2 · Aromatics"
    },
    {
        "class_label": "guava",
        "name": "Guava · Fresh White/Pink",
        "sku": "PRD-GUA-008",
        "category": "Produce",
        "unit_price": Decimal("2.10"),
        "on_hand": 65,
        "min_stock": 30,
        "freshness_score": 92,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Aisle 1 · Exotic Bay"
    },
    {
        "class_label": "guava_rotten",
        "name": "Guava · Rotten / Softened",
        "sku": "PRD-GUA-008-R",
        "category": "Spoilage Risk",
        "unit_price": Decimal("0.00"),
        "on_hand": 5,
        "min_stock": 0,
        "freshness_score": 20,
        "is_spoilage_risk": True,
        "status": "Spoiled / Flagged",
        "shelf_location": "Write-off Bin · Compost"
    },
    {
        "class_label": "lemon",
        "name": "Lemon · Eureka Fresh",
        "sku": "PRD-LEM-009",
        "category": "Produce",
        "unit_price": Decimal("0.75"),
        "on_hand": 150,
        "min_stock": 50,
        "freshness_score": 97,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Aisle 1 · Citrus Stand"
    },
    {
        "class_label": "mango",
        "name": "Mango · Alphonso Fresh",
        "sku": "PRD-MAN-010",
        "category": "Produce",
        "unit_price": Decimal("2.80"),
        "on_hand": 85,
        "min_stock": 35,
        "freshness_score": 93,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Aisle 1 · Tropical Bay"
    },
    {
        "class_label": "mango_rotten",
        "name": "Mango · Rotten / Fermented",
        "sku": "PRD-MAN-010-R",
        "category": "Spoilage Risk",
        "unit_price": Decimal("0.00"),
        "on_hand": 9,
        "min_stock": 0,
        "freshness_score": 14,
        "is_spoilage_risk": True,
        "status": "Spoiled / Flagged",
        "shelf_location": "Write-off Bin · Compost"
    },
    {
        "class_label": "nut",
        "name": "Hex Nut / Hardware Fastener",
        "sku": "HRD-NUT-011",
        "category": "Hardware & Non-Food",
        "unit_price": Decimal("0.45"),
        "on_hand": 120,
        "min_stock": 40,
        "freshness_score": 100,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Aisle 7 · Hardware Bay C"
    },
    {
        "class_label": "onion",
        "name": "Onion · Yellow Brown 1kg",
        "sku": "PRD-ONI-012",
        "category": "Produce",
        "unit_price": Decimal("1.99"),
        "on_hand": 210,
        "min_stock": 70,
        "freshness_score": 95,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Aisle 2 · Root Vegetables"
    },
    {
        "class_label": "orange",
        "name": "Orange · Navel Sweet",
        "sku": "PRD-ORA-013",
        "category": "Produce",
        "unit_price": Decimal("0.90"),
        "on_hand": 175,
        "min_stock": 60,
        "freshness_score": 96,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Aisle 1 · Citrus Stand"
    },
    {
        "class_label": "orange_rotten",
        "name": "Orange · Rotten / Molded",
        "sku": "PRD-ORA-013-R",
        "category": "Spoilage Risk",
        "unit_price": Decimal("0.00"),
        "on_hand": 7,
        "min_stock": 0,
        "freshness_score": 12,
        "is_spoilage_risk": True,
        "status": "Spoiled / Flagged",
        "shelf_location": "Write-off Bin · Compost"
    },
    {
        "class_label": "package",
        "name": "Packaged Goods / Box",
        "sku": "PKG-BOX-014",
        "category": "Packaging & General",
        "unit_price": Decimal("1.50"),
        "on_hand": 60,
        "min_stock": 20,
        "freshness_score": 100,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Checkout Depot · Kiosk Supply"
    },
    {
        "class_label": "pomegranate",
        "name": "Pomegranate · Wonderful Ruby",
        "sku": "PRD-POM-015",
        "category": "Produce",
        "unit_price": Decimal("3.20"),
        "on_hand": 55,
        "min_stock": 25,
        "freshness_score": 94,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Aisle 1 · Exotic Bay"
    },
    {
        "class_label": "pomegranate_rotten",
        "name": "Pomegranate · Rotten / Split",
        "sku": "PRD-POM-015-R",
        "category": "Spoilage Risk",
        "unit_price": Decimal("0.00"),
        "on_hand": 4,
        "min_stock": 0,
        "freshness_score": 19,
        "is_spoilage_risk": True,
        "status": "Spoiled / Flagged",
        "shelf_location": "Write-off Bin · Compost"
    },
    {
        "class_label": "potato",
        "name": "Potato · Russet Washed 2kg",
        "sku": "PRD-POT-016",
        "category": "Produce",
        "unit_price": Decimal("2.99"),
        "on_hand": 190,
        "min_stock": 65,
        "freshness_score": 97,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Aisle 2 · Root Vegetables"
    },
    {
        "class_label": "strawberry",
        "name": "Strawberry · Fresh Punnet 250g",
        "sku": "PRD-STR-017",
        "category": "Produce",
        "unit_price": Decimal("3.50"),
        "on_hand": 18,
        "min_stock": 40,
        "freshness_score": 91,
        "is_spoilage_risk": False,
        "status": "Low stock",
        "shelf_location": "Aisle 1 · Berries Chiller"
    },
    {
        "class_label": "strawberry_rotten",
        "name": "Strawberry · Rotten / Gray Mold",
        "sku": "PRD-STR-017-R",
        "category": "Spoilage Risk",
        "unit_price": Decimal("0.00"),
        "on_hand": 11,
        "min_stock": 0,
        "freshness_score": 8,
        "is_spoilage_risk": True,
        "status": "Spoiled / Flagged",
        "shelf_location": "Write-off Bin · Compost"
    },
    {
        "class_label": "tomato",
        "name": "Tomato · Roma Vine Ripened",
        "sku": "PRD-TOM-018",
        "category": "Produce",
        "unit_price": Decimal("2.25"),
        "on_hand": 140,
        "min_stock": 50,
        "freshness_score": 95,
        "is_spoilage_risk": False,
        "status": "In stock",
        "shelf_location": "Aisle 1 · Produce Bay B"
    },
    {
        "class_label": "tomato_rotten",
        "name": "Tomato · Rotten / Soft Rot",
        "sku": "PRD-TOM-018-R",
        "category": "Spoilage Risk",
        "unit_price": Decimal("0.00"),
        "on_hand": 8,
        "min_stock": 0,
        "freshness_score": 16,
        "is_spoilage_risk": True,
        "status": "Spoiled / Flagged",
        "shelf_location": "Write-off Bin · Compost"
    }
]

def seed_database():
    Base.metadata.create_all(bind=engine)
    try:
        from app.core.seeders import seed_default_stores
        seed_default_stores()
    except Exception as e:
        print(f"Note: seed_default_stores: {e}")
    db = SessionLocal()
    try:
        inserted = 0
        updated = 0
        for item in INVENTORY_DATA:
            existing = db.query(InventoryItem).filter(InventoryItem.class_label == item["class_label"]).first()
            if existing:
                for key, val in item.items():
                    setattr(existing, key, val)
                updated += 1
            else:
                db_item = InventoryItem(**item)
                db.add(db_item)
                inserted += 1
        db.commit()
        print(f"✓ Inventory seeding complete: {inserted} added, {updated} updated (Total: {len(INVENTORY_DATA)} items).")
    except Exception as e:
        db.rollback()
        print(f"Error seeding inventory: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
