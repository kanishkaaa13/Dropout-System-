# Contributing to JEE Dropout Prediction System

Thank you for your interest in contributing! This guide helps you get set up quickly.

---

## 🛠️ Local Dev Setup (No Docker)

### Prerequisites
- Python 3.11+
- Node.js 20+
- Git

### 1. Clone and install backend

```bash
git clone https://github.com/YOUR_USERNAME/jee-dropout.git
cd jee-dropout

# Create virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Set up environment
cp backend/.env.example backend/.env
# Edit backend/.env — set DATABASE_URL=sqlite:///./jee_dropout.db for local dev
```

### 2. Set up database and seed data

```bash
# Run migrations
alembic upgrade head

# Train models (required before first run)
python ml_training/train.py

# Seed demo data
python -m backend.app.utils.db_seed
```

### 3. Start backend

```bash
uvicorn backend.app.main:app --reload --port 8000
# API docs → http://localhost:8000/api/docs
```

### 4. Install and start frontend

```bash
cd frontend
cp .env.example .env
# Edit .env → VITE_API_URL=http://localhost:8000/api/v1

npm install
npm run dev
# Frontend → http://localhost:5173
```

---

## 📏 Coding Standards

### Python

| Tool     | Command                        | Purpose                     |
|----------|--------------------------------|-----------------------------|
| Black    | `black backend/ tests/`        | Code formatter (required)   |
| isort    | `isort backend/ tests/`        | Import sorting (required)   |
| Ruff     | `ruff check backend/`          | Fast linter                 |
| mypy     | `mypy backend/app/`            | Type checking (encouraged)  |

**Rules:**
- ✅ **Type hints required** on all function signatures
- ✅ **Docstrings required** on all public functions and classes
- ✅ **No bare `except:`** — always catch specific exceptions
- ✅ **No `print()`** — use `logging.getLogger(__name__)`
- ✅ Max line length: **100 characters** (Black default)
- ❌ No hardcoded secrets, URLs, or paths

```python
# ✅ Good
def get_student(student_id: int, db: Session) -> Optional[Student]:
    """Fetch a single student by primary key. Returns None if not found."""
    return db.query(Student).filter_by(id=student_id).first()

# ❌ Bad
def get_student(id, db):
    return db.query(Student).filter_by(id=id).first()
```

### JavaScript / React

- Use **functional components** with hooks only
- **No class components**
- All API calls go through `src/api/axiosConfig.js` — never use `fetch()` directly
- Use `clsx` for conditional classNames
- Keep components under 200 lines — split if larger

---

## 🧪 Running Tests

```bash
# Run all tests (fast — uses SQLite in-memory)
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend/app --cov-report=term-missing

# Run a specific test class
pytest tests/test_auth.py::TestLogin -v

# Run tests matching a keyword
pytest tests/ -k "predict" -v
```

**Rules for new tests:**
- ✅ Use the shared `client`, `admin_headers`, `faculty_headers` fixtures from `conftest.py`
- ✅ Mock all ML model calls — never load real `.pkl` files in tests
- ✅ Tests must be independent — no shared mutable state between tests
- ✅ Use `scope="module"` for expensive fixtures (DB rows), `scope="function"` for mutable state
- ✅ Every new router must have at least one test

---

## 🔄 Pull Request Guidelines

### Branch naming

```
feature/short-description       # new feature
fix/bug-description             # bug fix
docs/what-was-updated           # documentation only
test/what-was-tested            # tests only
refactor/what-was-changed       # refactor without feature change
```

### PR checklist

Before opening a PR, ensure:

- [ ] All existing tests pass: `pytest tests/ -q`
- [ ] New code has type hints
- [ ] New functions have docstrings
- [ ] Code is formatted: `black backend/ && isort backend/`
- [ ] No secrets or `.env` values committed
- [ ] PR description explains **what** changed and **why**

### PR size

- Keep PRs **focused and small** — one feature or fix per PR
- If your PR touches > 10 files, consider splitting it

---

## 🐛 Issue Templates

### Bug Report

```
**Description**: What went wrong?

**Steps to reproduce**:
1. ...
2. ...

**Expected**: What should have happened?
**Actual**: What actually happened?

**Environment**: Python version, OS, Docker version
**Logs**: Paste relevant error output
```

### Feature Request

```
**Problem**: What problem does this solve?

**Proposed solution**: How would you implement it?

**Alternatives considered**: What else did you consider?

**Is this a breaking change?**: Yes / No
```

---

## 📁 Project Conventions

| Convention | Rule |
|---|---|
| File names | `snake_case.py` for Python, `PascalCase.jsx` for React |
| DB models | Singular (`Student`, not `Students`) |
| API paths | Plural, kebab-case (`/api/v1/mock-tests`) |
| Response keys | `snake_case` (Python) → React converts on display |
| Error messages | Sentence case, no trailing period |
| Dates | Always UTC in DB, format `YYYY-MM-DDTHH:MM:SSZ` in API |

---

## 💬 Questions?

Open a [GitHub Discussion](https://github.com/YOUR_USERNAME/jee-dropout/discussions) or ping in the project Slack.
