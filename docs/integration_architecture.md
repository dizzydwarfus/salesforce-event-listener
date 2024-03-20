
# Integration Architecture V1

## Integration Architecture Sequence Diagram

The following sequence diagram illustrates the flow of data between Salesforce and SAP Business One using Kafka as the message broker. The diagram also shows the change data capture (CDC) mechanism in Salesforce and SAP Business One, and the consumer application that processes the events from Kafka and updates the respective system.

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

# Integration Architecture V2

## Integration Architecture Sequence Diagram V2

The following sequence diagram illustrates the flow of data between Salesforce and SAP Business One using Kafka as the message broker. The diagram also shows the change data capture (CDC) mechanism in Salesforce and SAP Business One, and the consumer application that processes the events from Kafka and updates the respective system.

```mermaid
sequenceDiagram
    participant Salesforce as Salesforce
    participant SF_Listener as Docker Container (SF Listener)
    participant Kafka as Kafka (Confluent)
    participant Cons_App as Docker Container (Consumer App)
    participant SAP_B1 as SAP Business One
    participant SAP_Listener as Docker Container (SAP Listener)

    Note over Salesforce,Kafka: Change Data Capture (CDC) Events from Salesforce
    Salesforce->>+SF_Listener: 1: Publish CDC Events
    SF_Listener->>+Kafka: 2: Publish to relevant Kafka Topics
    Kafka->>+Cons_App: 3: Consumer App consumes events
    Cons_App->>-Salesforce: 4a: Update Salesforce (if needed)
    Kafka->>+Cons_App: 4b: Consumer App consumes events
    Cons_App->>-SAP_B1: 4b: Update SAP Business One (if needed)

    Note over SAP_B1,Kafka: CDC Events from SAP Business One
    SAP_B1->>+SAP_Listener: 5: Publish CDC Events
    SAP_Listener->>+Kafka: 6: Publish to relevant Kafka Topics
    Kafka->>+Cons_App: 7: Consumer App consumes events
    Cons_App->>-SAP_B1: 8a: Update SAP Business One (if needed)
    Kafka->>+Cons_App: 8b: Consumer App consumes events
    Cons_App->>-Salesforce: 8b: Update Salesforce (if needed)
```

## Integration Architecture Flow Diagram

The following diagram illustrates the flow of data between Salesforce and SAP Business One using Kafka as the message broker. The diagram also shows the change data capture (CDC) mechanism in Salesforce and SAP Business One, and the consumer application that processes the events from Kafka and updates the respective system.

```mermaid
graph LR
    subgraph Salesforce ["Salesforce"]
    SF_CDC["Change Data Capture (CDC) Events"]
    end
    
    subgraph Kafka ["Confluent Kafka"]
    K_Topic_Accounts["Accounts Topic"]
    K_Topic_Products["Products Topic"]
    K_Topic_Opportunities["Opportunities Topic"]
    end
    
    subgraph SAP_B1 ["SAP Business One"]
    SAP_CDC["Change Data Capture (CDC) Events"]
    end
    
    subgraph Docker_SF_Listener ["Docker Container (SF Listener)"]
    SF_Listener["Salesforce Event Listener"]
    end
    
    subgraph Docker_SAP_Listener ["Docker Container (SAP Listener)"]
    SAP_Listener["SAP Event Listener"]
    end
    
    subgraph Consumer_App ["Docker Container (Consumer App)"]
    Cons_App["Kafka Consumer App"]
    end
    
    SF_CDC -->|Publish| SF_Listener
    SAP_CDC -->|Publish| SAP_Listener
    
    SF_Listener -->|Publish to Kafka| K_Topic_Accounts
    SF_Listener -->|Publish to Kafka| K_Topic_Products
    SF_Listener -->|Publish to Kafka| K_Topic_Opportunities
    
    SAP_Listener -->|Publish to Kafka| K_Topic_Accounts
    SAP_Listener -->|Publish to Kafka| K_Topic_Products
    
    K_Topic_Accounts -->|Consume| Cons_App
    K_Topic_Products -->|Consume| Cons_App
    K_Topic_Opportunities -->|Consume| Cons_App
    
    Cons_App -->|Update| SAP_B1
    Cons_App -->|Update| Salesforce
    
    classDef integration fill:#f9f,stroke:#333,stroke-width:2px;
    class Salesforce,Kafka,SAP_B1,Docker_SF_Listener,Docker_SAP_Listener,Consumer_App integration;
```
