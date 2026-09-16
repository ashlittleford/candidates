import json
import os


def load_standards_data():
    filepath = os.path.join(os.path.dirname(__file__), 'standards_data.json')
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading standards data: {e}")
        return []


def upsert_standards():
    """
    Insert or update every Standard row so it matches standards_data.json exactly.
    Must be called within an active app context.
    """
    from app import db
    from app.models import Standard

    data = load_standards_data()
    if not data:
        return

    existing = {std.id: std for std in Standard.query.all()}

    for item in data:
        std = existing.get(item['id'])
        if std is None:
            std = Standard(id=item['id'])
            db.session.add(std)

        std.attribute = item['attribute']
        std.beginning = "\n".join(item.get('beginning', []))
        std.developing = "\n".join(item.get('developing', []))
        std.established = "\n".join(item.get('established', []))
        std.lfd = "\n".join(item.get('lfd', []))

    db.session.commit()
