```mermaid
sequenceDiagram
    participant Salesforce
    participant SF_Middleware as SF_BUS Python Middleware
    participant AEG as Azure Event Grid
    participant Logger as Event Logger (DB)
    participant SAP_Middleware as SAP__BUS Python Middleware
    participant SAP_B1 as SAP Business One

    Salesforce->>+SF_Middleware: (1) Event Notification
    SF_Middleware-->>-Salesforce: (Optional) Feedback Event
    SAP_B1->>+SAP_Middleware: (1) Event Notification
    SAP_Middleware-->>-SAP_B1: (Optional) Feedback Event
    SF_Middleware->>+AEG: (2) Publish Event
    SAP_Middleware->>+AEG: (2) Publish Event
    AEG->>+Logger: (3) Log Event
    AEG->>+SAP_B1: (4) Direct Processing
    SAP_B1-->>-AEG: (Optional) Feedback Event
    

    Note over Salesforce,SAP_B1: Optional feedback for confirmation or further processing
```