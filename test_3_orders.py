# test_3_orders.py
# Warehouse Brain - Stage 2: Manual Testing Script
#
# This script tests 3 distinct warehouse orders to observe how Laya
# classifies them into 'low', 'medium', or 'high' urgency based on
# their real-world attributes (deadline, value, product type, fragility).

from laya import Router

# Initialize the router
router = Router()

# Define the single structured choice decision schema
URGENCY_DECISION_SCHEMA = {
    "urgency": {
        "type": "choice",
        "instructions": "Rate the urgency of processing this order:",
        "criteria": {
            "low": "low urgency: non-urgent, deferred fulfillment, can wait, relaxed schedule",
            "medium": "medium urgency: standard priority, regular timeline, ordinary package",
            "high": "high urgency: rush fulfillment, urgent deadline, emergency priority, high value"
        }
    }
}

# 3 Test Scenarios designed to exercise the low, medium, and high decisions
TEST_CASES = [
    {
        "label": "TEST CASE 1 (Emergency Medical Cargo)",
        "order": {
            "order_id": "ORD-001",
            "product_name": "Surgical Bone Drills",
            "destination": "Hospital Central, Chicago",
            "deadline": 2,          # 2 hours left
            "fragile": True,
            "value": 3500.0,
            "quantity": 2
        },
        "description": "Urgent high-priority order: Surgical bone drills, deadline in 2 hours, rush fulfillment needed."
    },
    {
        "label": "TEST CASE 2 (Standard Retail Shipment)",
        "order": {
            "order_id": "ORD-011",
            "product_name": "Vintage Vinyl Records",
            "destination": "Nashville, TN",
            "deadline": 18,         # 18 hours left
            "fragile": True,
            "value": 310.0,
            "quantity": 4
        },
        "description": "Standard medium-priority order: Vintage vinyl records, normal 18 hour schedule."
    },
    {
        "label": "TEST CASE 3 (Bulk Low-Priority Goods)",
        "order": {
            "order_id": "ORD-014",
            "product_name": "Bulk Garden Soil Bags",
            "destination": "Raleigh, NC",
            "deadline": 60,         # 60 hours left (2.5 days)
            "fragile": False,
            "value": 35.0,
            "quantity": 5
        },
        "description": "Non-urgent low-priority order: Bulk garden soil bags, 60 hours remaining, deferred shipping, can wait."
    }
]


def run_manual_tests():
    print("=" * 80)
    print("🧪 MANUAL TEST: 3 Different Warehouse Orders with Laya".center(80))
    print("=" * 80)

    for item in TEST_CASES:
        label = item["label"]
        order = item["order"]
        state_text = item["description"]

        print(f"\n▶ {label}")
        print(f"  Order ID    : {order['order_id']}")
        print(f"  Product     : {order['product_name']}")
        print(f"  Deadline    : {order['deadline']} hours remaining")
        print(f"  Value       : ${order['value']:,.2f}")
        print(f"  State Sent  : \"{state_text}\"")

        # -------------------------------------------------------------
        # EXACT POINT WHERE LAYA DECIDES:
        # -------------------------------------------------------------
        prediction = router.predict(state_text, URGENCY_DECISION_SCHEMA)
        # -------------------------------------------------------------

        # Inspect the output
        result = prediction["answers"]["urgency"]
        decision = result["choice"]
        probs = result["probabilities"]

        print(f"  🎯 Decision : [{decision.upper()}]")
        print("  📊 Calibrated Probabilities:")
        for outcome in ["low", "medium", "high"]:
            p = probs[outcome]
            bar = "█" * int(p * 25)
            print(f"     - {outcome:<6}: {p * 100:5.1f}% | {bar}")

    print("\n" + "=" * 80)
    print("Testing complete. Notice how Laya returns typed decisions, not prose!".center(80))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_manual_tests()
