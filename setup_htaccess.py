import os
import sys

def create_htaccess():
    app_root = os.getcwd()
    python_path = sys.executable
    base_uri = "/"

    # Check if we are in a subdirectory like 'candidates' to offer a smarter default?
    # For now, safe default is "/" but we print a message.

    htaccess_content = f"""# DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION BEGIN
PassengerAppRoot "{app_root}"
PassengerBaseURI "{base_uri}"
PassengerPython "{python_path}"
# DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION END
"""

    file_path = '.htaccess'

    if os.path.exists(file_path):
        print(f"Warning: {file_path} already exists. Overwriting...")

    try:
        with open(file_path, 'w') as f:
            f.write(htaccess_content)
        print(f"[SUCCESS] Created {file_path}")
        print("-" * 40)
        print(htaccess_content.strip())
        print("-" * 40)
        print(f"IMPORTANT: 'PassengerBaseURI' is set to '{base_uri}'.")
        print("If your app is hosted at a sub-url (e.g. encounteradelaide.com.au/candidates),")
        print("you MUST edit .htaccess and change PassengerBaseURI to '/candidates'.")
    except Exception as e:
        print(f"[ERROR] Failed to write {file_path}: {e}")

if __name__ == "__main__":
    create_htaccess()
