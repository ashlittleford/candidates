import os
import sys
import subprocess

print("--- DIAGNOSTIC SCRIPT START ---")
print(f"Current Working Directory: {os.getcwd()}")
print(f"Script Directory: {os.path.dirname(os.path.abspath(__file__))}")

print("\nChecking for critical files...")
files_to_check = ['passenger_wsgi.py', 'requirements.txt', 'app/__init__.py', '.htaccess']
for f in files_to_check:
    exists = os.path.exists(f)
    print(f"[{'OK' if exists else 'MISSING'}] {f}")
    if f == '.htaccess' and exists:
        print("    --- .htaccess content start ---")
        try:
            with open(f, 'r') as hf:
                print(hf.read())
        except Exception as e:
            print(f"    (Could not read file: {e})")
        print("    --- .htaccess content end ---")

print("\nChecking Git Repository State...")
if os.path.isdir('.git'):
    print("[OK] .git directory found.")
    try:
        print("    Running 'git remote -v':")
        sys.stdout.flush()
        subprocess.run(['git', 'remote', '-v'], check=False)

        print("    Running 'git branch -a':")
        sys.stdout.flush()
        subprocess.run(['git', 'branch', '-a'], check=False)

        print("    Running 'git status':")
        sys.stdout.flush()
        subprocess.run(['git', 'status'], check=False)

        # Check for origin/master specifically
        result = subprocess.run(['git', 'branch', '-r'], capture_output=True, text=True)
        if 'origin/master' not in result.stdout and 'origin/main' not in result.stdout:
            print("\n[WARNING] 'origin/master' (or main) seems missing from remote refs.")
            print("SUGGESTION: Run 'git fetch origin' in the terminal to fix synchronization issues.")
    except Exception as e:
        print(f"[ERROR] Failed to run git commands: {e}")
else:
    print("[WARNING] .git directory NOT found. This does not appear to be a git repository.")

print("\nAttempting to import app...")
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app import create_app
    app = create_app()
    print("[OK] Successfully imported 'app' and created application instance.")
except Exception as e:
    print(f"[FAIL] Could not import app: {e}")
    import traceback
    traceback.print_exc()

print("--- DIAGNOSTIC SCRIPT END ---")
