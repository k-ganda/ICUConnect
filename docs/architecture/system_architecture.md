# ICU Occupancy Prediction System - System Architecture

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        A[Web Browser]
        B[Mobile App - Future]
    end

    subgraph "Presentation Layer"
        C[Flask Web Application]
        D[HTML/CSS/JavaScript]
        E[Bootstrap UI Framework]
    end

    subgraph "Application Layer"
        F[Flask Routes]
        G[Authentication Module]
        H[Patient Management]
        I[Bed Management]
        J[Prediction Engine]
    end

    subgraph "Business Logic Layer"
        K[ARIMA Model]
        L[Data Processing]
        M[Business Rules]
        N[Validation Logic]
    end

    subgraph "Data Layer"
        O[PostgreSQL Database]
        P[Model Storage]
        Q[Patient Records]
        R[Bed Status]
    end

    subgraph "External Services"
        S[Render Cloud Platform]
        T[Email Service - Future]
        U[Notification Service - Future]
    end

    A --> C
    B --> C
    C --> F
    F --> G
    F --> H
    F --> I
    F --> J
    J --> K
    H --> L
    I --> L
    L --> M
    M --> N
    N --> O
    K --> P
    H --> Q
    I --> R
    C --> S
    S --> T
    S --> U
```

## 2. System Components Overview

### 2.1 Client Layer

- **Web Browser**: Primary interface for hospital staff
- **Mobile App**: Future enhancement for mobile access

### 2.2 Presentation Layer

- **Flask Web Application**: Main web framework
- **HTML/CSS/JavaScript**: Frontend technologies
- **Bootstrap**: UI framework for responsive design

### 2.3 Application Layer

- **Flask Routes**: API endpoints and page routing
- **Authentication Module**: User login and session management
- **Patient Management**: Admission and discharge operations
- **Bed Management**: Bed allocation and status tracking
- **Prediction Engine**: ARIMA model integration

### 2.4 Business Logic Layer

- **ARIMA Model**: Time series forecasting for bed occupancy
- **Data Processing**: Patient data aggregation and preprocessing
- **Business Rules**: Hospital-specific logic and constraints
- **Validation Logic**: Input validation and data integrity

### 2.5 Data Layer

- **PostgreSQL Database**: Primary data storage
- **Model Storage**: Saved ARIMA model files
- **Patient Records**: Admission and discharge history
- **Bed Status**: Real-time bed availability

### 2.6 External Services

- **Render Cloud Platform**: Hosting and deployment
- **Email Service**: Future notification system
- **Notification Service**: Future alert system

## 3. Technology Stack

| Layer           | Technology              | Purpose                    |
| --------------- | ----------------------- | -------------------------- |
| Frontend        | HTML5, CSS3, JavaScript | User interface             |
| UI Framework    | Bootstrap 5             | Responsive design          |
| Backend         | Python 3.11             | Server-side logic          |
| Web Framework   | Flask 3.0.3             | Web application framework  |
| Database        | PostgreSQL              | Data persistence           |
| ORM             | SQLAlchemy              | Database abstraction       |
| Authentication  | Flask-Login             | User session management    |
| ML Framework    | StatsModels             | ARIMA model implementation |
| Data Processing | Pandas, NumPy           | Data manipulation          |
| Deployment      | Render                  | Cloud hosting              |
| WSGI Server     | Gunicorn                | Production server          |

## 4. Data Flow Architecture

```mermaid
flowchart TD
    A[User Input] --> B[Authentication]
    B --> C{Valid User?}
    C -->|No| D[Login Page]
    C -->|Yes| E[Main Dashboard]

    E --> F[Patient Admission]
    E --> G[Patient Discharge]
    E --> H[Bed Management]
    E --> I[Occupancy Prediction]

    F --> J[Update Bed Status]
    G --> K[Free Bed]
    H --> L[Bed Allocation]
    I --> M[ARIMA Model]

    J --> N[Database]
    K --> N
    L --> N
    M --> O[Historical Data]
    O --> P[Forecast Results]
    P --> Q[Display Prediction]

    N --> R[Real-time Updates]
    R --> E
```

## 5. Security Architecture

```mermaid
graph LR
    A[User] --> B[HTTPS/SSL]
    B --> C[Authentication]
    C --> D[Session Management]
    D --> E[Authorization]
    E --> F[Role-based Access]
    F --> G[Database Access]
    G --> H[Data Encryption]
```

## 6. Deployment Architecture

```mermaid
graph TB
    subgraph "Render Cloud Platform"
        A[Web Service]
        B[PostgreSQL Database]
        C[Static Assets]
    end

    subgraph "External Access"
        D[Internet]
        E[Load Balancer]
    end

    subgraph "Application Components"
        F[Flask App]
        G[Gunicorn Server]
        H[ARIMA Model]
    end

    D --> E
    E --> A
    A --> F
    F --> G
    F --> H
    A --> B
    A --> C
```
