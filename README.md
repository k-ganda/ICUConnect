# ICUConnect

## 📌 Description

**ICUConnect** is a Flask-based web dashboard designed to coordinate ICU bed availability across public hospitals in Kenya. It integrates machine learning to predict ICU occupancy and facilitates hospital-to-hospital referrals, enhancing real-time visibility into ICU resources.

---

## 🔗 GitHub Repository

[https://github.com/k-ganda/ICUConnect](https://github.com/k-ganda/ICUConnect)

---

## ⚙️ Project Setup

### Directory Structure

```
ICUConnect/
├── app/
│   ├── __init__.py              # Application factory
│   ├── models.py                # Database models
│   ├── utils.py                 # Utility functions
│   ├── routes/                  # Route handlers
│   │   ├── auth.py             # Authentication routes
│   │   ├── admin.py            # Admin dashboard routes
│   │   ├── user_routes.py      # User dashboard routes
│   │   ├── admission_routes.py # Patient admission routes
│   │   ├── discharge_routes.py # Patient discharge routes
│   │   ├── referral_routes.py  # Referral management routes
│   │   ├── transfer_routes.py  # Patient transfer routes
│   │   └── prediction_routes.py # ML prediction routes
│   ├── templates/              # HTML templates
│   │   ├── auth/              # Authentication templates
│   │   ├── admin/             # Admin dashboard templates
│   │   └── users/             # User dashboard templates
│   ├── static/                # Static assets (CSS, JS, images)
│   └── Dataset/               # Training data for ML model
├── models/                    # Trained ML models
├── migrations/                # Database migrations
├── tests/                     # Test suite
├── deployment/                # Deployment configuration
└── run.py                     # Application entry point
```

## Steps to Run The App

1. **📁 Clone the Repository**

```
git clone https://github.com/k-ganda/ICUConnect.git
cd ICUConnect
```

2. **Create a Virtual Environment**

```
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. **Install the Dependencies**

```
pip install -r requirements.txt
```

4. **Run the Flask App**

```
python run.py
```

Open your browser and go to : http://127.0.0.1:5000/ .

**NOTE:**

You will be able to sign up, but login is restricted to verified users only due to ethical considerations around sensitive hospital data.

### Model Notebook

The machine learning model notebook can be found in

```
notebook/Predict_Occupancy_fixed.ipynb
```

It includes:

- Exploratory Data Analysis (EDA)

- Feature Engineering

- A baseline ARIMA model to forecast ICU occupancy

- Evaluation metrics including RMSE, MSE, MAE, and R² score

The dataset used is publicly available from the Ontario Open Data portal:

```
https://data.ontario.ca/dataset/availability-of-adult-icu-beds-and-occupancy-for-covid-related-critical-illness-crci/resource/c7f2590f-362a-498f-a06c-da127ec41a33
```

## Web Dashbaord Screenshots

### Login Page

![Alt text](screenshots/image.png)

### Sign UP

![Alt text](screenshots/part1sign.png)
![Alt text](screenshots/part2sign.png)

### Dashboard

![Alt text](screenshots/dash.png)
![Alt text](screenshots/dash2.png)

### Admission

![Alt text](screenshots/adm1.png)
![Alt text](screenshots/adm2.png)

### Discharge

![Alt text](screenshots/dis.png)

## Deployment Plan

### Phase 1- MVP(local Deployment)

- Run the Flask app locally

- Use SQLite as local database

- Manual updates of ICU bed records.

### Phase 2 - Cloud Deployment(Planned)

- Host on Render or similar cloud platform

- Use PostgreSQl for database management

- Deploy and integrate trained ML model

- Secure access and user role management

## Demo Video

https://www.youtube.com/watch?v=5yo5O3M0HZU

## Tools & Technologies

Flask – Backend web framework

Pandas, Matplotlib, Scikit-learn – data analysis & modeling

SQLite / SQLAlchemy – lightweight database(currently)

Bootstrap / HTML / CSS – frontend UI

Jupyter Notebook – ML Model Development

## Author

Kathrine Ganda

k.ganda@alustudent.com

Final Year Capstone Project - African Leadership University
