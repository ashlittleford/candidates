# Candidate Portal

A Flask-based web application for managing candidates, featuring user authentication, role-based access control (Admin and Candidate), and profile management.

## Prerequisites

- Python 3.x
- pip

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment (optional but recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Database Setup

Initialize the database and create default users by running:

```bash
python3 init_db.py
```

This will create a SQLite database `instance/site.db` (or `site.db` depending on Flask version, usually in `instance/` or root) and populate it with initial data.

## Running the Application

To run the application locally, simply execute:

```bash
python3 run.py
```

The application will be accessible at `http://localhost:5000/` (or your machine's IP address if accessing remotely). The `run.py` script automatically configures the server to listen on all public IP addresses (`0.0.0.0`).

### Alternative: Running with Flask Command Line

If you prefer to use the `flask` command directly:

```bash
export FLASK_APP=app
flask run --host=0.0.0.0
```

(On Windows PowerShell use `$env:FLASK_APP = "app"`)

**Note:** The `--host=0.0.0.0` flag tells Flask to listen on all public IPs, which is often required if running in a container (like Docker) or a remote environment.

## Default Credentials

The `init_db.py` script creates the following default users:

-   **Admin User:**
    -   Username: `admin`
    -   Password: `admin123`

-   **Candidate User:**
    -   Username: `candidate`
    -   Password: `password123`

-   **Panel Member User:**
    -   Username: `panel_member`
    -   Password: `password123`

**Important:** Please change these default passwords immediately after initial setup, especially in a production environment.

## Running Tests

To run the unit tests:

```bash
python3 -m unittest tests/test_app.py
```

## Troubleshooting

### OperationalError: no such column: profile.current_church

If you encounter an error like `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: profile.current_church` when running the application, it means your local database schema is outdated.

To fix this without losing your data, run the provided fix script:

```bash
python3 fix_schema.py
```

This script will update your existing database to include the missing column.
