# From Domain Model to Running Code: Next Steps Brainstorming

**Date:** March 2026
**Context:** Planning the next phase of the DDD Meets GenAI pipeline — moving from DMML to reference implementations of Cargo Shipping, Bringots, and Joe's Pizza as internal APIs on GitHub.

---

## 1. Where We Are

The current pipeline covers two transformations, each with its own skill:

```
Board Photo ──skill 1──▶ ESML ──skill 2──▶ DMML
              (transcribe)        (interpret)
```

Each step produces a machine-readable, human-reviewable YAML artifact. The specs (ESML v0.2.1 and DMML v0.1.0) define the format; the skills teach an LLM how to perform the transformation; the eval cases (three domains at increasing complexity) measure quality.

The DMML is deliberately technology-agnostic. Section 10 of the spec explicitly excludes implementation technology, code structure, event sourcing mechanics, and API contracts. This is by design — the domain model should be reusable across technology stacks. But it also means there's an intentional gap between "what the domain looks like" and "code that runs."

## 2. The Gap

The DMML gives us rich structural information that maps almost directly to code constructs:

| DMML Element | Code Construct |
|---|---|
| Bounded Context | Module/package boundary |
| Aggregate + Root Entity | Aggregate root class with identity and lifecycle |
| Child Entity | Nested class or separate class within aggregate package |
| Value Object | Immutable data class (record, data class, frozen dataclass) |
| Domain Event | Event class with typed payload |
| Command | Command class or method signature |
| Invariants | Validation logic in aggregate methods |
| Repository | Repository interface + implementation |
| Application Service | Service class orchestrating use cases |
| Policy | Event handler / reactor class |
| Domain Service | Stateless service class |
| Context Map relationship | Integration contracts between modules |

What the DMML does **not** provide (and code needs):

1. **Technology stack** — language, framework, build tool, runtime
2. **Architecture style** — hexagonal (ports & adapters), onion, layered, CQRS
3. **Persistence strategy** — in-memory, relational (JPA), document store, event-sourced
4. **API convention** — REST paths, HTTP methods, request/response shapes, error formats
5. **Cross-BC communication** — in-process events, message broker, HTTP calls
6. **Package structure** — how bounded contexts map to directories and namespaces
7. **Testing approach** — what to test, at what granularity, what frameworks
8. **Build and deployment** — how to compile, run, and ship

The question is: how much of this should be captured in a new specification vs. handled as skill configuration?

## 3. The Proposed Pipeline

I see two credible pipeline designs:

### Option A: One New Skill (Simpler)

```
DMML ──skill 3──▶ Working Project
       (implement)
```

A single `implementation-generator` skill takes the DMML plus a lightweight technology profile (a small YAML config, not a new spec) and produces a complete project: domain layer, application layer, infrastructure, API, and tests. The skill internally handles all the decisions about package structure, API conventions, and code patterns for the chosen stack.

**Pros:** Fewer moving parts. One skill to build, test, and maintain. Matches the presentation narrative: "run one skill, get running code."

**Cons:** The skill is doing a LOT — generating dozens of files across multiple concerns. Harder to evaluate (how do you define "correct" for generated code?). The API design is invisible — baked into the skill rather than reviewable.

### Option B: Two New Skills (Richer, my recommendation)

```
DMML ──skill 3──▶ OpenAPI Spec ──skill 4──▶ Working Project
       (design)                   (implement)
```

**Skill 3: `api-designer`** takes the DMML and produces an OpenAPI specification. This is the contract between the domain and the outside world — what endpoints exist, what the request/response shapes look like, what errors are possible. It's a well-known standard (no new spec to invent), reviewable by domain experts, and independently useful (client code-gen, documentation, contract testing).

**Skill 4: `implementation-generator`** takes the DMML + the OpenAPI spec + a technology profile and produces the working project. The OpenAPI spec constrains the API layer; the DMML drives the domain and application layers.

**Pros:** Adds another reviewable artifact to the pipeline — consistent with the spec-driven narrative. Separates "what should the API look like" from "how do we implement it." The OpenAPI spec is useful on its own. Cleaner evaluation: you can separately assess API design quality and code quality.

**Cons:** One more step. The API design for internal domain services is somewhat mechanical (commands → POST endpoints, read models → GET endpoints), so a separate skill might feel heavy. The api-designer skill would need to handle subtleties like: which aggregates are exposed, how cross-BC queries work, error response formats.

### My Recommendation: Option B

The consistency argument wins for me. The pipeline story is cleaner:

```
Conversation → Board → ESML → DMML → OpenAPI → Code
                        (ours)   (ours)  (standard)  (generated)
```

Each arrow is a skill. Each artifact is reviewable. And the use of OpenAPI (an existing, widely-adopted standard) instead of yet another custom spec is strategically smart — it shows the pipeline integrates with the broader ecosystem rather than being a closed loop.

For the presentation, you can show the OpenAPI spec in Swagger UI as a natural "pause point" before diving into code: "Here's the API our domain model produced. Let's review it before generating the implementation."

## 4. Technology Choice

This is the decision with the most long-term consequences. Here's my analysis:

### Kotlin + Spring Boot

**Why it fits:** Vernon's "Implementing DDD" examples are Java/Spring. Kotlin adds modern conciseness: `data class` for value objects, `sealed class` for lifecycle states and discriminated unions, null safety that maps to DMML's `nullable` field, coroutines for async event handling. Spring Boot provides DI, web layer, and testing infrastructure out of the box. The DDD + Spring ecosystem is the most mature.

**Concerns:** JVM dependency. Spring Boot's convention-over-configuration can hide DDD patterns behind framework magic. Build config (Gradle Kotlin DSL) adds noise. Heavier startup time for demos.

### Python + FastAPI

**Why it fits:** Already in the repo (validator scripts). Most accessible to a broad conference audience. FastAPI is modern, async-first, with good OpenAPI generation built in. Pydantic models map to value objects and event payloads naturally. Quickest to prototype.

**Concerns:** DDD patterns feel less idiomatic in Python. No real interfaces (ABCs exist but aren't enforced). No nominal typing (two value objects with the same fields are structurally identical). Aggregate invariant enforcement relies on discipline rather than type system. `dataclass(frozen=True)` is the closest to a real value object but lacks equality customization.

### TypeScript + NestJS

**Why it fits:** NestJS modules map cleanly to bounded contexts. Decorators are expressive for commands and events. Good TypeScript typing for domain contracts. Large audience familiarity.

**Concerns:** Structural typing makes it hard to distinguish entities from value objects. DDD patterns are less established in the TS ecosystem. NestJS adds its own patterns (providers, guards, interceptors) that can compete with DDD patterns for attention.

### My Recommendation: Kotlin

For a **reference implementation** that showcases DDD patterns, Kotlin is the strongest choice. The language was practically designed for DDD tactical patterns:

```kotlin
// Value Object — immutable by default
data class Money(val amount: BigDecimal, val currency: String = "BRL") {
    init { require(amount >= BigDecimal.ZERO) { "Amount must be non-negative" } }
}

// Aggregate root with lifecycle
class Order private constructor(
    val orderId: UUID,
    var status: OrderStatus,
    private val items: MutableList<OrderItem>,
    var deliveryInstructions: String? = null
) {
    // Invariant enforcement
    fun place(): OrderPlaced {
        require(items.isNotEmpty()) { "Order must have at least one item" }
        require(status == OrderStatus.PAID) { "Payment must be completed before placement" }
        status = OrderStatus.PLACED
        return OrderPlaced(orderId, items.toSummary(), placedAt = Instant.now())
    }
}

// Domain event — immutable data
data class OrderPlaced(
    val orderId: UUID,
    val items: List<OrderItemSummary>,
    val placedAt: Instant
)

// Sealed class for lifecycle states
enum class OrderStatus { CREATED, CONFIGURING, PAYMENT_PENDING, PAID, PLACED }
```

The mapping from DMML to Kotlin is almost 1:1, making the generated code readable and the skill's job tractable.

**However** — if audience accessibility is the priority over DDD purity, Python is the pragmatic choice. The XP audience may be more mixed than a DDD conference audience. If you go Python, I'd recommend using Pydantic v2 with `model_validator` for invariant enforcement and an explicit Aggregate base class to make the DDD patterns visible.

**My strong lean: Kotlin.** A reference implementation should be exemplary, not just accessible. People come to a reference to learn how to do it right. And the Kotlin code will look beautiful on slides.

## 5. Architecture Style

Regardless of language, the architecture should be **hexagonal (ports & adapters)**, which is the canonical DDD implementation architecture (Vernon, Chapter 4). Each bounded context has:

```
bc-order-management/
├── domain/                    # The heart — pure domain logic, no dependencies
│   ├── model/                 # Aggregates, entities, value objects
│   │   ├── Order.kt
│   │   ├── Customer.kt
│   │   ├── OrderItem.kt
│   │   └── Money.kt
│   ├── event/                 # Domain events
│   │   ├── OrderPlaced.kt
│   │   └── PaymentCompleted.kt
│   ├── command/               # Commands
│   │   ├── PlaceOrder.kt
│   │   └── SelectPizzaType.kt
│   ├── repository/            # Repository interfaces (ports)
│   │   └── OrderRepository.kt
│   └── service/               # Domain services (if any)
│
├── application/               # Use case orchestration
│   ├── PlaceOrderService.kt   # Application services
│   └── policy/                # Event-driven policies
│       └── PlaceOrderOnPayment.kt
│
├── infrastructure/            # Adapters — implementations of ports
│   ├── persistence/
│   │   └── InMemoryOrderRepository.kt
│   └── event/
│       └── InProcessEventPublisher.kt
│
└── api/                       # Inbound adapters — REST controllers
    └── OrderController.kt
```

**Key architectural rules:**

1. **Domain layer has zero dependencies** on framework, persistence, or API code. Pure Kotlin (or Python, or TS). This is the DDD gold standard.
2. **Application layer depends only on domain.** It orchestrates; it doesn't contain domain logic.
3. **Infrastructure implements domain interfaces.** Repositories, event publishers, etc.
4. **API layer calls application services.** Thin controllers that translate HTTP to commands.
5. **Cross-BC communication goes through events.** No direct aggregate access across boundaries. The context map relationship types from the DMML guide the integration pattern.

For the reference implementation, **in-memory persistence** is the right call. It keeps the focus on the domain model, not on database wiring. The repository interfaces are defined; swapping in JPA or a document store is a future exercise.

## 6. Repository Strategy

### Option A: Same repo, new top-level folder

```
ddd-meets-genai/
├── ESML-Specification-Draft.md
├── DMML-Specification-Draft.md
├── skills/
│   ├── event-storming-board-interpreter/
│   ├── domain-modeler/
│   ├── api-designer/          # NEW
│   └── implementation-generator/ # NEW
└── implementations/           # NEW
    ├── cargo-shipping/
    ├── bringots/
    └── joes-pizza/
```

**Pros:** One repo, one URL. Specs, skills, and implementations stay in sync. Simple to navigate.

**Cons:** Repo grows large. CI/CD for code is different from CI/CD for specs. Build tooling (Gradle, pip, npm) clutters the root. Different audiences browse different parts.

### Option B: Separate implementation repo

```
ddd-meets-genai/              # Specs + skills (existing)
ddd-meets-genai-reference/    # Implementations (new)
├── cargo-shipping/
├── bringots/
└── joes-pizza/
```

**Pros:** Clean separation. Each repo has its own CI, build config, and README. The spec repo stays lightweight and focused. The implementation repo can have language-specific tooling without polluting the spec repo.

**Cons:** Two repos to maintain. Cross-references between them can drift. Harder to navigate as a newcomer.

### Option C: Monorepo with implementation as a subproject

```
ddd-meets-genai/
├── specs/                     # ESML + DMML
├── skills/                    # Agent skills
└── reference/                 # Implementations
    ├── build.gradle.kts       # Root build for all domains
    ├── cargo-shipping/
    ├── bringots/
    └── joes-pizza/
```

**Pros:** Monorepo keeps everything together. The `reference/` folder is self-contained with its own build. Each domain is a Gradle subproject (or Python package, depending on language choice).

**Cons:** Root build config needed. Slightly more complex repo structure.

### My Recommendation: Option C (monorepo with clear separation)

The presentation benefits from "one repo, full pipeline." Attendees clone one repo and get specs, skills, AND working code. The `reference/` folder is self-contained — you can `cd reference && ./gradlew build` (or equivalent) without touching the rest. And the specs at the root provide the context for why the code looks the way it does.

## 7. Implementation Order

Not all three domains are equal in complexity. I'd build them in this order:

### Phase 1: Joe's Pizza (start here)

**Why first:** It's the real domain. You and Joe know it intimately. The transcripts contain rich domain knowledge. It has the most interesting DDD patterns (floating aggregates → separate BC views, concurrent events, three pivotal events marking clear BC boundaries). And it's the domain the audience will have seen in the Event Storming demo.

**Scope:** Three bounded contexts (Order Management, Kitchen, Delivery) + external Payment Gateway integration (mocked). Roughly 15-20 domain classes, 3 REST controllers, in-memory persistence.

**Estimated effort:** 2-3 working sessions with the implementation-generator skill, plus manual review and refinement.

### Phase 2: Cargo Shipping

**Why second:** Classic DDD domain (Evans' original example). The audience will recognize it. Good for validating that the same skill works across different domains.

**Scope:** Depends on the existing DMML complexity. Likely 2-3 bounded contexts with the classic Cargo, Voyage, and Handling patterns.

**Estimated effort:** 1-2 sessions (the skill should be tuned from Phase 1).

### Phase 3: Bringots

**Why last:** Most complex domain (5 bounded contexts including 2 external, rich lifecycle states, batch processing patterns). Also the most "exercise-like" — it's a fictional domain designed to be challenging.

**Scope:** Full implementation including the end-of-day settlement batch, AutoPay policy, cross-BC event flows.

**Estimated effort:** 2-3 sessions.

## 8. What This Means for XP 2026

The presentation narrative becomes the full pipeline:

```
Joe's Pizza Event Storming recording (2 min clip)
    ↓
Board Photo → ESML (skill 1, live or pre-recorded)
    ↓
ESML + Transcripts → DMML (skill 2, live or pre-recorded)
    ↓
DMML → OpenAPI (skill 3, show in Swagger UI)
    ↓
DMML + OpenAPI → Running API (skill 4, hit with curl)
```

The money shot: a domain expert conversation produces a running API, with every intermediate artifact reviewable and version-controlled. Each step is an AI agent skill. The specs ensure reproducibility. The eval cases ensure quality.

This is spec-driven development applied to the part of the SDLC that everyone skips.

## 9. New Skills: Detailed Design

### Skill 3: `api-designer`

**Input:** DMML file
**Output:** OpenAPI 3.1 specification (YAML)
**Transformation logic:**

- Each bounded context with aggregates → API tag/group
- Each command → POST endpoint
  - Path: `/{bc-name}/{aggregate-name}/{command-name}`
  - Request body: command attributes
  - Response: command result + emitted event summary
- Each read model → GET endpoint
  - Path: `/{bc-name}/{read-model-name}`
  - Response: read model attributes
- Value objects → reusable schema components
- Domain events → webhook/event schemas (for documentation)
- Error responses derived from preconditions and invariants
- External BCs → documented but not implemented (noted as external dependencies)

**Evaluation:** Compare generated OpenAPI against hand-crafted reference OpenAPI for each domain.

### Skill 4: `implementation-generator`

**Input:** DMML file + OpenAPI spec + technology profile (YAML config)
**Output:** Complete project directory
**Transformation logic (Kotlin example):**

- DMML bounded context → Kotlin module with hexagonal package structure
- DMML aggregate → aggregate root class with invariant enforcement
- DMML root entity → primary constructor with identity, lifecycle enum, attributes
- DMML child entity → nested or separate class within aggregate package
- DMML value object → `data class` (immutable, equality by all attributes)
- DMML domain event → `data class` with payload attributes
- DMML command → `data class` for input + method on aggregate for handling
- DMML invariants → `require()` / `check()` calls in aggregate methods
- DMML repository → interface in domain + in-memory implementation in infrastructure
- DMML application service → class in application layer coordinating aggregate + repo
- DMML policy → event handler class in application layer
- OpenAPI endpoints → REST controller classes in API layer
- Generate unit tests for: invariant enforcement, lifecycle transitions, value object equality
- Generate integration tests for: command→event flows via API
- Generate build config: Gradle Kotlin DSL + dependencies
- Generate README per domain

**Evaluation:** Generated project must compile, pass all tests, and respond correctly to API calls matching the OpenAPI spec.

## 10. Open Questions

These are the decisions I think you have opinions on:

1. **Language:** Kotlin (my recommendation for DDD purity) vs. Python (for accessibility) vs. something else?

2. **OpenAPI as intermediate artifact:** Worth the extra skill, or go directly from DMML to code? The OpenAPI adds a reviewable artifact but might feel like ceremony for internal APIs.

3. **Repo strategy:** Monorepo with `reference/` folder (my recommendation) vs. separate repo?

4. **Persistence:** In-memory only (simplest, purest) vs. also providing a JPA/SQLAlchemy implementation as an optional adapter?

5. **Event handling:** In-process synchronous events (simplest) vs. async with a lightweight event bus? For a reference implementation, synchronous is fine; for realism, async is better.

6. **How far to automate:** Should the implementation-generator produce code that compiles and passes tests on first run? Or is "90% scaffold + manual refinement" acceptable? The former is a much harder skill to build; the latter is more honest about the current state of LLM code generation.

7. **API granularity:** One API per bounded context (three separate services)? Or one unified API with BC-based routing? For a reference implementation, one process with BC-based packages is simpler. Three separate services is more "real" but adds deployment complexity.

8. **Timeline:** XP 2026 is April 8-11. That's about three weeks. Is the goal to have Joe's Pizza running by then? All three? Or is this a multi-month effort with the presentation showing the pipeline concept + partial results?

9. **Code generation skill naming:** `implementation-generator` is descriptive but clunky. Alternatives: `code-scaffolder`, `reference-builder`, `domain-implementer`, `ddd-coder`. What feels right?

10. **Should we create a new spec?** I argued against it above (use OpenAPI instead of inventing something), but there might be value in a lightweight "Implementation Profile" spec that captures the technology decisions in a standard way. This would make the pipeline fully reproducible: same DMML + same profile → same code.
