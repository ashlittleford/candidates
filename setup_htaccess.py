import os
import sys

def create_htaccess():
    # Use the directory where the script is located as the app root
    # This ensures consistency even if run from another directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_root = script_dir
    python_path = sys.executable
    base_uri = "/"

    print(f"Detected App Root: {app_root}")

    # Check for passenger_wsgi.py
    if not os.path.exists(os.path.join(app_root, 'passenger_wsgi.py')):
        print("[WARNING] 'passenger_wsgi.py' not found in the script directory.")
        print("          Ensure this script is located in the root of your Git repository.")

    htaccess_content = f"""# DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION BEGIN
PassengerAppRoot "{app_root}"
PassengerBaseURI "{base_uri}"
PassengerPython "{python_path}"
# DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION END
"""

    file_path = os.path.join(app_root, '.htaccess')

    if os.path.exists(file_path):
        print(f"Warning: {file_path} already exists. Overwriting...")

    try:
        with open(file_path, 'w') as f:
            f.write(htaccess_content)
        print(f"[SUCCESS] Created {file_path}")
        print("-" * 60)
        print(htaccess_content.strip())
        print("-" * 60)
        print("IMPORTANT DEPLOYMENT INSTRUCTIONS:")
        print("1. 'PassengerBaseURI' is set to '/'. If your app is hosted at a sub-url")
        print("   (e.g. encounteradelaide.com.au/candidates), you MUST edit .htaccess")
        print("   and change PassengerBaseURI to '/candidates'.")
        print("")
        print("2. LOCATION: This .htaccess file is now in your Repository folder.")
        print("   If your website is served from a DIFFERENT folder (e.g. public_html/candidates),")
        print("   you MUST COPY this .htaccess file to that folder.")
        print("-" * 60)
    except Exception as e:
        print(f"[ERROR] Failed to write {file_path}: {e}")

if __name__ == "__main__":
    create_htaccess()
