import os
import sys
import subprocess
import re

print("--- DIAGNOSTIC SCRIPT START ---")
print(f"Current Working Directory: {os.getcwd()}")
script_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Script Directory: {script_dir}")

# --- Check Repository Files ---
print("\nChecking for critical files in repository...")

cwd = os.getcwd()
if "repositories" in cwd:
    parent_folder = os.path.basename(cwd)
    print(f"[INFO] You seem to be in a repository folder: '{parent_folder}'")

files_to_check = ['passenger_wsgi.py', 'requirements.txt', 'app/__init__.py', '.htaccess']
repo_htaccess_content = None

for f in files_to_check:
    exists = os.path.exists(f)
    print(f"[{'OK' if exists else 'MISSING'}] {f}")
    if f == '.htaccess' and exists:
        try:
            with open(f, 'r') as hf:
                repo_htaccess_content = hf.read()
                print("    [INFO] Repository .htaccess found.")
        except Exception as e:
            print(f"    [ERROR] Could not read .htaccess: {e}")

# --- Check Public Directory (Heuristic) ---
print("\nChecking Public Directory (Heuristic)...")
home_dir = os.path.expanduser("~")
public_html = os.path.join(home_dir, "public_html")
candidates_path = os.path.join(public_html, "candidates")

if os.path.exists(public_html):
    print(f"[OK] Found public_html at: {public_html}")

    # Identify potential target directories
    potential_paths = []

    # 1. 'candidates' folder (hardcoded common case)
    if os.path.exists(candidates_path):
        potential_paths.append(candidates_path)

    # 2. Folder matching current repo name
    repo_name = os.path.basename(cwd)
    repo_path = os.path.join(public_html, repo_name)
    if os.path.exists(repo_path) and repo_path not in potential_paths:
        potential_paths.append(repo_path)

    target_found = False
    for p in potential_paths:
        print(f"\n[INFO] Checking potential public app folder: {p}")
        target_found = True
        public_htaccess = os.path.join(p, '.htaccess')

        if os.path.exists(public_htaccess):
            print(f"    [OK] .htaccess found in {p}")
            try:
                with open(public_htaccess, 'r') as phf:
                    public_content = phf.read()

                    # Check for Passenger Config
                    if "PassengerAppRoot" in public_content:
                        print("    [OK] .htaccess contains Passenger configuration.")
                    else:
                        print("    [WARNING] .htaccess exists but might NOT contain Passenger configuration.")

                    # Check for Subdomain vs Subfolder Mismatch
                    base_uri_match = re.search(r'PassengerBaseURI\s+"([^"]+)"', public_content)
                    if base_uri_match:
                        uri = base_uri_match.group(1)
                        folder_name = os.path.basename(p)
                        print(f"    [INFO] PassengerBaseURI is set to: '{uri}'")

                        if uri != "/" and folder_name in uri:
                            print(f"    [WARNING] POTENTIAL MISCONFIGURATION DETECTED!")
                            print(f"              You are in a subfolder '{folder_name}' but BaseURI is '{uri}'.")
                            print(f"              If this site is accessed via a subdomain (e.g., {folder_name}.domain.com),")
                            print(f"              the BaseURI MUST be '/'.")
                            print(f"              Run 'python3 setup_htaccess.py' and ensure Base URI is set to '/'.")
                        elif uri == "/" and folder_name:
                            print(f"    [OK] BaseURI is '/' which is correct for subdomain deployment.")
            except Exception as e:
                print(f"    [ERROR] Could not read .htaccess: {e}")
        else:
            print(f"    [CRITICAL] .htaccess MISSING in {p}")
            print(f"               This is likely causing 'Index of' errors.")
            print(f"               Action: Run 'python3 setup_htaccess.py' then copy the file.")

    if not target_found:
        print("[INFO] Could not automatically locate the public app folder under public_html.")
else:
    print(f"[INFO] public_html not found at {public_html} (This is normal if not on cPanel or different layout).")


# --- Git Check ---
print("\nChecking Git Repository State...")
if os.path.isdir('.git'):
    print("[OK] .git directory found.")
else:
    print("[WARNING] .git directory NOT found.")

print("\n--- DIAGNOSTIC SCRIPT END ---")
