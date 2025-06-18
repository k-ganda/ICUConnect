# Chapter 3: System Design and Architecture

## ICU Occupancy Prediction System

### 3.1 Introduction

This chapter presents the comprehensive system design and architecture of the ICU Occupancy Prediction System. The system is designed to provide real-time bed management and occupancy forecasting for pediatric intensive care units using ARIMA time series modeling.

### 3.2 System Overview

The ICU Occupancy Prediction System is a web-based application that combines hospital management functionality with machine learning capabilities to predict future bed occupancy. The system is built using a three-tier architecture:

- **Presentation Layer**: Web interface for hospital staff
- **Application Layer**: Business logic and prediction engine
- **Data Layer**: Database and model storage

### 3.3 High-Level Architecture

The system follows a layered architecture pattern with the following components:

#### 3.3.1 Client Layer

- **Web Browser**: Primary interface for hospital staff
- **Mobile App**: Future enhancement for mobile access

#### 3.3.2 Presentation Layer

- **Flask Web Application**: Main web framework
- **HTML/CSS/JavaScript**: Frontend technologies
- **Bootstrap**: UI framework for responsive design

#### 3.3.3 Application Layer

- **Flask Routes**: API endpoints and page routing
- **Authentication Module**: User login and session management
- **Patient Management**: Admission and discharge operations
- **Bed Management**: Bed allocation and status tracking
- **Prediction Engine**: ARIMA model integration

#### 3.3.4 Business Logic Layer

- **ARIMA Model**: Time series forecasting for bed occupancy
- **Data Processing**: Patient data aggregation and preprocessing
- **Business Rules**: Hospital-specific logic and constraints
- **Validation Logic**: Input validation and data integrity

#### 3.3.5 Data Layer

- **PostgreSQL Database**: Primary data storage
- **Model Storage**: Saved ARIMA model files
- **Patient Records**: Admission and discharge history
- **Bed Status**: Real-time bed availability

### 3.4 Technology Stack

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

### 3.5 System Components

#### 3.5.1 Core Models

1. **Hospital Model**

   - Manages hospital information and settings
   - Handles timezone configuration
   - Tracks bed capacity and availability

2. **User Management Models**

   - **Admin**: Super administrators with full system access
   - **User**: Regular hospital staff with role-based permissions

3. **Patient Management Models**

   - **Admission**: Tracks patient admissions and current status
   - **Discharge**: Records patient discharge information
   - **Bed**: Manages bed allocation and availability

4. **Prediction Model**
   - **ARIMA Model**: Time series forecasting engine
   - **Prediction Engine**: Orchestrates prediction workflows

#### 3.5.2 Key Features

1. **Authentication & Authorization**

   - Role-based access control
   - Session management
   - Secure password handling

2. **Patient Management**

   - Admission workflow
   - Discharge processing
   - Bed allocation
   - Status tracking

3. **Occupancy Prediction**

   - ARIMA model integration
   - Real-time forecasting
   - Historical data analysis
   - API endpoints for predictions

4. **Reporting & Analytics**
   - Bed utilization reports
   - Patient statistics
   - Occupancy trends
   - Performance metrics

### 3.6 Database Design

#### 3.6.1 Entity Relationship Model

The database consists of six main entities:

1. **Hospitals**: Central entity containing hospital information
2. **Admins**: System administrators with full privileges
3. **Users**: Regular hospital staff members
4. **Beds**: ICU bed management and status
5. **Admissions**: Patient admission records
6. **Discharges**: Patient discharge records

#### 3.6.2 Key Relationships

- One-to-Many: Hospital to Users, Admins, Beds, Admissions, Discharges
- One-to-Many: Admin to Users (approval relationship)
- One-to-Many: Bed to Admissions (accommodation relationship)
- One-to-One: Admission to Discharge (status transition)

### 3.7 Security Architecture

#### 3.7.1 Authentication Flow

1. User credentials validation
2. Session creation and management
3. Role-based authorization
4. Secure password hashing (Argon2)

#### 3.7.2 Data Protection

- HTTPS/SSL encryption
- Database connection security
- Input validation and sanitization
- SQL injection prevention

### 3.8 Deployment Architecture

#### 3.8.1 Cloud Platform

- **Render**: Primary hosting platform
- **PostgreSQL**: Managed database service
- **Static Assets**: CDN delivery

#### 3.8.2 Application Components

- **Flask Application**: Main web framework
- **Gunicorn**: WSGI server for production
- **ARIMA Model**: Pre-trained prediction model

### 3.9 Data Flow Architecture

#### 3.9.1 Patient Admission Flow

1. User authentication
2. Bed availability check
3. Patient information entry
4. Bed allocation
5. Database update
6. Success confirmation

#### 3.9.2 Prediction Flow

1. Prediction request
2. Model loading
3. Historical data retrieval
4. ARIMA forecasting
5. Result formatting
6. Response delivery

### 3.10 System Requirements

#### 3.10.1 Functional Requirements

- User authentication and authorization
- Patient admission and discharge management
- Bed allocation and status tracking
- Occupancy prediction using ARIMA model
- Real-time data updates
- Reporting and analytics

#### 3.10.2 Non-Functional Requirements

- **Performance**: Sub-second response times for predictions
- **Scalability**: Support for multiple hospitals
- **Reliability**: 99.9% uptime
- **Security**: HIPAA-compliant data protection
- **Usability**: Intuitive web interface

### 3.11 System Constraints

#### 3.11.1 Technical Constraints

- Python 3.11+ compatibility
- PostgreSQL database requirement
- Render platform limitations
- ARIMA model file size constraints

#### 3.11.2 Business Constraints

- Hospital data privacy regulations
- Real-time data accuracy requirements
- User training and adoption
- Integration with existing hospital systems

### 3.12 Future Enhancements

#### 3.12.1 Planned Features

- Mobile application development
- Email notification system
- Advanced analytics dashboard
- Multi-hospital support
- Real-time alerts and notifications

#### 3.12.2 Technical Improvements

- Model retraining automation
- Performance optimization
- Enhanced security features
- API rate limiting
- Caching mechanisms

### 3.13 Conclusion

The ICU Occupancy Prediction System is designed with a robust, scalable architecture that combines traditional hospital management functionality with advanced machine learning capabilities. The system's modular design allows for easy maintenance, updates, and future enhancements while ensuring data security and system reliability.

The architecture supports the core requirements of bed management and occupancy prediction while providing a foundation for future expansion and integration with other hospital systems.

---

**Note**: Detailed UML diagrams, sequence diagrams, and component diagrams are available in the `docs/architecture/` directory:

- `system_architecture.md`: High-level system architecture
- `uml_diagrams.md`: Comprehensive UML diagrams
- `uml_class_diagram.md`: Detailed class relationships
