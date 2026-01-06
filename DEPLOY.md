# Deployment Guide for cPanel

This guide provides step-by-step instructions for deploying the Candidate Portal application to a cPanel environment (like "ventrip").

## Prerequisites
*   Access to cPanel.
*   The Git repository URL for this project.
*   Domain or subdomain ready (e.g., `encounteradelaide.com.au/candidates`).

## Step 1: Clone the Repository in cPanel

1.  Log in to cPanel.
2.  Navigate to **Git Version Control** (under "Files").
3.  Click **Create**.
4.  **Clone URL**: Enter the Git repository URL.
5.  **Repository Path**: Enter a path, e.g., `repositories/candidate-portal`.
6.  **Repository Name**: (Optional) Enter a name like "Candidate Portal".
7.  Click **Create**.

## Step 2: Setup Python App

1.  Navigate to **Setup Python App** (under "Software").
2.  Click **Create Application**.
3.  **Python Version**: Select **3.9** or newer (recommended).
4.  **Application Root**: Enter the path where you cloned the repo (e.g., `repositories/candidate-portal`).
5.  **Application URL**: Select your domain and enter the sub-path if needed (e.g., `candidates`).
6.  **Application Startup File**: Enter `passenger_wsgi.py`.
    *   *Note: This file is included in the repository and configured to load the app correctly.*
7.  **Application Entry Point**: Enter `application`.
8.  Click **Create**.

## Step 3: Install Dependencies

1.  In the "Setup Python App" page, look for the **Command for entering virtual environment**. It will look something like:
    `source /home/username/virtualenv/repositories/candidate-portal/3.9/bin/activate && cd /home/username/repositories/candidate-portal`
2.  Copy this command.
3.  Open **Terminal** in cPanel (or SSH into the server).
4.  Paste the command to activate the virtual environment.
    *   *Note: If the command doesn't automatically change directory (`cd`), you must manually navigate to your application root folder.*
5.  **Verify you are in the correct directory:**
    ```bash
    ls -F
    ```
    *   You should see `requirements.txt`, `app/`, `run.py`, etc.
    *   **If you do not see these files:**
        *   Check if they are in a subdirectory (e.g., `cd candidate-portal`).
        *   Go back to **Git Version Control** and verify the "Repository Path".
6.  Run the following command to install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Step 4: Initialize the Database

1.  While still in the terminal (with the virtual environment active), run:
    ```bash
    python init_db.py
    ```
    *   This will create the database file `instance/site.db`, create an Admin user (admin/admin123), and populate initial data.

## Step 5: Restart the Application

1.  Go back to **Setup Python App** in cPanel.
2.  Click **Restart** for your application.

## Verification

1.  Visit your URL (e.g., `https://encounteradelaide.com.au/candidates`).
2.  You should see the login page.
3.  **Default Credentials**:
    *   **Admin**: username `admin`, password `admin123`
    *   **Candidate**: username `candidate`, password `password123`
4.  **Important**: Log in immediately and change the default passwords.

## Troubleshooting

*   **Error: "No such file or directory: 'requirements.txt'"**:
    *   This means you are not in the directory containing the code.
    *   Run `ls -la` to see current files.
    *   If the directory is empty, you might have skipped **Step 1** (Git Clone) or cloned into a different path.
    *   If you see a folder named after your repo, `cd` into it.
*   **500 Internal Server Error**: Check the error log in cPanel (often under `stderr.log` in the application root or via the "Errors" section in cPanel).
*   **Database Read-Only**: Ensure the `instance` folder has write permissions. You can check this in cPanel File Manager (permissions should usually be 755 or 775).
