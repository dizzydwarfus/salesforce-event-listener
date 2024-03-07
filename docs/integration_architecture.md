```mermaid
sequenceDiagram
    participant Salesforce
    participant SF_Middleware as SF_BUS Python Middleware (ACI)
    participant AEG as CosmosDB/Kafka/Outbox
    participant AFunc as Azure Function Dispatcher
    participant Broker as Kafka/EventHub/ServiceBus/EventGrid
    participant SAP_Middleware as SAP__BUS Python Middleware
    participant SAP_B1 as SAP Business One

    Salesforce->>+SF_Middleware: (1) Event Notification
    SAP_B1->>+SAP_Middleware: (1) Event Notification
    SF_Middleware->>+AEG: (2) Publish Event
    SAP_Middleware->>+AEG: (2) Publish Event
    AEG->>+AFunc: (3) Get outbox events
    AFunc->>+Broker: (4) Publish to broker
    AFunc->>+SAP_B1: (5) Process Event
    AFunc->>+Salesforce: (5) Process Event

    Note over Salesforce,SAP_B1: Optional feedback for confirmation or further processing
```