import sqlite3
c = sqlite3.connect('app.db')
c.execute("UPDATE products SET image_url='https://placehold.co/500x500/1e293b/10b981/png?text=Smart+Gimbal' WHERE id=6")
c.commit()
print("Updated successfully")
