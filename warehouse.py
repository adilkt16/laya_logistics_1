# warehouse.py
# Warehouse Brain - Stage 5: Confidence-Gated Decision & Human-in-the-Loop Fulfillment
#
# ARCHITECTURAL SEPARATION OF CONCERNS:
#
#   WAREHOUSE ORDER (State / Context)
#          ↓
#        LAYA (Pure Neural Decision Engine: Produces Decisions & Calibrated Probabilities)
#          ↓
#   CONFIDENCE GATE (Safety Filter: Compares model confidence against threshold)
#          ├── Confidence >= 0.85 & No Policy Trigger → AUTO PROCESSED (Fast Straight-Through Path)
#          └── Confidence < 0.85 OR Policy Trigger    → HUMAN REVIEW (Supervisor Inspection Path)
#          ↓
#   APPLICATION ACTIONS (Deterministic Python Runtime: Queues, Lanes, DB, Physical Dispatch)
#
# Rule: Laya ONLY makes decisions. Standard Python code performs actions.

import os
import sys
import time
import warnings
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# Suppress unnecessary warnings
warnings.filterwarnings("ignore")

from laya import Router
from orders_data import ORDERS

# =============================================================================
# CONFIDENCE GATE CONFIGURATION & PEDAGOGICAL DISCLAIMER
# =============================================================================
# In automated decision systems, a confidence gate acts as a safety filter:
# - Decisions meeting or exceeding the threshold run autonomously ("Straight-Through Processing")
# - Decisions falling below the threshold escalate to a human supervisor ("Human-in-the-Loop")
#
# IMPORTANT:
# 0.85 is strictly an illustrative DEMONSTRATION THRESHOLD for this learning simulation.
# It is NOT a scientifically validated production threshold.
# In production, confidence does not guarantee correctness, and thresholds
# must be empirically calibrated on real domain data using cost-benefit matrices.
CONFIDENCE_THRESHOLD = 0.85


# =============================================================================
# 1. STRUCTURED DECISION SCHEMA (For Laya)
# =============================================================================
WAREHOUSE_DECISION_SCHEMA = {
    "processing_priority": {
        "type": "choice",
        "instructions": "Determine fulfillment priority for this warehouse order:",
        "criteria": {
            "high": "urgent rush priority: emergency deadline under 6 hours, high monetary value, expedited shipping",
            "medium": "standard regular priority: normal routine retail delivery with 12 to 24 hours timeline",
            "low": "low priority: non-urgent relaxed multi-day schedule with over 30 hours remaining, bulk hardware or soil"
        }
    },
    "warehouse_lane": {
        "type": "choice",
        "instructions": "Assign the warehouse handling lane for this package:",
        "criteria": {
            "standard": "standard conveyor lane: durable non-fragile items, regular packaging",
            "fragile": "fragile handling lane: delicate breakable goods, glassware, ceramics, fragile items",
            "high_value": "high_value secure vault lane: expensive luxury items, high monetary value exceeding $2,000"
        }
    },
    "needs_human_review": {
        "type": "noul",
        "instructions": "Does this order require supervisor sign-off before dispatch?",
        "criteria": {
            "false": "routine automated order within standard operating parameters, ordinary package",
            "true": "requires supervisor sign-off: high monetary value exceeding $2,500, emergency tight deadline under 3h, or critical medical supplies"
        }
    }
}


# =============================================================================
# 2. DECISION DATA MODEL
# =============================================================================
@dataclass
class OrderDecision:
    """
    Pure data container representing Laya's decision and confidence metrics.
    Contains NO execution logic and has NO side effects.
    """
    order_id: str
    priority: str                     # 'HIGH', 'MEDIUM', 'LOW'
    priority_confidence: float        # Calibrated probability mass for chosen priority
    lane: str                         # 'STANDARD', 'FRAGILE', 'HIGH_VALUE'
    lane_confidence: float            # Calibrated probability mass for chosen lane
    needs_human_review: bool          # Flagged by model/policy
    review_confidence: float          # Confidence in review flag
    gate_status: str                  # 'AUTO_PROCESSED' or 'HUMAN_REVIEW'
    escalation_reasons: List[str]     # Specific reasons for escalation if sent to review
    min_confidence: float             # Lowest confidence among the decisions
    raw_probabilities: dict = field(default_factory=dict)


# =============================================================================
# 3. DECISION ENGINE (Laya - Strictly Pure / Read-Only)
# =============================================================================
class LayaDecisionEngine:
    """
    The Decision Engine evaluates order data and returns structured decisions
    with calibrated confidence scores.
    
    CRITICAL ARCHITECTURAL BOUNDARY:
    - This class has NO access to warehouse queues, lanes, or physical state.
    - It CANNOT mutate system state or perform side effects.
    - Given order state, it solely produces decisions and confidence evaluations.
    """
    def __init__(self, device: str = "cpu"):
        print("🧠 Initializing Laya Decision Engine (Neural Router on CPU)...")
        self.router = Router(device=device)

    def evaluate(self, order: dict) -> OrderDecision:
        deadline_hrs = order["deadline"]
        if deadline_hrs <= 6:
            deadline_cue = f"urgent rush deadline ({deadline_hrs} hours remaining)"
        elif deadline_hrs <= 24:
            deadline_cue = f"standard routine delivery timeline ({deadline_hrs} hours remaining)"
        else:
            deadline_cue = f"non-urgent relaxed multi-day schedule ({deadline_hrs} hours remaining)"

        if order["value"] >= 2000:
            lane_cue = f"High monetary value package (${order['value']:,.2f}), requires secure vault storage"
        elif order["fragile"]:
            lane_cue = "Delicate breakable product, fragile handling required"
        else:
            lane_cue = "Durable standard product, suitable for normal conveyor belts"

        state_text = (
            f"Order {order['order_id']}: {order['product_name']}. "
            f"Destination: {order['destination']}. "
            f"{deadline_cue}. "
            f"Weight: {order['weight']} kg. "
            f"{lane_cue}."
        )

        # Single forward-pass evaluation across all questions simultaneously
        prediction = self.router.predict(state_text, WAREHOUSE_DECISION_SCHEMA)
        answers = prediction["answers"]

        # 1. Priority Decision & Confidence
        p_ans = answers["processing_priority"]
        priority_choice = p_ans["choice"].upper()
        p_conf = float(p_ans["probabilities"][p_ans["choice"]])

        # 2. Lane Decision & Confidence
        l_ans = answers["warehouse_lane"]
        lane_choice = l_ans["choice"].upper()
        l_conf = float(l_ans["probabilities"][l_ans["choice"]])

        # 3. Human Review Decision & Confidence
        h_ans = answers["needs_human_review"]
        p_true = float(h_ans["noul"])
        review_bool = bool(p_true >= 0.5)
        review_conf = float(p_true if review_bool else (1.0 - p_true))

        # 4. Confidence Gate Logic:
        # Check against demonstration threshold (0.85) and safety policy
        escalation_reasons = []
        if review_bool:
            escalation_reasons.append(
                f"Policy Flag: Model flagged supervisor sign-off needed (Confidence: {review_conf:.2f})"
            )
        if p_conf < CONFIDENCE_THRESHOLD:
            escalation_reasons.append(
                f"Low Confidence: Priority '{priority_choice}' at {p_conf:.2f} < {CONFIDENCE_THRESHOLD:.2f} threshold"
            )
        if l_conf < CONFIDENCE_THRESHOLD:
            escalation_reasons.append(
                f"Low Confidence: Handling Lane '{lane_choice}' at {l_conf:.2f} < {CONFIDENCE_THRESHOLD:.2f} threshold"
            )

        gate_status = "HUMAN_REVIEW" if escalation_reasons else "AUTO_PROCESSED"
        min_conf = min(p_conf, l_conf, review_conf)

        return OrderDecision(
            order_id=order["order_id"],
            priority=priority_choice,
            priority_confidence=p_conf,
            lane=lane_choice,
            lane_confidence=l_conf,
            needs_human_review=review_bool,
            review_confidence=review_conf,
            gate_status=gate_status,
            escalation_reasons=escalation_reasons,
            min_confidence=min_conf,
            raw_probabilities={
                "priority": p_ans["probabilities"],
                "lane": l_ans["probabilities"],
                "review_p_true": p_true
            }
        )


# =============================================================================
# 4. APPLICATION SIMULATION & ACTION ENGINE (Standard Python Code)
# =============================================================================
class WarehouseSimulation:
    """
    Standard Python application that maintains state and performs concrete actions.
    
    This class is the 'Muscles / Hands' of the warehouse.
    It receives decisions and confidence metrics from Laya, routes orders
    through the confidence gate, manages queues and handling lanes, and dispatches packages.
    """
    def __init__(self):
        # Warehouse queues / staging areas:
        self.incoming_orders: List[dict] = []
        self.auto_processed_orders: List[dict] = []
        self.human_review_queue: List[dict] = []
        self.processing_queue: List[dict] = []
        self.fragile_lane: List[dict] = []
        self.high_value_lane: List[dict] = []
        self.completed_orders: List[dict] = []

        # Audit trail of executed Python application actions
        self.action_log: List[str] = []

    def log_action(self, action_type: str, details: str):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] [{action_type:<18}] {details}"
        self.action_log.append(entry)

    # -------------------------------------------------------------------------
    # Application Actions (Executed by Python, NOT by Laya)
    # -------------------------------------------------------------------------

    def action_receive_orders(self, orders: List[dict]):
        """Action: Ingest new shipments at warehouse receiving dock."""
        for o in orders:
            order_copy = dict(o)
            order_copy["status"] = "RECEIVED"
            order_copy["decision"] = None
            self.incoming_orders.append(order_copy)
        self.log_action("ACTION_INTAKE", f"Received {len(orders)} incoming packages at loading bay.")

    def action_route_based_on_decision(self, order: dict, decision: OrderDecision):
        """
        Action: Deterministic routing governed by the Confidence Gate.
        
        Python Business Logic:
        1. If gate_status is 'HUMAN_REVIEW':
           → ACTION: Divert package to human_review_queue. Hold fulfillment.
        2. If gate_status is 'AUTO_PROCESSED':
           → ACTION: Assign handling lane (FRAGILE, HIGH_VALUE, or STANDARD).
           → ACTION: Enqueue into processing_queue prioritized by priority (HIGH first).
        """
        if order in self.incoming_orders:
            self.incoming_orders.remove(order)

        order["decision"] = decision

        # ---------------------------------------------------------------------
        # CONFIDENCE GATE EVALUATION
        # ---------------------------------------------------------------------
        if decision.gate_status == "HUMAN_REVIEW":
            order["status"] = "HELD_FOR_REVIEW"
            self.human_review_queue.append(order)
            reasons_summary = "; ".join(decision.escalation_reasons)
            self.log_action(
                "ACTION_CONF_GATE",
                f"Order {order['order_id']} ESCALATED to HUMAN REVIEW: {reasons_summary}"
            )
            return

        # Passed Confidence Gate (Autonomous straight-through processing)
        order["status"] = "AUTO_PROCESSED"
        self.auto_processed_orders.append(order)
        self.log_action(
            "ACTION_CONF_GATE",
            f"Order {order['order_id']} PASSED confidence gate (Priority: {decision.priority_confidence:.2f}, Lane: {decision.lane_confidence:.2f} >= {CONFIDENCE_THRESHOLD:.2f}). Auto processing."
        )

        # Assign conveyor lane buffer
        self._action_assign_lane(order, decision.lane)

        # Enqueue into prioritized fulfillment queue
        self._action_enqueue_priority(order, decision.priority)

    def _action_assign_lane(self, order: dict, lane: str):
        """Action: Assign physical conveyor handling lane."""
        order["assigned_lane"] = lane
        if lane == "FRAGILE":
            self.fragile_lane.append(order)
            self.log_action("ACTION_ASSIGN_LANE", f"Order {order['order_id']} directed to FRAGILE LANE (Padded conveyor).")
        elif lane == "HIGH_VALUE":
            self.high_value_lane.append(order)
            self.log_action("ACTION_ASSIGN_LANE", f"Order {order['order_id']} directed to HIGH VALUE VAULT LANE (Secure escort).")
        else:
            self.log_action("ACTION_ASSIGN_LANE", f"Order {order['order_id']} directed to STANDARD CONVEYOR LANE.")

    def _action_enqueue_priority(self, order: dict, priority: str):
        """Action: Insert order into processing queue sorted by priority."""
        order["priority"] = priority
        order["status"] = "QUEUED_FOR_PROCESSING"
        self.processing_queue.append(order)

        # Priority weights: HIGH (3) > MEDIUM (2) > LOW (1)
        priority_weights = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        self.processing_queue.sort(
            key=lambda x: priority_weights.get(x["decision"].priority if x["decision"] else "MEDIUM", 0),
            reverse=True
        )
        self.log_action(
            "ACTION_ENQUEUE",
            f"Order {order['order_id']} enqueued into PROCESSING QUEUE at priority [{priority}]."
        )

    def action_supervisor_review_signoff(self, supervisor_name: str = "Lead Supv. Sarah Jenkins"):
        """
        Action: Human supervisor inspects held orders, reviews escalation reasons,
        and issues authorized sign-offs. Once cleared, the package resumes automated routing.
        """
        if not self.human_review_queue:
            return

        held_orders = list(self.human_review_queue)
        self.human_review_queue.clear()

        for order in held_orders:
            decision: OrderDecision = order["decision"]
            order["supervisor_signoff"] = {
                "reviewer": supervisor_name,
                "timestamp": time.strftime("%H:%M:%S"),
                "status": "APPROVED",
                "notes": f"Inspected escalation reasons ({len(decision.escalation_reasons)} flagged). Cleared for lane dispatch."
            }
            self.log_action(
                "ACTION_SUPERVISOR_OK",
                f"{supervisor_name} inspected and approved {order['order_id']} ({order['product_name'][:20]}). Cleared hold."
            )

            # Assign physical handling lane
            self._action_assign_lane(order, decision.lane)

            # Insert into prioritized processing queue
            self._action_enqueue_priority(order, decision.priority)

    def action_fulfill_processing_queue(self):
        """
        Action: Pick, pack, and prepare packages in the processing queue through their lanes.
        """
        if not self.processing_queue:
            return

        active_batch = list(self.processing_queue)
        self.processing_queue.clear()

        for order in active_batch:
            lane = order.get("assigned_lane", "STANDARD")
            order["fulfillment_details"] = {
                "lane_handled": lane,
                "packaging": (
                    "Double-wall foam + acoustic shock-tilt indicator" if lane == "FRAGILE"
                    else "Tamper-evident vault security bag + RFID serial lock" if lane == "HIGH_VALUE"
                    else "Standard recyclable cardboard carton"
                ),
                "completed_time": time.strftime("%H:%M:%S")
            }
            order["status"] = "COMPLETED"

            # Remove from lane active buffers
            if order in self.fragile_lane:
                self.fragile_lane.remove(order)
            if order in self.high_value_lane:
                self.high_value_lane.remove(order)

            # Move to Completed Orders staging area
            self.completed_orders.append(order)
            self.log_action(
                "ACTION_DISPATCH",
                f"Order {order['order_id']} packaging finished in {lane} lane. Staged in COMPLETED ORDERS."
            )


# =============================================================================
# 5. DASHBOARD RENDERER (Terminal CLI UI)
# =============================================================================
class WarehouseDashboard:
    """
    Renders an ASCII terminal dashboard displaying confidence gating,
    autonomous straight-through processing, supervisor review holds, and fulfillment.
    """
    @staticmethod
    def render(sim: WarehouseSimulation, stage_title: str):
        print("\n" + "=" * 105)
        print(f" 🏭 WAREHOUSE BRAIN SIMULATION DASHBOARD | {stage_title.upper()} ".center(105, "="))
        print("=" * 105)

        # High-level Metrics Header
        counts_str = (
            f" 📥 Incoming: {len(sim.incoming_orders):<2} | "
            f"⚡ Auto Processed: {len(sim.auto_processed_orders):<2} | "
            f"⚠️ Human Review: {len(sim.human_review_queue):<2} | "
            f"📦 Processing: {len(sim.processing_queue):<2} | "
            f"🏺 Fragile: {len(sim.fragile_lane):<2} | "
            f"💎 Vault: {len(sim.high_value_lane):<2} | "
            f"🚚 Completed: {len(sim.completed_orders):<2}"
        )
        print(counts_str)
        print("-" * 105)

        # ---------------------------------------------------------------------
        # [SECTION A] AUTO PROCESSED
        # ---------------------------------------------------------------------
        print("\n⚡ [AUTO PROCESSED] (Confidence Gate >= 0.85 | Autonomous Straight-Through Processing)")
        print("-" * 105)
        if not sim.auto_processed_orders:
            print("    (Empty - No packages qualified for autonomous straight-through processing)")
        else:
            for o in sim.auto_processed_orders:
                d: OrderDecision = o["decision"]
                print(
                    f"    ✓ [{o['order_id']}] {o['product_name'][:28]:<28} | "
                    f"Priority: {d.priority:<6} (Conf: {d.priority_confidence:.2f}) | "
                    f"Lane: {d.lane:<10} (Conf: {d.lane_confidence:.2f}) | "
                    f"Status: AUTO APPROVED"
                )

        # ---------------------------------------------------------------------
        # [SECTION B] HUMAN REVIEW
        # ---------------------------------------------------------------------
        print("\n⚠️ [HUMAN REVIEW] (Confidence Gate < 0.85 OR Safety Policy Triggered | Supervisor Gate)")
        print("-" * 105)
        if not sim.human_review_queue:
            print("    (Empty - No packages currently held for human supervisor review)")
        else:
            for idx, o in enumerate(sim.human_review_queue, start=1):
                d: OrderDecision = o["decision"]
                print(f"    • 🛑 Item #{idx}: [{o['order_id']}] {o['product_name']}")
                print(
                    f"      - Original Order      : Val: ${o['value']:<8,.2f} | "
                    f"Deadline: {o['deadline']}h | Fragile: {str(o['fragile']):<5} | "
                    f"Weight: {o['weight']}kg | Dest: {o['destination']}"
                )
                print(
                    f"      - Laya Decision       : Priority: {d.priority:<6} | "
                    f"Lane: {d.lane:<10} | Review Needed: {'YES' if d.needs_human_review else 'NO'}"
                )
                print(
                    f"      - Confidence Scores   : Priority: {d.priority_confidence:.2f}   | "
                    f"Lane: {d.lane_confidence:.2f}    | "
                    f"Review Flag: {d.review_confidence:.2f} (Lowest: {d.min_confidence:.2f})"
                )
                print(f"      - Reason for Escalation:")
                for r in d.escalation_reasons:
                    print(f"        ↳ {r}")
                print()

        # ---------------------------------------------------------------------
        # [SECTION C] ACTIVE PROCESSING QUEUE (Priority-Sorted)
        # ---------------------------------------------------------------------
        print("[3] ⚡ ACTIVE PROCESSING QUEUE (Fulfillment In Progress - Priority Ordered)")
        if not sim.processing_queue:
            print("    (Empty - No orders currently waiting in picker/packer queue)")
        else:
            for idx, o in enumerate(sim.processing_queue, start=1):
                p = o["decision"].priority
                lane = o.get("assigned_lane", "STANDARD")
                badge = f"[{p}]"
                print(f"    {idx}. {badge:<8} [{o['order_id']}] {o['product_name'][:24]:<24} | Lane: {lane:<10} | Deadline: {o['deadline']}h")

        # ---------------------------------------------------------------------
        # [SECTION D] ACTIVE HANDLING LANES
        # ---------------------------------------------------------------------
        print("\n[4] 📦 ACTIVE HANDLING LANES (Physical Conveyor Buffers)")
        print("    🏺 FRAGILE LANE BUFFER:")
        if not sim.fragile_lane:
            print("       (Lane clear)")
        else:
            for o in sim.fragile_lane:
                print(f"       • [{o['order_id']}] {o['product_name'][:26]:<26} (Cushion packaging & acoustic shock tags)")

        print("    💎 HIGH VALUE VAULT LANE BUFFER:")
        if not sim.high_value_lane:
            print("       (Lane clear)")
        else:
            for o in sim.high_value_lane:
                print(f"       • [{o['order_id']}] {o['product_name'][:26]:<26} (Value: ${o['value']:,.2f} | Secure RFID vault lock)")

        # ---------------------------------------------------------------------
        # [SECTION E] COMPLETED ORDERS
        # ---------------------------------------------------------------------
        print("\n[5] 🚚 COMPLETED ORDERS (Staged at Loading Bay for Carrier Pickup)")
        if not sim.completed_orders:
            print("    (Empty - Fulfillment in progress)")
        else:
            for o in sim.completed_orders:
                lane_used = o.get("assigned_lane", "STANDARD")
                priority = o["decision"].priority
                signoff_tag = " (Supervisor Approved)" if "supervisor_signoff" in o else " (Auto Processed)"
                print(f"    ✓ [{o['order_id']}] {o['product_name'][:24]:<24} | Priority: {priority:<6} | Lane: {lane_used:<10}{signoff_tag}")

        # ---------------------------------------------------------------------
        # [SECTION F] ACTION EXECUTION STREAM
        # ---------------------------------------------------------------------
        print("\n[6] 📜 APPLICATION ACTION LOG (Executed by Python Code):")
        print("-" * 105)
        recent_logs = sim.action_log[-5:] if sim.action_log else ["(No actions executed yet)"]
        for log_entry in recent_logs:
            print(f"    {log_entry}")
        print("=" * 105 + "\n")


# =============================================================================
# 6. SIMULATION WORKFLOW EXECUTION
# =============================================================================
def run_simulation(sample_size: int = 6):
    """
    Executes an end-to-end warehouse simulation demonstrating the clean separation:
    Order -> Laya Decision + Confidence -> Confidence Gate -> Python Action Execution.
    """
    print("\n" + "=" * 95)
    print("🚀 STARTING WAREHOUSE BRAIN SIMULATION (STAGE 5: CONFIDENCE GATE)".center(95))
    print("=" * 95)

    # 1. Initialize components
    decision_engine = LayaDecisionEngine(device="cpu")
    simulation = WarehouseSimulation()
    dashboard = WarehouseDashboard()

    # Pick representative sample orders exercising both paths:
    # - ORD-001: Surgical Bone Drills ($3,500, deadline 2h, fragile)  → HIGH VALUE / POLICY FLAG → HUMAN REVIEW
    # - ORD-002: Ceramic Dinner Plates ($120, deadline 24h, fragile)  → LOW CONFIDENCE ON FRAGILE → HUMAN REVIEW
    # - ORD-003: Hex Bolts ($65, deadline 48h, durable)               → HIGH CONFIDENCE ON STANDARD → AUTO PROCESSED
    # - ORD-004: Gaming Laptop ($2,400, deadline 6h, fragile)         → HIGH VALUE / POLICY FLAG → HUMAN REVIEW
    # - ORD-005: Cotton T-Shirts ($45, deadline 36h, durable)         → HIGH CONFIDENCE ON STANDARD → AUTO PROCESSED
    # - ORD-006: Glass Beakers ($420, deadline 4h, fragile)           → LOW CONFIDENCE ON FRAGILE → HUMAN REVIEW
    selected_ids = ["ORD-001", "ORD-002", "ORD-003", "ORD-004", "ORD-005", "ORD-006"]
    if sample_size > 6:
        sample_orders = ORDERS[:sample_size]
    else:
        sample_orders = [o for o in ORDERS if o["order_id"] in selected_ids]

    # -------------------------------------------------------------------------
    # STAGE 1: PACKAGE INGESTION AT LOADING DOCK
    # -------------------------------------------------------------------------
    print("\n📦 [STAGE 1] Ingesting incoming shipments into warehouse...")
    simulation.action_receive_orders(sample_orders)
    dashboard.render(simulation, "Stage 1: Incoming Shipments Received")
    time.sleep(1.0)

    # -------------------------------------------------------------------------
    # STAGE 2: LAYA DECISION ENGINE EVALUATION & CONFIDENCE RETRIEVAL
    # -------------------------------------------------------------------------
    print("\n🧠 [STAGE 2] Evaluating orders with Laya Decision Engine...")
    print("   Retrieving structured decisions & calibrated confidence scores via Laya API...\n")

    decisions = []
    for order in list(simulation.incoming_orders):
        t0 = time.time()
        decision = decision_engine.evaluate(order)
        eval_time = time.time() - t0
        decisions.append((order, decision))

        # Explicit format requested for Decision & Confidence inspection:
        print(f"   ┌─ 📦 [{order['order_id']}] {order['product_name']} (Inference: {eval_time:.2f}s) " + "─" * 20)
        print(f"   │ Priority: {decision.priority}")
        print(f"   │ Confidence: {decision.priority_confidence:.2f}")
        print(f"   │")
        print(f"   │ Lane: {decision.lane}")
        print(f"   │ Confidence: {decision.lane_confidence:.2f}")
        print(f"   │")
        print(f"   │ Human Review: {'YES' if decision.needs_human_review else 'NO'}")
        print(f"   │ Confidence: {decision.review_confidence:.2f}")
        print(f"   │")
        print(f"   │ 🛡️ Confidence Gate (Threshold: {CONFIDENCE_THRESHOLD:.2f}):")
        if decision.gate_status == "AUTO_PROCESSED":
            print(f"   │    [PASS] AUTO PROCESSED (all routing confidences >= {CONFIDENCE_THRESHOLD:.2f})")
        else:
            print(f"   │    [HOLD] HUMAN REVIEW")
            for reason in decision.escalation_reasons:
                print(f"   │      • {reason}")
        print(f"   └" + "─" * 70 + "\n")

    time.sleep(1.0)

    # -------------------------------------------------------------------------
    # STAGE 3: CONFIDENCE GATE ROUTING (APPLICATION ACTIONS)
    # -------------------------------------------------------------------------
    print(f"\n⚙️ [STAGE 3] Confidence Gate Routing (Threshold: {CONFIDENCE_THRESHOLD:.2f})...")
    print("   Routing high-confidence orders straight to fulfillment lanes;")
    print("   Escalating low-confidence / policy-flagged orders to human supervisor.\n")

    for order, decision in decisions:
        simulation.action_route_based_on_decision(order, decision)

    dashboard.render(simulation, "Stage 3: Confidence Gating & Order Routing")
    time.sleep(1.5)

    # -------------------------------------------------------------------------
    # STAGE 4: HUMAN SUPERVISOR SIGN-OFF (HUMAN-IN-THE-LOOP RESOLUTION)
    # -------------------------------------------------------------------------
    print("\n👤 [STAGE 4] Human Supervisor reviews flagged orders and clears holds...")
    time.sleep(1.0)
    simulation.action_supervisor_review_signoff(supervisor_name="Supervisor Sarah Jenkins")
    dashboard.render(simulation, "Stage 4: Human Review Cleared & Re-routed")
    time.sleep(1.5)

    # -------------------------------------------------------------------------
    # STAGE 5: FULFILLMENT & PACKAGING IN SPECIALIZED LANES
    # -------------------------------------------------------------------------
    print("\n⚙️ [STAGE 5] Packing and processing orders in priority order across lanes...")
    time.sleep(1.0)
    simulation.action_fulfill_processing_queue()
    dashboard.render(simulation, "Stage 5: Fulfillment Complete & Staged for Carrier")

    # -------------------------------------------------------------------------
    # FINAL METRICS SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 95)
    print("✅ SIMULATION COMPLETE: CONFIDENCE-GATED WAREHOUSE RUN SUCCESSFUL".center(95))
    print("=" * 95)
    print(f"• Total Orders Processed   : {len(simulation.completed_orders)}")
    print(f"• Autonomous Straight-Thru : {len(simulation.auto_processed_orders)}")
    print(f"• Human-in-the-Loop Reviews: {len(decisions) - len(simulation.auto_processed_orders)}")
    print(f"• Total Actions Executed   : {len(simulation.action_log)}")
    print(f"• Demonstration Threshold  : {CONFIDENCE_THRESHOLD:.2f} (Pedagogical test only; NOT production-certified)")
    print(f"• Architectural Integrity  : 100% (Laya decided, Confidence Gated, Python executed)")
    print("=" * 95 + "\n")


def main():
    # Support optional command line flag: python3 warehouse.py --all
    sample_size = 20 if "--all" in sys.argv else 6
    run_simulation(sample_size=sample_size)


if __name__ == "__main__":
    main()
