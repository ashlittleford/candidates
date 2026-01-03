import sqlite3
import os
import sys

def fix_schema():
    # Define database path
    # Handle different environments (e.g. if run from root or elsewhere)
    # We assume run from root as per README instructions
    db_path = os.path.join('instance', 'site.db')

    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}.")
        print("Please ensure you have initialized the database using 'python3 init_db.py' first.")
        sys.exit(1)

    print(f"Checking database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if 'current_church' column exists in 'profile' table
        cursor.execute("PRAGMA table_info(profile)")
        columns_info = cursor.fetchall()
        columns = [info[1] for info in columns_info]

        if 'current_church' not in columns:
            print("Missing column 'current_church' detected in 'profile' table.")
            print("Adding 'current_church' column...")

            # Add the column
            # Matching the definition in app/models.py: db.String(150), nullable=True
            cursor.execute("ALTER TABLE profile ADD COLUMN current_church VARCHAR(150)")
            conn.commit()
            print("Successfully added 'current_church' column.")
        else:
            print("Column 'current_church' already exists. No changes needed.")

    except sqlite3.OperationalError as e:
        print(f"Error accessing database: {e}")
        print("The database schema might be significantly different or corrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    fix_schema()
