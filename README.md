# CloudDeploy — Phase 1: Project Foundation

## Project Overview

**CloudDeploy** is a self-service cloud deployment platform designed with automated rollback and release management capabilities. The platform enables development teams to:

- Connect and manage source code repositories (such as GitHub).
- Register and configure web applications and microservices.
- Trigger and manage automated deployments across environments (Development, Staging, Production).
- Monitor deployment health and execution status.
- Manage releases and safely rollback to prior healthy versions.

The first managed application scheduled for deployment via CloudDeploy is a spices e-commerce website.

Phase 1 establishes the clean, modular backend foundation using Django 5.2 LTS and Django REST Framework, setting up core models (custom user, application, deployment), health monitoring, and Django Admin administration.

---

## Technology Stack

- **Language:** Python 3.12+ (tested on Python 3.13)
- **Framework:** Django 5.2 LTS (`django>=5.2,<5.3`)
- **API Framework:** Django REST Framework (`djangorestframework>=3.15.0`)
- **Environment Management:** `python-dotenv`
- **Initial Database:** SQLite 3 (configured with clean separation to allow seamless transition to PostgreSQL in future phases without application coupling)
- **Version Control:** Git

---

## Folder Structure

```text
CloudDeploy/
├── .gitignore                     # Repository-level ignore rules
├── README.md                      # Developer documentation and project guide
└── backend/
    ├── accounts/                  # Custom user model, roles, and auth admin
    │   ├── migrations/
    │   │   ├── 0001_initial.py
    │   │   └── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── models.py
    │   └── tests.py
    ├── applications/              # Application registration and repository metadata
    │   ├── migrations/
    │   │   ├── 0001_initial.py
    │   │   └── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── models.py
    │   └── tests.py
    ├── deployments/               # Deployment jobs, environment targets, and statuses
    │   ├── migrations/
    │   │   ├── 0001_initial.py
    │   │   └── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── models.py
    │   └── tests.py
    ├── common/                    # Shared utilities and health-check endpoints
    │   ├── admin.py
    │   ├── apps.py
    │   ├── tests.py
    │   ├── urls.py
    │   └── views.py
    ├── config/                    # Django project core configuration
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── .env.example               # Environment variables template
    ├── .gitignore                 # Backend-specific ignore rules
    ├── manage.py                  # Django CLI management entrypoint
    └── requirements.txt           # Python project dependencies
```

---

## Prerequisites

- **Python:** Version 3.12 or higher installed.
- **Git:** Version 2.x installed.
- **PowerShell:** On Windows (or Bash / Zsh on macOS/Linux).

---

## Virtual Environment Setup

### Windows PowerShell

1. Open PowerShell and navigate to the project root:
   ```powershell
   cd "c:\Users\abyjoseph\Desktop\Cloud Deploy"
   ```

2. Create the virtual environment:
   ```powershell
   python -m venv .venv
   ```

3. If running scripts is restricted in your PowerShell session, permit execution:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   ```

4. Activate the virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

### macOS / Linux (Equivalent)

```bash
cd "Cloud Deploy"
python3 -m venv .venv
source .venv/bin/activate
```

---

## Installation Commands

With your virtual environment activated:

```powershell
cd backend
pip install -r requirements.txt
```

---

## Environment Configuration

Copy the template `.env.example` into `.env` inside the `backend` directory:

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### macOS / Linux

```bash
cp .env.example .env
```

### Configurable Variables

| Variable | Description | Default in Development |
| :--- | :--- | :--- |
| `SECRET_KEY` | Django cryptographic signing key | Insecure dev key |
| `DEBUG` | Enables/disables debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated list of accepted host headers | `localhost,127.0.0.1,[::1]` |

---

## Database Migration & Readiness

The custom user model (`accounts.User`) is configured as `AUTH_USER_MODEL` prior to applying any migrations to guarantee clean database initialization.

Execute migrations with the following commands:

```powershell
cd backend
python manage.py makemigrations
python manage.py migrate
```

Verify that the system checks pass:

```powershell
python manage.py check
```

---

## Superuser Creation

Create an administrator account to access the Django Admin interface:

```powershell
python manage.py createsuperuser
```

*Note:* CloudDeploy automatically assigns the `ADMIN` role to accounts created via `createsuperuser`.

---

## Running the Development Server

Start Django's built-in WSGI development server:

```powershell
python manage.py runserver
```

- **Base URL:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Django Admin Interface:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## Running Tests

Run the automated test suite using Django's test runner:

```powershell
cd backend
python manage.py test
```

To run tests for individual applications:

```powershell
python manage.py test accounts
python manage.py test applications
python manage.py test deployments
python manage.py test common
```

All tests execute in an isolated SQLite memory/test database, preserving existing development data.

---

## Health Check Endpoint

CloudDeploy provides a service and database health check endpoint:

- **Method:** `GET`
- **URL:** `http://127.0.0.1:8000/api/health/`

### Sample Response (Healthy)

```json
{
  "status": "ok",
  "service": "CloudDeploy API",
  "database": "ok"
}
```

### Degraded Response (Database Unavailable)

```json
{
  "status": "degraded",
  "service": "CloudDeploy API",
  "database": "unavailable"
}
```

*Security guarantee:* The health endpoint does not leak credentials, file paths, or internal tracebacks upon failure.

---

## Current Phase Limitations & Scope

**Phase 1** focuses strictly on the architectural foundation:

- **Metadata Models:** `Application` and `Deployment` models store metadata only.
- **No External Integrations:** In this phase, GitHub cloning, Docker builds, AWS provisioning (EC2, ECR, IAM), and automated rollback engines are explicitly out of scope.
- **Database:** SQLite is used for local development; transition to PostgreSQL will occur in a later phase.
- **Frontend:** No frontend UI (React) is included in Phase 1.

