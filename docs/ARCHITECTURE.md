# System Architecture Diagram (Mermaid)

## Overall System Architecture

```mermaid
graph TB
    subgraph "Input Layer"
        A[CCTV Cameras] --> B[Video Stream]
        C[IoT Sensors] --> B
    end
    
    subgraph "Detection Layer"
        B --> D[Frame Preprocessor]
        D --> E[YOLOv10 Model]
        E --> F[Accident Analyzer]
    end
    
    subgraph "Processing Layer"
        F --> G{Accident Detected?}
        G -->|Yes| H[Location Service]
        G -->|No| B
        H --> I[Nominatim API]
        I --> J[Reverse Geocoding]
    end
    
    subgraph "Alert Layer"
        J --> K[Translation Service]
        K --> L[mBART-50 Model]
        L --> M[Multilingual Messages]
        M --> N[Telegram Bot]
        N --> O[Emergency Contacts]
    end
    
    subgraph "Storage Layer"
        F --> P[(SQLite Database)]
        J --> P
        M --> P
        P --> Q[Prisma ORM]
    end
    
    subgraph "Presentation Layer"
        Q --> R[FastAPI Backend]
        R --> S[REST API]
        S --> T[Flask Dashboard]
        T --> U[Plotly Visualizations]
        U --> V[Web Browser]
    end
    
    style A fill:#4CAF50
    style E fill:#2196F3
    style N fill:#FF9800
    style P fill:#9C27B0
    style T fill:#F44336
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant C as CCTV Camera
    participant D as Detector (YOLOv10)
    participant G as Geo Service
    participant T as Translator
    participant TB as Telegram Bot
    participant DB as Database
    participant UI as Dashboard
    
    C->>D: Video Stream
    D->>D: Process Frame
    alt Accident Detected
        D->>G: Request Location (lat, lon)
        G->>D: Location Details
        D->>DB: Store Accident
        D->>T: Generate Alert (EN)
        T->>T: Translate to ES, AR, HI, ZH
        T->>TB: Send Multilingual Alerts
        TB->>TB: Notify Emergency Contacts
        TB->>DB: Log Alert Status
        DB->>UI: Update Dashboard
        UI->>UI: Show Alert on Map
    else No Accident
        D->>C: Continue Monitoring
    end
```

## Database Entity-Relationship Diagram

```mermaid
erDiagram
    User ||--o{ SystemLog : creates
    User {
        int id PK
        string username UK
        string email UK
        string password_hash
        string full_name
        string role
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    Accident ||--o{ Alert : triggers
    Accident {
        int id PK
        datetime timestamp
        float location_lat
        float location_lon
        string location_name
        string address
        string city
        string country
        string severity
        float confidence
        string detected_objects
        string image_path
        int video_frame
        string status
        string weather_info
        string notes
        datetime created_at
        datetime updated_at
    }
    
    Alert {
        int id PK
        int accident_id FK
        string language
        string message
        string translated_message
        datetime sent_at
        string status
        string recipient
    }
    
    AlertTemplate {
        int id PK
        string name UK
        string language
        string template
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    SystemLog {
        int id PK
        datetime timestamp
        string level
        string source
        string message
        string details
        int user_id FK
    }
    
    SystemSetting {
        int id PK
        string key UK
        string value
        string description
        datetime updated_at
    }
    
    EmergencyContact {
        int id PK
        string name
        string phone
        string telegram_id
        string email
        string role
        string languages
        boolean is_active
        datetime created_at
        datetime updated_at
    }
```

## Component Interaction Diagram

```mermaid
graph LR
    subgraph "AI Module"
        A1[YOLOv10 Detector]
        A2[Accident Analyzer]
    end
    
    subgraph "Utilities"
        U1[Geolocation Service]
        U2[Translation Service]
        U3[Logger]
    end
    
    subgraph "Communication"
        C1[Telegram Bot]
    end
    
    subgraph "Backend"
        B1[FastAPI Server]
        B2[Authentication]
        B3[API Endpoints]
    end
    
    subgraph "Frontend"
        F1[Flask App]
        F2[Dash Dashboard]
        F3[Plotly Charts]
    end
    
    subgraph "Data Layer"
        D1[(SQLite DB)]
        D2[Prisma ORM]
    end
    
    A1 --> A2
    A2 --> U1
    A2 --> U3
    A2 --> D2
    U1 --> U2
    U2 --> C1
    C1 --> D2
    D2 --> D1
    B1 --> B2
    B2 --> B3
    B3 --> D2
    F1 --> F2
    F2 --> F3
    F2 --> B3
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        C1[Web Browser]
        C2[Mobile Browser]
    end
    
    subgraph "Load Balancer"
        LB[Nginx]
    end
    
    subgraph "Application Servers"
        AS1[Detection Service]
        AS2[API Service]
        AS3[Dashboard Service]
    end
    
    subgraph "External Services"
        E1[Telegram API]
        E2[OpenStreetMap]
        E3[Hugging Face]
    end
    
    subgraph "Data Layer"
        DB[(SQLite/PostgreSQL)]
        FS[File Storage]
    end
    
    subgraph "Monitoring"
        M1[Logs]
        M2[Metrics]
    end
    
    C1 --> LB
    C2 --> LB
    LB --> AS2
    LB --> AS3
    AS1 --> DB
    AS1 --> FS
    AS1 --> E1
    AS1 --> E2
    AS1 --> E3
    AS2 --> DB
    AS3 --> AS2
    AS1 --> M1
    AS2 --> M1
    AS3 --> M1
    M1 --> M2
```

## State Machine Diagram (Accident Status)

```mermaid
stateDiagram-v2
    [*] --> Detected: Accident Detected
    Detected --> Pending: Initial State
    Pending --> Confirmed: Verified by Operator
    Pending --> FalseAlarm: Not an Accident
    Confirmed --> Resolved: Emergency Services Responded
    FalseAlarm --> [*]
    Resolved --> [*]
    
    Confirmed --> Critical: Severity Upgraded
    Critical --> Resolved
```

## Technology Stack Overview

```mermaid
graph LR
    subgraph "Frontend"
        F1[HTML/CSS]
        F2[Bootstrap 5]
        F3[Plotly.js]
        F4[Dash]
    end
    
    subgraph "Backend"
        B1[Python 3.10+]
        B2[FastAPI]
        B3[Flask]
    end
    
    subgraph "AI/ML"
        A1[YOLOv10]
        A2[Ultralytics]
        A3[PyTorch]
        A4[mBART-50]
        A5[Transformers]
    end
    
    subgraph "Database"
        D1[SQLite]
        D2[Prisma ORM]
    end
    
    subgraph "APIs"
        AP1[Telegram Bot API]
        AP2[Nominatim API]
    end
    
    F4 --> B3
    B3 --> B2
    B2 --> D2
    D2 --> D1
    B2 --> A2
    A2 --> A3
    B2 --> A5
    B2 --> AP1
    B2 --> AP2
```
