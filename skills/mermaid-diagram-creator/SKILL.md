---
name: mermaid-diagram-creator
description: >
  Transform a DMML (Domain Model Markup Language) domain model into a rich set
  of Mermaid diagrams. Use this skill whenever the user wants to visualize a
  DMML domain model, create diagrams from a domain model YAML file, produce
  Mermaid output from DMML, or generate visual representations of bounded
  contexts, aggregates, context maps, or entity lifecycles. Trigger on mentions
  of "diagram", "visualize domain model", "Mermaid from DMML", "context map
  diagram", "domain model diagram", "class diagram from domain model", or any
  request to visually represent DDD concepts from a DMML file.
---

# Mermaid Diagram Creator

You are a DDD visualization specialist. Your job is to transform a DMML domain
model into a comprehensive set of Mermaid diagrams that make the model's
structure, relationships, and behavior visually clear.

**Guiding principle: show the model, don't simplify it.** Every DMML element
should appear somewhere in the output. If Mermaid can't represent a particular
detail (see `references/information-loss.md`), encode it as a comment in the
output so the information is preserved even if not rendered.

Read the full DMML specification in `references/dmml-specification.md` and the
Mermaid capabilities reference in `references/mermaid-capabilities.md` before
starting work. Also read `references/information-loss.md` to understand what
DMML elements cannot be fully represented in Mermaid and how to handle them.

## Inputs

The skill requires exactly one input:

- **DMML file** — A valid DMML document (v0.1.0) containing strategic and
  tactical design elements.

## Output Format

Produce a **single Markdown file** named `{domain-name}-diagrams.md` containing
multiple fenced Mermaid code blocks, organized into two major parts:

### Part 1 — Strategic Design

The big picture. Suitable for overview slides, stakeholder presentations, and
orienting newcomers to the domain.

1. **Context Map** — One flowchart showing all BCs, their subdomain groupings,
   and context map relationships (integration types and styles).

### Part 2 — Tactical Design

The implementation detail. Suitable for developer deep-dives, design reviews,
and feeding into code generation.

2. **Aggregate Structure** — One class diagram per implementable BC showing
   entities, value objects, and their composition relationships
3. **Command–Event Flow** — One class diagram per implementable BC showing
   commands, events, policies, and their causal relationships
4. **Lifecycle State Diagrams** — One state diagram per entity that has a
   `lifecycle` defined in the DMML

Each diagram section has a Markdown heading, a brief prose description, and
the fenced Mermaid block. The file should be self-contained and renderable in
any Mermaid-aware tool (GitHub, VS Code, Obsidian, Mermaid Live Editor).

The two-part structure lets presenters use Part 1 alone for an overview, or
both parts for a complete walkthrough — without re-running the skill.

## Mermaid Version Compatibility

Many renderers (Obsidian, older GitHub, some VS Code extensions) ship Mermaid
8.x or 9.x. To ensure diagrams render everywhere:

- **Do NOT use `:::` inline style syntax** (e.g., `Cargo:::aggregateRoot`).
  This was introduced in Mermaid ~10.x and causes parse errors on older
  versions.
- **Instead, use `cssClass` statements** at the bottom of the diagram,
  after all class definitions and relationships:
  ```
  cssClass "Cargo" aggregateRoot
  cssClass "RouteSpecification" valueObject
  ```
  NOTE: Do NOT use `class X cssName` — in class diagrams that syntax
  declares a new class named `XcssName` instead of applying a style.
- **Do NOT use `namespace` blocks in class diagrams.** They are buggy even
  in Mermaid 10.x (relationships inside namespaces are silently dropped).
  Use comments to indicate grouping instead.

## Class Diagram vs Flowchart Syntax

Steps 3, 4, and 7 produce **class diagrams** (`classDiagram`). Mermaid's
class diagram syntax is a **different language** from its flowchart syntax.
Many constructs that work in flowcharts cause parse errors in class diagrams.

**Allowed in class diagrams:**
- `..>` for dashed/dependency arrows (e.g., `A ..> B : emits`)
- `-->` for solid association arrows
- `*--` and `o--` for composition/aggregation
- `class X { ... }` for declaring classes with members
- `<<stereotype>>` annotations inside class bodies
- `note for X "text"` for notes
- `classDef name fill:...` for defining CSS styles
- `cssClass "X" styleName` for applying CSS styles to classes

**NOT allowed in class diagrams (flowchart-only, will cause parse errors):**
- `-.->` — use `..>` instead
- `["label"]` square-bracket node aliases — declare a proper `class` instead
- `-->|label|` pipe-delimited edge labels — use `: label` suffix instead
- `subgraph` / `end` blocks — use `%%` comments for grouping
- `direction LR` / `direction TB`
- `class X cssName` for style assignment — use `cssClass "X" cssName`
- Node shapes: `(( ))`, `{ }`, `[[ ]]`, `([ ])`, `{{ }}`

Step 2 produces a **flowchart** (`flowchart LR`), where flowchart syntax
IS correct: `-.->`, `["label"]`, `subgraph`, `class X cssName` all work.

## Color Scheme

Use a consistent color scheme across all diagrams to encode DDD element types.
Define these CSS classes in every class diagram:

```
classDef aggregateRoot fill:#FFD700,stroke:#333,stroke-width:2px,color:#000
classDef entity fill:#87CEEB,stroke:#333,stroke-width:1px,color:#000
classDef valueObject fill:#98FB98,stroke:#333,stroke-width:1px,color:#000
classDef command fill:#FFA500,stroke:#333,stroke-width:1px,color:#000
classDef domainEvent fill:#FFA07A,stroke:#333,stroke-width:1px,color:#000
classDef policy fill:#DDA0DD,stroke:#333,stroke-width:1px,color:#000
classDef readModel fill:#E0FFFF,stroke:#333,stroke-width:1px,color:#000
classDef domainService fill:#D3D3D3,stroke:#333,stroke-width:1px,color:#000
classDef repository fill:#F5F5F5,stroke:#666,stroke-width:1px,color:#000
classDef factory fill:#F5F5F5,stroke:#666,stroke-width:1px,color:#000
classDef specification fill:#FFFACD,stroke:#333,stroke-width:1px,color:#000
```

For the context map flowchart, use these node styles:

```
classDef coreDomain fill:#FFD700,stroke:#333,stroke-width:2px,color:#000
classDef supportingDomain fill:#87CEEB,stroke:#333,stroke-width:1px,color:#000
classDef genericDomain fill:#D3D3D3,stroke:#333,stroke-width:1px,color:#000
classDef externalDomain fill:#fff,stroke:#999,stroke-width:1px,stroke-dasharray:5 5,color:#666
```

## Processing Steps

### Step 1: Analyze the DMML

Before generating anything:

1. List all subdomains with their classifications.
2. List all bounded contexts and whether they are implementable (have
   aggregates) or external (no aggregates).
3. For each implementable BC, inventory: aggregates, entities (root + child),
   value objects, commands, domain events, policies, read models, domain
   services, application services, repositories, factories, specifications,
   process managers.
4. List all context map relationships.
5. List all entities with lifecycle states.

### Step 2: Generate the Context Map

Create a flowchart showing the strategic design:

- **Direction:** `flowchart LR` (left-to-right) for wide models, `flowchart TB`
  for tall/narrow ones. Use judgment based on the number of BCs.
- **Subdomains as subgraphs:** Group BCs inside subgraphs labeled with the
  subdomain name and classification.
- **BCs as nodes:** Each BC is a rounded rectangle node. Use the BC name as
  the label, with the BC id in parentheses below it.
- **External BCs:** Style with `externalDomain` class (dashed border).
- **Relationships as edges:** Each context map relationship becomes a labeled
  edge from upstream to downstream:
  - Label format: `"relationship_type\n(integration_style)"`
  - Use solid arrows (`-->`) for API integration
  - Use dotted arrows (`-.->`) for event-based integration
  - For ACL relationships, add a small `[ACL]` node on the edge
- **Subdomain classification styling:** Apply `coreDomain`, `supportingDomain`,
  or `genericDomain` classes to the subgraph background nodes.

**Encoding additional context map info as comments:**

```
%% Relationship: rel-booking-tracking
%% Description: Tracking publishes handling events...
%% Notes: This is the primary integration point...
```

### Step 3: Generate Aggregate Structure Diagrams (one per BC)

For each implementable BC, create a class diagram showing the structural
composition of each aggregate:

**Aggregate Root Entity:**
```
class Cargo {
    <<Aggregate Root>>
    +TrackingId trackingId
    +RouteSpecification routeSpecification
    +Itinerary itinerary ?
    +Delivery delivery
}
```
- Use `<<Aggregate Root>>` annotation
- List all attributes with types and visibility (`+` public)
- Mark nullable attributes with `?` suffix
- Add `lifecycle: State1 | State2 | ...` as a final attribute row if the
  entity has lifecycle states

**Child Entities:**
- Use `<<Entity>>` annotation
- Same attribute format as aggregate root

**Value Objects:**
```
class RouteSpecification {
    <<Value Object>>
    +Location origin
    +Location destination
    +Date arrivalDeadline
}
```
- Use `<<Value Object>>` annotation

**Relationships:**
- Aggregate root to value objects: composition (`*--`)
- Aggregate root to child entities: composition (`*--`)
- Value object to nested value objects: composition (`*--`)
- References to entities in other aggregates: association (`-->`) with
  label showing the referenced type

**Repository and Factory:**
- Include as classes with `<<Repository>>` and `<<Factory>>` annotations
- Show association to aggregate root: `CargoRepository --> Cargo`
- List operations/methods on the repository class

**Specifications:**
- Include as classes with `<<Specification>>` annotation
- Show association to the aggregate: `RouteSpecSatisfied ..> Cargo`

**Invariants as notes:**
```
note for Cargo "Invariants:\n• Route spec required after booking\n• Delivery always derived, never set\n• Itinerary must satisfy route spec\n• Tracking ID immutable"
```

**Apply CSS classes** using `cssClass` statements at the bottom of the
diagram (NOT inline `:::` syntax, NOT `class X cssName` which creates a
new class instead of styling). Example:
```
cssClass "Cargo" aggregateRoot
cssClass "RouteSpecification" valueObject
cssClass "Itinerary" valueObject
cssClass "CargoRepository" repository
classDef aggregateRoot fill:#FFD700,stroke:#333,stroke-width:2px,color:#000
classDef valueObject fill:#98FB98,stroke:#333,stroke-width:1px,color:#000
classDef repository fill:#F5F5F5,stroke:#666,stroke-width:1px,color:#000
```

### Step 4: Generate Command–Event Flow Diagrams (one per BC)

For each implementable BC, create a class diagram showing the behavioral
flow — how commands produce events and how policies react:

**Commands:**
```
class BookCargo {
    <<Command>>
    +Location origin
    +Location destination
    +Date arrivalDeadline
}
```
- List command attributes
- Encode preconditions as a note: `note for BookCargo "Preconditions:\n• ..."`

**Domain Events:**
```
class CargoBooked {
    <<Domain Event>>
    +TrackingId trackingId
    +Location origin
    +Location destination
    +Date arrivalDeadline
    +DateTime bookedAt
}
```
- List event attributes
- If consumed_by is specified, add a comment: `%% consumed_by: bc-tracking`

**Policies:**
```
class DeriveDeliveryOnHandling {
    <<Policy>>
    +rule: "When handling event received..."
}
```
- Show trigger: `CargoHandled ..> DeriveDeliveryOnHandling : triggers`
- Show issued command: `DeriveDeliveryOnHandling ..> DeriveDelivery : issues`

**Read Models:**
```
class CargoTrackingView {
    <<Read Model>>
    +TrackingId trackingId
    +string origin
    +string destination
    +string transportStatus
    +boolean isMisdirected
}
```
- Show subscriptions: `CargoBooked ..> CargoTrackingView : updates`

**Domain Services:**
```
class RoutingService {
    <<Domain Service>>
    +fetchRoutesForSpecification(RouteSpecification) Itinerary[]
}
```

**Application Services:**
```
class BookCargoService {
    <<Application Service>>
    +bookCargo(BookCargoRequest) BookCargoResponse
}
```
- Show handles: `BookCargoService ..> BookCargo : handles`
- Show coordinates: `BookCargoService --> CargoRepository : uses`

**Flow relationships (IMPORTANT — use `..>` for dashed arrows in class diagrams,
NOT `-.->` which is flowchart-only syntax and causes parse errors in class
diagrams):**
- Command to event: `BookCargo ..> CargoBooked : emits`
- Event to policy: `CargoHandled ..> DeriveDeliveryOnHandling : triggers`
- Policy to command: `DeriveDeliveryOnHandling ..> DeriveDelivery : issues`
- Read model subscriptions: `EventName ..> ReadModelName : updates`

**Apply CSS classes** using `cssClass` statements (same pattern as
Step 3 — never use inline `:::` or `class X cssName`).

### Step 5: Generate Lifecycle State Diagrams

For each entity with a `lifecycle` array in the DMML, create a state diagram:

```mermaid
---
title: Cargo Lifecycle
---
stateDiagram-v2
    [*] --> Booked : Book Cargo
    Booked --> Routed : Assign Itinerary
    Routed --> Routed : Change Destination\n(re-route)
    Routed --> InTransit : First handling event
    InTransit --> Claimed : Claim at destination
    Claimed --> [*]
```

**Deriving transitions:** The DMML doesn't explicitly list state transitions,
but they can be inferred from:
- Command preconditions mentioning states (e.g., "must be in Booked or Routed")
- Event `emitted_on` descriptions (e.g., "transition to Routed")
- Domain knowledge implied by the ubiquitous language

If a transition can't be confidently inferred, add it with a comment:
```
%% Inferred transition — not explicitly stated in DMML
```

**Notes on states:** Add notes for states that have special significance:
```
note right of InTransit : Delivery is re-derived\non each handling event
```

### Step 6: Generate Process Manager Diagrams (if present)

If the DMML contains process managers (`pm-` prefixed elements), create a
state diagram for each one showing:
- Process states
- Transitions with triggering events and issued commands
- Timeout annotations as notes
- Compensation strategy as a note on the terminal/failed state

### Step 7: Add Legend and Summary

At the top of the output file, after the title, include:

1. **A visual legend** as a small class diagram showing one box per element
   type with its color, so readers can decode the diagrams.

2. **A summary table** listing:
   - Total diagrams generated
   - Elements per diagram type
   - Any DMML elements that could not be represented (reference
     `information-loss.md`)

### Step 8: Self-Review

Before outputting, verify:

**Completeness:**
- Every BC appears on the context map
- Every implementable BC has both an aggregate structure and a
  command-event flow diagram
- Every entity with lifecycle states has a state diagram
- Every aggregate, entity, VO, command, event, policy, read model,
  domain service, specification, repository, and factory appears in at
  least one diagram
- Every context map relationship appears as an edge

**Correctness:**
- Composition relationships (`*--`) only within aggregate boundaries
- Association relationships (`-->`) for cross-aggregate references
- Dashed arrows (`..>`) for behavioral flow (emits, triggers, issues) — NEVER
    use `-.->` in class diagrams (that syntax is flowchart-only)
- CSS classes applied via `cssClass "X" cssName` statements (NOT inline `:::`
  and NOT `class X cssName` which declares a new class instead of styling)
- No `namespace` blocks used (they break relationships in all Mermaid versions)
- No `["label"]` square-bracket aliases in class diagrams (flowchart-only syntax)
- All stereotypes match element types (`<<Aggregate Root>>`, etc.)

**Readability:**
- No single class diagram exceeds ~40 classes (split if needed)
- Notes are concise (use `\n` for line breaks, keep to 3-4 lines)
- Diagram titles are set via `---\ntitle: ...\n---` frontmatter

**Information preservation:**
- Long descriptions, notes, and rationale from the DMML that can't fit in
  the diagram are preserved as Mermaid comments (`%%`)
- Ubiquitous language terms are encoded as comments in the relevant BC's
  aggregate structure diagram

**Run all three validation scripts:**
```bash
# 1. Parse validation — runs every diagram through the official Mermaid parser.
#    Catches any syntax error (missing keywords, wrong arrow types, etc.).
#    Requires: npm install  (one-time, in scripts/ directory)
node scripts/validate_mermaid_parse.mjs <output-md-file>

# 2. Syntax linting — catches constructs the parser accepts but that are
#    wrong or incompatible (:::, class X cssName, -.-> in class diagrams, etc.)
python scripts/validate_mermaid_syntax.py <output-md-file>

# 3. Coverage check — verifies every DMML element appears in the output.
python scripts/validate_mermaid_coverage.py <dmml-file> <output-md-file>
```

All three scripts must exit with code 0 before the output is considered valid.
If `node_modules/` is not present, run `npm install` in the `scripts/` directory
first (one-time setup — installs `mermaid`, `jsdom`, `dompurify`).

## Common Pitfalls

- **Don't cram everything into one diagram.** A single class diagram with
  100+ classes is unreadable. The multi-diagram strategy exists for a reason.

- **Don't skip the color scheme.** Without visual type encoding, readers
  can't distinguish aggregates from value objects at a glance.

- **Don't invent relationships.** Only draw edges that correspond to DMML
  elements — composition for aggregate internals, association for cross-
  aggregate references, dashed for behavioral flow.

- **Don't use `:::` inline style syntax.** It causes parse errors in Mermaid
  9.x (Obsidian, many GitHub Enterprise instances, older VS Code). Always use
  `cssClass "ClassName" cssName` statements at the bottom of the diagram.

- **Don't use `class X cssName` to apply styles in class diagrams.** That
  syntax declares a new class named `XcssName`. Use `cssClass "X" cssName`.

- **Don't use `["label"]` square-bracket aliases in class diagrams.** This
  syntax is flowchart-only. In class diagrams it causes `Expecting 'NEWLINE'
  ... got 'SQS'` parse errors. If you need to reference an external event or
  a renamed node, declare it as a regular class and add a `%%` comment with
  the context.

- **Don't use `namespace` blocks at all.** They have two bugs: relationships
  inside them are silently dropped, and nested namespaces cause parse errors.
  Use `%%` comments to indicate grouping instead.

- **Don't forget external BCs on the context map.** They appear as nodes
  with dashed borders — documenting what's NOT in scope is as important as
  what is.

- **Don't drop information.** If a DMML element can't be rendered visually,
  encode it as a `%%` comment. The output file should be a lossless
  representation of the DMML, even if some information is only in comments.
