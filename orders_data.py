# orders_data.py
# Fictional warehouse order dataset for the "Warehouse Brain" project.
#
# Each order represents a real-world package waiting in our fulfillment center.
# We represent each order as a standard Python dictionary with 8 key attributes:
#
# - order_id:     A unique identifier for tracking (e.g., "ORD-001")
# - product_name: The human-readable name of the item
# - destination:  Where the package is going (city or zone)
# - deadline:     Hours remaining until this shipment must leave the warehouse (e.g., 2 = 2 hours left)
# - weight:       Package weight in kilograms (kg)
# - fragile:      Boolean (True or False) indicating if special handling is required
# - value:        Monetary worth of the product in USD ($)
# - quantity:     How many units of the item are in this order

ORDERS = [
    {
        "order_id": "ORD-001",
        "product_name": "Surgical Bone Drills",
        "destination": "Hospital Central, Chicago",
        "deadline": 2,          # Very urgent: 2 hours left
        "weight": 4.5,
        "fragile": True,
        "value": 3500.0,
        "quantity": 2
    },
    {
        "order_id": "ORD-002",
        "product_name": "Ceramic Dinner Plates Set",
        "destination": "Austin, TX",
        "deadline": 24,         # Standard delivery: 24 hours left
        "weight": 8.2,
        "fragile": True,
        "value": 120.0,
        "quantity": 1
    },
    {
        "order_id": "ORD-003",
        "product_name": "Industrial Hex Bolts (Box of 500)",
        "destination": "Detroit, MI",
        "deadline": 48,         # Low urgency: 48 hours left
        "weight": 25.0,
        "fragile": False,
        "value": 65.0,
        "quantity": 4
    },
    {
        "order_id": "ORD-004",
        "product_name": "High-End Gaming Laptop",
        "destination": "Seattle, WA",
        "deadline": 6,          # Rush shipping: 6 hours left
        "weight": 3.1,
        "fragile": True,
        "value": 2400.0,
        "quantity": 1
    },
    {
        "order_id": "ORD-005",
        "product_name": "Organic Cotton T-Shirts",
        "destination": "Brooklyn, NY",
        "deadline": 36,
        "weight": 1.2,
        "fragile": False,
        "value": 45.0,
        "quantity": 3
    },
    {
        "order_id": "ORD-006",
        "product_name": "Laboratory Glass Beakers",
        "destination": "Cambridge, MA",
        "deadline": 4,          # High urgency + fragile
        "weight": 2.8,
        "fragile": True,
        "value": 420.0,
        "quantity": 6
    },
    {
        "order_id": "ORD-007",
        "product_name": "Smartphone OLED Screens",
        "destination": "San Jose, CA",
        "deadline": 5,          # High value + urgent + fragile
        "weight": 1.5,
        "fragile": True,
        "value": 5200.0,
        "quantity": 10
    },
    {
        "order_id": "ORD-008",
        "product_name": "Cast Iron Dumbbell Set",
        "destination": "Denver, CO",
        "deadline": 72,         # Long deadline + heavy
        "weight": 40.0,
        "fragile": False,
        "value": 110.0,
        "quantity": 2
    },
    {
        "order_id": "ORD-009",
        "product_name": "Insulin Cold-Storage Cooler",
        "destination": "Miami, FL",
        "deadline": 3,          # Time-sensitive medical package
        "weight": 5.0,
        "fragile": True,
        "value": 1800.0,
        "quantity": 1
    },
    {
        "order_id": "ORD-010",
        "product_name": "Wireless Mechanical Keyboards",
        "destination": "Portland, OR",
        "deadline": 28,
        "weight": 2.2,
        "fragile": False,
        "value": 160.0,
        "quantity": 2
    },
    {
        "order_id": "ORD-011",
        "product_name": "Vintage Vinyl Records",
        "destination": "Nashville, TN",
        "deadline": 18,
        "weight": 1.8,
        "fragile": True,
        "value": 310.0,
        "quantity": 4
    },
    {
        "order_id": "ORD-012",
        "product_name": "Automotive Car Batteries",
        "destination": "Atlanta, GA",
        "deadline": 12,
        "weight": 32.0,
        "fragile": False,
        "value": 380.0,
        "quantity": 2
    },
    {
        "order_id": "ORD-013",
        "product_name": "Luxury Silk Scarves",
        "destination": "Manhattan, NY",
        "deadline": 8,
        "weight": 0.4,
        "fragile": False,
        "value": 850.0,
        "quantity": 5
    },
    {
        "order_id": "ORD-014",
        "product_name": "Bulk Garden Soil Bags",
        "destination": "Raleigh, NC",
        "deadline": 60,
        "weight": 50.0,
        "fragile": False,
        "value": 35.0,
        "quantity": 5
    },
    {
        "order_id": "ORD-015",
        "product_name": "Drone 4K Camera Gimbal",
        "destination": "Phoenix, AZ",
        "deadline": 7,
        "weight": 1.1,
        "fragile": True,
        "value": 1150.0,
        "quantity": 1
    },
    {
        "order_id": "ORD-016",
        "product_name": "Hardcover Programming Books",
        "destination": "Salt Lake City, UT",
        "deadline": 40,
        "weight": 6.0,
        "fragile": False,
        "value": 180.0,
        "quantity": 3
    },
    {
        "order_id": "ORD-017",
        "product_name": "Emergency Backup Generator",
        "destination": "New Orleans, LA",
        "deadline": 5,          # High value, urgent, heavy
        "weight": 48.0,
        "fragile": False,
        "value": 2900.0,
        "quantity": 1
    },
    {
        "order_id": "ORD-018",
        "product_name": "Fine Wine Wooden Crate",
        "destination": "Napa Valley, CA",
        "deadline": 14,
        "weight": 9.5,
        "fragile": True,
        "value": 750.0,
        "quantity": 1
    },
    {
        "order_id": "ORD-019",
        "product_name": "Stainless Steel Kitchen Utensils",
        "destination": "Dallas, TX",
        "deadline": 30,
        "weight": 3.4,
        "fragile": False,
        "value": 70.0,
        "quantity": 2
    },
    {
        "order_id": "ORD-020",
        "product_name": "Optics Calibration Laser",
        "destination": "Boulder, CO",
        "deadline": 3,          # Ultra high value, tight deadline, fragile
        "weight": 2.1,
        "fragile": True,
        "value": 6800.0,
        "quantity": 1
    }
]
