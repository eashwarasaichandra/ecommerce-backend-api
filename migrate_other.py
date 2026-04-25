import sqlite3

c = sqlite3.connect('app.db')
c.execute("UPDATE products SET category = 'Other' WHERE category = 'Uncategorized' OR category IS NULL OR category = ''")
c.commit()
print("Migrated Uncategorized to Other in DB")
