import sqlite3

c = sqlite3.connect('app.db')
c.execute("UPDATE products SET category = 'Office' WHERE id IN (3, 5)")
c.execute("UPDATE products SET category = 'Gaming' WHERE id IN (4, 7)")
c.execute("UPDATE products SET category = 'Electronics' WHERE id IN (1, 2, 6)")
c.commit()
print("Updated categories in database")
