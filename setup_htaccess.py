import os
import sys
import argparse

def create_htaccess():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Generate .htaccess for cPanel/Passenger deployment.")
    parser.add_argument("--base-uri", help="The Base URI for the application (e.g., '/' or '/candidates').")
    args = parser.parse_args()

    # Use the directory where the script is located as the app root
    # This ensures consistency even if run from another directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_root = script_dir
    python_path = sys.executable

    print(f"Detected App Root: {app_root}")

    # Determine Base URI
    if args.base_uri:
        base_uri = args.base_uri
    else:
        # Interactive prompt
        print("\n--- Configuration ---")
        user_input = input("Enter the Base URI (default is '/'): ").strip()
        base_uri = user_input if user_input else "/"

    print(f"Using Base URI: {base_uri}")

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

        print("\n" + "="*70)
        print("                  .htaccess GENERATED SUCCESSFULLY")
        print("="*70)
        print(f"File created at: {file_path}")
        print("-"*70)
        print(htaccess_content.strip())
        print("-"*70)

        print("\n" + "#"*70)
        print("                     CRITICAL NEXT STEP")
        print("#"*70)
        print("If you are seeing an 'Index of /' page, you MUST perform this step.")
        print("")
        print("This .htaccess file is currently in your REPOSITORY folder.")
        print("The web server looks for it in your PUBLIC_HTML (or subdomain) folder.")
        print("")
        print(">> ACTION REQUIRED: COPY THIS FILE")
        print("   Copy the generated .htaccess file to the folder your domain points to.")
        print("")
        print("   Example Command (Adjust target path as needed):")
        print(f"   cp {file_path} ~/public_html{base_uri if base_uri != '/' else ''}")
        print("")
        print("#"*70 + "\n")

    except Exception as e:
        print(f"[ERROR] Failed to write {file_path}: {e}")

if __name__ == "__main__":
    create_htaccess()
