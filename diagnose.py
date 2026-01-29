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

        # Validate .htaccess content
        print("    Checking .htaccess configuration...")
        try:
            with open(f, 'r') as hf:
                content = hf.read()

                # Check App Root
                import re
                app_root_match = re.search(r'PassengerAppRoot\s+"([^"]+)"', content)
                if app_root_match:
                    config_root = app_root_match.group(1)
                    current_root = os.getcwd()
                    if config_root != current_root:
                        print(f"    [WARNING] PassengerAppRoot mismatch!")
                        print(f"        .htaccess: {config_root}")
                        print(f"        Actual:    {current_root}")
                    else:
                        print(f"    [OK] PassengerAppRoot matches current directory.")
                else:
                    print("    [WARNING] Could not find PassengerAppRoot in .htaccess")

                # Check Python Path
                python_match = re.search(r'PassengerPython\s+"([^"]+)"', content)
                if python_match:
                    config_python = python_match.group(1)
                    current_python = sys.executable
                    # Simple check: paths might differ due to symlinks, but it's a good hint
                    if config_python != current_python:
                        print(f"    [NOTE] PassengerPython path differs (this might be okay if using symlinks):")
                        print(f"        .htaccess: {config_python}")
                        print(f"        Actual:    {current_python}")
                    else:
                        print(f"    [OK] PassengerPython matches current interpreter.")
        except Exception as e:
            print(f"    (Could not validate .htaccess: {e})")

print("\nChecking for Syntax Errors in Python Scripts...")
import glob
py_files = glob.glob("*.py")
for py_file in py_files:
    try:
        with open(py_file, 'r') as f:
            content = f.read()
        compile(content, py_file, 'exec')
        print(f"[OK] {py_file} passed syntax check.")
    except SyntaxError as e:
        print(f"[FAIL] SyntaxError in {py_file}:")
        print(f"    Line {e.lineno}: {e.msg}")
        print(f"    Text: {e.text.strip() if e.text else '?'}")
    except Exception as e:
        print(f"[WARNING] Could not check {py_file}: {e}")

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
