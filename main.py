from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

login_manager = LoginManager(app)
login_manager.login_view = 'login'

connection = sqlite3.connect("SQLite.db", check_same_thread=False)
cursor = connection.cursor()


class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    user = cursor.execute('SELECT * FROM user where id=?', (user_id,)).fetchone()
    if user is not None:
        return User(user[0], user[1], user[2])
    return None


def close_db(connection=None):
    if connection is not None:
        connection.close()


@app.teardown_appcontext
def close_connection(exception):
    close_db()


@app.route('/post/<post_id>')
def post(post_id):
    cursor.execute("SELECT * FROM post WHERE id = ?", (post_id,))
    posts = cursor.fetchone()
    cursor.execute("SELECT * FROM comment WHERE post_id = ?", (post_id,))
    comments = cursor.fetchall()
    cursor.execute("SELECT * FROM user WHERE id=?", (post_id,))
    user = cursor.fetchone()
    post_dict = {"post_id": posts[0], "title": posts[1], "content": posts[2]}
    return render_template("post.html", post=post_dict, comments=comments, user=user)


@app.route('/')
def index():
    cursor.execute('''
    SELECT 
        post.id,
        post.title, 
        post.content,
        post.author_id,
        user.username,
        COUNT(like.id) AS likes
    FROM 
        post
    JOIN 
        user ON post.author_id = user.id
    LEFT JOIN
        like ON like.post_id = post.id
    GROUP BY
        post.id, post.title, post.content, post.author_id, user.username
    ''')
    result = cursor.fetchall()
    posts = []
    for post in reversed(result):
        posts.append({'id': post[0], 'title': post[1], 'content': post[2], 'author_id': post[3], 'username': post[4],
                      'likes': post[5]})
        if current_user.is_authenticated:
            cursor.execute('SELECT post_id FROM like WHERE user_id=?', (current_user.id,))
            likes_result = cursor.fetchall()
            liked_posts = []
            for likes in likes_result:
                liked_posts.append(likes[0])
            posts[-1]['liked_posts'] = liked_posts
    context = {'posts': posts}
    # print(result)
    # user_id = posts[3]
    # cursor.execute("SELECT * FROM user WHERE id=?", (user_id,))
    # user=cursor.fetchone()
    return render_template('index.html', **context)


@app.route('/add/', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        cursor.execute("INSERT INTO post (title, content, author_id) VALUES (?, ?, ?)",
                       (title, content, current_user.id))
        connection.commit()
        return redirect(url_for('index'))
    return render_template('add_post.html')


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        try:
            cursor.execute(
                "INSERT INTO user (username, password_hash, email) VALUES (?, ?, ?)",
                (username, generate_password_hash(password, method="pbkdf2:sha256"), email if email else None))
            connection.commit()
            print('Login succesfully')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            return render_template('register.html', message='Login failed. Username already exists')
    return render_template('register.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        user = cursor.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
        if user and User(user[0], user[1], user[2]).check_password(password):
            login_user(User(user[0], user[1], user[2]))
            return redirect(url_for('index'))
        else:
            return render_template('login.html', message='Login failed. Invalid username or password')
    return render_template('login.html')


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete(post_id):
    post = cursor.execute("SELECT * FROM post WHERE id = ?", (post_id,)).fetchone()
    if post and post[3] == current_user.id:
        cursor.execute("DELETE FROM post WHERE id = ?", (post_id,)).fetchone()
        connection.commit()
        return redirect(url_for('index'))
    else:
        return render_template('index')


# @app.route('/like/', methods=['POST'])
# @login_required
# def like(post_id):
#     user_id=cursor.execute("SELECT * FROM user WHERE id = ?", (post_id,)).fetchone()[0]
#     if user_id==current_user.id:
#         cursor.execute("DELETE FROM like WHERE id = ?", (post_id,)).fetchone()
#         connection.commit()
#     else:
#         cursor.execute('INSERT INTO like (id, user_id, post_id) VALUES (?, ?, ?)', (id, post_id, user_id))
#         connection.commit()

def user_is_liking(user_id, post_id):
    like = cursor.execute("SELECT * FROM like WHERE user_id = ? AND post_id=?", (user_id, post_id,)).fetchone()
    return bool(like)


@app.route('/like/<int:post_id>')
@login_required
def like(post_id):
    post = cursor.execute("SELECT * FROM post WHERE id = ?", (post_id,)).fetchone()
    if post:
        if user_is_liking(current_user.id, post_id):
            cursor.execute('DELETE from like where user_id=? AND post_id=?', (current_user.id, post_id))
            connection.commit()
            print('you unliked')
        else:
            cursor.execute('INSERT INTO like (user_id, post_id) VALUES (?, ?)', (current_user.id, post_id))
            connection.commit()
            print('you liked')
        return redirect(url_for('index'))
    return 'not found', 404


@app.route('/edit/', methods=['GET', 'POST'])
@login_required
def edit():
    post_id = request.args.get('post_id')
    if not post_id:
        return "Post ID is required", 400

    post = cursor.execute("SELECT * FROM post WHERE id = ?", (post_id,)).fetchone()

    if not post:
        return 'Post not found', 404

    if post[3] == current_user.id:
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            cursor.execute('UPDATE post SET title = ?, content = ? WHERE id = ?',
                           (title, content, post_id))
            connection.commit()
            return redirect(url_for('index'))
    post_dict = {"id": post[0], "title": post[1], "content": post[2]}
    return render_template('edit_post.html', post=post_dict)


@app.route('/comment/<int:post_id>', methods=['GET', 'POST'])
@login_required
def add_comment(post_id):
    text = request.form['text']

    cursor.execute("INSERT INTO comment (text, post_id, user_id) values (?, ?, ?)", (text, post_id, current_user.id))
    connection.commit()
    return redirect(url_for('post', post_id=post_id))


if __name__ == '__main__':
    app.run()
