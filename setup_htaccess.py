import os
import sys
import argparse

def create_htaccess():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Generate .htaccess for cPanel/Passenger deployment.")
    parser.add_argument("--base-uri", help="The Base URI for the application (e.g., '/' or '/candidates').")
    parser.add_argument("--target-dir", help="The relative path in public_html (e.g. 'candidates').")
    args = parser.parse_args()

    # Use the directory where the script is located as the app root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_root = script_dir
    cwd_name = os.path.basename(script_dir)
    python_path = sys.executable

    print(f"Detected App Root: {app_root}")

    # --- Configuration ---
    print("\n" + "="*60)
    print("                  CONFIGURATION")
    print("="*60)

    # WARNING about order of operations
    print("\n[IMPORTANT WARNING]")
    print("If you have NOT yet created the application in cPanel 'Setup Python App',")
    print("DO NOT COPY the file yet! Doing so might block cPanel from creating the app.")
    print("Create the app in cPanel first, THEN overwrite the .htaccess if needed.")

    # 1. Base URI
    if args.base_uri:
        base_uri = args.base_uri
    else:
        print("\n[Step 1] Base URI")
        print("-----------------")
        print("This tells Passenger where the app is in the URL.")
        print(" - SUBDOMAIN (e.g. candidates.site.com) -> Enter '/'")
        print(" - SUBFOLDER (e.g. site.com/candidates) -> Enter '/candidates'")

        base_uri_input = input(f"Base URI [default: '/']: ").strip()
        base_uri = base_uri_input if base_uri_input else "/"

    # 2. Target Directory
    if args.target_dir:
        target_rel_path = args.target_dir
    else:
        print("\n[Step 2] Public Folder")
        print("----------------------")
        print("Where does your domain point to on the file system?")
        print(f" - Usually matches your repo name: '{cwd_name}'")
        print(f" - If pointing to public_html root, enter '/'")

        target_input = input(f"Folder name in public_html [default: '{cwd_name}']: ").strip()

        if target_input == "":
            target_rel_path = cwd_name
        elif target_input == "/" or target_input == ".":
            target_rel_path = ""
        else:
            target_rel_path = target_input.strip("/")

    print(f"\nUsing Base URI: {base_uri}")
    print(f"Target Folder: public_html/{target_rel_path if target_rel_path else ''}")

    htaccess_content = f"""# DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION BEGIN
PassengerAppRoot "{app_root}"
PassengerBaseURI "{base_uri}"
PassengerPython "{python_path}"
# DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION END
"""

    file_path = os.path.join(app_root, '.htaccess')

    if os.path.exists(file_path):
        print(f"\nWarning: {file_path} already exists. Overwriting...")

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
        target_dir = os.path.join(public_html, target_rel_path)

        print("\n" + "#"*70)
        print("                     CRITICAL NEXT STEP")
        print("#"*70)

        if base_uri != "/" and target_rel_path != "" and base_uri.strip('/') != target_rel_path:
             print("NOTE: Your Base URI and Target Folder are different.")
             print("      Ensure this is intentional (e.g. mapping /app to folder /other).")

        copy_cmd = f"cp {file_path} {target_dir}/"

        print(f"You must copy the .htaccess file to: {target_dir}/")
        print(">> ACTION REQUIRED: RUN THIS COMMAND NOW:")
        print("")
        print(f"   {copy_cmd}")
        print("")
        print("[NOTE] If cPanel says 'Alias already used', DELETE the .htaccess in")
        print(f"       {target_dir}/ first, create the app in cPanel, then copy this file.")
        print("#"*70 + "\n")

    except Exception as e:
        print(f"[ERROR] Failed to write {file_path}: {e}")

if __name__ == "__main__":
    create_htaccess()
