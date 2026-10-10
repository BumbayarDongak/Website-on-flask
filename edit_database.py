import sqlite3
from werkzeug.security import generate_password_hash

connection = sqlite3.connect("SQLite.db", check_same_thread=False)
cursor = connection.cursor()

# password='1qazxcvb'
#cursor.execute('SELECT user SET email = "test@gmail.com" WHERE id = 1')
# cursor.execute('SELECT * FROM like')
# print(cursor.fetchall())
# cursor.execute('SELECT * FROM user WHERE id=?', (password,))
# result = cursor.fetchone()
# print(cursor.fetchall())
cursor.execute("SELECT * from user WHERE username = '123'")
result = cursor.fetchone()
print(result)

connection.commit()
connection.close()