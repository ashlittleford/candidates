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

To run the application locally:

```bash
export FLASK_APP=app
flask run
```

(On Windows PowerShell use `$env:FLASK_APP = "app"`)

The application will be accessible at `http://127.0.0.1:5000/`.

## Default Credentials

The `init_db.py` script creates the following default users:

-   **Admin User:**
    -   Username: `admin`
    -   Password: `admin123`

-   **Candidate User:**
    -   Username: `candidate`
    -   Password: `password123`

## Running Tests

To run the unit tests:

```bash
python3 -m unittest tests/test_app.py
```
