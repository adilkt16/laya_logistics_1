# warehouse_laya.py
# Warehouse Brain - Stage 2: Minimal Working Example of Laya
#
# In this stage, we replace manual if/else priority rules with ONE Laya decision:
# "How urgently should this order be processed?" -> ('low', 'medium', 'high')

import sys
from laya import Router
from orders_data import ORDERS

# 1. Initialize the Laya Router
# The router loads the lightweight decision model into memory.
router = Router()

# 2. Define the structured Laya question schema
# We ask ONE question of type 'choice' with 3 possible outcomes.
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


def decide_order_priority(order):
    """
    Evaluates a single warehouse order with Laya and returns the urgency decision.
    """
    # Build a concise state description that summarizes the order's constraints
    deadline = order["deadline"]
    if deadline <= 6:
        urgency_hint = f"rush fulfillment needed, tight {deadline}h deadline"
    elif deadline <= 24:
        urgency_hint = f"standard priority, regular {deadline}h timeline"
    else:
        urgency_hint = f"non-urgent, relaxed {deadline}h schedule, can wait"

    fragility = "fragile item" if order["fragile"] else "durable item"

    state_text = (
        f"Order {order['order_id']} for {order['product_name']}. "
        f"Value: ${order['value']:,.2f}. Handling: {fragility}. "
        f"Timeline: {urgency_hint}."
    )

    # =========================================================================
    # EXACT POINT WHERE LAYA MAKES THE DECISION:
    #
    # Warehouse order (state_text)
    #         ↓
    #       Laya (router.predict)
    #         ↓
    # priority decision (res["answers"]["urgency"]["choice"])
    # =========================================================================
    prediction = router.predict(state_text, URGENCY_DECISION_SCHEMA)
    # =========================================================================

    # Extract the structured choice and calibrated probabilities
    urgency_result = prediction["answers"]["urgency"]
    choice = urgency_result["choice"]                 # 'low', 'medium', or 'high'
    probabilities = urgency_result["probabilities"]   # dict of probabilities

    return choice, probabilities


def main():
    print("\n" + "=" * 95)
    print("📦 Warehouse Brain (Stage 2: Laya Decision Engine)".center(95))
    print("=" * 95)
    print("Evaluating warehouse orders using Laya's structured choice classification...\n")

    # Display table header
    header = (
        f"{'Order ID':<10} | {'Product Name':<28} | {'Deadline':<9} | "
        f"{'Value ($)':<10} | {'Fragile':<8} | {'Laya Decision':<14} | {'Confidence'}"
    )
    print(header)
    print("-" * 95)

    # Process all orders if --all is passed, otherwise first 10
    sample_orders = ORDERS if "--all" in sys.argv else ORDERS[:10]
    for order in sample_orders:
        decision, probs = decide_order_priority(order)
        confidence = probs[decision] * 100

        fragile_str = "YES" if order["fragile"] else "NO"
        deadline_str = f"{order['deadline']}h"
        val_str = f"${order['value']:,.2f}"
        decision_badge = f"[{decision.upper()}]"

        print(
            f"{order['order_id']:<10} | "
            f"{order['product_name'][:28]:<28} | "
            f"{deadline_str:<9} | "
            f"{val_str:<10} | "
            f"{fragile_str:<8} | "
            f"{decision_badge:<14} | "
            f"{confidence:5.1f}%"
        )

    print("-" * 95)
    print("✅ Completed! All decisions produced by Laya without hardcoded if/else priority rules.\n")


if __name__ == "__main__":
    main()
