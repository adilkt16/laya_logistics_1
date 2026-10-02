# test_suite.py
# Warehouse Brain - Stage 6: Evaluation & Weakness Discovery Test Suite
#
# This test suite systematically evaluates Laya's decision-making behavior
# across 35 realistic and edge-case warehouse shipments.
#
# We test 10 distinct categories:
# 1. Obvious cases
# 2. Ambiguous cases
# 3. Conflicting signals
# 4. Unusual values
# 5. Extremely urgent orders
# 6. Extremely fragile orders
# 7. Very high-value orders
# 8. Low-value urgent orders
# 9. High-value non-urgent orders
# 10. Contradictory-looking cases
#
# IMPORTANT: Expected decisions reflect human logistics ground truth.
# We do NOT adjust expected answers to flatter the model.

import os
import sys
import time

from warehouse import LayaDecisionEngine

# Remove HF_HUB_OFFLINE if set by warehouse.py to ensure Hugging Face snapshot downloads complete smoothly
os.environ.pop("HF_HUB_OFFLINE", None)

# =============================================================================
# 1. TEST SUITE DATASET (35 FICTIONAL ORDERS ACROSS 10 TEST CATEGORIES)
# =============================================================================
TEST_SUITE = [
    # -------------------------------------------------------------------------
    # Category 1: Obvious Cases (Clean, textbook scenarios)
    # -------------------------------------------------------------------------
    {
        "order_id": "TEST-01",
        "category": "Obvious Cases",
        "product_name": "Emergency Cardiac Stent Delivery",
        "destination": "Cleveland Clinic, OH",
        "deadline": 1,
        "weight": 0.4,
        "fragile": True,
        "value": 4500.0,
        "quantity": 2,
        "expected_decision": "HIGH",
        "rationale": "Critical 1h hospital emergency deadline with high monetary value."
    },
    {
        "order_id": "TEST-02",
        "category": "Obvious Cases",
        "product_name": "Standard Office Ballpoint Pens (Box of 50)",
        "destination": "Columbus, OH",
        "deadline": 18,
        "weight": 1.2,
        "fragile": False,
        "value": 24.50,
        "quantity": 10,
        "expected_decision": "MEDIUM",
        "rationale": "Standard routine delivery with normal 18-hour timeline and low value."
    },
    {
        "order_id": "TEST-03",
        "category": "Obvious Cases",
        "product_name": "Bulk Crushed Limestone Gravel (5 Bags)",
        "destination": "Quarry Depot, Dallas, TX",
        "deadline": 96,
        "weight": 125.0,
        "fragile": False,
        "value": 65.0,
        "quantity": 5,
        "expected_decision": "LOW",
        "rationale": "Relaxed 4-day delivery schedule for heavy durable commodity hardware."
    },
    {
        "order_id": "TEST-04",
        "category": "Obvious Cases",
        "product_name": "Standard Running Sneakers & Gym Socks",
        "destination": "Orlando, FL",
        "deadline": 16,
        "weight": 1.4,
        "fragile": False,
        "value": 115.0,
        "quantity": 1,
        "expected_decision": "MEDIUM",
        "rationale": "Typical everyday e-commerce consumer order with 16h standard schedule."
    },

    # -------------------------------------------------------------------------
    # Category 2: Ambiguous Cases (Borderline timelines and blurred boundaries)
    # -------------------------------------------------------------------------
    {
        "order_id": "TEST-05",
        "category": "Ambiguous Cases",
        "product_name": "Replacement USB-C Laptop Charger",
        "destination": "Austin, TX",
        "deadline": 7,
        "weight": 0.5,
        "fragile": False,
        "value": 55.0,
        "quantity": 1,
        "expected_decision": "MEDIUM",
        "rationale": "7h deadline sits right on the boundary between rush (<=6h) and standard (12-24h)."
    },
    {
        "order_id": "TEST-06",
        "category": "Ambiguous Cases",
        "product_name": "Ceramic Subway Tiles (Box of 20)",
        "destination": "Seattle, WA",
        "deadline": 26,
        "weight": 16.5,
        "fragile": True,
        "value": 130.0,
        "quantity": 2,
        "expected_decision": "LOW",
        "rationale": "26h timeline lies between standard 24h cutoff and relaxed multi-day schedule."
    },
    {
        "order_id": "TEST-07",
        "category": "Ambiguous Cases",
        "product_name": "Artisan Cold-Pressed Extra Virgin Olive Oil",
        "destination": "Portland, OR",
        "deadline": 24,
        "weight": 3.2,
        "fragile": True,
        "value": 78.0,
        "quantity": 3,
        "expected_decision": "MEDIUM",
        "rationale": "Exactly on the 24-hour upper boundary for standard regular priority."
    },
    {
        "order_id": "TEST-08",
        "category": "Ambiguous Cases",
        "product_name": "Commercial Floor Cleaning Solvent (5 Gal)",
        "destination": "Detroit, MI",
        "deadline": 30,
        "weight": 18.0,
        "fragile": False,
        "value": 92.0,
        "quantity": 1,
        "expected_decision": "LOW",
        "rationale": "30h deadline sits exactly on the threshold between standard and relaxed schedule."
    },

    # -------------------------------------------------------------------------
    # Category 3: Conflicting Signals (Contrasting attributes tugging decisions)
    # -------------------------------------------------------------------------
    {
        "order_id": "TEST-09",
        "category": "Conflicting Signals",
        "product_name": "Bulk Quarry Boulders for Emergency Seawall",
        "destination": "Tampa Coastal Bay, FL",
        "deadline": 4,
        "weight": 420.0,
        "fragile": False,
        "value": 180.0,
        "quantity": 2,
        "expected_decision": "HIGH",
        "rationale": "Extremely tight 4h deadline overrides low value and heavy bulk nature."
    },
    {
        "order_id": "TEST-10",
        "category": "Conflicting Signals",
        "product_name": "Antique Handcrafted Grandfather Clock",
        "destination": "Beacon Hill, Boston, MA",
        "deadline": 120,
        "weight": 55.0,
        "fragile": True,
        "value": 7200.0,
        "quantity": 1,
        "expected_decision": "LOW",
        "rationale": "Ultra-fragile and high-value, but client booked a relaxed 5-day delivery window."
    },
    {
        "order_id": "TEST-11",
        "category": "Conflicting Signals",
        "product_name": "Hospital Emergency Saline IV Solution Bags",
        "destination": "Denver General Hospital, CO",
        "deadline": 3,
        "weight": 110.0,
        "fragile": False,
        "value": 140.0,
        "quantity": 10,
        "expected_decision": "HIGH",
        "rationale": "Urgent 3h hospital delivery deadline conflicts with heavy commodity weight."
    },

    # -------------------------------------------------------------------------
    # Category 4: Unusual Values (Extreme numerical scales, zero price, huge weights)
    # -------------------------------------------------------------------------
    {
        "order_id": "TEST-12",
        "category": "Unusual Values",
        "product_name": "Industrial Steam Power Turbine Rotor Shaft",
        "destination": "Houston Energy Hub, TX",
        "deadline": 5,
        "weight": 920.0,
        "fragile": False,
        "value": 160000.0,
        "quantity": 1,
        "expected_decision": "HIGH",
        "rationale": "Extreme value ($160k), extreme weight (920kg), and tight 5h rush turnaround."
    },
    {
        "order_id": "TEST-13",
        "category": "Unusual Values",
        "product_name": "Promotional Brand Decal & Sticker Pack",
        "destination": "New York, NY",
        "deadline": 1,
        "weight": 0.02,
        "fragile": False,
        "value": 0.0,
        "quantity": 1,
        "expected_decision": "HIGH",
        "rationale": "Zero monetary value ($0.00), but strict 1h rush SLA for event opening."
    },
    {
        "order_id": "TEST-14",
        "category": "Unusual Values",
        "product_name": "Overstocked Winter Wool Parkas (Wholesale Return)",
        "destination": "Chicago Logistics Yard, IL",
        "deadline": 350,
        "weight": 80.0,
        "fragile": False,
        "value": 4200.0,
        "quantity": 20,
        "expected_decision": "LOW",
        "rationale": "Unusually huge deadline (350h / 14 days) makes urgency definitely low despite $4.2k value."
    },
    {
        "order_id": "TEST-15",
        "category": "Unusual Values",
        "product_name": "Gallium Nitride Semiconductor Wafer Ingot",
        "destination": "San Jose Tech Lab, CA",
        "deadline": 2,
        "weight": 0.35,
        "fragile": True,
        "value": 48000.0,
        "quantity": 1,
        "expected_decision": "HIGH",
        "rationale": "Extremely high value ($48k), featherweight, fragile, and critical 2h deadline."
    },

    # -------------------------------------------------------------------------
    # Category 5: Extremely Urgent Orders (Sub-3 hour life-or-death & AOG deadlines)
    # -------------------------------------------------------------------------
    {
        "order_id": "TEST-16",
        "category": "Extremely Urgent Orders",
        "product_name": "Cryogenic Human Organ Transplant Container",
        "destination": "Johns Hopkins Hospital, MD",
        "deadline": 1,
        "weight": 2.2,
        "fragile": True,
        "value": 9500.0,
        "quantity": 1,
        "expected_decision": "HIGH",
        "rationale": "Life-critical 1h surgical window requiring immediate top-tier expediting."
    },
    {
        "order_id": "TEST-17",
        "category": "Extremely Urgent Orders",
        "product_name": "Commercial Jet Aircraft AOG Hydraulic Servo Valve",
        "destination": "Atlanta Hartsfield Airport, GA",
        "deadline": 2,
        "weight": 4.1,
        "fragile": True,
        "value": 14200.0,
        "quantity": 1,
        "expected_decision": "HIGH",
        "rationale": "Aircraft On Ground (AOG) emergency holding flight passenger departures."
    },
    {
        "order_id": "TEST-18",
        "category": "Extremely Urgent Orders",
        "product_name": "Municipal Power Substation High-Voltage Relay",
        "destination": "Phoenix Power Station, AZ",
        "deadline": 1,
        "weight": 3.6,
        "fragile": False,
        "value": 2100.0,
        "quantity": 1,
        "expected_decision": "HIGH",
        "rationale": "Critical grid blackout restoration requiring 1h immediate dispatch."
    },

    # -------------------------------------------------------------------------
    # Category 6: Extremely Fragile Orders (Delicate goods testing handling bias)
    # -------------------------------------------------------------------------
    {
        "order_id": "TEST-19",
        "category": "Extremely Fragile Orders",
        "product_name": "Museum Venetian Blown-Glass Chandelier Core",
        "destination": "Metropolitan Museum, NY",
        "deadline": 48,
        "weight": 7.5,
        "fragile": True,
        "value": 15000.0,
        "quantity": 1,
        "expected_decision": "LOW",
        "rationale": "Extremely delicate and high value, but 48h deadline means fulfillment is non-urgent."
    },
    {
        "order_id": "TEST-20",
        "category": "Extremely Fragile Orders",
        "product_name": "Handcrafted Kyoto Ceramic Matcha Tea Set",
        "destination": "San Francisco, CA",
        "deadline": 20,
        "weight": 1.6,
        "fragile": True,
        "value": 420.0,
        "quantity": 1,
        "expected_decision": "MEDIUM",
        "rationale": "Breakable artisanal pottery on a routine 20-hour fulfillment timeline."
    },
    {
        "order_id": "TEST-21",
        "category": "Extremely Fragile Orders",
        "product_name": "Laser Optics Quartz Spectrometry Prism",
        "destination": "MIT Physics Lab, Cambridge, MA",
        "deadline": 72,
        "weight": 0.45,
        "fragile": True,
        "value": 3400.0,
        "quantity": 1,
        "expected_decision": "LOW",
        "rationale": "High-precision fragile optics, but 72h schedule allows relaxed pacing."
    },

    # -------------------------------------------------------------------------
    # Category 7: Very High-Value Orders (Vault goods testing monetary value bias)
    # -------------------------------------------------------------------------
    {
        "order_id": "TEST-22",
        "category": "Very High-Value Orders",
        "product_name": "Certified GIA Solitaire Diamond Engagement Ring",
        "destination": "Beverly Hills, CA",
        "deadline": 96,
        "weight": 0.12,
        "fragile": True,
        "value": 29500.0,
        "quantity": 1,
        "expected_decision": "LOW",
        "rationale": "Astronomical monetary value, but 4-day deadline means urgency is low."
    },
    {
        "order_id": "TEST-23",
        "category": "Very High-Value Orders",
        "product_name": "Physical 99.99% Fine Gold Cast Bullion Bars (2x 1kg)",
        "destination": "Wall Street Vault, NY",
        "deadline": 144,
        "weight": 2.0,
        "fragile": False,
        "value": 140000.0,
        "quantity": 2,
        "expected_decision": "LOW",
        "rationale": "$140k vault shipment on a relaxed 6-day armored transport schedule."
    },
    {
        "order_id": "TEST-24",
        "category": "Very High-Value Orders",
        "product_name": "Financial High-Frequency Trading Server Blade",
        "destination": "Secaucus Data Center, NJ",
        "deadline": 4,
        "weight": 14.5,
        "fragile": True,
        "value": 26000.0,
        "quantity": 1,
        "expected_decision": "HIGH",
        "rationale": "Both high-value ($26k) and emergency 4h rush deadline align."
    },

    # -------------------------------------------------------------------------
    # Category 8: Low-Value Urgent Orders (Penny items that must ship right now)
    # -------------------------------------------------------------------------
    {
        "order_id": "TEST-25",
        "category": "Low-Value Urgent Orders",
        "product_name": "Assembly Line Replacement Brass Hex Lock Nut",
        "destination": "Automotive Plant, Gary, IN",
        "deadline": 1,
        "weight": 0.04,
        "fragile": False,
        "value": 1.25,
        "quantity": 2,
        "expected_decision": "HIGH",
        "rationale": "Cost $1.25, but line stoppage requires 1h emergency rush dispatch."
    },
    {
        "order_id": "TEST-26",
        "category": "Low-Value Urgent Orders",
        "product_name": "Emergency Sterile Disposable Scalpel Blades",
        "destination": "Urgent Care Clinic, St. Louis, MO",
        "deadline": 2,
        "weight": 0.15,
        "fragile": True,
        "value": 6.50,
        "quantity": 5,
        "expected_decision": "HIGH",
        "rationale": "Very cheap consumable ($6.50), but needed within 2 hours."
    },
    {
        "order_id": "TEST-27",
        "category": "Low-Value Urgent Orders",
        "product_name": "Backup Generator Slow-Blow Ceramic Fuse",
        "destination": "Community Shelter, Miami, FL",
        "deadline": 2,
        "weight": 0.08,
        "fragile": False,
        "value": 3.75,
        "quantity": 1,
        "expected_decision": "HIGH",
        "rationale": "Trivial $3.75 part with an urgent 2h storm disaster deadline."
    },

    # -------------------------------------------------------------------------
    # Category 9: High-Value Non-Urgent Orders (Expensive cargo with long runways)
    # -------------------------------------------------------------------------
    {
        "order_id": "TEST-28",
        "category": "High-Value Non-Urgent Orders",
        "product_name": "Swiss Luxury Perpetual Calendar Gold Watch",
        "destination": "Aspen, CO",
        "deadline": 120,
        "weight": 0.35,
        "fragile": True,
        "value": 24000.0,
        "quantity": 1,
        "expected_decision": "LOW",
        "rationale": "High value ($24k) requires vault security, but 5-day deadline is non-urgent."
    },
    {
        "order_id": "TEST-29",
        "category": "High-Value Non-Urgent Orders",
        "product_name": "Professional 8K Full-Frame Cinema Camera Body",
        "destination": "Hollywood Studio, CA",
        "deadline": 72,
        "weight": 3.6,
        "fragile": True,
        "value": 11800.0,
        "quantity": 1,
        "expected_decision": "LOW",
        "rationale": "High-tier cinema equipment on a relaxed 3-day freight delivery."
    },
    {
        "order_id": "TEST-30",
        "category": "High-Value Non-Urgent Orders",
        "product_name": "Hand-Cast Architectural Bronze Entrance Sconce",
        "destination": "Palm Beach Estate, FL",
        "deadline": 80,
        "weight": 26.0,
        "fragile": True,
        "value": 8200.0,
        "quantity": 2,
        "expected_decision": "LOW",
        "rationale": "Expensive custom architectural decor with a relaxed 80-hour delivery window."
    },

    # -------------------------------------------------------------------------
    # Category 10: Contradictory-Looking Cases (Deceptive wording & counter-intuitive cues)
    # -------------------------------------------------------------------------
    {
        "order_id": "TEST-31",
        "category": "Contradictory-Looking Cases",
        "product_name": "Crushed Industrial Plastic Scrap Pellets for Chemical Testing",
        "destination": "Plastics Testing Facility, Akron, OH",
        "deadline": 2,
        "weight": 14.0,
        "fragile": False,
        "value": 0.50,
        "quantity": 1,
        "expected_decision": "HIGH",
        "rationale": "Garbage-grade scrap ($0.50), but customer paid for emergency 2h laboratory testing pickup."
    },
    {
        "order_id": "TEST-32",
        "category": "Contradictory-Looking Cases",
        "product_name": "Live Freshwater Aquarium Flora (Perishable Delicate Plants)",
        "destination": "Aquatic Center, Raleigh, NC",
        "deadline": 4,
        "weight": 1.1,
        "fragile": True,
        "value": 18.0,
        "quantity": 3,
        "expected_decision": "HIGH",
        "rationale": "Low dollar value ($18), but live perishable plants must ship in 4h before dying."
    },
    {
        "order_id": "TEST-33",
        "category": "Contradictory-Looking Cases",
        "product_name": "Used Corrugated Cardboard Moving Boxes",
        "destination": "Recycling Center, Memphis, TN",
        "deadline": 72,
        "weight": 6.0,
        "fragile": False,
        "value": 0.0,
        "quantity": 10,
        "expected_decision": "LOW",
        "rationale": "Common packing material with relaxed 72h window, no urgency despite warehouse branding."
    },
    {
        "order_id": "TEST-34",
        "category": "Contradictory-Looking Cases",
        "product_name": "Haute Couture Silk Evening Gown",
        "destination": "Upper East Side, New York, NY",
        "deadline": 22,
        "weight": 1.1,
        "fragile": False,
        "value": 3600.0,
        "quantity": 1,
        "expected_decision": "MEDIUM",
        "rationale": "Luxury garment ($3,600) with standard 22h delivery timeline."
    },
    {
        "order_id": "TEST-35",
        "category": "Contradictory-Looking Cases",
        "product_name": "Economy Ground Label on Temperature-Sensitive Insulin Cooler",
        "destination": "Rural Clinic, Billings, MT",
        "deadline": 3,
        "weight": 3.8,
        "fragile": True,
        "value": 1650.0,
        "quantity": 1,
        "expected_decision": "HIGH",
        "rationale": "Cold-chain insulin with only 3 hours ice life remaining overrides misleading economy billing tag."
    }
]


# =============================================================================
# 2. TEST EXECUTION & EVALUATION RUNNER
# =============================================================================
def run_evaluation_suite():
    print("=" * 105)
    print("🧪 WAREHOUSE BRAIN EVALUATION SUITE: 35 FICTIONAL ORDERS".center(105))
    print("=" * 105)
    print("Testing Laya Decision Engine for sensible logistics routing across edge cases & conflicting cues.\n")

    engine = LayaDecisionEngine()

    total_tests = len(TEST_SUITE)
    correct_count = 0
    incorrect_count = 0

    results = []

    print("\n" + "=" * 105)
    print(f"{'ID':<8} | {'Category':<26} | {'Deadline':<8} | {'Value ($)':<9} | {'Expected':<8} | {'Laya':<8} | {'Conf':<6} | {'Match'}")
    print("-" * 105)

    start_time = time.time()

    for item in TEST_SUITE:
        order = {
            "order_id": item["order_id"],
            "product_name": item["product_name"],
            "destination": item["destination"],
            "deadline": item["deadline"],
            "weight": item["weight"],
            "fragile": item["fragile"],
            "value": item["value"],
            "quantity": item["quantity"]
        }

        # Run pure Laya decision
        decision = engine.evaluate(order)

        laya_decision = decision.priority
        confidence = decision.priority_confidence
        expected = item["expected_decision"]
        is_match = (laya_decision == expected)

        if is_match:
            correct_count += 1
            match_badge = "✅ YES"
        else:
            incorrect_count += 1
            match_badge = "❌ NO "

        results.append({
            "item": item,
            "order": order,
            "decision": decision,
            "expected": expected,
            "laya": laya_decision,
            "confidence": confidence,
            "match": is_match,
            "raw_probs": decision.raw_probabilities.get("priority", {})
        })

        print(
            f"{item['order_id']:<8} | "
            f"{item['category'][:26]:<26} | "
            f"{item['deadline']:>6}h | "
            f"${item['value']:>8,.0f} | "
            f"{expected:<8} | "
            f"{laya_decision:<8} | "
            f"{confidence * 100:5.1f}% | "
            f"{match_badge}"
        )

    elapsed = time.time() - start_time
    accuracy = (correct_count / total_tests) * 100.0

    # =========================================================================
    # 3. EVALUATION SUMMARY
    # =========================================================================
    print("=" * 105)
    print("📊 EVALUATION SUMMARY".center(105))
    print("=" * 105)
    print(f"  • Total tests         : {total_tests}")
    print(f"  • Correct decisions   : {correct_count}")
    print(f"  • Incorrect decisions : {incorrect_count}")
    print(f"  • Accuracy            : {accuracy:.2f}%")
    print(f"  • Elapsed Time        : {elapsed:.2f}s ({elapsed / total_tests:.2f}s per test)")
    print("-" * 105)

    # =========================================================================
    # 4. WEAKNESS ANALYSIS: MISMATCHES & UNCERTAIN DECISIONS
    # =========================================================================
    print("\n" + "=" * 105)
    print("🔍 DISCOVERED WEAKNESSES: MISMATCHES & UNEXPECTED DECISIONS".center(105))
    print("=" * 105)

    mismatches = [r for r in results if not r["match"]]
    if not mismatches:
        print("  None! All decisions matched expected outcomes.")
    else:
        for idx, r in enumerate(mismatches, 1):
            it = r["item"]
            probs = r["raw_probs"]
            print(f"\n[{idx}] ❌ MISMATCH: {it['order_id']} - {it['product_name']}")
            print(f"    Category        : {it['category']}")
            print(f"    Attributes      : Deadline={it['deadline']}h, Value=${it['value']:,.2f}, Weight={it['weight']}kg, Fragile={it['fragile']}")
            print(f"    Expected Reason : {it['rationale']}")
            print(f"    Expected Decision: [{r['expected']}]")
            print(f"    Laya Decision   : [{r['laya']}] (Confidence: {r['confidence']*100:.1f}%)")
            print(f"    Probability Mass: HIGH={probs.get('high', 0)*100:4.1f}% | MEDIUM={probs.get('medium', 0)*100:4.1f}% | LOW={probs.get('low', 0)*100:4.1f}%")

    print("\n" + "=" * 105)
    print("🤔 UNCERTAIN PREDICTIONS (Confidence < 75% or Dispersed Probability Mass)".center(105))
    print("=" * 105)

    uncertain_cases = [r for r in results if r["confidence"] < 0.75]
    if not uncertain_cases:
        print("  None! Model expressed >= 75% confidence on all items.")
    else:
        for idx, r in enumerate(uncertain_cases, 1):
            it = r["item"]
            probs = r["raw_probs"]
            match_str = "MATCH" if r["match"] else "MISMATCH"
            print(f"\n[{idx}] ⚠️ LOW CONFIDENCE ({match_str}): {it['order_id']} - {it['product_name']}")
            print(f"    Category        : {it['category']}")
            print(f"    Laya Decision   : [{r['laya']}] with confidence {r['confidence']*100:.1f}% (Expected: [{r['expected']}])")
            print(f"    Probability Mass: HIGH={probs.get('high', 0)*100:4.1f}% | MEDIUM={probs.get('medium', 0)*100:4.1f}% | LOW={probs.get('low', 0)*100:4.1f}%")

    # =========================================================================
    # 5. CATEGORY BREAKDOWN
    # =========================================================================
    print("\n" + "=" * 105)
    print("📋 CATEGORY-BY-CATEGORY BREAKDOWN".center(105))
    print("=" * 105)

    categories = list(dict.fromkeys(r["item"]["category"] for r in results))
    for cat in categories:
        cat_results = [r for r in results if r["item"]["category"] == cat]
        cat_correct = sum(1 for r in cat_results if r["match"])
        cat_total = len(cat_results)
        cat_acc = (cat_correct / cat_total) * 100.0
        avg_conf = sum(r["confidence"] for r in cat_results) / cat_total * 100.0
        print(f"  • {cat:<32}: {cat_correct}/{cat_total} ({cat_acc:5.1f}%) | Avg Conf: {avg_conf:5.1f}%")

    print("=" * 105 + "\n")
    return results


if __name__ == "__main__":
    run_evaluation_suite()
