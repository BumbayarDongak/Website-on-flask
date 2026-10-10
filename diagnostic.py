import sqlite3

conn = sqlite3.connect('templates/SQLite.db')
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(user)")
columns = cursor.fetchall()

print("Columns in 'user' table:")
for col in columns:
    print(f"  {col[1]}: nullable={'NO' if col[3]==0 else 'YES'}, type={col[2]}")

cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='user'")
indexes = cursor.fetchall()
print("\nIndexes:")
for idx in indexes:
    print(f"  {idx}")

conn.close()