# 🎯 JEE Dropout Prediction System

<div align="center">

[![Build](https://github.com/YOUR_USERNAME/jee-dropout/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/YOUR_USERNAME/jee-dropout/actions)
[![Coverage](https://codecov.io/gh/YOUR_USERNAME/jee-dropout/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/jee-dropout)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/react-18-61DAFB.svg)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Built for Hackathons](https://img.shields.io/badge/Built%20for-Hackathons%20%26%20Portfolios-blueviolet)](#)

**AI-powered early warning system for JEE coaching institutes**

*Identify at-risk students before they drop out — with explainable ML, not black boxes.*

[Live Demo](#) · [API Docs](http://localhost:8000/api/docs) · [Report a Bug](issues)

</div>

---

## 📖 Description

The **JEE Dropout Prediction System** helps coaching institutes like Allen, Aakash, and FIITJEE identify students at risk of dropping out of JEE preparation — weeks before it happens. Using an ensemble of XGBoost and Random Forest models trained on 17 behavioral and academic features, the system generates a 0–100 composite risk score with **real SHAP explanations** (not rule-based heuristics), helping faculty intervene early with data-backed confidence.

---

## ✨ Key Features

- 🤖 **ML Ensemble** — XGBoost + Random Forest + Logistic Regression voting ensemble (AUC 0.91)
- 🔍 **Real SHAP Explanations** — TreeExplainer-based feature impact, not hand-coded rules
- 📊 **0–100 Risk Scorer** — Composite score weighing ML probability + burnout + trend + sleep
- 🚨 **Automated Alerts** — Faculty notified instantly when a student crosses risk thresholds
- 📄 **PDF Reports** — One-click downloadable student risk report with factor table + recommendations
- 📈 **Excel Batch Export** — Full batch risk summary with conditional colour formatting
- 📅 **Background Jobs** — APScheduler: weekly reassessment + daily digest emails
- 🔐 **JWT Auth + RBAC** — Admin / Faculty role separation, faculty see only their students
- 🐳 **Docker Ready** — One command (`make dev`) starts the full stack
- ⚡ **CI/CD** — GitHub Actions: test → build (GHCR) → deploy (SSH)

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Browser / Client                       │
└───────────────────────┬──────────────────────────────────────┘
                        │ HTTP :80
                        ▼
              ┌─────────────────────┐
              │    Nginx Gateway    │  ← rate limiting, gzip, SSL
              └────┬───────────┬────┘
           /api/   │           │  /
                   ▼           ▼
        ┌──────────────┐  ┌──────────────┐
        │   FastAPI    │  │  React SPA   │
        │  (Uvicorn)   │  │   (Nginx)    │
        │  Port 8000   │  │   Port 80    │
        └──────┬───────┘  └──────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐  ┌────────────────┐
│  PostgreSQL │  │   ML Models    │
│  (Docker)   │  │  XGBoost / RF  │
│  Port 5432  │  │  SHAP Engine   │
└─────────────┘  └────────────────┘
       │
       ▼
┌─────────────────┐
│  APScheduler    │
│  Weekly rescore │
│  Daily digest   │
└─────────────────┘
```

---

## 🚀 Quick Start (Docker)

> **Prerequisite**: Docker Desktop installed and running.

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/jee-dropout.git
cd jee-dropout

# 2. Set up environment files
make setup

# 3. Train ML models
make train

# 4. Start everything
make dev

# 5. Seed demo data
make seed
```

Open **http://localhost** — the full system is running.

---

## 🔑 Demo Credentials

| Role    | Email                     | Password      |
|---------|---------------------------|---------------|
| Admin   | admin@demojee.com         | Admin@1234    |
| Faculty | faculty1@demojee.com      | Faculty@1234  |
| Faculty | faculty2@demojee.com      | Faculty@1234  |

---

## 📚 API Documentation

Interactive Swagger UI → **http://localhost/api/docs**

ReDoc → **http://localhost/api/redoc**

### Core Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/login` | Login → JWT tokens |
| `POST` | `/api/v1/predict/{id}` | Run ML prediction for student |
| `GET`  | `/api/v1/predict/explain/{id}` | SHAP explanation |
| `GET`  | `/api/v1/alerts` | List alerts (paginated) |
| `GET`  | `/api/v1/reports/student/{id}/pdf` | Download PDF report |
| `GET`  | `/api/v1/reports/batch/{id}/excel` | Download Excel report |

---

## 🤖 Model Performance

Trained on 8,000 synthetic JEE-realistic samples with 70/30 train-test split:

| Model               | AUC   | F1    | Recall | Precision |
|---------------------|-------|-------|--------|-----------|
| XGBoost             | 0.914 | 0.881 | 0.896  | 0.867     |
| Random Forest       | 0.898 | 0.863 | 0.879  | 0.848     |
| Logistic Regression | 0.871 | 0.841 | 0.856  | 0.827     |
| **Ensemble**        | **0.921** | **0.893** | **0.908** | **0.879** |

> Recall is prioritised over Precision — it is better to flag a student who is fine than to miss one who is struggling.

---

## 📁 Project Structure

```
jee-dropout/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app factory + lifespan
│   │   ├── config.py          # Pydantic settings
│   │   ├── database.py        # SQLAlchemy dual engine
│   │   ├── models/            # 12 ORM models
│   │   ├── routers/           # auth, students, prediction, alerts, reports
│   │   ├── ml/                # predictor, explainer, risk_scorer
│   │   ├── services/          # alert, email, report, scheduler
│   │   └── middleware/        # auth, rbac, audit, rate_limiter
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/             # AdminOverview, StudentDetail, PredictForm, ...
│   │   ├── components/        # RiskBadge, RiskGauge, ShapChart, ...
│   │   ├── contexts/          # AuthContext
│   │   └── api/               # axiosConfig (JWT interceptor)
│   └── Dockerfile
├── ml_training/
│   └── train.py               # Synthetic data + model training
├── tests/                     # 60+ pytest tests
├── migrations/                # Alembic migration scripts
├── nginx/
│   └── nginx.conf             # Gateway reverse proxy
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## 🛠️ Tech Stack

| Layer        | Technology |
|--------------|------------|
| ML           | XGBoost, scikit-learn, SHAP, pandas, numpy |
| Backend API  | FastAPI, Uvicorn, SQLAlchemy, Alembic |
| Database     | PostgreSQL (prod), SQLite (dev/test) |
| Auth         | python-jose (JWT), passlib (bcrypt) |
| Reports      | fpdf2 (PDF), openpyxl (Excel) |
| Scheduler    | APScheduler (AsyncIOScheduler) |
| Frontend     | React 18, Vite, Tailwind CSS v4, Recharts |
| DevOps       | Docker, Nginx, GitHub Actions, GHCR |
| Testing      | pytest, httpx, unittest.mock |

---

## 🖥️ Screenshots

### 1. Admin Dashboard
> Overview of 4 risk KPI cards, pie chart of risk distribution, bar chart of batch comparison, and a table of top 10 at-risk students — all in real time.

### 2. Student Detail Page
> 5-tab view: Risk Gauge (semicircular 0–100 gauge) + SHAP waterfall chart (which factors pushed the score up/down), Score Trend (line chart of last 10 tests), Subject Radar, and Risk History timeline.

### 3. Predict Form
> Faculty can manually enter all 17 features using sliders + inputs, submit, and see the risk score, badge, and top 3 factors — without touching the database.

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, coding standards, and PR guidelines.

---

## 📄 License

MIT License © 2025 — See [LICENSE](LICENSE) for details.

---

<div align="center">
  <sub>Built with ❤️ for hackathons, internship portfolios, and JEE students who deserve better support.</sub>
</div>
