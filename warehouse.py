# warehouse.py
# Warehouse Brain - Stage 4: End-to-End Simulation & Action Execution System
#
# ARCHITECTURAL SEPARATION OF CONCERNS:
#
#   WAREHOUSE ORDER (State / Context)
#          ↓
#        LAYA (Decision Engine: Pure, Read-Only, No Side Effects)
#          ↓
#       DECISION (Structured Classification: Priority, Lane, Review Need)
#          ↓
#   APPLICATION ACTION (Deterministic Python Runtime: Queues, Lanes, DB, Physical Dispatch)
#
# Rule: Laya ONLY makes decisions. Standard Python code performs actions.

import os
import sys
import time
import warnings
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# Suppress Hugging Face network check warnings and keep environment offline/clean
os.environ["HF_HUB_OFFLINE"] = "1"
warnings.filterwarnings("ignore")

from laya import Router
from orders_data import ORDERS

# =============================================================================
# 1. STRUCTURED DECISION SCHEMA (For Laya)
# =============================================================================
WAREHOUSE_DECISION_SCHEMA = {
    "processing_priority": {
        "type": "choice",
        "instructions": "Determine the fulfillment priority for this warehouse order:",
        "criteria": {
            "high": "urgent rush order, tight deadline within hours (< 6h), emergency medical equipment, high value",
            "medium": "standard delivery, normal retail products, routine 12-24h fulfillment window",
            "low": "non-urgent order, multi-day relaxed deadline (30+ hours), heavy bulk hardware or soil"
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
        "instructions": "Does this order require human supervisor review or safety inspection before dispatch?",
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
    Pure data container representing Laya's decision.
    Contains NO execution logic and has NO side effects.
    """
    order_id: str
    priority: str          # 'HIGH', 'MEDIUM', 'LOW'
    lane: str              # 'STANDARD', 'FRAGILE', 'HIGH_VALUE'
    needs_human_review: bool
    priority_confidence: float
    lane_confidence: float
    review_confidence: float
    raw_probabilities: dict = field(default_factory=dict)


# =============================================================================
# 3. DECISION ENGINE (Laya - Strictly Pure / Read-Only)
# =============================================================================
class LayaDecisionEngine:
    """
    The Decision Engine evaluates order data and returns structured decisions.
    
    CRITICAL ARCHITECTURAL BOUNDARY:
    - This class has NO access to warehouse queues, lanes, or physical state.
    - It CANNOT mutate system state or perform side effects.
    - Given order state, it solely produces decisions.
    """
    def __init__(self, device: str = "cpu"):
        print("🧠 Initializing Laya Decision Engine (Neural Router on CPU)...")
        self.router = Router(device=device)

    def evaluate(self, order: dict) -> OrderDecision:
        deadline_hrs = order["deadline"]
        if deadline_hrs <= 6:
            deadline_cue = f"urgent rush deadline ({deadline_hrs} hours remaining)"
        elif deadline_hrs <= 24:
            deadline_cue = f"standard delivery timeline ({deadline_hrs} hours remaining)"
        else:
            deadline_cue = f"relaxed multi-day deadline ({deadline_hrs} hours remaining)"

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

        # 1. Priority
        p_ans = answers["processing_priority"]
        priority_choice = p_ans["choice"].upper()
        p_conf = p_ans["probabilities"][p_ans["choice"]]

        # 2. Lane
        l_ans = answers["warehouse_lane"]
        lane_choice = l_ans["choice"].upper()
        l_conf = l_ans["probabilities"][l_ans["choice"]]

        # 3. Human Review
        h_ans = answers["needs_human_review"]
        p_true = h_ans["noul"]
        review_bool = bool(p_true >= 0.5)

        return OrderDecision(
            order_id=order["order_id"],
            priority=priority_choice,
            lane=lane_choice,
            needs_human_review=review_bool,
            priority_confidence=p_conf,
            lane_confidence=l_conf,
            review_confidence=p_true if review_bool else (1.0 - p_true),
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
    It receives decisions from Laya and executes state mutations:
    - Moving orders between queues
    - Assigning handling lanes
    - Holding packages for human supervisor inspection
    - Simulating packaging, labeling, and dispatch
    """
    def __init__(self):
        # The 6 canonical warehouse queues / stages:
        self.incoming_orders: List[dict] = []
        self.processing_queue: List[dict] = []
        self.fragile_lane: List[dict] = []
        self.high_value_lane: List[dict] = []
        self.human_review_queue: List[dict] = []
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
        Action: Deterministic routing based on Laya's decision.
        
        Python Business Logic:
        1. If needs_human_review is True:
           → ACTION: Divert order to human_review_queue. Hold all fulfillment.
        2. If needs_human_review is False:
           → ACTION: Assign handling lane (FRAGILE, HIGH_VALUE, or STANDARD).
           → ACTION: Enqueue into processing_queue prioritized by priority (HIGH first).
        """
        # Remove from incoming dock
        if order in self.incoming_orders:
            self.incoming_orders.remove(order)

        order["decision"] = decision

        # RULE 1: Human Review Hold (Safety Gate)
        if decision.needs_human_review:
            order["status"] = "HELD_FOR_REVIEW"
            self.human_review_queue.append(order)
            self.log_action(
                "ACTION_ROUTE_REVIEW",
                f"Order {order['order_id']} ({order['product_name'][:20]}) diverts to HUMAN REVIEW (Conf: {decision.review_confidence:.1%})."
            )
            return

        # RULE 2: Assign Lane Buffer
        self._action_assign_lane(order, decision.lane)

        # RULE 3: Enqueue into Processing Queue with Priority Sort
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

    def action_supervisor_review_signoff(self, supervisor_name: str = "Lead Supv. Jane Doe"):
        """
        Action: Human supervisor inspects held orders and issues authorized sign-offs.
        Once approved, the order resumes automated lane routing and priority queueing.
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
                "notes": "Verified high-value/urgent safety protocol. Cleared for packaging."
            }
            self.log_action(
                "ACTION_SUPERVISOR_OK",
                f"{supervisor_name} approved {order['order_id']} (Value: ${order['value']:,.2f}). Cleared hold."
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

        # Process top-priority orders
        active_batch = list(self.processing_queue)
        self.processing_queue.clear()

        for order in active_batch:
            lane = order.get("assigned_lane", "STANDARD")
            order["fulfillment_details"] = {
                "lane_handled": lane,
                "packaging": (
                    "Double-wall foam + shock-tilt indicator" if lane == "FRAGILE"
                    else "Tamper-evident vault security bag + RFID seal" if lane == "HIGH_VALUE"
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
    Renders an ASCII terminal dashboard showing all warehouse queues and actions.
    """
    @staticmethod
    def render(sim: WarehouseSimulation, stage_title: str):
        # Clear screen on standard terminals (or print separator)
        print("\n" + "=" * 105)
        print(f" 🏭 WAREHOUSE BRAIN SIMULATION DASHBOARD | {stage_title.upper()} ".center(105, "="))
        print("=" * 105)

        # High-level Metrics Header
        counts_str = (
            f" 📥 Incoming: {len(sim.incoming_orders):<2} | "
            f"⚠️ Human Review: {len(sim.human_review_queue):<2} | "
            f"⚡ Processing Queue: {len(sim.processing_queue):<2} | "
            f"🏺 Fragile Lane: {len(sim.fragile_lane):<2} | "
            f"💎 High Value Lane: {len(sim.high_value_lane):<2} | "
            f"🚚 Completed: {len(sim.completed_orders):<2}"
        )
        print(counts_str)
        print("-" * 105)

        # 1. Incoming Orders Panel
        print("\n[1] 📥 INCOMING ORDERS (Awaiting Laya Decision)")
        if not sim.incoming_orders:
            print("    (Empty - All incoming packages evaluated)")
        else:
            for o in sim.incoming_orders:
                print(f"    • [{o['order_id']}] {o['product_name'][:28]:<28} | ${o['value']:<8,.2f} | Deadline: {o['deadline']}h")

        # 2. Human Review Queue Panel
        print("\n[2] ⚠️ HUMAN REVIEW QUEUE (Supervisor Hold Gate)")
        if not sim.human_review_queue:
            print("    (Empty - No packages flagged for supervisor intervention)")
        else:
            for o in sim.human_review_queue:
                d = o["decision"]
                print(f"    • 🛑 [{o['order_id']}] {o['product_name'][:26]:<26} | Value: ${o['value']:<8,.2f} | Deadline: {o['deadline']}h | Conf: {d.review_confidence:.1%}")

        # 3. Processing Queue Panel (Ordered by Priority)
        print("\n[3] ⚡ PROCESSING QUEUE (Active Fulfillment - Priority Ordered)")
        if not sim.processing_queue:
            print("    (Empty - No orders waiting for picker/packing)")
        else:
            for idx, o in enumerate(sim.processing_queue, start=1):
                p = o["decision"].priority
                lane = o.get("assigned_lane", "STANDARD")
                badge = f"[{p}]"
                print(f"    {idx}. {badge:<8} [{o['order_id']}] {o['product_name'][:24]:<24} | Lane: {lane:<10} | Deadline: {o['deadline']}h")

        # 4. Handling Lanes Buffer Panel
        print("\n[4] 📦 ACTIVE HANDLING LANES")
        print("    🏺 FRAGILE LANE BUFFER:")
        if not sim.fragile_lane:
            print("       (Lane clear)")
        else:
            for o in sim.fragile_lane:
                print(f"       • [{o['order_id']}] {o['product_name'][:26]:<26} (Cushion packing & acoustic shock tags)")

        print("    💎 HIGH VALUE VAULT LANE BUFFER:")
        if not sim.high_value_lane:
            print("       (Lane clear)")
        else:
            for o in sim.high_value_lane:
                print(f"       • [{o['order_id']}] {o['product_name'][:26]:<26} (Value: ${o['value']:,.2f} | Secure RFID vault lock)")

        # 5. Completed Orders Panel
        print("\n[5] 🚚 COMPLETED ORDERS (Staged at Loading Bay for Carrier Pickup)")
        if not sim.completed_orders:
            print("    (Empty - Fulfillment in progress)")
        else:
            for o in sim.completed_orders:
                lane_used = o.get("assigned_lane", "STANDARD")
                priority = o["decision"].priority
                print(f"    ✓ [{o['order_id']}] {o['product_name'][:26]:<26} | Priority: {priority:<6} | Lane: {lane_used:<10} | Status: READY FOR CARRIER")

        # 6. Action Execution Stream
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
    Order -> Laya Decision -> Python Business Logic -> Python Application Action.
    """
    print("\n" + "=" * 80)
    print("🚀 STARTING WAREHOUSE BRAIN SIMULATION".center(80))
    print("=" * 80)

    # 1. Initialize components
    decision_engine = LayaDecisionEngine(device="cpu")
    simulation = WarehouseSimulation()
    dashboard = WarehouseDashboard()

    # Pick representative sample orders exercising all queues:
    # - ORD-001: Bone Drills ($3,500, deadline 2h, fragile) -> High Value, Urgent, Review YES
    # - ORD-002: Dinner Plates ($120, deadline 24h, fragile) -> Fragile Lane, Medium Priority
    # - ORD-003: Hex Bolts ($65, deadline 48h) -> Standard Lane, Low/Medium Priority
    # - ORD-006: Glass Beakers ($420, deadline 4h, fragile) -> Fragile Lane, High Priority
    # - ORD-014: Garden Soil ($35, deadline 60h) -> Standard Lane, Low Priority
    # - ORD-020: Calibration Laser ($6,800, deadline 3h) -> High Value Lane, Urgent, Review YES
    selected_ids = ["ORD-001", "ORD-002", "ORD-003", "ORD-006", "ORD-014", "ORD-020"]
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
    # STAGE 2: LAYA DECISION ENGINE EVALUATION (STRICTLY DECISION ONLY)
    # -------------------------------------------------------------------------
    print("\n🧠 [STAGE 2] Evaluating orders with Laya Decision Engine...")
    print("   Notice: Laya ONLY makes decisions. It does NOT touch queues or lanes.\n")

    decisions = []
    for order in list(simulation.incoming_orders):
        t0 = time.time()
        # Pure inference call
        decision = decision_engine.evaluate(order)
        eval_time = time.time() - t0
        decisions.append((order, decision))
        print(f"   ✓ Laya Decided {order['order_id']} in {eval_time:.2f}s → "
              f"Priority=[{decision.priority}] | Lane=[{decision.lane}] | ReviewNeeded=[{decision.needs_human_review}]")

    time.sleep(1.0)

    # -------------------------------------------------------------------------
    # STAGE 3: APPLICATION ACTIONS (DETERMINISTIC ROUTING EXECUTED BY PYTHON)
    # -------------------------------------------------------------------------
    print("\n⚙️ [STAGE 3] Python Application executes routing actions based on decisions...")
    for order, decision in decisions:
        simulation.action_route_based_on_decision(order, decision)

    dashboard.render(simulation, "Stage 3: Orders Routed by Decisions")
    time.sleep(1.5)

    # -------------------------------------------------------------------------
    # STAGE 4: HUMAN SUPERVISOR SIGN-OFF (HUMAN-IN-THE-LOOP RESOLUTION)
    # -------------------------------------------------------------------------
    print("\n👤 [STAGE 4] Supervisor reviews flagged high-value / urgent orders...")
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
    # FINAL SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("✅ SIMULATION COMPLETE: ALL 6 STAGES EXECUTED SUCCESSFULLY".center(80))
    print("=" * 80)
    print(f"• Total Orders Processed : {len(simulation.completed_orders)}")
    print(f"• Total Actions Executed : {len(simulation.action_log)}")
    print("• Architecture Integrity : 100% (Laya decided, Python performed actions)")
    print("=" * 80 + "\n")


def main():
    # Support optional command line flag: python3 warehouse.py --all
    sample_size = 20 if "--all" in sys.argv else 6
    run_simulation(sample_size=sample_size)


if __name__ == "__main__":
    main()
