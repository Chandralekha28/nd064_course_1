import sqlite3
import logging
import sys
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort


def check_db_connection(connection):
     try:
        connection.cursor()
        return True
     except Exception as exception:
        app.logger.error('db connection failed ', exception)
        return False

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    if check_db_connection:
        app.config['current_connections_counter'] +=1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

app.config['current_connections_counter'] = 0

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    app.config['current_connections_counter'] -=1
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.info('Article not found')
        return render_template('404.html'), 404
    else:
        app.logger.info(f'Article "{post["title"]}" retrieved!')
        return render_template('post.html', post=post)
      

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('About Us page retrieved')
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
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.config['current_connections_counter'] -=1
            app.logger.info(f' New Article with title: "{title}" created.')
            return redirect(url_for('index'))

    return render_template('create.html')

# Define the health check
@app.route('/healthz')
def status():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )

    return response

# Define the metrics endpoint
@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    posts = connection.execute('SELECT COUNT(*) FROM posts')

    response = app.response_class(
            response=json.dumps({"Current database connections":app.config['current_connections_counter'],"Total posts":posts}),
            status=200,
            mimetype='application/json'
    )
    connection.close()
    app.config['current_connections_counter'] -=1
    app.logger.info('Metrics request successful')
    return response


# start the application on port 3111
if __name__ == "__main__":

    stdout_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(
        format='%(levelname)s:%(name)s:%(asctime)s, %(message)s',
        level=logging.DEBUG,
        datefmt='%m-%d-%Y, %H:%M:%S',
        handlers= [stdout_handler]
    )

    app.run(host='0.0.0.0', port='3111')
