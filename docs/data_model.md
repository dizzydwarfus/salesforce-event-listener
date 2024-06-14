# Data Processing Architecture - Data Model

The diagram below illustrates the data processing architecture for the data model. The data model is built using various data processing and transformation tools and the prepared data models are used in Tableau for visualization.

```mermaid
graph LR
    A[SAP] -->|Data Ingestion| D[Kafka/Fivetran/Airbyte]
    B[Salesforce] -->|Data Ingestion| D
    C[Manual Excel Tables] -->|Data Ingestion| D
    D -->|Raw Data Storage| E[Amazon S3/Azure Blob Storage]
    E -->|ETL Processing| F[Apache Spark/Azure Data Factory]
    F -->|Transformed Data| G[Data Warehouse Redshift/BigQuery/Snowflake]
    G -->|Data Modeling| H[dbt]
    H -->|Prepared Data Models| I[Tableau]

    classDef source fill:#f9f,stroke:#333,stroke-width:2px;
    classDef storage fill:#bbf,stroke:#333,stroke-width:2px;
    classDef process fill:#fbf,stroke:#333,stroke-width:2px;
    classDef database fill:#bfb,stroke:#333,stroke-width:2px;
    classDef bi fill:#fbb,stroke:#333,stroke-width:2px;
    class A,B,C source;
    class D process;
    class E storage;
    class F,G process;
    class H database;
    class I bi;
```