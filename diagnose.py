import os
import sys

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
