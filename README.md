---
title: Cakes Warehouse
emoji: 🍰
colorFrom: pink
colorTo: red
sdk: docker
app_port: 7860
pinned: false
---

# 🏭 Warehouse Brain (learn-laya)

An intelligent, simulated warehouse fulfillment and routing system powered by **[Laya](https://huggingface.co/convaiinnovations/laya)**.

This repository demonstrates:
1. **Separation of Concerns**: Laya acts as a pure, read-only decision engine; standard Python code acts as the deterministic action engine.
2. **Confidence-Gated Decisions & Human-in-the-Loop (HITL)**: Using model confidence scores to safely balance autonomous throughput against supervisor inspection.

---

## 🏗️ Architecture: Separation of Concerns & Confidence Gating

```
    WAREHOUSE SHIPMENT (Context / State)
              │
              ▼
    LAYA ROUTER (Pure Neural Decision Engine)
    ├── processing_priority  → HIGH | MEDIUM | LOW        (+ confidence score)
    ├── warehouse_lane       → STANDARD | FRAGILE | VAULT (+ confidence score)
    └── needs_human_review   → True | False               (+ confidence score)
              │
              ▼
    CONFIDENCE GATE (Safety Filter)
    ├── If ALL relevant routing confidences >= 0.85 & no policy flag:
    │   └── ⚡ AUTO PROCESSED (Straight-Through Autonomous Fulfillment)
    └── If ANY confidence < 0.85 OR supervisor review flagged:
        └── ⚠️ HUMAN REVIEW (Supervisor Inspection Hold Gate)
              │
              ▼
    PYTHON SIMULATION RUNTIME (Action Engine)
    ├── Receiving Dock Intake
    ├── Confidence Gate Routing & Audit Logging
    ├── Supervisor Review Sign-Off & Hold Clearance
    ├── Handling Lane Buffers (Fragile / Vault / Standard)
    ├── Priority Fulfillment Queue (Pick & Pack)
    └── Carrier Dispatch Staging Area
```

> **Core Architectural Rule**: Laya *never* alters state, touches queues, or directly sends packages. It strictly produces typed classifications with calibrated probability distributions. Python standard logic evaluates these decisions through a confidence gate and executes state transitions.

---

## 🧠 Confidence in Automated Decision Systems

### ⚠️ Critical Disclaimer: The 0.85 Demonstration Threshold
> In this learning simulation, **`0.85` is strictly an illustrative pedagogical threshold**, NOT a scientifically validated production threshold. A particular confidence number **never guarantees correctness**. In real-world deployments, thresholds must be empirically determined on domain data.

### 1. What Model Confidence Means
Model confidence represents the numerical probability mass that a neural model assigns to its predicted output relative to alternative candidates, given the input context and criteria descriptions. If Laya predicts `Priority: HIGH` with confidence `0.97`, it indicates that 97% of the normalized probability mass is concentrated on "HIGH".

### 2. What Probability Means Here
In Laya's non-autoregressive routing architecture, probability is a normalized mathematical value (between `0.0` and `1.0`) computed from semantic embeddings and similarity metrics across candidate criteria. It is **not** a classical frequentist probability of the physical world (e.g., "if shipped 100 times, 97 times it is urgent"). Rather, it reflects geometric alignment in high-dimensional embedding space between the order's state description and the candidate's criteria.

### 3. Why Confidence is Useful
- **Selective Automation**: Enables systems to separate routine, straightforward decisions from edge cases and ambiguous requests.
- **Risk Mitigation**: High-consequence decisions (e.g., routing expensive surgical lasers or handling breakable laboratory glass) can require higher confidence levels before allowing automated execution.
- **Operational Efficiency**: Supervisors don't need to manually verify every single routine package; they can focus their attention where the model is uncertain.

### 4. Why Confidence Does NOT Mean Certainty
- **Overconfidence & Miscalibration**: Deep neural networks can assign high confidence (e.g., 0.95+) to incorrect predictions, particularly when given noisy, contradictory, or misleading input text.
- **Out-of-Distribution (OOD) Blind Spots**: When presented with order descriptions unlike anything seen during development, a model may confidently force-fit the input into an incorrect label.
- **Ambiguity**: Real-world constraints often overlap (e.g., a package with a 24-hour deadline that contains both durable and delicate sub-items). A high score reflects the model's top guess, not an absolute guarantee of truth.

### 5. Why Thresholds Must Be Evaluated on Real Domain Data
Threshold selection is fundamentally an operational cost-benefit tradeoff:
- **Threshold too high (e.g., 0.99)**: Almost every shipment diverts to human review. The automated system stalls, bottlenecking throughput and increasing labor overhead.
- **Threshold too low (e.g., 0.50)**: High automation speed, but misclassifications slip through (e.g., fragile crystal glassware routed to an unpadded standard conveyor).

Production thresholds require empirical validation on labeled test datasets using:
- **Precision-Recall & ROC Curves**: To measure true positive vs. false positive trade-offs.
- **Cost Matrices**: Weighing the financial/safety cost of an automated misclassification against the labor cost of human inspection.

### 6. How Human-in-the-Loop (HITL) Systems Work
A human-in-the-loop system combines automated throughput with human judgment:
1. **Dual-Path Routing**: High-confidence orders take the fast straight-through path; low-confidence or high-risk orders take the human supervisor path.
2. **Context-Rich Escalation**: When an order is held, the supervisor receives the full original order, Laya's decisions, confidence scores, and explicit reasons for escalation.
3. **Supervisor Sign-Off**: The supervisor validates or overrides the classification and releases the package to fulfillment.
4. **Continuous Learning Loop**: Escalated cases and supervisor resolutions create a gold-standard dataset for tuning prompt criteria and evaluating future model versions.

---

## 📁 Repository Structure

| File | Description |
| :--- | :--- |
| **`warehouse.py`** | End-to-end 5-stage simulation with Confidence Gate, Decision/Confidence reporting, terminal dashboard, and action auditing. |
| **`orders_data.py`** | Synthetic dataset of 20 realistic warehouse shipments with diverse deadlines, monetary values, weights, and fragility flags. |
| **`warehouse_laya.py`** | Minimal working example demonstrating a single Laya structured choice decision (`urgency` classification). |
| **`test_3_orders.py`** | Targeted test script evaluating 3 edge-case scenarios (emergency cargo, standard retail, bulk goods). |
| **`requirements.txt`** | Python dependencies (`laya>=0.3.22`). |

---

## 💻 Running the Scripts

### Full Warehouse Simulation Dashboard
Runs the complete 5-stage lifecycle (Intake → Laya Evaluation + Confidence → Confidence Gate Routing → Human Supervisor Review → Priority Fulfillment & Carrier Dispatch):

```bash
# Run with standard sample set (6 representative orders exercising all queues)
python3 warehouse.py

# Or process all 20 orders in the dataset
python3 warehouse.py --all
```

### Inspecting Decision & Confidence Outputs
During Stage 2 of `warehouse.py`, every order outputs its typed decisions alongside its calibrated confidence scores:

```text
Priority: HIGH
Confidence: 0.97

Lane: HIGH_VALUE
Confidence: 0.91

Human Review: YES
Confidence: 0.83
```

### Dashboard Sections: AUTO PROCESSED vs. HUMAN REVIEW
In Stage 3, the dashboard categorizes shipments into:
- **`AUTO PROCESSED`**: Shipments whose decision confidences meet or exceed `0.85` with no policy triggers.
- **`HUMAN REVIEW`**: Shipments held for supervisor inspection, displaying:
  - Original order details (Value, Deadline, Fragility, Weight, Destination)
  - Laya's decision (Priority, Lane, Review Need)
  - Confidence scores for all dimensions
  - Explicit reason for escalation (e.g., low lane confidence or supervisor policy flag)

---

## 📜 License

This project is licensed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0).
