import sqlite3

try:
    c = sqlite3.connect('app.db')
    c.execute("ALTER TABLE products ADD COLUMN category VARCHAR(50) DEFAULT 'Uncategorized'")
    c.commit()
    print("Added category column to products")
except Exception as e:
    print("Column already exists or error", e)

try:
    from app import app, db
    with app.app_context():
        db.create_all()
        print("Created new tables (like reviews)")
except Exception as e:
    print("Error creating tables", e)
