# ESML — Event Storming Markup Language

## Specification Draft v0.2.0

**Authors:** Marden Neubert & Joseph Yoder

**Date:** March 2026

**Purpose:** A YAML-based format for high-fidelity, machine-readable representation of Event Storming boards.

---

## 1. Design Goals

1. **High-fidelity board transcription, not interpretation.** ESML captures what is *on the board* — the stickies, their spatial relationships, their groupings. Domain interpretation (bounded contexts, subdomain classification, strategic patterns) belongs downstream in domain modeling, not here.

2. **Verifiable against the source image.** Every element carries provenance metadata linking it to a region in the original board image, enabling automated or human verification.

3. **LLM-friendly.** YAML format, consistent naming conventions, flat-where-possible structures, inline examples. An LLM should be able to produce valid ESML from a board photo without additional tooling.

4. **Human-readable and editable.** A domain expert should be able to read and correct an ESML file without technical training.

5. **Variation-aware.** Supports Big Picture, Process Modeling, and Design Level Event Storming boards through a single schema with optional sections.

---

## 2. Canonical Event Storming Elements

Based on Alberto Brandolini's original formulation and the [ddd-crew Event Storming Glossary & Cheat Sheet](https://github.com/ddd-crew/eventstorming-glossary-cheat-sheet), the following elements may appear on an Event Storming board.

### 2.1 Elements Present in All Variations

| Element | Sticky Color | Description |
|---------|-------------|-------------|
| **Domain Event** | Orange | Something that happened that is relevant to the domain. Written in past tense. The foundational element of all Event Storming. |
| **Hotspot** | Neon Pink (tilted) | An unresolved question, conflict, inconsistency, or point of contention. Placed by the facilitator or any participant to flag areas needing further discussion. |
| **Actor** | Small Yellow | A person, role, team, or department that initiates an action or is involved around a group of domain events. |

### 2.2 Big Picture Elements

| Element | Sticky Color | Description |
|---------|-------------|-------------|
| **External System** | Wide Pink | A deployable IT system (anything from a spreadsheet to a microservice) that participates in the domain flow. |
| **Opportunity** | Green | A positive insight or improvement idea identified during exploration. Counterpart to Hotspots. |
| **Value** | Red (negative) / Green (positive, small) | Marks where business value is created, captured, or destroyed. |
| **Pivotal Event** | Orange (marked/highlighted) | A domain event of exceptional significance that typically marks a phase transition in the business flow. Used to identify natural boundaries. |
| **Swimlane** | (structural, not a sticky) | A horizontal division on the board, typically assigned to an actor or department, to organize parallel flows. |
| **Group** | (structural — a boundary drawn around stickies) | A spatial clustering of related stickies, often a first indicator of a candidate bounded context. NOT a bounded context; that is an interpretation for downstream modeling. |

### 2.3 Process Modeling Elements (adds to Big Picture)

| Element | Sticky Color | Description |
|---------|-------------|-------------|
| **Command** | Blue | A decision, action, or intent. Represents something an actor or policy asks the system to do. Written in imperative form. |
| **Policy** | Large Lilac/Purple | An automation rule following the pattern "Whenever [Event] happens, then [Command/Action]." Also called reactor, rule, or eventual business constraint. |
| **Read Model** | Green | Information that an actor needs to see before making a decision (issuing a command). Represents a view or query of the current state. |

### 2.4 Design Level Elements (adds to Process Modeling)

| Element | Sticky Color | Description |
|---------|-------------|-------------|
| **Aggregate** | Large Yellow | A consistency and decision boundary. The part of the domain model that receives commands, enforces invariants, and produces domain events. Named with a noun. |
| **Constraint** | Large Yellow (alt.) | A business rule or restriction that must be satisfied for a command to succeed within an aggregate. Sometimes written on the aggregate sticky itself. |
| **UI/UX Mockup** | White | A sketch of the user interface that displays a read model or captures input for a command. |

### 2.5 Canonical Flow Pattern (Design Level)

The canonical left-to-right flow on a Design Level board follows this pattern:

```
                  ┌────────────┐
                  │ Read Model │ (green)
                  │  (view)    │
                  └─────┬──────┘
                        │ informs
                        ▼
┌─────────┐      ┌───────────┐      ┌─────────────┐      ┌──────────────┐
│  Actor  │─────▶│  Command  │─────▶│  Aggregate  │─────▶│ Domain Event │
│ (yellow)│      │  (blue)   │      │  (yellow)   │      │  (orange)    │
└─────────┘      └───────────┘      └─────────────┘      └──────┬───────┘
                                                                 │
                      ┌──────────────────────────────────────────┤
                      │                                          │
                      ▼                                          ▼
               ┌────────────┐                            ┌─────────────┐
               │   Policy   │──triggers──▶ Command       │   External  │
               │  (lilac)   │                            │   System    │
               └────────────┘                            │   (pink)    │
                                                         └─────────────┘
```

Alternative initiators (instead of Actor):
- A **Policy** can trigger a Command (automated reaction to an event).
- An **External System** can raise a Domain Event directly.

---

## 3. ESML YAML Schema

### 3.1 Document Envelope

```yaml
esml: "0.2.0"                        # REQUIRED — ESML specification version
board:                                # REQUIRED — metadata about the board
  title: "string"                     # REQUIRED — workshop or board title
  variation: big_picture              # REQUIRED — one of: big_picture,
                                      #   process_modeling, design_level
  date: "YYYY-MM-DD"                  # OPTIONAL — date of the workshop
  facilitator: "string"               # OPTIONAL
  participants:                       # OPTIONAL
    - "string"
  notes: "string"                     # OPTIONAL — free-form notes

sources:                              # REQUIRED — source images of the board
  - id: src-001                       # REQUIRED — unique source identifier
    file: "board-photo-1.jpg"         # REQUIRED — filename or path
    width_px: 4000                    # OPTIONAL — image dimensions in pixels
    height_px: 3000                   # OPTIONAL
```

### 3.2 Provenance: The `origin` Field

Every element in ESML carries an `origin` field that links it to a region in the source image. This enables verification — a human or tool can check whether the transcribed element matches what's actually on the board.

```yaml
origin:                               # REQUIRED on every element
  source: src-001                     # REQUIRED — references a source id
  bbox: [x, y, w, h]                 # REQUIRED — bounding box in pixels
                                      #   (top-left corner x, y; width, height)
  color_observed: "#FF9933"           # REQUIRED — the actual color detected
  text_confidence: 0.92               # REQUIRED — OCR/reading confidence 0.0–1.0
  text_raw: "Ordr Placd"             # OPTIONAL — the raw OCR text before
                                      #   normalization (useful for audit)
```

**Design rationale:**
- `color_observed` captures the *actual* sticky color, not the canonical one. This allows verification of element type classification (e.g., "you called this a Command, but the observed color is orange, not blue — was it misclassified?").
- `text_raw` preserves the OCR output before the interpreter normalized it to proper English. Enables auditing of interpretation choices.
- `text_confidence` applies to the text reading, not the element classification. A high-confidence reading on a miscolored sticky is still a useful signal.

### 3.3 Element ID Conventions

All IDs use kebab-case with a type prefix:

| Element Type | Prefix | Example |
|---|---|---|
| Domain Event | `evt-` | `evt-order-placed` |
| Command | `cmd-` | `cmd-place-order` |
| Actor | `act-` | `act-customer` |
| Aggregate | `agg-` | `agg-order` |
| Policy | `pol-` | `pol-payment-required` |
| Read Model | `rm-` | `rm-order-summary` |
| External System | `sys-` | `sys-payment-gateway` |
| Hotspot | `hot-` | `hot-delivery-radius-unclear` |
| Opportunity | `opp-` | `opp-loyalty-program` |
| Constraint | `cst-` | `cst-minimum-order-value` |
| Group | `grp-` | `grp-ordering` |
| Pivotal Event | (uses `evt-` with `pivotal: true`) | |

### 3.4 Core Elements

#### Domain Events

```yaml
events:                               # REQUIRED — the backbone of the board
  - id: evt-order-placed              # REQUIRED — unique, prefixed
    name: "Order Placed"              # REQUIRED — past tense, human-readable
    sequence: 5                       # REQUIRED — ordinal position on the
                                      #   timeline (left-to-right), starting at 1
    pivotal: false                    # OPTIONAL — true if marked as pivotal
    group: grp-ordering               # OPTIONAL — which group this belongs to
    origin: { ... }                   # REQUIRED — provenance (see 3.2)
```

**The `sequence` field** captures the left-to-right temporal ordering on the board. This is critical information that the board's spatial layout encodes but that would be lost in an unordered list. Sequence numbers are ordinal (relative order), not absolute positions. Multiple events may share a sequence number if they are vertically aligned (concurrent).

#### Commands

```yaml
commands:                             # OPTIONAL — present in process_modeling
                                      #   and design_level variations
  - id: cmd-place-order
    name: "Place Order"               # Imperative form
    sequence: 4                       # Position on timeline (before its event)
    initiated_by:                     # WHO or WHAT triggers this command
      actor: act-customer             # Either actor OR policy, not both
      # OR: policy: pol-auto-reorder
    targets:                          # WHAT receives this command
      aggregate: agg-order            # Either aggregate OR external_system
      # OR: external_system: sys-payment-gateway
    emits:                            # Domain events this command produces
      - evt-order-placed              #   (through the aggregate)
    group: grp-ordering
    origin: { ... }
```

**Design note on `initiated_by` and `targets`:** These fields capture the relationships *as observed on the board* — which actor sticky is placed next to which command, which aggregate sits between the command and the event. The interpreter should populate these from spatial proximity, not from inference.

#### Actors

```yaml
actors:
  - id: act-customer
    name: "Customer"
    group: grp-ordering               # OPTIONAL
    origin: { ... }
```

#### Aggregates (Design Level only)

```yaml
aggregates:                           # OPTIONAL — present in design_level only
  - id: agg-order
    name: "Order"
    receives:                         # Commands this aggregate handles
      - cmd-place-order
      - cmd-cancel-order
    produces:                         # Events this aggregate emits
      - evt-order-placed
      - evt-order-cancelled
    constraints:                      # OPTIONAL — business rules observed on
      - cst-minimum-order-value       #   or near the aggregate sticky
    group: grp-ordering
    origin: { ... }
```

**Design note:** The `receives`/`produces` lists are the aggregate's *public interface as visible on the board*. They capture which command stickies are placed to the left and which event stickies to the right of the aggregate. This is high-fidelity transcription: the board spatially encodes these relationships.

#### Policies

```yaml
policies:
  - id: pol-payment-required
    name: "Payment Required After Order"
    rule: "Whenever Order Placed, then Initiate Payment"
                                      # OPTIONAL — natural-language rule in
                                      #   "Whenever X, then Y" form
    listens_to:                       # Events that trigger this policy
      - evt-order-placed
    triggers:                         # Commands this policy initiates
      - cmd-initiate-payment
    group: grp-ordering
    origin: { ... }
```

#### Read Models

```yaml
read_models:
  - id: rm-order-summary
    name: "Order Summary"
    description: "Current order status and items"
                                      # OPTIONAL — what info is displayed
    informs:                          # OPTIONAL — which command decisions
      - cmd-confirm-order             #   this read model supports
    subscribes_to:                    # OPTIONAL — events that update this
      - evt-order-placed              #   read model
      - evt-item-added
    group: grp-ordering
    origin: { ... }
```

#### External Systems

```yaml
external_systems:
  - id: sys-payment-gateway
    name: "Payment Gateway"
    receives:                         # OPTIONAL — commands sent to this system
      - cmd-initiate-payment
    produces:                         # OPTIONAL — events raised by this system
      - evt-payment-confirmed
      - evt-payment-failed
    group: grp-payment
    origin: { ... }
```

### 3.5 Annotation Elements

These elements annotate or organize the board but don't participate in the domain flow.

#### Hotspots

```yaml
hotspots:
  - id: hot-delivery-radius-unclear
    name: "Delivery radius policy unclear"
    description: "No agreement on maximum delivery distance"
                                      # OPTIONAL — expanded description
    near:                             # OPTIONAL — which elements this hotspot
      - evt-delivery-requested        #   is placed near on the board
    origin: { ... }
```

#### Opportunities (Big Picture)

```yaml
opportunities:
  - id: opp-loyalty-program
    name: "Loyalty program for repeat customers"
    near:
      - evt-order-delivered
    origin: { ... }
```

#### Values (Big Picture)

```yaml
values:
  - id: val-revenue-capture
    name: "Revenue captured"
    sentiment: positive               # positive | negative
    near:
      - evt-payment-confirmed
    origin: { ... }
```

#### Constraints (Design Level)

```yaml
constraints:
  - id: cst-minimum-order-value
    name: "Minimum order value $10"
    rule: "Order total must be >= $10"
                                      # OPTIONAL — natural-language rule
    applies_to:                       # Which aggregate(s) enforce this
      - agg-order
    origin: { ... }
```

#### UI/UX Mockups (Design Level)

```yaml
mockups:
  - id: ux-order-form
    name: "Order Form"
    description: "Pizza selection and customization interface"
    displays:                         # OPTIONAL — which read model it shows
      - rm-menu
    captures:                         # OPTIONAL — which command it feeds
      - cmd-place-order
    origin: { ... }
```

### 3.6 Structural Elements

#### Groups

Groups tend to become Bounded Contexts as the modeling evolves. However, at this stage, we still cannot call them Bounded Contexts.

```yaml
groups:                               # OPTIONAL — spatial clusters on the board
  - id: grp-ordering
    name: "Ordering"                  # The label on the boundary, if any
    description: "Customer order flow from selection to placement"
                                      # OPTIONAL
    origin:                           # The boundary/border region on the board
      source: src-001
      bbox: [100, 50, 1200, 800]      # The bounding region of the entire group
      color_observed: "#000000"       # Border color, if visible
      text_confidence: 0.90
```

#### Swimlanes

```yaml
swimlanes:                            # OPTIONAL — horizontal divisions
  - id: lane-kitchen
    name: "Kitchen"
    actor: act-kitchen-staff          # OPTIONAL — which actor owns this lane
    origin: { ... }
```

### 3.7 Completeness and Confidence

#### Unreadable or Uncertain Elements

When the interpreter detects a sticky but cannot read or classify it with confidence, it should still be captured:

```yaml
unresolved:
  - id: unresolved-001
    suspected_type: event             # Best guess: event | command | actor |
                                      #   aggregate | policy | read_model |
                                      #   external_system | hotspot | unknown
    text_raw: "Pzz Dlvrd?"           # Whatever OCR could extract
    notes: "Partially obscured sticky in lower right of board"
    origin: { ... }                   # Provenance is especially important here
```

#### Confidence Defaults

```yaml
confidence_defaults:                  # OPTIONAL — board-level confidence notes
  overall_text_extraction: 0.87       # Average OCR confidence across all elements
  overall_classification: 0.82        # Average confidence in element type
                                      #   assignment (color → type)
  notes: "Board was well-lit with clearly separated stickies.
          Some overlap in the Payment group made readings less confident."
```

---

## 4. Variation Rules

Not all element types are expected in all Event Storming variations. The `board.variation` field determines which sections are valid:

| Section | `big_picture` | `process_modeling` | `design_level` |
|---------|:---:|:---:|:---:|
| `events` | REQUIRED | REQUIRED | REQUIRED |
| `actors` | optional | optional | optional |
| `hotspots` | optional | optional | optional |
| `groups` | optional | optional | optional |
| `swimlanes` | optional | optional | optional |
| `external_systems` | optional | optional | optional |
| `opportunities` | optional | — | — |
| `values` | optional | — | — |
| `commands` | — | optional | optional |
| `policies` | — | optional | optional |
| `read_models` | — | optional | optional |
| `aggregates` | — | — | optional |
| `constraints` | — | — | optional |
| `mockups` | — | — | optional |
| `unresolved` | optional | optional | optional |

**"—"** means the section is not expected for that variation. If present, a validator should emit a warning (not an error — boards in practice often mix elements across variations).

---

## 5. Validation Rules

An ESML document is valid if:

1. It is valid YAML 1.2.
2. `esml` version field is present.
3. `board` section is present with `title` and `variation`.
4. At least one `sources` entry exists.
5. At least one `events` entry exists (a board without events is not an Event Storming board).
6. Every `id` is globally unique across all sections.
7. Every cross-reference (`group`, `actor`, `policy`, `aggregate`, `external_system`, items in `listens_to`, `triggers`, `emits`, `receives`, `produces`, `subscribes_to`, `informs`, `near`, `applies_to`, `displays`, `captures`) resolves to an existing element ID.
8. Every element has a valid `origin` with a `source` that references an existing source ID.
9. ID prefixes match element types (e.g., `evt-` for events, `cmd-` for commands).
10. `initiated_by` on a command specifies either `actor` or `policy`, not both.
11. `targets` on a command specifies either `aggregate` or `external_system`, not both.

**Warnings** (non-fatal):
- Events without a `sequence` value.
- Commands without `initiated_by` or `targets` (common when the board is incomplete).
- Elements present that don't match the declared `variation` (see Section 4).
- `text_confidence` below 0.5 on any element.
- Groups referenced by elements but not defined in the `groups` section.

---

## 6. Complete Example: Joe's Pizza (Design Level)

```yaml
esml: "0.2.0"

board:
  title: "Joe's Pizza — Design Level Event Storming"
  variation: design_level
  date: "2025-08-12"
  facilitator: "Marden Neubert"
  participants:
    - "Joseph Yoder"
    - "Marden Neubert"
  notes: "Focused on the ordering and payment flow."

sources:
  - id: src-001
    file: "joes-pizza-event-storming-board.png"
    width_px: 4000
    height_px: 3000

groups:
  - id: grp-ordering
    name: "Ordering"
    origin:
      source: src-001
      bbox: [50, 50, 1500, 900]
      color_observed: "#000000"
      text_confidence: 0.95
  - id: grp-kitchen
    name: "Kitchen"
    origin:
      source: src-001
      bbox: [1600, 50, 1200, 900]
      color_observed: "#000000"
      text_confidence: 0.93
  - id: grp-delivery
    name: "Delivery"
    origin:
      source: src-001
      bbox: [2850, 50, 1100, 900]
      color_observed: "#000000"
      text_confidence: 0.91

actors:
  - id: act-customer
    name: "Customer"
    group: grp-ordering
    origin:
      source: src-001
      bbox: [80, 100, 140, 100]
      color_observed: "#FFEB3B"
      text_confidence: 0.94
  - id: act-kitchen-staff
    name: "Kitchen Staff"
    group: grp-kitchen
    origin:
      source: src-001
      bbox: [1650, 100, 160, 100]
      color_observed: "#FFEB3B"
      text_confidence: 0.88
  - id: act-driver
    name: "Delivery Driver"
    group: grp-delivery
    origin:
      source: src-001
      bbox: [2900, 100, 170, 100]
      color_observed: "#FFEB3B"
      text_confidence: 0.90

events:
  - id: evt-order-requested
    name: "Order Requested"
    sequence: 1
    group: grp-ordering
    origin:
      source: src-001
      bbox: [200, 300, 130, 70]
      color_observed: "#FF9933"
      text_confidence: 0.95
  - id: evt-pizza-type-selected
    name: "Pizza Type Selected"
    sequence: 2
    group: grp-ordering
    origin:
      source: src-001
      bbox: [350, 300, 150, 70]
      color_observed: "#FF9933"
      text_confidence: 0.92
  - id: evt-delivery-info-entered
    name: "Delivery Information Entered"
    sequence: 3
    group: grp-ordering
    origin:
      source: src-001
      bbox: [520, 300, 170, 70]
      color_observed: "#FF9933"
      text_confidence: 0.93
  - id: evt-order-placed
    name: "Order Placed"
    sequence: 4
    pivotal: true
    group: grp-ordering
    origin:
      source: src-001
      bbox: [750, 300, 130, 70]
      color_observed: "#FF9933"
      text_confidence: 0.97
  - id: evt-payment-confirmed
    name: "Payment Confirmed"
    sequence: 5
    pivotal: true
    group: grp-ordering
    origin:
      source: src-001
      bbox: [950, 300, 160, 70]
      color_observed: "#FF9933"
      text_confidence: 0.91
  - id: evt-kitchen-notified
    name: "Kitchen Notified"
    sequence: 6
    group: grp-kitchen
    origin:
      source: src-001
      bbox: [1700, 300, 150, 70]
      color_observed: "#FF9933"
      text_confidence: 0.89
  - id: evt-pizza-prepared
    name: "Pizza Prepared"
    sequence: 7
    group: grp-kitchen
    origin:
      source: src-001
      bbox: [1900, 300, 140, 70]
      color_observed: "#FF9933"
      text_confidence: 0.90
  - id: evt-order-packed
    name: "Order Packed"
    sequence: 8
    group: grp-kitchen
    origin:
      source: src-001
      bbox: [2100, 300, 130, 70]
      color_observed: "#FF9933"
      text_confidence: 0.92
  - id: evt-driver-notified
    name: "Driver Notified"
    sequence: 9
    group: grp-delivery
    origin:
      source: src-001
      bbox: [2950, 300, 150, 70]
      color_observed: "#FF9933"
      text_confidence: 0.88
  - id: evt-order-picked-up
    name: "Order Picked Up"
    sequence: 10
    group: grp-delivery
    origin:
      source: src-001
      bbox: [3150, 300, 140, 70]
      color_observed: "#FF9933"
      text_confidence: 0.91
  - id: evt-order-delivered
    name: "Order Delivered"
    sequence: 11
    pivotal: true
    group: grp-delivery
    origin:
      source: src-001
      bbox: [3350, 300, 140, 70]
      color_observed: "#FF9933"
      text_confidence: 0.94

commands:
  - id: cmd-start-order
    name: "Start Order"
    sequence: 1
    initiated_by:
      actor: act-customer
    targets:
      aggregate: agg-order
    emits:
      - evt-order-requested
    group: grp-ordering
    origin:
      source: src-001
      bbox: [160, 250, 120, 60]
      color_observed: "#4FC3F7"
      text_confidence: 0.90
  - id: cmd-select-pizza
    name: "Select Pizza Type"
    sequence: 2
    initiated_by:
      actor: act-customer
    targets:
      aggregate: agg-order
    emits:
      - evt-pizza-type-selected
    group: grp-ordering
    origin:
      source: src-001
      bbox: [310, 250, 140, 60]
      color_observed: "#4FC3F7"
      text_confidence: 0.88
  - id: cmd-place-order
    name: "Place Order"
    sequence: 4
    initiated_by:
      actor: act-customer
    targets:
      aggregate: agg-order
    emits:
      - evt-order-placed
    group: grp-ordering
    origin:
      source: src-001
      bbox: [710, 250, 120, 60]
      color_observed: "#4FC3F7"
      text_confidence: 0.93
  - id: cmd-initiate-payment
    name: "Initiate Payment"
    sequence: 4
    initiated_by:
      policy: pol-payment-on-order
    targets:
      external_system: sys-payment-gateway
    emits:
      - evt-payment-confirmed
    group: grp-ordering
    origin:
      source: src-001
      bbox: [870, 250, 150, 60]
      color_observed: "#4FC3F7"
      text_confidence: 0.87

aggregates:
  - id: agg-order
    name: "Order"
    receives:
      - cmd-start-order
      - cmd-select-pizza
      - cmd-place-order
    produces:
      - evt-order-requested
      - evt-pizza-type-selected
      - evt-order-placed
    constraints:
      - cst-minimum-order
    group: grp-ordering
    origin:
      source: src-001
      bbox: [400, 180, 200, 50]
      color_observed: "#FFF176"
      text_confidence: 0.95

policies:
  - id: pol-payment-on-order
    name: "Payment Required on Order"
    rule: "Whenever Order Placed, then Initiate Payment"
    listens_to:
      - evt-order-placed
    triggers:
      - cmd-initiate-payment
    group: grp-ordering
    origin:
      source: src-001
      bbox: [800, 400, 180, 80]
      color_observed: "#CE93D8"
      text_confidence: 0.86
  - id: pol-notify-kitchen
    name: "Notify Kitchen on Payment"
    rule: "Whenever Payment Confirmed, then Notify Kitchen"
    listens_to:
      - evt-payment-confirmed
    triggers:
      - cmd-notify-kitchen
    group: grp-kitchen
    origin:
      source: src-001
      bbox: [1650, 400, 180, 80]
      color_observed: "#CE93D8"
      text_confidence: 0.84

read_models:
  - id: rm-menu
    name: "Menu & Availability"
    description: "Available pizzas, sizes, crusts, and toppings"
    informs:
      - cmd-select-pizza
    group: grp-ordering
    origin:
      source: src-001
      bbox: [250, 150, 140, 60]
      color_observed: "#81C784"
      text_confidence: 0.89

external_systems:
  - id: sys-payment-gateway
    name: "Payment Gateway"
    receives:
      - cmd-initiate-payment
    produces:
      - evt-payment-confirmed
    group: grp-ordering
    origin:
      source: src-001
      bbox: [1000, 200, 200, 70]
      color_observed: "#F48FB1"
      text_confidence: 0.91

constraints:
  - id: cst-minimum-order
    name: "Minimum Order Value"
    rule: "Order total must be at least $10"
    applies_to:
      - agg-order
    origin:
      source: src-001
      bbox: [420, 230, 160, 40]
      color_observed: "#FFF176"
      text_confidence: 0.82

hotspots:
  - id: hot-delivery-radius
    name: "Delivery radius policy unclear"
    description: "No agreement on maximum delivery distance or how to handle
                  edge cases"
    near:
      - evt-driver-notified
    origin:
      source: src-001
      bbox: [2920, 420, 130, 80]
      color_observed: "#FF1493"
      text_confidence: 0.78

confidence_defaults:
  overall_text_extraction: 0.90
  overall_classification: 0.88
  notes: "Board was photographed under good lighting. Some stickies
          in the Kitchen group were partially overlapping."
```

---

## 7. What ESML Intentionally Does NOT Capture

1. **Bounded Contexts.** Groups are spatial clusters, not bounded contexts. The classification of groups into bounded contexts is a domain modeling interpretation.

2. **Subdomain classification.** Whether "Ordering" is a Core vs. Supporting subdomain is a strategic modeling decision, not a board observation.

3. **Context Map relationships.** Customer-Supplier, Anti-Corruption Layer, etc. are DDD patterns identified during domain modeling, not during Event Storming.

4. **Entity/Value Object detail.** Field names, data types, invariant specifications — these belong in the domain model, not in the board transcription.

5. **Implementation concerns.** Technology choices, API contracts, database schemas — entirely out of scope.

ESML's job is to faithfully represent what's on the board. Everything else is downstream.

---

## 8. Notes for LLM Implementors

When generating ESML from a board image:

1. **Scan the board systematically.** Start from the top-left, work left-to-right, top-to-bottom. Assign `sequence` numbers to events and commands based on their horizontal position.

2. **Classify by color first, then refine by context.** A sticky's color is the primary signal for its type. If the color is ambiguous (e.g., a yellowish-orange that could be an event or an actor), use size and position as secondary signals. Record the observed color in `color_observed` regardless.

3. **Capture relationships from spatial proximity.** If a blue sticky (command) is placed immediately to the left of a yellow sticky (aggregate) which is immediately to the left of an orange sticky (event), that's the canonical command→aggregate→event flow. Encode it.

4. **Don't infer what isn't visible.** If no policy sticky connects two events, don't create a policy. If no read model is visible, don't add one. The ESML represents what's *on the board*, not what *should be* on the board.

5. **Use `unresolved` for anything uncertain.** It's better to capture a low-confidence element in `unresolved` than to guess its type and get it wrong.

6. **Validate cross-references.** Before outputting, verify that every ID referenced in `emits`, `listens_to`, `triggers`, `receives`, `produces`, `subscribes_to`, `informs`, `near`, `applies_to`, etc. actually exists as an element ID.

---

## 9. References

- Brandolini, Alberto. "Introducing Event Storming." EventStorming.com.
- [ddd-crew Event Storming Glossary & Cheat Sheet](https://github.com/ddd-crew/eventstorming-glossary-cheat-sheet)
- [Context Mapper — Model Event Storming Results](https://contextmapper.org/docs/event-storming/)
- Neubert, M. & Yoder, J. "Domain Modeling Meets Generative AI." Agile Brazil 2025.
