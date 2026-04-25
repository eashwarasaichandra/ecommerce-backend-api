import sqlite3
c = sqlite3.connect('app.db')
try:
    c.execute("ALTER TABLE orders ADD COLUMN payment_status VARCHAR(50) DEFAULT 'processing'")
    c.commit()
    print("Altered orders table")
except Exception as e:
    print("Already exists or error", e)
