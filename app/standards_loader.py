import json
import os

def load_standards():
    filepath = os.path.join(os.path.dirname(__file__), 'standards_data.json')
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading standards: {e}")
        return []
