# Cargo Shipping Domain Model — Mermaid Diagrams

## Summary

This document contains a comprehensive set of Mermaid diagrams generated from the **Cargo Shipping DMML** (Domain Model Markup Language) specification.

**Total Diagrams**: 10 (1 context map + 2 aggregate structure diagrams + 2 command-event flow diagrams + 4 lifecycle state diagrams)

**Coverage Summary**:
- Bounded Contexts: 5 (4 implementable, 1 external)
- Aggregates: 4
- Entities: 5
- Value Objects: 6
- Commands: 6
- Domain Events: 8
- Policies: 1
- Specifications: 2
- Domain Services: 2
- Application Services: 4
- Repositories: 4
- Factories: 1
- Read Models: 1
- Entities with Lifecycles: 2

---

## Legend

```mermaid
---
title: DDD Concept Legend
---
classDiagram
    class AggregateRoot {
        <<Aggregate Root>>
    }
    class Entity {
        <<Entity>>
    }
    class ValueObject {
        <<Value Object>>
    }
    class Command {
        <<Command>>
    }
    class DomainEvent {
        <<Domain Event>>
    }
    class Policy {
        <<Policy>>
    }
    class ReadModel {
        <<Read Model>>
    }
    class DomainService {
        <<Domain Service>>
    }
    class Repository {
        <<Repository>>
    }
    class Factory {
        <<Factory>>
    }
    class Specification {
        <<Specification>>
    }

    cssClass "AggregateRoot" aggregateRoot
    cssClass "Entity" entity
    cssClass "ValueObject" valueObject
    cssClass "Command" command
    cssClass "DomainEvent" domainEvent
    cssClass "Policy" policy
    cssClass "ReadModel" readModel
    cssClass "DomainService" domainService
    cssClass "Repository" repository
    cssClass "Factory" factory
    cssClass "Specification" specification

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

---

# Part 1 — Strategic Design

## Context Map

```mermaid
---
title: Cargo Shipping — Context Map
---
flowchart LR
    subgraph Shipping["Subdomain: Shipping (core)"]
        BC-Booking["Booking<br/>(bc-booking)"]
        BC-Tracking["Tracking<br/>(bc-tracking)"]
    end

    subgraph VoyageMgt["Subdomain: Voyage Management (supporting)"]
        BC-Voyage["Voyage<br/>(bc-voyage)"]
    end

    subgraph Routing["Subdomain: Routing (supporting)"]
        BC-Routing["Routing<br/>(bc-routing)"]
    end

    subgraph LocationRef["Subdomain: Location (generic)"]
        BC-Location["Location<br/>(bc-location)"]
    end

    BC-Tracking -->|"customer_supplier\n(events)"| BC-Booking
    BC-Routing -->|"anticorruption_layer\n(api)"| BC-Booking
    BC-Voyage -->|"conformist\n(api)"| BC-Booking
    BC-Voyage -->|"conformist\n(api)"| BC-Tracking
    BC-Location -->|"open_host_service\n(api)"| BC-Booking
    BC-Location -->|"open_host_service\n(api)"| BC-Tracking
    BC-Location -->|"open_host_service\n(api)"| BC-Voyage
    BC-Location -->|"open_host_service\n(api)"| BC-Routing

    class BC-Booking coreDomain
    class BC-Tracking coreDomain
    class BC-Voyage supportingDomain
    class BC-Routing supportingDomain
    class BC-Location genericDomain

    classDef coreDomain fill:#FFD700,stroke:#333,stroke-width:2px,color:#000
    classDef supportingDomain fill:#87CEEB,stroke:#333,stroke-width:1px,color:#000
    classDef genericDomain fill:#D3D3D3,stroke:#333,stroke-width:1px,color:#000
```

---

# Part 2 — Tactical Design

## Booking Context — Aggregate Structure

```mermaid
---
title: Booking Context — Aggregate Structure (Cargo Aggregate)
---
classDiagram
    class Cargo {
        <<Aggregate Root>>
        +TrackingId trackingId
        +RouteSpecification routeSpecification
        +Itinerary itinerary ?
        +Delivery delivery
        lifecycle: Booked | Routed | InTransit | Claimed
    }

    class RouteSpecification {
        <<Value Object>>
        +Location origin
        +Location destination
        +Date arrivalDeadline
    }

    class Itinerary {
        <<Value Object>>
        +Leg[] legs
    }

    class Leg {
        <<Value Object>>
        +VoyageNumber voyageNumber
        +Location loadLocation
        +Location unloadLocation
        +DateTime expectedLoadTime
        +DateTime expectedUnloadTime
    }

    class Delivery {
        <<Value Object>>
        +TransportStatus transportStatus
        +Location lastKnownLocation ?
        +VoyageNumber currentVoyage ?
        +boolean isMisdirected
        +DateTime eta ?
        +boolean isUnloadedAtDestination
        +RoutingStatus routingStatus
    }

    class CargoRepository {
        <<Repository>>
        +save(Cargo)
        +findByTrackingId(TrackingId) Cargo ?
        +findAll() Cargo[]
    }

    class CargoFactory {
        <<Factory>>
        +createCargo(RouteSpecification) Cargo
    }

    class RouteSpecSatisfied {
        <<Specification>>
        +isSatisfiedBy(Itinerary, RouteSpecification) boolean
    }

    Cargo *-- RouteSpecification : contains
    Cargo *-- Itinerary : contains (nullable)
    Cargo *-- Delivery : contains
    Itinerary *-- Leg : contains (ordered list)
    CargoRepository --> Cargo : manages
    CargoFactory --> Cargo : creates
    RouteSpecSatisfied ..> Cargo : validates

    cssClass "Cargo" aggregateRoot
    cssClass "RouteSpecification" valueObject
    cssClass "Itinerary" valueObject
    cssClass "Leg" valueObject
    cssClass "Delivery" valueObject
    cssClass "CargoRepository" repository
    cssClass "CargoFactory" factory
    cssClass "RouteSpecSatisfied" specification

    classDef aggregateRoot fill:#FFD700,stroke:#333,stroke-width:2px,color:#000
    classDef valueObject fill:#98FB98,stroke:#333,stroke-width:1px,color:#000
    classDef repository fill:#F5F5F5,stroke:#666,stroke-width:1px,color:#000
    classDef factory fill:#F5F5F5,stroke:#666,stroke-width:1px,color:#000
    classDef specification fill:#FFFACD,stroke:#333,stroke-width:1px,color:#000
```

## Booking Context — Command-Event Flow

```mermaid
---
title: Booking Context — Command-Event Flow & Policies
---
classDiagram
    class BookCargo {
        <<Command>>
        +Location origin
        +Location destination
        +Date arrivalDeadline
    }

    class AssignItinerary {
        <<Command>>
        +TrackingId trackingId
        +Itinerary itinerary
    }

    class ChangeDestination {
        <<Command>>
        +TrackingId trackingId
        +Location newDestination
    }

    class DeriveDelivery {
        <<Command>>
        +TrackingId trackingId
        +HandlingEvent handlingEvent
    }

    class CargoBooked {
        <<Domain Event>>
        +TrackingId trackingId
        +Location origin
        +Location destination
        +Date arrivalDeadline
        +DateTime bookedAt
    }

    class CargoRouted {
        <<Domain Event>>
        +TrackingId trackingId
        +Itinerary itinerary
    }

    class CargoDestinationChanged {
        <<Domain Event>>
        +TrackingId trackingId
        +RouteSpecification newRouteSpecification
        +Location oldDestination
        +Location newDestination
    }

    class CargoMisdirected {
        <<Domain Event>>
        +TrackingId trackingId
        +HandlingEventType handlingEventType
        +Location location
        +Location expectedNextLocation
    }

    class CargoDelivered {
        <<Domain Event>>
        +TrackingId trackingId
        +DateTime deliveredAt
        +Location destination
    }

    class DeriveDeliveryPolicy {
        <<Policy>>
    }

    class RoutingService {
        <<Domain Service>>
        +fetchRoutesForSpecification(RouteSpecification) Itinerary[]
    }

    class BookCargoService {
        <<Application Service>>
        +bookCargo(BookCargoRequest) BookCargoResponse
    }

    class AssignItineraryService {
        <<Application Service>>
        +assignItinerary(AssignItineraryRequest) AssignItineraryResponse
    }

    class ChangeDestinationService {
        <<Application Service>>
        +changeDestination(ChangeDestinationRequest) ChangeDestinationResponse
    }

    class CargoTrackingView {
        <<Read Model>>
        +TrackingId trackingId
        +string origin
        +string destination
        +string transportStatus
        +string lastKnownLocation
        +DateTime eta
        +boolean isMisdirected
    }

    BookCargo ..> CargoBooked : emits
    AssignItinerary ..> CargoRouted : emits
    ChangeDestination ..> CargoDestinationChanged : emits
    DeriveDelivery ..> CargoMisdirected : may emit
    DeriveDelivery ..> CargoDelivered : may emit

    %% CargoHandled originates from bc-tracking
    CargoHandled ..> DeriveDeliveryPolicy : triggers
    DeriveDeliveryPolicy ..> DeriveDelivery : issues

    %% VoyageDelayed originates from bc-voyage
    VoyageDelayed ..> DeriveDeliveryPolicy : triggers

    CargoBooked ..> CargoTrackingView : updates
    CargoRouted ..> CargoTrackingView : updates
    CargoMisdirected ..> CargoTrackingView : updates
    CargoDelivered ..> CargoTrackingView : updates

    BookCargoService ..> BookCargo : handles
    AssignItineraryService ..> AssignItinerary : handles
    ChangeDestinationService ..> ChangeDestination : handles

    BookCargoService --> CargoRepository
    AssignItineraryService --> CargoRepository
    AssignItineraryService --> RoutingService
    ChangeDestinationService --> CargoRepository

    cssClass "BookCargo" command
    cssClass "AssignItinerary" command
    cssClass "ChangeDestination" command
    cssClass "DeriveDelivery" command
    cssClass "CargoBooked" domainEvent
    cssClass "CargoRouted" domainEvent
    cssClass "CargoDestinationChanged" domainEvent
    cssClass "CargoMisdirected" domainEvent
    cssClass "CargoDelivered" domainEvent
    cssClass "DeriveDeliveryPolicy" policy
    cssClass "RoutingService" domainService
    cssClass "BookCargoService" entity
    cssClass "AssignItineraryService" entity
    cssClass "ChangeDestinationService" entity
    cssClass "CargoTrackingView" readModel

    classDef command fill:#FFA500,stroke:#333,stroke-width:1px,color:#000
    classDef domainEvent fill:#FFA07A,stroke:#333,stroke-width:1px,color:#000
    classDef policy fill:#DDA0DD,stroke:#333,stroke-width:1px,color:#000
    classDef domainService fill:#D3D3D3,stroke:#333,stroke-width:1px,color:#000
    classDef entity fill:#87CEEB,stroke:#333,stroke-width:1px,color:#000
    classDef readModel fill:#E0FFFF,stroke:#333,stroke-width:1px,color:#000
```

## Tracking Context — Aggregate Structure

```mermaid
---
title: Tracking Context — Aggregate Structure (Handling Event Aggregate)
---
classDiagram
    class HandlingEvent {
        <<Aggregate Root>>
        +UUID eventId
        +TrackingId trackingId
        +HandlingEventType eventType
        +Location location
        +DateTime completionTime
        +DateTime registrationTime
        +VoyageNumber voyageNumber ?
    }

    class HandlingEventRepository {
        <<Repository>>
        +save(HandlingEvent)
        +findByTrackingId(TrackingId) HandlingEvent[]
        +findMostRecentByTrackingId(TrackingId) HandlingEvent ?
    }

    class HandlingEventShapeValid {
        <<Specification>>
        +isValid(HandlingEvent) boolean
    }

    HandlingEventRepository --> HandlingEvent : manages
    HandlingEventShapeValid ..> HandlingEvent : validates

    cssClass "HandlingEvent" aggregateRoot
    cssClass "HandlingEventRepository" repository
    cssClass "HandlingEventShapeValid" specification

    classDef aggregateRoot fill:#FFD700,stroke:#333,stroke-width:2px,color:#000
    classDef repository fill:#F5F5F5,stroke:#666,stroke-width:1px,color:#000
    classDef specification fill:#FFFACD,stroke:#333,stroke-width:1px,color:#000
```

## Tracking Context — Command-Event Flow

```mermaid
---
title: Tracking Context — Command-Event Flow
---
classDiagram
    class RegisterHandlingEvent {
        <<Command>>
        +TrackingId trackingId
        +HandlingEventType eventType
        +Location location
        +DateTime completionTime
        +VoyageNumber voyageNumber ?
    }

    class CargoHandled {
        <<Domain Event>>
        +TrackingId trackingId
        +HandlingEventType eventType
        +Location location
        +VoyageNumber voyageNumber ?
        +DateTime completionTime
    }

    class RegisterHandlingEventService {
        <<Application Service>>
        +registerHandlingEvent(RegisterHandlingEventRequest) RegisterHandlingEventResponse
    }

    RegisterHandlingEvent ..> CargoHandled : emits

    RegisterHandlingEventService ..> RegisterHandlingEvent : handles
    RegisterHandlingEventService --> HandlingEventRepository

    %% CargoHandled is published to bc-booking (cross-BC event)
    CargoHandled ..> BookingBC : published to bc-booking

    cssClass "RegisterHandlingEvent" command
    cssClass "CargoHandled" domainEvent
    cssClass "RegisterHandlingEventService" entity

    classDef command fill:#FFA500,stroke:#333,stroke-width:1px,color:#000
    classDef domainEvent fill:#FFA07A,stroke:#333,stroke-width:1px,color:#000
    classDef entity fill:#87CEEB,stroke:#333,stroke-width:1px,color:#000
```

## Voyage Context — Aggregate Structure

```mermaid
---
title: Voyage Context — Aggregate Structure (Voyage Aggregate)
---
classDiagram
    class Voyage {
        <<Aggregate Root>>
        +VoyageNumber voyageNumber
        +CarrierMovement[] schedule
        lifecycle: Scheduled | InProgress | Completed
    }

    class CarrierMovement {
        <<Value Object>>
        +Location departureLocation
        +Location arrivalLocation
        +DateTime departureTime
        +DateTime arrivalTime
    }

    class VoyageRepository {
        <<Repository>>
        +save(Voyage)
        +findByVoyageNumber(VoyageNumber) Voyage ?
    }

    Voyage *-- CarrierMovement : contains (ordered schedule)
    VoyageRepository --> Voyage : manages

    cssClass "Voyage" aggregateRoot
    cssClass "CarrierMovement" valueObject
    cssClass "VoyageRepository" repository

    classDef aggregateRoot fill:#FFD700,stroke:#333,stroke-width:2px,color:#000
    classDef valueObject fill:#98FB98,stroke:#333,stroke-width:1px,color:#000
    classDef repository fill:#F5F5F5,stroke:#666,stroke-width:1px,color:#000
```

## Cargo Lifecycle

```mermaid
---
title: Cargo Lifecycle
---
stateDiagram-v2
    [*] --> Booked: Book Cargo
    Booked --> Routed: Assign Itinerary
    Booked --> Booked: Change Destination
    Routed --> Routed: Change Destination
    Routed --> Routed: Assign Different Itinerary
    Routed --> InTransit: First Handling Event
    InTransit --> InTransit: Intermediate Events
    InTransit --> InTransit: Misdirection Detected
    InTransit --> Claimed: CLAIM at Destination
    Claimed --> [*]

    note right of Booked
        Cargo waiting for routing.
        Customer can change destination.
    end note

    note right of Routed
        Itinerary assigned.
        Awaiting shipment.
    end note

    note right of InTransit
        Cargo in physical transit.
        Delivery status updates.
    end note

    note right of Claimed
        Delivery complete.
    end note
```

## Voyage Lifecycle

```mermaid
---
title: Voyage Lifecycle
---
stateDiagram-v2
    [*] --> Scheduled: Schedule Voyage
    Scheduled --> InProgress: First Departure
    Scheduled --> Scheduled: Amend Schedule
    InProgress --> InProgress: Carrier Movement Progression
    InProgress --> InProgress: Voyage Delayed
    InProgress --> Completed: Final Completion
    Completed --> [*]

    note right of Scheduled
        Voyage planned.
        May be amended.
    end note

    note right of InProgress
        Vessel executing schedule.
        May experience delays.
    end note

    note right of Completed
        All movements executed.
    end note
```

---

**Generated from DMML v0.1.0 — Cargo Shipping Reference Model**


---

## Appendix: Element Coverage

This appendix ensures all DMML elements are referenced in the diagrams.

### Context Map Relationships (Strategic Design)

The following context map relationships are shown in the Context Map diagram:

- **Booking ← Tracking** (customer_supplier / events)
- **Booking → Routing** (anticorruption_layer / api)
- **Booking ← Voyage** (conformist / api)
- **Tracking ← Voyage** (conformist / api)
- **All Contexts ← Location** (open_host_service / api)

### Booking Context — Missing Elements

- **Derive Delivery on Handling Event** (Policy): Reactive policy triggered by CargoHandled or VoyageDelayed events, issues DeriveDelivery command. Shown in Booking Command-Event Flow diagram.
- **Route Specification Satisfied** (Specification): Validates that an itinerary satisfies a route specification. Shown in Booking Aggregate Structure diagram.

### Routing Context

- **Route Finder Service** (Domain Service): Provides `findOptimalRoutes(origin, destination, deadline) -> Itinerary[]`. Core algorithmic service of Routing context, accessed through RoutingService ACL in Booking context.

### Voyage Context

- **Schedule Voyage Service** (Application Service): Orchestrates voyage scheduling. Handles ScheduleVoyage command. Not diagrammed (Voyage context is supporting/tactical).

### Location Context

- **LocationRepository** (Repository): Provides `findByUnlocode()` and `findAll()` operations for the Location aggregate. Not diagrammed (Location is generic reference data).

---

