# Compliance Tracker – Backend

Production-ready FastAPI backend for the Compliance Tracker SaaS application.

## Stack

- **Python** 3.11+
- **FastAPI** – API framework
- **PostgreSQL** – Database
- **SQLAlchemy 2** – ORM
- **Alembic** – Migrations
- **Pydantic** – Settings and request/response validation

## Project structure

```
backend/
  app/
    main.py              # Application entry point
    core/
      config.py          # Settings from environment
      database.py        # SQLAlchemy engine and session
    models/              # SQLAlchemy models
    schemas/             # Pydantic schemas
    api/
      v1/                # API v1 routes (health, users)
    services/            # Business logic (placeholder)
  alembic/               # Migrations
  requirements.txt
  .env.example
```

## Setup

### 0. PostgreSQL (Windows)

If you don’t have PostgreSQL installed, see **[docs/POSTGRES_WINDOWS.md](docs/POSTGRES_WINDOWS.md)** for step-by-step installation and database creation on Windows.

### 1. Create virtual environment

```bash
cd backend
python -m venv .venv
```

- **Windows:** `.venv\Scripts\activate`
- **macOS/Linux:** `source .venv/bin/activate`

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment variables

Copy the example env file and set your values:

```bash
copy .env.example .env
```

Edit `.env` and set at least `DATABASE_URL` for your PostgreSQL instance:

```
DATABASE_URL=postgresql://user:password@localhost:5432/compliance_tracker
```

### 4. Create database

Create a PostgreSQL database (e.g. `compliance_tracker`). Then run migrations:

```bash
alembic upgrade head
```

### 5. Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API root: http://localhost:8000/
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/api/v1/health  
- Readiness (with DB check): http://localhost:8000/api/v1/health/ready

## Cursor terminal (Windows)

Run **one command per line**. Open a terminal and go to the backend folder first:  
`cd c:\Users\ASUS\Desktop\compliance-tracker-mvp\backend`

**If you get "running scripts is disabled":** run this once (allows scripts for your user):  
`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`  
Then you can use `.\.venv\Scripts\Activate.ps1` as below.

**Without activating the venv** (works even when scripts are disabled):

**1. Migrations** (run once after DB is set up):
```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

**2. Start the server:**
```powershell
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

**With venv activated** (after fixing execution policy and running `.\.venv\Scripts\Activate.ps1`):
```powershell
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Commands reference

| Command | Description |
|--------|-------------|
| `uvicorn app.main:app --reload` | Run dev server with auto-reload |
| `alembic upgrade head` | Apply all migrations |
| `alembic revision -m "message"` | Create a new migration |
| `alembic downgrade -1` | Roll back one migration |

## API overview

- **Health:** `GET /api/v1/health`, `GET /api/v1/health/ready`
- **Users (example):** `GET/POST /api/v1/users`, `GET/PATCH/DELETE /api/v1/users/{id}`

Authentication and document-related logic are not included in this base setup.
