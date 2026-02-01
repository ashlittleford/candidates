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


# --- ZOMBIE CONFIG SCAN ---
print("\n" + "!"*60)
print("SCANNING FOR CONFLICTING CONFIGURATIONS (ZOMBIE APPS)")
print("!"*60)
print("Searching public_html for hidden .htaccess files that might be blocking new app creation...")

zombies_found = []
if os.path.exists(public_html):
    for root, dirs, files in os.walk(public_html):
        if '.htaccess' in files:
            full_path = os.path.join(root, '.htaccess')
            try:
                with open(full_path, 'r', errors='ignore') as f:
                    content = f.read()
                    if 'PassengerAppRoot' in content:
                        zombies_found.append(full_path)
            except:
                pass

if zombies_found:
    print("\n[CRITICAL WARNING] Found existing Python App configurations!")
    print("These files might cause 'Alias already used' errors when creating a new app in cPanel.")
    print("If you are trying to create a NEW app for these paths, you must DELETE these files first.")
    print("")
    for z in zombies_found:
        print(f"  -> {z}")
    print("")
    print("ACTION: If you are getting an error in cPanel, rename or delete the file(s) above.")
else:
    print("[OK] No conflicting .htaccess files found in public_html scan.")


# --- Git Check ---
print("\nChecking Git Repository State...")
if os.path.isdir('.git'):
    print("[OK] .git directory found.")
else:
    print("[WARNING] .git directory NOT found.")

print("\n--- DIAGNOSTIC SCRIPT END ---")
