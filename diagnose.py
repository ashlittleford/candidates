import os
import sys
import subprocess
import re

print("--- DIAGNOSTIC SCRIPT START ---")
print(f"Current Working Directory: {os.getcwd()}")
print(f"Script Directory: {os.path.dirname(os.path.abspath(__file__))}")

# --- Check Repository Files ---
print("\nChecking for critical files in repository...")

# Verify CWD matches assumed structure
cwd = os.getcwd()
print(f"[INFO] Current Directory: {cwd}")
if "repositories" in cwd:
    parent_folder = os.path.basename(cwd)
    print(f"[INFO] You seem to be in a repository folder: '{parent_folder}'")
    print("       Ensure this matches the 'Application Root' in cPanel Setup Python App.")

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

    # Try to guess the app folder
    # We look for folders that might match the app name
    potential_paths = [candidates_path]

    # Check if we can deduce from .htaccess
    if repo_htaccess_content:
        base_uri_match = re.search(r'PassengerBaseURI\s+"([^"]+)"', repo_htaccess_content)
        if base_uri_match:
            uri = base_uri_match.group(1).strip('/')
            if uri:
                potential_paths.insert(0, os.path.join(public_html, uri))

    target_found = False
    for p in potential_paths:
        if os.path.exists(p):
            print(f"[INFO] Checking potential public app folder: {p}")
            target_found = True
            public_htaccess = os.path.join(p, '.htaccess')
            if os.path.exists(public_htaccess):
                print(f"    [OK] .htaccess found in {p}")
                # Compare content?
                try:
                    with open(public_htaccess, 'r') as phf:
                        public_content = phf.read()
                        if "PassengerAppRoot" in public_content:
                            print("    [OK] .htaccess appears to contain Passenger configuration.")
                        else:
                            print("    [WARNING] .htaccess exists but might NOT contain Passenger configuration.")
                except:
                    pass
            else:
                print(f"    [CRITICAL] .htaccess MISSING in {p}")
                print(f"               This is likely causing 'Index of' errors.")
                print(f"               Action: cp {os.path.join(os.getcwd(), '.htaccess')} {p}/")

    if not target_found:
        print("[INFO] Could not automatically locate the public app folder under public_html.")
else:
    print(f"[INFO] public_html not found at {public_html} (This is normal if not on cPanel or different layout).")


# --- Git Check ---
print("\nChecking Git Repository State...")
if os.path.isdir('.git'):
    print("[OK] .git directory found.")
    try:
        # Check for origin/master specifically
        result = subprocess.run(['git', 'branch', '-r'], capture_output=True, text=True)
        if 'origin/master' not in result.stdout and 'origin/main' not in result.stdout:
            print("\n[WARNING] 'origin/master' (or main) seems missing from remote refs.")
            print("SUGGESTION: Run 'git fetch origin' in the terminal to fix synchronization issues.")
    except Exception as e:
        print(f"[ERROR] Failed to run git commands: {e}")
else:
    print("[WARNING] .git directory NOT found. This does not appear to be a git repository.")

# --- Import Check ---
print("\nAttempting to import app...")
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app import create_app
    app = create_app()
    print("[OK] Successfully imported 'app' and created application instance.")
except Exception as e:
    print(f"[FAIL] Could not import app: {e}")
    # import traceback
    # traceback.print_exc()

print("--- DIAGNOSTIC SCRIPT END ---")
