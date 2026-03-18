# AGENTS.md — Reference Implementation Conventions

**Project:** DDD Meets GenAI — Reference Implementations
**Authors:** Marden Neubert & Joseph Yoder
**Date:** March 2026

This file defines the architectural conventions and technology decisions for
generating reference implementations from DMML domain models. It is designed
to be read by any AI coding agent (Claude Code, Cursor, GitHub Copilot, Codex,
or similar) as the authoritative source of project conventions.

**The key design principle:** The DMML is the specification. This file defines
how to turn that specification into running code. Changing the decisions in
this file (language, framework, persistence, architecture) should produce a
different implementation from the _same_ DMML — without touching the domain
model. That separation is the whole point.

---

## 1. Technology Stack

| Concern | Choice | Rationale |
|---|---|---|
| Language | **TypeScript 5.x** | Accessibility for a broad audience. Strong typing for DDD patterns. |
| Runtime | **Node.js 22+** | LTS, native ESM, built-in test runner available as fallback. |
| HTTP Framework | **Fastify 5.x** | Lightweight, schema-first, fast. Less opinionated than NestJS. |
| Validation | **Zod 3.x** | Runtime schema validation with TypeScript inference. Maps cleanly to DMML attributes and invariants. |
| Testing | **Vitest 3.x** | Fast, ESM-native, Jest-compatible API. Excellent DX. |
| Package Manager | **pnpm** | Strict, fast, workspace support for monorepo. |
| Build | **tsup** or **tsc** | Simple bundling. No Webpack complexity. |
| Linting | **Biome** | Fast, opinionated, replaces ESLint + Prettier. |

### Why TypeScript Over Kotlin

Kotlin maps more naturally to DDD patterns (`data class`, `sealed class`,
`require()`). We chose TypeScript because: (1) broader audience accessibility
at XP 2026, (2) demonstrates that the DMML-to-code pipeline is language-
agnostic — the domain model doesn't care about the target language, and
(3) TypeScript's structural typing is "good enough" with disciplined use of
branded types and readonly patterns.

**This is a pluggable decision.** The same DMML + a Kotlin version of this
AGENTS.md file would produce a Kotlin/Spring Boot implementation. The domain
modeling work carries over completely.

---

## 2. Architecture: Hexagonal (Ports & Adapters)

Every bounded context follows hexagonal architecture as described by Vernon
(IDDD Chapter 4). The domain layer is the center with zero external
dependencies. Everything else depends inward.

```
┌─────────────────────────────────────────────────┐
│                  API Layer (Inbound Adapters)    │
│            Fastify routes → Application Services │
├─────────────────────────────────────────────────┤
│               Application Layer                  │
│       Use-case orchestration, event dispatch      │
├─────────────────────────────────────────────────┤
│                 Domain Layer                      │
│  Aggregates, Entities, Value Objects, Events,    │
│  Commands, Invariants, Repository Interfaces     │
├─────────────────────────────────────────────────┤
│           Infrastructure (Outbound Adapters)     │
│     In-memory repos, event publisher, ACLs       │
└─────────────────────────────────────────────────┘
```

### Dependency Rules

1. **Domain layer imports nothing** outside itself. No framework types, no
   infrastructure, no HTTP concepts. Pure TypeScript with Zod schemas.
2. **Application layer imports domain only.** It orchestrates aggregates,
   repositories (via interfaces), and event dispatch.
3. **Infrastructure implements domain interfaces.** Repository implementations,
   event publisher adapters, ACL translators.
4. **API layer calls application services.** Thin Fastify route handlers that
   translate HTTP requests into commands and return responses.

### Package Structure Per Bounded Context

Each bounded context is a self-contained package in the pnpm workspace:

```
packages/
  bc-order-management/
    src/
      domain/
        model/              # Aggregates, entities, value objects
          Order.ts          # Aggregate root
          OrderItem.ts      # Child entity
          Money.ts          # Value object
          OrderStatus.ts    # Lifecycle enum/union
        event/              # Domain events
          OrderPlaced.ts
          PaymentCompleted.ts
        command/            # Command types
          PlaceOrder.ts
          SelectPizzaType.ts
        repository/         # Repository interfaces (ports)
          OrderRepository.ts
        service/            # Domain services (if any)
      application/
        PlaceOrderService.ts    # Application service
        policy/                 # Event-driven policies
          PlaceOrderOnPayment.ts
      infrastructure/
        persistence/
          InMemoryOrderRepository.ts
        event/
          InProcessEventPublisher.ts
        acl/                    # Anti-corruption layers
          PaymentGatewayACL.ts
      api/
        routes/
          orderRoutes.ts    # Fastify route definitions
        schemas/            # Zod schemas for API validation
          orderSchemas.ts
    test/
      domain/               # Unit tests for domain logic
      application/          # Integration tests for use cases
      api/                  # API acceptance tests
    package.json
    tsconfig.json
```

### One API Per Bounded Context

Each bounded context runs as its own Fastify instance on its own port. For the
reference implementation, all three can run in the same process for simplicity,
but the package boundary is strict — no shared imports between BC packages
except through published events.

---

## 3. Persistence: In-Memory

All repositories are implemented as `Map<string, Aggregate>` behind the
repository interface. This is deliberate:

- **Focus stays on domain logic**, not database wiring.
- **The hexagonal boundary is real.** Swapping in PostgreSQL/Prisma or
  MongoDB/Mongoose is a matter of writing new adapters that implement the
  same repository interface.
- **Tests run fast.** No database setup, no teardown, no flaky connections.
- **Demonstrates the architecture.** The repository interface IS the port.
  The in-memory implementation IS the adapter. This is hexagonal architecture
  made concrete.

```typescript
// Domain port (in domain/repository/)
export interface OrderRepository {
  save(order: Order): Promise<void>;
  findById(orderId: string): Promise<Order | null>;
  findByCustomerId(customerId: string): Promise<Order[]>;
}

// Infrastructure adapter (in infrastructure/persistence/)
export class InMemoryOrderRepository implements OrderRepository {
  private readonly store = new Map<string, Order>();

  async save(order: Order): Promise<void> {
    this.store.set(order.orderId, order);
  }

  async findById(orderId: string): Promise<Order | null> {
    return this.store.get(orderId) ?? null;
  }

  async findByCustomerId(customerId: string): Promise<Order[]> {
    return [...this.store.values()].filter(o => o.customerId === customerId);
  }
}
```

Repository methods are `async` even though in-memory operations are synchronous.
This preserves the interface contract — a real database adapter would be async.

---

## 4. Event Handling: In-Process Synchronous

Domain events are dispatched synchronously within the same process. No message
broker, no event bus library, no async complexity.

```typescript
// Simple event dispatcher
type EventHandler = (event: DomainEvent) => Promise<void>;

export class EventDispatcher {
  private handlers = new Map<string, EventHandler[]>();

  on(eventType: string, handler: EventHandler): void {
    const existing = this.handlers.get(eventType) ?? [];
    this.handlers.set(eventType, [...existing, handler]);
  }

  async dispatch(event: DomainEvent): Promise<void> {
    const handlers = this.handlers.get(event.type) ?? [];
    for (const handler of handlers) {
      await handler(event);
    }
  }
}
```

### Cross-BC Communication

When an event in one bounded context triggers behavior in another (e.g.,
`evt-order-placed` in Order Management triggers `pol-notify-kitchen-on-order-placed`
in Kitchen), the event dispatcher connects them. The policy in the downstream
BC subscribes to events from the upstream BC.

This is the actor-model style: each BC processes events sequentially,
maintaining its own state. No shared mutable state between BCs.

**Why not async:** For a reference implementation, synchronous dispatch makes
the flow easier to follow, debug, and test. The architecture supports swapping
in an async event bus (RabbitMQ, Kafka, even a simple Node.js EventEmitter in
async mode) without changing domain or application code — only the
infrastructure adapter changes.

---

## 5. Domain Modeling Patterns in TypeScript

### 5.1 Value Objects

Immutable, equality by value. Use `readonly` and branded types.

```typescript
// Branded type for type safety
type Money = Readonly<{
  readonly amount: number;
  readonly currency: string;
}>;

function createMoney(amount: number, currency: string = "BRL"): Money {
  if (amount < 0) throw new DomainError("Amount must be non-negative");
  return Object.freeze({ amount, currency });
}

function moneyEquals(a: Money, b: Money): boolean {
  return a.amount === b.amount && a.currency === b.currency;
}
```

### 5.2 Entities

Identity-based, mutable state, lifecycle tracking.

```typescript
export class Order {
  readonly orderId: string;
  private _status: OrderStatus;
  private readonly _items: OrderItem[];

  // Private constructor — use factory or command
  private constructor(orderId: string, customerId: string) { ... }

  get status(): OrderStatus { return this._status; }
  get items(): ReadonlyArray<OrderItem> { return this._items; }

  // Command methods enforce invariants and emit events
  selectPizzaType(items: OrderItemInput[]): TypeOfPizzasSelected {
    this.assertStatus("Created", "Configuring");
    if (items.length === 0) throw new DomainError("At least one item required");
    this._items.push(...items.map(toOrderItem));
    this._status = "Configuring";
    return { type: "TypeOfPizzasSelected", orderId: this.orderId, items: ... };
  }
}
```

### 5.3 Aggregate Roots

Aggregates own their children. External access goes through the root only.
Child entities are not directly accessible from outside the aggregate.

### 5.4 Domain Events

Plain readonly objects with a `type` discriminator.

```typescript
export type OrderPlacedEvent = Readonly<{
  type: "OrderPlaced";
  orderId: string;
  customerId: string;
  items: ReadonlyArray<OrderItemSummary>;
  deliveryAddress: DeliveryAddress;
  price: Money;
  placedAt: string; // ISO 8601
}>;
```

### 5.5 Commands

Command types are inputs to aggregate methods. Validated at the API boundary
with Zod, then passed to the application service.

```typescript
export const PlaceOrderSchema = z.object({
  customerId: z.string().uuid(),
  items: z.array(OrderItemInputSchema).min(1),
  deliveryAddress: DeliveryAddressSchema,
});
export type PlaceOrderCommand = z.infer<typeof PlaceOrderSchema>;
```

---

## 6. Error Taxonomy

Errors follow a consistent classification that maps to HTTP status codes at
the API boundary.

| Error Type | Domain Meaning | HTTP Status | Example |
|---|---|---|---|
| `DomainError` | Invariant violation or business rule failure | 422 | "Order must have at least one item" |
| `NotFoundError` | Aggregate not found by ID | 404 | "Order abc-123 not found" |
| `ConflictError` | Invalid state transition | 409 | "Cannot place order in Created state" |
| `ValidationError` | Input validation failure (Zod) | 400 | "customerId must be a UUID" |
| `ExternalServiceError` | External system failure (Payment Gateway) | 502 | "Payment gateway timeout" |

```typescript
export class DomainError extends Error {
  readonly code = "DOMAIN_ERROR" as const;
  constructor(message: string) {
    super(message);
    this.name = "DomainError";
  }
}

export class NotFoundError extends Error {
  readonly code = "NOT_FOUND" as const;
  constructor(entityType: string, id: string) {
    super(`${entityType} ${id} not found`);
    this.name = "NotFoundError";
  }
}

export class ConflictError extends Error {
  readonly code = "CONFLICT" as const;
  constructor(message: string) {
    super(message);
    this.name = "ConflictError";
  }
}
```

### Error Response Format

All API errors return a consistent JSON structure:

```json
{
  "error": {
    "code": "DOMAIN_ERROR",
    "message": "Order must have at least one item",
    "details": {}
  }
}
```

---

## 7. Testing Strategy

Tests are the primary harness for the coding agent loop. They are derived
mechanically from the DMML and run repeatedly until green.

### 7.1 Test Categories (Derived from DMML)

| DMML Source | Test Type | What It Verifies |
|---|---|---|
| Invariants | Unit tests | Business rules hold under valid and invalid inputs |
| Command preconditions | Guard tests | Commands reject invalid state transitions |
| Entity lifecycle | State machine tests | Only valid transitions are allowed |
| Domain events + `emitted_on` | Emission tests | Correct events fire on correct transitions |
| Value object `equality` | Equality tests | Immutability and value-based comparison |
| Policies + `trigger_events` | Reactive behavior tests | Events trigger correct downstream commands |
| Aggregate boundaries | Encapsulation tests | Child entities not accessible outside aggregate |
| Context map relationships | Integration tests | Cross-BC event flow works correctly |
| OpenAPI endpoints | Acceptance tests | HTTP API matches spec (request/response/errors) |

### 7.2 Test Derivation Examples

**From an invariant:**
```yaml
# DMML
invariants:
  - "Order must have at least one OrderItem"
```
```typescript
// Test
describe("Order invariants", () => {
  it("rejects placement with zero items", () => {
    const order = createOrder({ customerId: "abc" });
    expect(() => order.place()).toThrow("at least one");
  });
});
```

**From a lifecycle:**
```yaml
# DMML
lifecycle:
  - Created
  - Configuring
  - PaymentPending
  - Paid
  - Placed
```
```typescript
// Tests
describe("Order lifecycle", () => {
  it("transitions Created → Configuring on pizza selection", () => { ... });
  it("rejects payment entry from Created state", () => { ... });
  it("rejects placement from Configuring state", () => { ... });
});
```

**From a policy:**
```yaml
# DMML
policies:
  - id: pol-place-order-on-payment
    trigger_events: [evt-payment-completed]
    rule: "Whenever Payment Completed, finalize order and emit Order Placed"
```
```typescript
// Test
describe("PlaceOrderOnPayment policy", () => {
  it("emits OrderPlaced when PaymentCompleted is dispatched", async () => {
    const events: DomainEvent[] = [];
    dispatcher.on("OrderPlaced", (e) => events.push(e));
    await dispatcher.dispatch(paymentCompletedEvent);
    expect(events).toHaveLength(1);
    expect(events[0].type).toBe("OrderPlaced");
  });
});
```

### 7.3 The Agent Loop (TDD from DMML)

The workflow for generating a reference implementation:

1. **Generate tests from DMML + OpenAPI.** The test suite is the spec.
2. **Run tests.** Everything is red (no implementation yet).
3. **Generate domain code** to make domain tests pass.
4. **Generate application code** to make integration tests pass.
5. **Generate infrastructure + API code** to make acceptance tests pass.
6. **Run tests again.** If red, fix. Repeat until green.

This is TDD with the domain model as the source of truth — the tests are
generated, not hand-written. The agent loop continues until all tests pass.

---

## 8. API Conventions

API design follows the OpenAPI specification generated by the `api-designer`
skill. The conventions below apply to all bounded contexts.

### 8.1 URL Structure

```
/{bc-name}/{aggregate-or-resource}/{action-or-id}
```

Examples:
- `POST /order-management/orders` — Create/request a new order
- `POST /order-management/orders/:orderId/select-pizza` — Execute a command
- `GET  /order-management/orders/:orderId` — Read model / query
- `POST /kitchen/kitchen-orders/:id/prep-pizza` — Kitchen command
- `POST /delivery/deliveries/:id/notify-delivered` — Delivery command

### 8.2 Request/Response

- **Commands** are `POST` with JSON body matching the command attributes.
- **Queries** are `GET` returning the read model attributes.
- **Command responses** include the emitted event(s) in the response body.
- **All responses** include standard error format on failure.

### 8.3 Content Type

`application/json` for all requests and responses. No XML, no form encoding.

---

## 9. Project Structure (Monorepo)

```
reference/
  joes-pizza/                    # First implementation
    package.json                 # Root workspace config
    pnpm-workspace.yaml
    vitest.config.ts             # Shared test config
    packages/
      bc-order-management/       # One package per bounded context
      bc-kitchen/
      bc-delivery/
      shared/                    # Shared kernel (value objects, event types)
    openapi/
      joes-pizza-api.openapi.yaml  # Generated by api-designer skill
```

### The `shared` Package

Cross-cutting types that appear in multiple bounded contexts:
- `DomainEvent` base type
- `EventDispatcher` interface
- Common value objects used across BCs (e.g., `Money`)
- Error types (`DomainError`, `NotFoundError`, etc.)

This is minimal — most types live inside their bounded context. Only truly
shared infrastructure contracts go here.

---

## 10. What This File Does NOT Cover

The following are handled by the DMML, not by this file:
- Domain structure (subdomains, bounded contexts, aggregates)
- Business rules and invariants
- Domain events and their payloads
- Commands and their preconditions
- Context map relationships

The following are out of scope for the reference implementation:
- UI/UX (no frontend — API only)
- Deployment (no Docker, no Kubernetes, no CI/CD)
- Production persistence (no database — in-memory only)
- Authentication/authorization (no auth — open API)
- Monitoring/observability (no metrics, no tracing)

---

## 11. Portability Statement

This AGENTS.md defines ONE set of technology choices. The DMML domain model
is independent of all of them. To produce a different implementation:

1. Copy this file.
2. Change the technology decisions (e.g., Kotlin + Spring Boot + PostgreSQL).
3. Run the agent loop with the same DMML + new AGENTS.md.
4. Get a different implementation of the same domain.

The domain modeling work — Event Storming, ESML, DMML — carries over
completely. That is the value proposition of spec-driven domain design.
