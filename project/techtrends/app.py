import sqlite3

import logging
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash, Response
from werkzeug.exceptions import abort

#Counter to track number of database connections
logging.basicConfig(level=logging.DEBUG, \
                    format=f'%(asctime)s %(levelname)s %(name)s %(message)s',\
                    datefmt='%Y-%m-%d,%H:%M:%S')

connection_count = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Function to get a post's title by ID
def get_post_title(post_id):
    connection = get_db_connection()
    title = connection.execute('SELECT title FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    title = title[0]
    connection.close()
    return title


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'


# Define the main route of the web application
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    global connection_count
    connection_count += 1
    post = get_post(post_id)
    if post is None:
      app.logger.info('Non-existing article accessed')
      return render_template('404.html'), 404
    else:
      app.logger.info('Article "' + get_post_title(post_id) + '" retrieved')
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('"About Us" page retrieved')
    return render_template('about.html')

# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            app.logger.info('New article "' + title + '" created')
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')

# Route for health check endpoint
@app.route('/healthz')
def healthz():
    return jsonify({'result':'OK - healthy'})

# Route for metrics endpoint
@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    post_count = connection.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
    response = app.response_class(
        response=json.dumps({"db_connection_count": connection_count, "post_count": post_count}),
        status=200,
        mimetype='application/json'
    )
    return response

# start the application on port 3111
if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111')
