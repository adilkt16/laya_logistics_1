# 🏭 Warehouse Brain (learn-laya)

An intelligent, simulated warehouse fulfillment and routing system powered by **[Laya](https://huggingface.co/convaiinnovations/laya)**.

This repository demonstrates the **separation of concerns** between neural decision engines and deterministic business logic:
- **Laya** acts as the *Decision Engine* (pure, read-only, non-autoregressive classification with calibrated probabilities).
- **Python** acts as the *Action Engine* (state mutation, queue management, conveyor routing, supervisor hold gates, and dispatch).

---

## 🏗️ Architecture: Separation of Concerns

```
    WAREHOUSE SHIPMENT (Context / State)
              │
              ▼
    LAYA ROUTER (Pure Decision Engine)
    ├── processing_priority  → HIGH | MEDIUM | LOW
    ├── warehouse_lane       → STANDARD | FRAGILE | HIGH_VALUE
    └── needs_human_review   → True | False
              │
              ▼
    STRUCTURED DECISION (Typed Data Container)
              │
              ▼
    PYTHON SIMULATION RUNTIME (Action Engine)
    ├── Intake Dock
    ├── Human Supervisor Gate
    ├── Lane Conveyor Buffers (Fragile / Vault / Standard)
    ├── Priority Fulfillment Queue
    └── Loading Bay Carrier Dispatch
```

> **Key Rule**: Laya *never* alters state, touches queues, or directly sends packages. It strictly produces typed decisions with calibrated confidence scores. Python standard logic evaluates these decisions and executes deterministic state transitions.

---

## 📁 Repository Structure

| File | Description |
| :--- | :--- |
| **`orders_data.py`** | Synthetic dataset of 20 realistic warehouse shipments with diverse deadlines, monetary values, weights, and fragility flags. |
| **`warehouse_laya.py`** | Minimal working example demonstrating a single Laya structured choice decision (`urgency` classification). |
| **`test_3_orders.py`** | Targeted test script evaluating 3 edge-case scenarios (emergency medical cargo, standard retail shipment, bulk low-priority goods). |
| **`warehouse.py`** | Full end-to-end 6-stage warehouse simulation with terminal dashboard and live action auditing. |
| **`requirements.txt`** | Python package dependencies. |
| **`.gitignore`** | Excludes compiled bytecode, virtual environments, and editor caches. |

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.9+
- Linux, macOS, or Windows

### 2. Installation

Clone this repository and set up a virtual environment:

```bash
# Clone the repository
git clone https://github.com/<your-username>/learn-laya.git
cd learn-laya

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 💻 Running the Scripts

### Full Warehouse Simulation Dashboard
Runs the complete 6-stage lifecycle (Intake → Laya Evaluation → Automated Routing → Human Review Sign-Off → Priority Fulfillment → Loading Bay Dispatch):

```bash
# Run with standard sample set (6 representative orders)
python3 warehouse.py

# Or process all 20 orders in the dataset
python3 warehouse.py --all
```

### Targeted 3-Order Scenario Test
Demonstrates how Laya evaluates emergency cargo, regular retail, and heavy bulk goods:

```bash
python3 test_3_orders.py
```

### Minimal Laya Decision Example
A concise, zero-boilerplate introduction to Laya's `Router.predict()` API:

```bash
python3 warehouse_laya.py
```

---

## 🧠 Decision Schema

In `warehouse.py`, Laya evaluates three decisions simultaneously in a single forward pass:

```python
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
```

---

## 📜 License

This project is licensed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0).
