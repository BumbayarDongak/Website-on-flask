import sqlite3

connection = sqlite3.connect('SQLite.db')
cursor = connection.cursor()
# cursor.execute('''CREATE TABLE like (id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER NOT NULL, user_id INTEGER NOT NULL);''')
# connection.commit()
cursor.execute('''CREATE TABLE comment (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, post_id INTEGER NOT NULL, user_id INTEGER NOT NULL);''')
connection.commit()
connection.close()