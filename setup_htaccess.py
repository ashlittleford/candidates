import os
import sys
import argparse
import shutil

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

        # Detect Public HTML
        home_dir = os.path.expanduser("~")
        public_html = os.path.join(home_dir, "public_html")

        # Deduce target directory from base_uri
        # e.g. /candidates -> ~/public_html/candidates
        # e.g. / -> ~/public_html

        rel_path = base_uri.strip('/')
        target_dir = os.path.join(public_html, rel_path)

        print("\n" + "#"*70)
        print("                     DEPLOYMENT STEP")
        print("#"*70)

        if os.path.exists(target_dir):
            print(f"Detected Public Directory: {target_dir}")
            target_file = os.path.join(target_dir, '.htaccess')

            # Check if target file already exists
            if os.path.exists(target_file):
                print(f"[WARNING] An .htaccess file already exists at {target_file}")

            confirm = input(f"Do you want to copy the generated .htaccess to {target_dir}? [y/N]: ").strip().lower()
            if confirm == 'y':
                try:
                    shutil.copy2(file_path, target_file)
                    print(f"\n[SUCCESS] Copied .htaccess to {target_file}")
                    print("The website should be working now.")
                except Exception as e:
                    print(f"\n[ERROR] Failed to copy file: {e}")
                    print(f"Please manually copy the file:\n   cp {file_path} {target_dir}/")
            else:
                print("\nSkipped automatic copy.")
                print(f"Please manually copy the file if needed:\n   cp {file_path} {target_dir}/")

        else:
             print(f"Could not automatically find the public directory: {target_dir}")
             print(">> ACTION REQUIRED: COPY THIS FILE")
             print("   Copy the generated .htaccess file to the folder your domain points to.")
             print(f"   Example Command: cp {file_path} ~/public_html{base_uri if base_uri != '/' else ''}")

        print("")
        print("#"*70 + "\n")

    except Exception as e:
        print(f"[ERROR] Failed to write {file_path}: {e}")

if __name__ == "__main__":
    create_htaccess()
