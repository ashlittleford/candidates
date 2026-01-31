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
    *   **Note:** You may see an error stating "The system cannot deploy" or complaining about a missing `.cpanel.yml` file. **You can safely ignore this.** We are configuring the application to run directly from the repository using the "Setup Python App" tool in the next step, so we do not use the "Deploy" feature in the Git Version Control page.

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
        *   **Use this command to find where the files are:**
            ```bash
            find . -maxdepth 3 -name init_db.py
            ```
        *   If it returns something like `./candidate-portal/init_db.py`, then type:
            ```bash
            cd candidate-portal
            ```
        *   Now you should be in the right place.
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

*   **Problem: I see "Index of /candidates/" or "Index of /home/" (Directory Listing)**:
    *   **Explanation**: This error confirms that the web server is looking at your files but **does not know it is a Python application**. It means the `.htaccess` file is missing or invalid.
    *   **Immediate Fix**: You **MUST** ensure an `.htaccess` file exists in the directory shown in the "Index of" page.
    *   **Note**: This file is specific to your server (it contains your unique paths). **It should NOT be in your Git repository.** We have added it to `.gitignore` to prevent accidental commits.
    *   **Solution 0: Automatic Fix (Easiest)**
        1.  Open **Terminal** in cPanel.
        2.  Navigate to your **Repository Folder** (e.g., `cd repositories/candidate-portal`).
        3.  Run the setup script:
            ```bash
            python setup_htaccess.py
            ```
            *   *Note: The script will ask for the Base URI (e.g., `/` or `/candidates`).*
        4.  **CHECK THE OUTPUT:** The script will generate the file and **show you the exact command** to copy it to your public folder.
        5.  **ACTION REQUIRED:**
            *   **Most Likely:** If the website is serving files from a public folder (e.g., `public_html/candidates`) and you see an "Index of" page there, you MUST **copy** the generated `.htaccess` file.
            *   **Run the command provided by the script output.**
            *   Example: `cp .htaccess ~/public_html/candidates/`
        6.  **Verify:** Visit your website again. The "Index of" page should be gone.

    *   **Solution 1: Manually Create `.htaccess`**
        1.  Go to **File Manager** in cPanel.
        2.  Navigate to the folder you see in the "Index of" page (likely `repositories/candidate-portal` or `public_html/candidates`).
        3.  Ensure **Settings > Show Hidden Files** is checked (top right corner).
        4.  Create a **new file** named `.htaccess` (starts with a dot).
        5.  Edit the file and paste the content from the `htaccess.example` file included in this repository.
        6.  **IMPORTANT:** You must update the paths in the file to match your server environment!
            ```apache
            # DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION BEGIN
            PassengerAppRoot "/home/encosnpm/repositories/candidate-portal"
            PassengerBaseURI "/"
            PassengerPython "/home/encosnpm/virtualenv/repositories/candidate-portal/3.12/bin/python"
            # DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION END
            ```
            *   **Note:** If you are deploying to a subfolder (e.g., `encounteradelaide.com.au/candidates`), change `PassengerBaseURI` to `"/candidates"`.
            *   **Note:** If you cloned into `public_html`, your App Root might be `/home/encosnpm/public_html/candidates`.
        *   **How to find the correct paths?**
            *   Open the Terminal in cPanel.
            *   Navigate to your app folder (`cd repositories/candidate-portal`).
            *   Type `pwd` and press Enter. This is your **PassengerAppRoot**.
            *   The **PassengerPython** path is visible in the "Setup Python App" page as the "Command for entering virtual environment" (the path ending in `.../bin/python` inside the source command).
    *   **Solution 2: Re-create the App**:
        1.  In **Setup Python App**, find your application and click the **Delete (Trash/X)** icon. *This only deletes the configuration, not your code.*
        2.  Create the application again (follow **Step 2**), ensuring the **Application URL** matches exactly (e.g., `candidates`).
        3.  Click **Create**. This forces cPanel to generate the necessary `.htaccess` file.

*   **Problem: Files are nested too deep**:
    *   **Check File Manager**: Go to cPanel > File Manager and look in your repository folder (e.g., `repositories/candidate-portal`).
        *   **If it is empty:** The Git Clone failed. Delete the folder and try **Step 1** again.
        *   **If you see another folder inside** (e.g., `candidate-portal` inside `candidate-portal`): Your files are nested too deep. Move them up one level so `app/`, `requirements.txt`, and `passenger_wsgi.py` are directly in the Application Root.
*   **Error: "The following untracked working tree files would be overwritten by merge: passenger_wsgi.py"**:
    *   This happens because cPanel or you created a `passenger_wsgi.py` file locally, but now one also exists in the git repository.
    *   **Solution**:
        1.  Open **File Manager** or **Terminal**.
        2.  Navigate to your repository folder.
        3.  Delete or rename the existing `passenger_wsgi.py` file (e.g., rename to `passenger_wsgi.py.bak`).
        4.  Try the **Git Pull** or update operation again.
*   **Error: "The system cannot deploy... A valid .cpanel.yml file exists..."**:
    *   **Ignore this.** This error appears in the "Git Version Control" page if you click "Deploy HEAD" or if cPanel tries to auto-deploy. Since we are running the app directly from the source code folder (via Setup Python App), we do not need to "deploy" (copy) files to another location.
*   **Error: "No such file or directory: 'requirements.txt'" or "can't open file 'init_db.py'"**:
    *   This means you are not in the exact folder containing the code files in the Terminal.
    *   Run `find . -maxdepth 3 -name init_db.py` to locate the file.
    *   `cd` into the directory shown in the result (e.g., `cd repositories/candidate-portal`).
*   **500 Internal Server Error**: Check the error log in cPanel (often under `stderr.log` in the application root or via the "Errors" section in cPanel).
*   **Database Read-Only**: Ensure the `instance` folder has write permissions. You can check this in cPanel File Manager (permissions should usually be 755 or 775).
*   **Error: (XID ...) "/usr/local/cpanel/3rdparty/bin/git" reported error code "128"... fatal: 'origin/master' is not a commit**:
    *   This error usually appears in the "Git Version Control" page and indicates the local repository on the server is incomplete or out of sync with the remote.
    *   **Solution**:
        1.  Open **Terminal** in cPanel.
        2.  Navigate to your repository folder (e.g., `cd repositories/candidate-portal`).
        3.  Run the following commands to resync with GitHub:
            ```bash
            git fetch origin
            git checkout master
            ```
            *   If `git checkout master` fails, try `git checkout -b master origin/master`.
        4.  Run `python diagnose.py` to verify the git state.
