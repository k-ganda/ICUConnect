# UML Diagrams - ICU Occupancy Prediction System

## 1. Class Diagram

```mermaid
classDiagram
    class UserMixin {
        <<interface>>
        +get_id() String
        +is_authenticated Boolean
        +is_active Boolean
        +is_anonymous Boolean
    }

    class Hospital {
        +id: Integer
        +name: String
        +verification_code: String
        +is_active: Boolean
        +created_at: DateTime
        +latitude: Float
        +longitude: Float
        +level: Integer
        +timezone: String
        +get_timezone() Timezone
        +total_beds: Integer
        +available_beds: Integer
    }

    class Admin {
        +id: Integer
        +hospital_id: Integer
        +email: String
        +password_hash: String
        +privilege_level: String
        +verification_docs: String
        +is_verified: Boolean
        +created_by: Integer
        +created_at: DateTime
        +set_password(password: String)
        +check_password(password: String): Boolean
        +get_id(): String
    }

    class User {
        +id: Integer
        +hospital_id: Integer
        +admin_id: Integer
        +email: String
        +employee_id: String
        +role: String
        +is_approved: Boolean
        +approval_date: DateTime
        +created_at: DateTime
        +name: String
        +password_hash: String
        +set_password(password: String)
        +check_password(password: String): Boolean
        +get_id(): String
        +get_type(): String
        +get_hospital(): Hospital
    }

    class Bed {
        +id: Integer
        +hospital_id: Integer
        +bed_number: Integer
        +is_occupied: Boolean
        +bed_type: String
        +__repr__(): String
    }

    class Admission {
        +id: Integer
        +hospital_id: Integer
        +patient_name: String
        +bed_id: Integer
        +doctor: String
        +reason: Text
        +priority: String
        +age: Integer
        +gender: String
        +admission_time: DateTime
        +discharge_time: DateTime
        +status: String
        +local_admission_time: DateTime
        +local_discharge_time: DateTime
        +masked_patient_name: String
        +patient_initials: String
        +length_of_stay: Float
    }

    class Discharge {
        +id: Integer
        +hospital_id: Integer
        +patient_name: String
        +bed_number: Integer
        +admission_time: DateTime
        +discharge_time: DateTime
        +discharging_doctor: String
        +discharge_type: String
        +notes: Text
        +local_admission_time: DateTime
        +local_discharge_time: DateTime
        +patient_initials: String
        +length_of_stay: Integer
    }

    class ARIMAModel {
        +model_file: String
        +order: Tuple
        +load_model()
        +predict(weeks_ahead: Integer): Array
        +save_model()
    }

    class PredictionEngine {
        +arima_model: ARIMAModel
        +load_model()
        +make_prediction(weeks_ahead: Integer): Dict
        +validate_input(data: Dict): Boolean
    }

    %% Relationships
    UserMixin <|-- Admin
    UserMixin <|-- User

    Hospital ||--o{ Admin : has
    Hospital ||--o{ User : has
    Hospital ||--o{ Bed : has
    Hospital ||--o{ Admission : has
    Hospital ||--o{ Discharge : has

    Admin ||--o{ User : approves

    Bed ||--o{ Admission : accommodates

    Admission ||--|| Discharge : becomes

    PredictionEngine --> ARIMAModel : uses
```

## 2. Database Entity Relationship Diagram

```mermaid
erDiagram
    HOSPITALS {
        int id PK
        string name
        string verification_code
        boolean is_active
        datetime created_at
        float latitude
        float longitude
        int level
        string timezone
    }

    ADMINS {
        int id PK
        int hospital_id FK
        string email
        string password_hash
        string privilege_level
        string verification_docs
        boolean is_verified
        int created_by
        datetime created_at
    }

    USERS {
        int id PK
        int hospital_id FK
        int admin_id FK
        string email
        string employee_id
        string role
        boolean is_approved
        datetime approval_date
        datetime created_at
        string name
        string password_hash
    }

    BEDS {
        int id PK
        int hospital_id FK
        int bed_number
        boolean is_occupied
        string bed_type
    }

    ADMISSIONS {
        int id PK
        int hospital_id FK
        string patient_name
        int bed_id FK
        string doctor
        text reason
        string priority
        int age
        string gender
        datetime admission_time
        datetime discharge_time
        string status
    }

    DISCHARGES {
        int id PK
        int hospital_id FK
        string patient_name
        int bed_number
        datetime admission_time
        datetime discharge_time
        string discharging_doctor
        string discharge_type
        text notes
    }

    HOSPITALS ||--o{ ADMINS : "has"
    HOSPITALS ||--o{ USERS : "has"
    HOSPITALS ||--o{ BEDS : "has"
    HOSPITALS ||--o{ ADMISSIONS : "has"
    HOSPITALS ||--o{ DISCHARGES : "has"
    ADMINS ||--o{ USERS : "approves"
    BEDS ||--o{ ADMISSIONS : "accommodates"
```

## 3. Use Case Diagram

```mermaid
graph TB
    subgraph "Actors"
        A[Admin User]
        B[Regular User]
        C[System]
    end

    subgraph "Use Cases"
        D[Login/Logout]
        E[Manage Users]
        F[Admit Patient]
        G[Discharge Patient]
        H[View Bed Status]
        I[Predict Occupancy]
        J[View Reports]
        K[Manage Hospital Settings]
        L[Generate Predictions]
    end

    A --> D
    A --> E
    A --> F
    A --> G
    A --> H
    A --> I
    A --> J
    A --> K

    B --> D
    B --> F
    B --> G
    B --> H
    B --> I

    C --> L
    L --> I
```

## 4. Sequence Diagram - Patient Admission Process

```mermaid
sequenceDiagram
    participant U as User
    participant F as Flask App
    participant A as Auth Manager
    participant D as Database
    participant B as Bed Manager

    U->>F: Submit Admission Form
    F->>A: Validate User Session
    A->>F: Return User Info
    F->>D: Check Bed Availability
    D->>F: Return Available Beds
    F->>B: Allocate Bed
    B->>D: Update Bed Status
    D->>B: Confirm Update
    F->>D: Create Admission Record
    D->>F: Return Admission ID
    F->>U: Show Success Message
```

## 5. Sequence Diagram - Occupancy Prediction Process

```mermaid
sequenceDiagram
    participant U as User
    participant F as Flask App
    participant P as Prediction Engine
    participant M as ARIMA Model
    participant D as Database

    U->>F: Request Prediction
    F->>P: Trigger Prediction
    P->>M: Load Model
    M->>P: Model Loaded
    P->>D: Get Historical Data
    D->>P: Return Data
    P->>M: Make Prediction
    M->>P: Return Forecast
    P->>F: Format Results
    F->>U: Display Prediction
```

## 6. Activity Diagram - Patient Admission Workflow

```mermaid
flowchart TD
    A[Start] --> B[User Login]
    B --> C{Valid Credentials?}
    C -->|No| D[Show Error]
    C -->|Yes| E[Access Dashboard]
    E --> F[Select New Admission]
    F --> G[Fill Patient Details]
    G --> H[Select Available Bed]
    H --> I{Valid Input?}
    I -->|No| J[Show Validation Error]
    I -->|Yes| K[Submit Admission]
    K --> L[Update Bed Status]
    L --> M[Create Admission Record]
    M --> N[Show Success Message]
    N --> O[End]

    D --> B
    J --> G
```

## 7. State Diagram - Patient Status

```mermaid
stateDiagram-v2
    [*] --> Admitted
    Admitted --> Active: Patient Checked In
    Active --> Discharged: Patient Discharged
    Discharged --> [*]

    Active --> Active: Update Patient Info
    Active --> Discharged: Emergency Discharge
```

## 8. Component Diagram

```mermaid
graph TB
    subgraph "Web Interface"
        A[Login Page]
        B[Dashboard]
        C[Admission Form]
        D[Discharge Form]
        E[Prediction Interface]
    end

    subgraph "Backend Services"
        F[Authentication Service]
        G[Patient Management Service]
        H[Bed Management Service]
        I[Prediction Service]
        J[Data Processing Service]
    end

    subgraph "Data Layer"
        K[PostgreSQL Database]
        L[ARIMA Model Files]
        M[Configuration Files]
    end

    subgraph "External Systems"
        N[Render Platform]
        O[Email Service]
        P[Notification Service]
    end

    A --> F
    B --> G
    B --> H
    B --> I
    C --> G
    D --> G
    E --> I

    F --> K
    G --> K
    H --> K
    I --> L
    J --> K

    F --> N
    G --> O
    I --> P
```

## 9. Package Diagram

```mermaid
graph TB
    subgraph "app"
        A[models.py]
        B[__init__.py]
        C[utils.py]
    end

    subgraph "app/routes"
        D[main.py]
        E[auth.py]
        F[admin.py]
        G[user_routes.py]
        H[admission_routes.py]
        I[discharge_routes.py]
        J[prediction_routes.py]
    end

    subgraph "app/templates"
        K[users/]
        L[admin/]
    end

    subgraph "app/static"
        M[css/]
        N[js/]
        O[images/]
    end

    subgraph "models"
        P[arima_model1.pkl]
    end

    A --> D
    A --> E
    A --> F
    A --> G
    A --> H
    A --> I
    A --> J

    B --> A
    B --> C

    D --> K
    E --> K
    F --> L
    G --> K
    H --> K
    I --> K
    J --> K

    K --> M
    K --> N
    K --> O

    J --> P
```

## 10. Deployment Diagram

```mermaid
graph TB
    subgraph "Client"
        A[Web Browser]
        B[Mobile Browser]
    end

    subgraph "Render Cloud Platform"
        C[Web Service]
        D[PostgreSQL Database]
        E[Static Assets]
    end

    subgraph "Application Server"
        F[Flask Application]
        G[Gunicorn WSGI]
        H[ARIMA Model]
    end

    subgraph "External Services"
        I[Email Service]
        J[Notification Service]
    end

    A --> C
    B --> C
    C --> F
    F --> G
    F --> H
    F --> D
    F --> E
    F --> I
    F --> J
```
