# DMML — Domain Model Markup Language

## Specification Draft v0.1.0

**Authors:** Marden Neubert & Joseph Yoder

**Date:** March 2026

**Purpose:** A YAML-based format for machine-readable, progressively elaborated domain models following Domain-Driven Design principles.

---

## 1. Design Goals

1. **Unified strategic and tactical representation.** A single DMML document captures both the strategic view (subdomains, bounded contexts, context map) and the tactical view (aggregates, entities, value objects, services, etc.) in one coherent structure. No separate files, no phase transitions — just progressive deepening of the same document.

2. **Nesting over references.** Elements that are wholly contained within another are nested inside their parent: aggregates inside bounded contexts, entities and value objects inside aggregates, terms inside bounded contexts. This eliminates the need for `bc_ref`, `aggregate_ref`, and similar cross-reference fields, making the document structurally self-describing.

3. **Progressive elaboration.** Every element carries a `status` field (`draft`, `proposed`, `accepted`) enabling incremental refinement. A model starts mostly `draft` at the strategic stage and evolves toward `accepted` as tactical decisions solidify. LLMs and humans can work on the same document across multiple sessions.

4. **Traceable reasoning.** Every element carries a `notes` field for free-form text documenting the rationale, uncertainties, alternatives considered, or observations behind that element. This captures the *thinking process*, not just the result.

5. **Faithful to Evans and Vernon.** The schema covers every DDD building block from Eric Evans' "Domain-Driven Design" (2003) and Vaughn Vernon's "Implementing Domain-Driven Design" (2013). If Evans or Vernon named it, DMML has a place for it.

6. **LLM-friendly.** YAML format, consistent naming, inline examples. An LLM should be able to produce a valid DMML from an ESML file plus transcripts without additional tooling.

7. **Human-readable and editable.** A domain expert should be able to review, annotate, and correct a DMML file without technical training.

8. **ESML-compatible.** DMML is designed as the natural downstream consumer of ESML. The `esml_source` field references the upstream ESML document, and ESML groups, events, commands, and aggregates map predictably into DMML structures.

---

## 2. Relationship to ESML

ESML captures **what is on the board** — a high-fidelity transcription. DMML captures **what the board means** — a domain interpretation.

| Concern | ESML | DMML |
|---------|------|------|
| Groups → Bounded Contexts | Groups are spatial clusters | Bounded contexts are semantic boundaries with responsibilities |
| Events → Domain Events | Board stickies with sequence | Typed events with payloads, emitters, consumers |
| Aggregates | Labeled stickies with receives/produces | Consistency boundaries with root entities, invariants, lifecycle |
| Actors → Not modeled directly | Board participants | Actors become part of application services or use cases |
| Subdomains | Not captured | Classified as Core / Supporting / Generic |
| Context Map | Not captured | Full relationship topology |
| Entities, Value Objects | Not captured | Detailed tactical building blocks inside aggregates |

DMML intentionally **reinterprets** ESML content. An ESML group named "Orders" may become a bounded context named "Order Management" with a refined responsibility statement. An ESML event `evt-order-placed` may gain a typed payload and be linked to specific aggregates and policies.

---

## 3. DMML YAML Schema

### 3.1 Document Envelope

```yaml
dmml: "0.1.0"                        # REQUIRED — DMML specification version

model:                                # REQUIRED — metadata about the domain model
  name: "string"                      # REQUIRED — the domain or project name
  description: "string"               # OPTIONAL — what this domain is about
  status: draft                       # REQUIRED — draft | proposed | accepted
  date: "YYYY-MM-DD"                  # OPTIONAL — when this version was produced
  authors:                            # OPTIONAL
    - "string"
  notes: "string"                     # OPTIONAL — free-form notes about the model
  esml_source: "path/to/file.esml.yaml"
                                      # OPTIONAL — reference to the upstream ESML
                                      #   document that informed this model
```

### 3.2 The `status` Field

Every element in DMML carries a `status` field:

| Status | Meaning |
|--------|---------|
| `draft` | Initial hypothesis. Derived from board interpretation or early discussion. May change significantly. |
| `proposed` | Reviewed and refined. The modeler has confidence in this element but it hasn't been formally accepted by the team. |
| `accepted` | Agreed upon by the team. This element is stable and can be used as a basis for implementation. |

**Default:** If `status` is omitted on any element, it inherits the parent's status. If the root `model.status` is `draft`, all children without an explicit status are `draft`.

### 3.3 The `notes` Field

Every element in DMML carries an optional `notes` field:

```yaml
notes: |
  We debated whether to split this into two bounded contexts
  (one for order capture, one for fulfillment). Decided to keep
  it unified because the invariant "order must be paid before
  kitchen starts" crosses both concerns. Revisit if the team
  grows beyond 8 people.
```

**Guidelines for notes:**
- Document *why*, not *what* — the YAML structure already captures the what.
- Record alternatives that were considered and rejected.
- Flag uncertainties or conditions that would trigger a redesign.
- Use notes to preserve workshop discussions, expert opinions, or domain expert quotes.
- Notes are for humans (and LLMs in future sessions); they are never consumed programmatically.

### 3.4 Element ID Conventions

All IDs use kebab-case with a type prefix:

| Element Type | Prefix | Example |
|---|---|---|
| Subdomain | `sd-` | `sd-ordering` |
| Bounded Context | `bc-` | `bc-order-management` |
| Aggregate | `agg-` | `agg-order` |
| Entity | `ent-` | `ent-order` |
| Value Object | `vo-` | `vo-money` |
| Domain Event | `evt-` | `evt-order-placed` |
| Command | `cmd-` | `cmd-place-order` |
| Domain Service | `svc-` | `svc-pricing` |
| Application Service | `app-` | `app-place-order` |
| Policy | `pol-` | `pol-payment-on-order` |
| Process Manager | `pm-` | `pm-order-fulfillment` |
| Repository | `repo-` | `repo-order` |
| Factory | `fac-` | `fac-order` |
| Specification | `spec-` | `spec-premium-customer` |
| Read Model | `rm-` | `rm-order-summary` |
| Module | `mod-` | `mod-ordering` |
| Context Map Relationship | `rel-` | `rel-orders-payments` |
| Ubiquitous Language Term | `term-` | `term-order` |

---

## 4. Strategic Design

### 4.1 Subdomains

Subdomains represent areas of the business, classified by their strategic importance.

```yaml
subdomains:                           # REQUIRED — at least one
  - id: sd-ordering
    name: "Ordering"
    classification: core              # REQUIRED — core | supporting | generic
    description: "Captures customer intent and converts it into committed orders.
                  This is the primary revenue-generating capability."
    business_value: "Direct revenue capture and customer experience differentiation."
    status: proposed
    notes: "Joe considers this the heart of his business — the moment a
            customer commits to an order is where value is created."
```

**Classification guidance (per Evans):**

| Classification | Definition | Typical Approach |
|---|---|---|
| `core` | The domain area that provides competitive advantage. Worth investing the best talent and custom development. | Custom-built, DDD tactical patterns |
| `supporting` | Necessary for the business but not a differentiator. Important but wouldn't outsource it. | Simpler models, less ceremony |
| `generic` | Solved problems with off-the-shelf solutions. Not unique to this business. | Buy, integrate, or use open-source |

### 4.2 Bounded Contexts

Bounded contexts are the central pattern in strategic DDD — explicit boundaries within which a domain model is defined and consistent.

```yaml
bounded_contexts:                     # REQUIRED — at least one
  - id: bc-order-management
    name: "Order Management"
    subdomain: sd-ordering            # REQUIRED — which subdomain this belongs to
    description: "Manages the full lifecycle of a customer order from creation
                  through payment to fulfillment handoff."
    responsibilities:                 # REQUIRED — what this context is accountable for
      - "Create and validate customer orders"
      - "Process payment authorization"
      - "Emit order events for downstream contexts"
    status: proposed
    notes: "Maps to ESML groups grp-ordering and grp-payment. We merged them
            because the 'order must be paid before kitchen starts' invariant
            means payment is inseparable from order lifecycle."

    # --- Ubiquitous Language (nested) ---
    ubiquitous_language:              # OPTIONAL
      - id: term-order
        term: "Order"
        definition: "A confirmed customer request for one or more pizzas,
                     with delivery details and payment authorization."
      - id: term-order-line
        term: "Order Line"
        definition: "A single pizza within an order, specifying type, size,
                     crust, and toppings."

    # --- Tactical elements are nested inside (see Section 5) ---
    aggregates: [...]                 # OPTIONAL — see Section 5.1
    domain_services: [...]            # OPTIONAL — see Section 5.6
    application_services: [...]       # OPTIONAL — see Section 5.7
    policies: [...]                   # OPTIONAL — see Section 5.8
    process_managers: [...]           # OPTIONAL — see Section 5.9
    read_models: [...]                # OPTIONAL — see Section 5.10
    modules: [...]                    # OPTIONAL — see Section 5.11
```

**Why nest tactical elements inside bounded contexts:** A bounded context is, by definition, the boundary within which a model is consistent. All tactical elements (aggregates, entities, services) exist *within* a bounded context. Nesting makes this containment relationship structural rather than referential — you can't accidentally define an aggregate that belongs to no context, and you can read a bounded context's full model by reading a single YAML subtree.

### 4.3 Context Map

The context map captures how bounded contexts relate to each other. Evans defined nine relationship patterns; Vernon elaborated on their practical implementation.

```yaml
context_map:                          # OPTIONAL — but strongly recommended
  description: "Integration topology for Joe's Pizza domain"
  status: draft
  notes: "Initial map based on event flow observed on the ES board.
          Relationship types are hypotheses pending team review."

  relationships:
    - id: rel-orders-kitchen
      name: "Order Management → Kitchen"
      type: customer_supplier          # REQUIRED — see relationship types below
      upstream: bc-order-management
      downstream: bc-kitchen
      description: "Kitchen depends on Order Management for order details."
      integration_style: events        # OPTIONAL — events | api | messaging | shared_db
      status: proposed
      notes: "Kitchen team needs order details within 2 seconds of payment
              confirmation. Current plan is async event, but may need sync
              API for order amendments."

    - id: rel-kitchen-delivery
      name: "Kitchen → Delivery"
      type: customer_supplier
      upstream: bc-kitchen
      downstream: bc-delivery
      integration_style: events
      status: draft
```

#### Context Map Relationship Types

| Type (YAML value) | Evans Pattern | Nature | Description |
|---|---|---|---|
| `partnership` | Partnership | Symmetric | Two teams succeed or fail together. Joint planning and evolution of shared interfaces. |
| `shared_kernel` | Shared Kernel | Symmetric | Two contexts share a subset of the domain model. Changes require agreement from both teams. |
| `customer_supplier` | Customer-Supplier | Asymmetric | Downstream priorities influence upstream planning. Upstream accommodates downstream needs. |
| `conformist` | Conformist | Asymmetric | Downstream conforms entirely to upstream model. No negotiation power. |
| `anticorruption_layer` | Anticorruption Layer | Asymmetric | Downstream builds a translation layer to isolate itself from upstream model. |
| `open_host_service` | Open Host Service | Asymmetric | Upstream provides a well-defined, public API for multiple consumers. |
| `published_language` | Published Language | Symmetric | A shared, well-documented language (schema, protocol) for information exchange. Often combined with Open Host Service. |
| `separate_ways` | Separate Ways | Independent | No integration. Each context solves its own problems independently. |
| `big_ball_of_mud` | Big Ball of Mud | Degenerate | Legacy system with no clear boundaries. Demarcated to prevent contamination. |

**Combining patterns:** Real-world relationships often combine multiple patterns. For example, an upstream context may offer an Open Host Service with a Published Language, while the downstream applies an Anticorruption Layer. DMML handles this with a list:

```yaml
    - id: rel-orders-payment-gateway
      type: [open_host_service, anticorruption_layer]
      upstream: bc-payment-gateway     # external / generic subdomain
      downstream: bc-order-management
      notes: "Payment gateway exposes OHS. We built an ACL to translate
              their payment model into our order-centric language."
```

---

## 5. Tactical Design

Tactical elements are **nested inside their bounded context**. This section defines each element type.

### 5.1 Aggregates

An aggregate is a cluster of entities and value objects treated as a single unit for data changes. It has a root entity through which all external access occurs. The aggregate enforces invariants across its members.

```yaml
    aggregates:
      - id: agg-order
        name: "Order"
        description: "Consistency boundary for the full order lifecycle."
        status: proposed
        notes: "Root entity is Order. Contains OrderLines as child entities.
                Money is a value object shared across lines and totals."

        # --- Root Entity (exactly one per aggregate) ---
        root_entity:
          id: ent-order
          name: "Order"
          identity:                   # REQUIRED — what makes this entity unique
            field: orderId
            type: UUID
            generation: system        # OPTIONAL — system | user | external
          lifecycle:                  # OPTIONAL — states this entity passes through
            - Draft
            - Submitted
            - Paid
            - Preparing
            - Ready
            - Delivered
            - Cancelled
          fields:                     # OPTIONAL — attributes beyond identity
            - name: customerId
              type: UUID
              description: "Reference to the ordering customer"
            - name: status
              type: OrderStatus
              description: "Current lifecycle state"
            - name: total
              type: Money
              description: "Computed total including all lines"
            - name: placedAt
              type: DateTime
              description: "When the order was submitted"
              nullable: true
          status: proposed
          notes: "Joe insists that an order without a customer is invalid.
                  CustomerId is required from creation."

        # --- Child Entities (zero or more) ---
        entities:
          - id: ent-order-line
            name: "Order Line"
            identity:
              field: lineId
              type: UUID
            fields:
              - name: pizzaType
                type: string
                constraints: ["Margherita", "Pepperoni", "Hawaiian", "Custom"]
              - name: size
                type: PizzaSize
              - name: crust
                type: CrustType
              - name: toppings
                type: Topping[]
              - name: quantity
                type: int
                constraints: ["min=1", "max=20"]
              - name: lineTotal
                type: Money
            status: proposed

        # --- Value Objects (zero or more) ---
        value_objects:
          - id: vo-money
            name: "Money"
            fields:
              - name: amount
                type: decimal
                constraints: ["min=0"]
              - name: currency
                type: string
                constraints: ["ISO 4217"]
            equality: all_fields      # REQUIRED — all_fields | subset
            notes: "Standard money pattern from Evans. Currency is always
                    USD for now but modeled for future multi-currency."

          - id: vo-delivery-address
            name: "Delivery Address"
            fields:
              - name: street
                type: string
              - name: city
                type: string
              - name: zipCode
                type: string
              - name: coordinates
                type: GeoPoint
                nullable: true
            equality: all_fields

        # --- Invariants (aggregate-level business rules) ---
        invariants:
          - "Order must have at least one OrderLine"
          - "Order total must equal sum of line totals"
          - "Order cannot transition to Paid without payment confirmation"
          - "Cancelled orders cannot be modified"

        # --- Domain Events emitted by this aggregate ---
        domain_events:
          - id: evt-order-placed
            name: "Order Placed"
            description: "Emitted when a customer submits a complete order."
            emitted_on: "Transition from Draft to Submitted"
            payload:
              - { name: orderId, type: UUID }
              - { name: customerId, type: UUID }
              - { name: lines, type: OrderLineSummary[] }
              - { name: total, type: Money }
              - { name: deliveryAddress, type: DeliveryAddress }
              - { name: placedAt, type: DateTime }
            consumed_by:               # OPTIONAL — known consumers
              - bc-kitchen
              - pol-payment-on-order
            status: proposed
            notes: "This is the pivotal event on the ES board. Everything
                    downstream depends on it."

          - id: evt-order-paid
            name: "Order Paid"
            emitted_on: "Transition from Submitted to Paid"
            payload:
              - { name: orderId, type: UUID }
              - { name: paymentReference, type: string }
              - { name: paidAt, type: DateTime }
            consumed_by:
              - bc-kitchen

        # --- Commands handled by this aggregate ---
        commands:
          - id: cmd-place-order
            name: "Place Order"
            description: "Submit a complete order for processing."
            payload:
              - { name: customerId, type: UUID }
              - { name: lines, type: OrderLineInput[] }
              - { name: deliveryAddress, type: DeliveryAddress }
            preconditions:
              - "Order is in Draft status"
              - "At least one line item exists"
              - "Delivery address is within service area"
            emits:
              - evt-order-placed
            status: proposed

          - id: cmd-cancel-order
            name: "Cancel Order"
            payload:
              - { name: orderId, type: UUID }
              - { name: reason, type: string }
            preconditions:
              - "Order is not yet in Preparing status"
            emits:
              - evt-order-cancelled
            status: draft

        # --- Repository for this aggregate ---
        repository:                   # OPTIONAL — one per aggregate
          id: repo-order
          name: "OrderRepository"
          operations:
            - "save"
            - "findById"
            - "findByCustomer"
          status: draft
          notes: "Standard aggregate repository. Implementation could be
                  SQL, document store, or event-sourced."

        # --- Factory for this aggregate ---
        factory:                      # OPTIONAL — one per aggregate
          id: fac-order
          name: "OrderFactory"
          description: "Encapsulates the complex creation logic including
                        price calculation and address validation."
          status: draft
          notes: "Needed because Order creation involves validating
                  delivery address against service area and computing
                  line totals — too complex for a simple constructor."

        # --- Specifications (query/validation predicates) ---
        specifications:               # OPTIONAL
          - id: spec-cancellable-order
            name: "Cancellable Order"
            description: "An order can be cancelled if it has not yet entered
                          the kitchen preparation phase."
            predicate: "order.status in [Draft, Submitted, Paid]"
            status: draft
```

### 5.2 Entities (Summary)

Entities are objects defined by their identity rather than their attributes. In DMML, entities appear in two positions:

- **Root entity:** Nested directly under `root_entity` in an aggregate. Exactly one per aggregate.
- **Child entities:** Listed under `entities` in an aggregate. Zero or more.

Both share the same schema:

```yaml
          id: ent-xxx                 # REQUIRED — prefixed with ent-
          name: "string"              # REQUIRED
          identity:                   # REQUIRED
            field: "string"           # The identity field name
            type: "string"            # The identity type (UUID, int, string, etc.)
            generation: system        # OPTIONAL — system | user | external
          lifecycle:                  # OPTIONAL — state enumeration
            - "state1"
            - "state2"
          fields:                     # OPTIONAL
            - name: "string"
              type: "string"
              description: "string"   # OPTIONAL
              constraints: [...]      # OPTIONAL
              nullable: false         # OPTIONAL — defaults to false
          status: draft
          notes: "string"
```

### 5.3 Value Objects (Summary)

Value objects are immutable objects defined by their attributes, with no conceptual identity. Two value objects with the same attributes are equal.

```yaml
          id: vo-xxx                  # REQUIRED — prefixed with vo-
          name: "string"              # REQUIRED
          fields:                     # REQUIRED — at least one
            - name: "string"
              type: "string"
              constraints: [...]      # OPTIONAL
          equality: all_fields        # REQUIRED — all_fields | subset
          status: draft
          notes: "string"
```

**Evans' distinction:** Entities have identity and continuity; value objects have attributes and equality. When in doubt about whether something is an entity or value object, prefer value object — it's simpler, safer, and more composable. Value objects are always immutable by definition — this is not modeled as a field because it is inherent to the concept.

### 5.4 Domain Events (Summary)

Domain events represent something significant that happened in the domain. In DMML they are nested inside the aggregate that emits them.

```yaml
          id: evt-xxx                 # REQUIRED — prefixed with evt-
          name: "string"              # REQUIRED — past tense
          description: "string"       # OPTIONAL
          emitted_on: "string"        # OPTIONAL — when this event fires
                                      #   (e.g., "Transition from X to Y")
          payload:                    # OPTIONAL — data carried by the event
            - name: "string"
              type: "string"
          consumed_by: [...]          # OPTIONAL — known consumers
                                      #   (bounded context IDs or policy IDs)
          status: draft
          notes: "string"
```

### 5.5 Commands (Summary)

Commands represent an intent to change the domain state. They target an aggregate.

```yaml
          id: cmd-xxx                 # REQUIRED — prefixed with cmd-
          name: "string"              # REQUIRED — imperative form
          description: "string"       # OPTIONAL
          payload:                    # OPTIONAL
            - name: "string"
              type: "string"
          preconditions: [...]        # OPTIONAL — what must be true
          emits: [...]                # OPTIONAL — events produced on success
          status: draft
          notes: "string"
```

### 5.6 Domain Services

Domain services encapsulate domain logic that doesn't naturally belong to any single entity or value object. They are stateless and operate on domain objects.

```yaml
    domain_services:
      - id: svc-pricing
        name: "Pricing Service"
        description: "Calculates order totals including per-pizza pricing,
                      size modifiers, topping surcharges, and delivery fees."
        operations:
          - name: calculateLineTotal
            params: [{ name: line, type: OrderLine }]
            returns: Money
          - name: calculateDeliveryFee
            params: [{ name: address, type: DeliveryAddress }]
            returns: Money
        status: draft
        notes: "Per Evans: use a domain service when the operation conceptually
                belongs to the domain but not to any single object. Pricing
                spans multiple order lines and delivery address."
```

**When to use domain services (Evans' guidance):** When an operation is an important domain concept that doesn't belong to an Entity or Value Object; when the interface is defined in terms of other domain model elements; when the operation is stateless.

### 5.7 Application Services

Application services orchestrate use cases. They coordinate domain objects and infrastructure but contain no domain logic themselves. Vernon emphasizes these as the transaction boundary.

```yaml
    application_services:
      - id: app-place-order
        name: "Place Order Service"
        description: "Orchestrates the order placement use case: validates
                      input, creates order aggregate, persists, and publishes
                      domain events."
        use_case: "Customer places a new order"
        coordinates:                  # What domain elements this service uses
          - repo-order
          - fac-order
          - svc-pricing
        handles:                      # Which command(s) this service handles
          - cmd-place-order
        status: draft
        notes: "This is the thin orchestration layer Vernon describes in
                IDDD Chapter 14. No domain logic here — just coordination."
```

### 5.8 Policies (Event-Driven Reactions)

Policies (also called reactors or listeners) represent automated reactions: "whenever X happens, do Y." They bridge events to commands, often across aggregate or context boundaries.

```yaml
    policies:
      - id: pol-payment-on-order
        name: "Initiate Payment on Order Placed"
        description: "Whenever an order is placed, automatically initiate
                      payment processing."
        trigger_events:               # REQUIRED — what triggers this policy
          - evt-order-placed
        issues_commands:              # REQUIRED — what this policy does
          - cmd-initiate-payment
        rule: "Whenever Order Placed, then Initiate Payment"
                                      # OPTIONAL — natural language rule
        status: proposed
        notes: "Direct mapping from ESML pol-payment-on-order. The board
                showed a lilac sticky between evt-order-placed and
                cmd-initiate-payment."
```

### 5.9 Process Managers (Sagas)

Process managers (Vernon's term; also called sagas) coordinate long-running business processes that span multiple aggregates or bounded contexts. They maintain state and react to events over time.

```yaml
    process_managers:
      - id: pm-order-fulfillment
        name: "Order Fulfillment Process"
        description: "Orchestrates the end-to-end order fulfillment from
                      payment confirmation through kitchen preparation to
                      delivery completion."
        states:                       # REQUIRED — the process states
          - awaiting_payment
          - payment_confirmed
          - in_kitchen
          - ready_for_delivery
          - in_delivery
          - delivered
          - failed
        transitions:                  # REQUIRED — state machine transitions
          - from: awaiting_payment
            on_event: evt-order-paid
            to: payment_confirmed
            issues: [cmd-notify-kitchen]
          - from: payment_confirmed
            on_event: evt-kitchen-notified
            to: in_kitchen
          - from: in_kitchen
            on_event: evt-order-packed
            to: ready_for_delivery
            issues: [cmd-notify-delivery]
          - from: ready_for_delivery
            on_event: evt-order-picked-up
            to: in_delivery
          - from: in_delivery
            on_event: evt-order-delivered
            to: delivered
        timeout:                      # OPTIONAL
          duration: "45m"
          action: "Escalate to operations"
        compensation:                 # OPTIONAL — rollback strategy
          description: "If payment fails, cancel the order. If kitchen
                        cannot fulfill, refund payment."
        status: draft
        notes: "This is the full happy path from the ES board read
                left-to-right. The board doesn't show failure paths
                explicitly — those are inferred from domain knowledge."
```

### 5.10 Read Models (Projections)

Read models represent the query side of the domain — views optimized for reading, typically updated asynchronously from domain events. Vernon covers these extensively in his CQRS chapters.

```yaml
    read_models:
      - id: rm-order-summary
        name: "Order Summary"
        description: "Denormalized view showing current order status,
                      line items, and delivery ETA for the customer."
        subscribes_to:                # Events that update this projection
          - evt-order-placed
          - evt-order-paid
          - evt-kitchen-notified
          - evt-order-delivered
        fields:
          - { name: orderId, type: UUID }
          - { name: customerName, type: string }
          - { name: status, type: string }
          - { name: lines, type: OrderLineSummary[] }
          - { name: total, type: Money }
          - { name: estimatedDelivery, type: DateTime }
        consumers:                    # OPTIONAL — who uses this read model
          - "Customer order tracking UI"
          - "Customer service dashboard"
        status: draft
```

### 5.11 Modules (Packages)

Evans introduced modules as a way to organize elements within a bounded context into cohesive groups. They map to packages, namespaces, or directories in implementation.

```yaml
    modules:
      - id: mod-ordering
        name: "ordering"
        description: "Core order creation and lifecycle management"
        contains:                     # Elements grouped in this module
          - agg-order
          - svc-pricing
          - pol-payment-on-order
        status: draft
        notes: "Per Evans, modules should have low coupling and high
                cohesion, and their names should be part of the
                ubiquitous language."
```

---

## 6. Complete Element Reference

### 6.1 All Top-Level Sections

```yaml
dmml: "0.1.0"
model: { ... }

# Strategic
subdomains: [...]
bounded_contexts: [...]
context_map: { ... }

# Tactical (nested inside bounded_contexts)
#   bounded_contexts[].aggregates[]
#     .root_entity
#     .entities[]
#     .value_objects[]
#     .domain_events[]
#     .commands[]
#     .invariants[]
#     .repository
#     .factory
#     .specifications[]
#   bounded_contexts[].domain_services[]
#   bounded_contexts[].application_services[]
#   bounded_contexts[].policies[]
#   bounded_contexts[].process_managers[]
#   bounded_contexts[].read_models[]
#   bounded_contexts[].modules[]
#   bounded_contexts[].ubiquitous_language[]
```

### 6.2 Coverage Matrix: Evans & Vernon

| DDD Concept | Evans Chapter | Vernon Chapter | DMML Location |
|---|---|---|---|
| Ubiquitous Language | 2 | 1 | `bounded_contexts[].ubiquitous_language[]` |
| Bounded Context | 14 | 2, 3 | `bounded_contexts[]` |
| Context Map | 14 | 3 | `context_map` |
| Subdomains | 15 | 2 | `subdomains[]` |
| Entities | 5 | 5 | `aggregates[].root_entity`, `aggregates[].entities[]` |
| Value Objects | 5 | 6 | `aggregates[].value_objects[]` |
| Aggregates | 6 | 10 | `bounded_contexts[].aggregates[]` |
| Domain Events | — | 8 | `aggregates[].domain_events[]` |
| Domain Services | 5 | 7 | `bounded_contexts[].domain_services[]` |
| Application Services | — | 14 | `bounded_contexts[].application_services[]` |
| Repositories | 6 | 12 | `aggregates[].repository` |
| Factories | 6 | 11 | `aggregates[].factory` |
| Specifications | 9 | — | `aggregates[].specifications[]` |
| Modules | 5 | 9 | `bounded_contexts[].modules[]` |
| Policies / Reactors | — | 8 | `bounded_contexts[].policies[]` |
| Process Managers / Sagas | — | 8 | `bounded_contexts[].process_managers[]` |
| Read Models / Projections | — | 4 (CQRS) | `bounded_contexts[].read_models[]` |
| Partnership | 14 | 3 | `context_map.relationships[]` |
| Shared Kernel | 14 | 3 | `context_map.relationships[]` |
| Customer-Supplier | 14 | 3 | `context_map.relationships[]` |
| Conformist | 14 | 3 | `context_map.relationships[]` |
| Anticorruption Layer | 14 | 3 | `context_map.relationships[]` |
| Open Host Service | 14 | 3 | `context_map.relationships[]` |
| Published Language | 14 | 3 | `context_map.relationships[]` |
| Separate Ways | 14 | 3 | `context_map.relationships[]` |
| Big Ball of Mud | — | 3 | `context_map.relationships[]` |

---

## 7. Validation Rules

A DMML document is valid if:

1. It is valid YAML 1.2.
2. `dmml` version field is present.
3. `model` section is present with `name` and `status`.
4. At least one `subdomains` entry exists.
5. At least one `bounded_contexts` entry exists.
6. Every bounded context references an existing subdomain ID.
7. Every `id` is globally unique across all sections and nesting levels.
8. ID prefixes match element types (e.g., `ent-` for entities, `vo-` for value objects).
9. Every aggregate has exactly one `root_entity`.
10. Every cross-reference (in `consumed_by`, `coordinates`, `handles`, `trigger_events`, `issues_commands`, `contains`, context map `upstream`/`downstream`) resolves to an existing element ID.
12. Every context map relationship has a valid `type` from the defined set.
13. Symmetric relationship types (`partnership`, `shared_kernel`, `published_language`, `separate_ways`) should not have `upstream`/`downstream` — they should use `participants` instead.
14. `status` values are one of: `draft`, `proposed`, `accepted`.

**Warnings** (non-fatal):

- Bounded contexts without any aggregates (strategic-only model).
- Aggregates without domain events.
- Commands without preconditions.
- Entities without fields beyond identity.
- Domain services without operations.
- Missing `notes` on `draft` elements (encouraged but not required).
- Policies with `trigger_events` or `issues_commands` that reference elements in a different bounded context (may indicate a cross-context concern worth discussing).

---

## 8. Progressive Elaboration Workflow

DMML supports a natural workflow from strategic discovery through tactical refinement:

### Phase 1: Strategic Skeleton

Start with subdomains, bounded contexts (names + responsibilities only), and a rough context map. All elements are `status: draft`. This phase typically follows a Big Picture Event Storming session.

```yaml
# Phase 1 — everything is a sketch
bounded_contexts:
  - id: bc-order-management
    name: "Order Management"
    subdomain: sd-ordering
    responsibilities:
      - "Handle customer orders"
    status: draft
    notes: "Derived from ESML groups grp-ordering and grp-payment."
```

### Phase 2: Tactical Scaffolding

Add aggregates with root entities (identity + lifecycle only), domain events (name + key payload fields), and commands. Mark refined elements as `proposed`. This phase typically follows a Design Level Event Storming session.

```yaml
# Phase 2 — aggregates appear, events get payloads
    aggregates:
      - id: agg-order
        name: "Order"
        status: proposed
        root_entity:
          id: ent-order
          name: "Order"
          identity: { field: orderId, type: UUID }
          lifecycle: [Draft, Submitted, Paid, Preparing, Ready, Delivered]
        domain_events:
          - id: evt-order-placed
            name: "Order Placed"
            payload:
              - { name: orderId, type: UUID }
              - { name: total, type: Money }
            status: proposed
```

### Phase 3: Full Tactical Detail

Add child entities, value objects, invariants, repositories, factories, specifications, services. Refine all fields and constraints. Move elements to `accepted` as the team agrees on them.

### Phase 4: Implementation Handoff

The `accepted` DMML document serves as the specification for implementation. Code generators, LLM coding agents, or human developers can consume it directly.

---

## 9. Splitting Large Models

For large domains, a single DMML file may become unwieldy. The recommended splitting strategy:

1. **One file per bounded context.** Each file contains the full bounded context definition with all nested tactical elements. The context map and subdomains remain in a root file.

```
domain-model/
├── model.dmml.yaml           # dmml version, model metadata, subdomains, context_map
├── bc-order-management.dmml.yaml
├── bc-kitchen.dmml.yaml
└── bc-delivery.dmml.yaml
```

2. **Cross-file references.** When splitting, IDs remain globally unique. Cross-file references use the same ID format — the consuming tool is responsible for loading all files.

3. **When to split.** A reasonable heuristic: split when a single file exceeds ~1000 lines or when different teams own different bounded contexts.

---

## 10. What DMML Intentionally Does NOT Capture

1. **Implementation technology.** No database schemas, API contracts, framework annotations, or deployment configurations. DMML is technology-agnostic.

2. **UI/UX details.** Screen layouts, component hierarchies, and interaction flows belong in separate artifacts.

3. **Non-functional requirements.** Performance SLAs, scalability targets, security policies. These inform implementation but are not part of the domain model.

4. **Code structure beyond modules.** Class hierarchies, interface definitions, dependency injection configurations. The module section suggests organizational boundaries; implementation fills in the rest.

5. **Event sourcing mechanics.** While DMML models domain events and their payloads, the decision to use event sourcing (persisting events as the source of truth) is an implementation choice, not a domain modeling choice. DMML events describe *what happened*; how they're stored is out of scope.

---

## 11. Notes for LLM Implementors

When generating DMML from ESML plus transcripts:

1. **Start strategic, go tactical.** First map ESML groups to subdomains and bounded contexts. Classify subdomains. Draft the context map. Only then dive into aggregates.

2. **ESML groups ≠ bounded contexts.** Groups are spatial clusters; bounded contexts are semantic boundaries. Two groups may merge into one context (if they share invariants) or one group may split into multiple contexts.

3. **Use transcripts for domain knowledge.** ESML captures what's on the board. Transcripts capture *why* things are on the board — the discussions, trade-offs, and domain expert insights. Extract ubiquitous language terms, invariants, and business rules from transcripts.

4. **Populate `notes` generously.** When you make an interpretation choice (e.g., classifying a subdomain as Core, merging two groups into one context), explain your reasoning in the `notes` field. This is critical for human review.

5. **Mark uncertainty with `draft`.** If you're not confident in a classification, relationship type, or structural decision, mark it `draft` and explain in `notes` what additional information would resolve the uncertainty.

6. **Validate cross-references.** Before outputting, verify that every ID referenced anywhere (consumed_by, trigger_events, coordinates, upstream/downstream, contains) exists as a defined element.

7. **Don't invent what isn't supported by evidence.** If the ESML and transcripts don't mention a factory or specification, don't create one. Progressive elaboration means the model grows as knowledge grows.

---

## 12. References

- Evans, Eric. "Domain-Driven Design: Tackling Complexity in the Heart of Software." Addison-Wesley, 2003.
- Vernon, Vaughn. "Implementing Domain-Driven Design." Addison-Wesley, 2013.
- Evans, Eric. "Domain-Driven Design Reference." Domain Language, Inc., 2015.
- Brandolini, Alberto. "Introducing Event Storming." EventStorming.com.
- [ddd-crew Context Mapping](https://github.com/ddd-crew/context-mapping)
- [Context Mapper — DDD Patterns](https://contextmapper.org/docs/context-map/)
- Neubert, M. & Yoder, J. "Domain Modeling Meets Generative AI." Agile Brazil 2025.
- ESML — Event Storming Markup Language, Specification Draft v0.2.0.
