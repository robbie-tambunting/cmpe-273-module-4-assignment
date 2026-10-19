# Order and Inventory Services

A small distributed system made of two independent Python services. The **Order Service** accepts
requests to place orders and owns order records. Before accepting an order it asks the **Inventory
Service**, which owns stock levels, whether the requested quantity is available. The services
communicate over synchronous HTTP, keep their data in memory, and fail independently: if Inventory is
down, Order reports a clear error and keeps running. A third service, Notification, is designed to react
to an `OrderCreated` event through a message broker but is intentionally not implemented.

## Architecture

### Component diagram

```mermaid
flowchart LR
    Client([Client / curl])

    subgraph OrderSvc["Order Service :8080"]
        O[Order API]
        ODB[(Orders<br/>in-memory)]
        O --- ODB
    end

    subgraph InvSvc["Inventory Service :8081"]
        I[Inventory API]
        IDB[(Stock levels<br/>in-memory)]
        I --- IDB
    end

    subgraph NotifSvc["Notification Service (designed, not implemented)"]
        N[Notification Handler]
        NDB[(Notification log<br/>+ contact prefs)]
        N --- NDB
    end

    Broker{{Message Broker<br/>planned}}

    Client -- "POST /orders<br/>(Command)" --> O
    O -- "GET /items/{id}/availability<br/>(Query, sync HTTP, 2s timeout)" --> I
    I -- "available / unavailable" --> O
    O -. "OrderCreated<br/>(Event, async)" .-> Broker
    Broker -. "subscribe" .-> N

    classDef planned stroke-dasharray: 5 5,opacity:0.7
    class NotifSvc,N,NDB,Broker planned
```

### Sequence diagram

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant O as Order Service
    participant I as Inventory Service
    participant B as Message Broker (planned)

    Client->>O: POST /orders {item_id, quantity} «command»
    O->>I: GET /items/{id}/availability?qty=N «query»
    I-->>O: 200 {available: true}
    O->>O: store order (status CREATED)
    O-)B: OrderCreated «event»
    O-->>Client: 201 {id, item_id, quantity, status, created_at}

    Note over O,I: Failure path: if Inventory is down (connection refused),<br/>the call in step 2 fails. Order logs the error, returns 503<br/>{"detail": "inventory service unavailable"}, stores no order,<br/>and keeps serving other requests.
```

**Legend:** solid arrows are implemented and synchronous. Dashed arrows and boxes (the message broker and
the Notification Service) are designed but not implemented. In the sequence diagram, the open-headed
arrow (`-)`) marks the asynchronous event; it is also designed but not implemented, and Order currently
only logs the event it would publish.
