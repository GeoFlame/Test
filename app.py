# Flask imports
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
from datetime import datetime
from flask_mail import Mail, Message
import os
import random
from werkzeug.utils import secure_filename
import sqlite3
import bcrypt

#from openai import OpenAI
#client = OpenAI()

#response = client.moderations.create(input="fuck you")

#output = response.results[0]
#print(output)

# Flask app setup
app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'forum.db'
app.config['UPLOAD_FOLDER'] = 'C:/Users/049081/OneDrive - Ambrose Treacy College/GeoFlameUSB/FilesLOL!!!/My Website/Website/static/'

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465  # Use port 465 for SSL or 587 for TLS
app.config['MAIL_USE_SSL'] = True  # Enable SSL
app.config['MAIL_USE_TLS'] = False  # Disable TLS
app.config['MAIL_USERNAME'] = 'geoflame00@gmail.com'  # Your email username
app.config['MAIL_PASSWORD'] = 'tobodude66'  # Your email password

# Initialize Mail
mail = Mail(app)

# Function to create database connection
def create_connection():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    return conn, c

# Function to create database tables
def create_tables():
    conn, c = create_connection()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                about_me TEXT DEFAULT '',
                is_admin INTEGER DEFAULT 0,
                banned INTEGER DEFAULT 0,
                profile_picture TEXT DEFAULT 'Guest.jpg',
                email TEXT NOT NULL,
                coins INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                username TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username))''')
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username))''')
    c.execute('''CREATE TABLE IF NOT EXISTS follows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    follower_id INTEGER NOT NULL,
                    followed_id INTEGER NOT NULL,
                    FOREIGN KEY (follower_id) REFERENCES users(id),
                    FOREIGN KEY (followed_id) REFERENCES users(id)
                )''')
    conn.commit()
    conn.close()

create_tables()

# Function to generate and send the verification code
def verif(email):
    # Generate 6-digit code
    code = str(random.randint(100000, 999999))

    # Store the code temporarily, for example, in session
    session['verif'] = code

    # Send email
    msg = Message('Verification Code', sender='geoflame00@gmail.com', recipients=[email])
    msg.body = f'Your verification code is: {code}'
    mail.send(msg)

# Function to check if a user is an admin
def is_admin(username):
    conn, c = create_connection()
    c.execute("SELECT is_admin FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user and user[0] == 1

def get_sparks(username):
    conn, c = create_connection()
    c.execute("SELECT coins FROM users WHERE username=?", (username,))
    balance = c.fetchone()
    conn.close()
    return str(balance[0])

# Function to set user's balance
def set_sparks(username, sparks):
    conn, c = create_connection()

    # Update the user's balance
    c.execute("UPDATE users SET coins = ? WHERE username = ?", (sparks, username))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

# Home page route
@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn, c = create_connection()
    c.execute("SELECT * FROM posts")
    posts = c.fetchall()
    conn.close()
    username = session.get('username')
    coins = get_sparks(username)

    return render_template('home.html', username=session['username'], posts=posts, coins=coins)

# Function to create notifications
def create_notification(message, username):
    conn, c = create_connection()
    c.execute("INSERT INTO notifications (message, username, created_at) VALUES (?, ?, ?)",
              (message, username, datetime.now()))
    conn.commit()
    conn.close()

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the user exists
        conn, c = create_connection()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user:
            # Check if the user is banned
            ban_status = user[5]  # Assuming the ban status is stored in the sixth column
            
            if ban_status == 1:  # If the user is banned
                return render_template('ban_page.html')  # Redirect to the ban page

            # Check if the password is correct
            if bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
                session['username'] = username
                return redirect(url_for('home'))
        
        return "Invalid username or password"
    
    return render_template('login.html')


# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

# Sign-up route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].lower()  # Convert username to lowercase
        email = request.form['email']  # Retrieve the value of the email field
        #verif(email)
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Check if the username is already taken
        conn, c = create_connection()
        c.execute("SELECT * FROM users WHERE LOWER(username)=?", (username,))
        existing_user = c.fetchone()
        conn.close()
        
        if existing_user:
            return "Username already exists. Please choose a different username."
        
        # Username is available, proceed with registration
        conn, c = create_connection()
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, hashed_password))
        conn.commit()
        conn.close()
        session['username'] = username
        return redirect(url_for('home'))
    
    return render_template('signup.html')


# Admin panel route
@app.route('/admin')
def admin_panel():
    username = session.get('username')
    if not username or not is_admin(username):
        return redirect(url_for('home'))  # Redirect to login if not logged in or not an admin
    conn, c = create_connection()
    c.execute("SELECT username FROM users")
    users = c.fetchall()
    conn.close()
    return render_template('admin_panel.html', users=users)

# Route to delete a post
@app.route('/delete_post', methods=['POST'])
def delete_post():
    post_id = request.form['post_id']
    conn, c = create_connection()
    c.execute("DELETE FROM posts WHERE id=?", (post_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

# Route to delete a user
@app.route('/delete_user', methods=['POST'])
def delete_user():
    username = request.form['username']
    conn, c = create_connection()
    c.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

# Route to ban a user
@app.route('/ban_user', methods=['POST'])
def ban_user():
    if request.method == 'POST':
        if not is_admin(session.get('username')):
            return "Unauthorized", 401  # Return unauthorized status if the requester is not an admin
        
        # Get the username of the user to ban from the request data
        username_to_ban = request.form['username']
        
        # Update the database record to set the 'banned' field to 1 for the selected user
        conn, c = create_connection()
        c.execute("UPDATE users SET banned = 1 WHERE username = ?", (username_to_ban,))
        conn.commit()
        conn.close()
        
        return "User banned successfully"
    else:
        return "Method Not Allowed", 405  # Return method not allowed status if the request method is not POST

# Route to unban a user
@app.route('/unban_user', methods=['POST'])
def unban_user():
    if request.method == 'POST':
        if not is_admin(session.get('username')):
            return "Unauthorized", 401  # Return unauthorized status if the requester is not an admin
        
        # Get the username of the user to ban from the request data
        username_to_ban = request.form['username']
        
        # Update the database record to set the 'banned' field to 1 for the selected user
        conn, c = create_connection()
        c.execute("UPDATE users SET banned = 0 WHERE username = ?", (username_to_ban,))
        conn.commit()
        conn.close()
        
        return "User unbanned successfully"
    else:
        return "Method Not Allowed", 405  # Return method not allowed status if the request method is not POST

# Route to post a message
@app.route('/post_message', methods=['POST'])
def post_message():
    if request.method == 'POST':
        username = session.get('username')
        if not username:
            return redirect(url_for('login'))  # Redirect to login if not logged in
        
        content = request.form['content']  # Assuming the content is submitted via a form field named 'content'
        
        # Here you can process the content, such as saving it to the database
        # Example:
        conn, c = create_connection()
        c.execute("INSERT INTO posts (username, content) VALUES (?, ?)", (username, content))
        conn.commit()
        
        # Get the usernames of followers
        c.execute("SELECT username FROM users WHERE id IN (SELECT follower_id FROM follows WHERE followed_id = (SELECT id FROM users WHERE username=?))", (username,))
        followers = c.fetchall()
        
        # Create notifications for each follower
        for follower in followers:
            follower_username = follower[0]
            message = "{} posted: ".format(username) + content
            create_notification(message, follower_username)
        
        conn.commit()
        conn.close()

        sparks = int(get_sparks(username))
        sparks += 1
        set_sparks(username, sparks)

        # After processing, you can redirect the user to a different page
        return redirect(url_for('home'))  # Redirect to the home page or any other appropriate page
    else:
        # If the request method is not POST, return a method not allowed error
        return "Method Not Allowed", 405

# Route to view a user's profile
@app.route('/user/<username>')
def profile(username):
    conn, c = create_connection()
    c.execute("SELECT * FROM users WHERE LOWER(username)=?", (username.lower(),))
    user = c.fetchone()
    if not user:
        return render_template('error.html', message='User not found')

    coins = get_sparks(session['username'])
    
    # Check if the current user is following the user being viewed
    is_following = False
    if 'username' in session:
        current_username = session['username']
        c.execute("SELECT id FROM users WHERE username=?", (current_username,))
        current_user_id = c.fetchone()[0]
        c.execute("SELECT id FROM users WHERE username=?", (username,))
        viewed_user_id = c.fetchone()[0]
        c.execute("SELECT * FROM follows WHERE follower_id=? AND followed_id=?", (current_user_id, viewed_user_id))
        if c.fetchone():
            is_following = True
    
    # Count the number of followers for the viewed user
    c.execute("SELECT COUNT(*) FROM follows WHERE followed_id=?", (user[0],))
    followers_count = c.fetchone()[0]

    c.execute("SELECT * FROM posts WHERE LOWER(username)=?", (username.lower(),))
    posts = c.fetchall()
    conn.close()

    return render_template('profile.html', user=user, posts=posts, is_following=is_following, followers_count=followers_count, coins=coins)




# Route to promote a user to admin
@app.route('/promote_admin', methods=['POST'])
def promote_admin():
    if request.method == 'POST':
        if not is_admin(session.get('username')):
            return "Unauthorized", 401  # Return unauthorized status if the requester is not an admin
        
        # Get the username of the user to promote from the request data
        username_to_promote = request.form['username']
        
        # Update the database record to set the 'is_admin' field to True for the selected user
        conn, c = create_connection()
        c.execute("UPDATE users SET is_admin = 1 WHERE username = ?", (username_to_promote,))
        conn.commit()
        conn.close()
        
        return "User promoted to admin successfully"
    else:
        return "Method Not Allowed", 405  # Return method not allowed status if the request method is not POST

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    conn, c = create_connection()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()

    if request.method == 'POST':
        about_me = request.form['about_me']
        conn, c = create_connection()
        c.execute("UPDATE users SET about_me=? WHERE username=?", (about_me, username))
        conn.commit()
        conn.close()
        return redirect(url_for('profile', username=username))

    return render_template('edit_profile.html', user=user)

@app.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    if 'profile_picture' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['profile_picture']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Update the database with the file path
    conn, c = create_connection()
    c.execute("UPDATE users SET profile_picture = ? WHERE username = ?", (filename, username))
    conn.commit()
    conn.close()
    
    return redirect(url_for('profile', username=username))

# Route to display notifications
@app.route('/notifications')
def notifications():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    conn, c = create_connection()
    c.execute("SELECT * FROM notifications WHERE username=? ORDER BY created_at DESC", (username,))
    notifications = c.fetchall()
    conn.close()
    
    return render_template('notifications.html', notifications=notifications)

# Route to follow a user
@app.route('/follow_user', methods=['POST'])
def follow_user():
    if request.method == 'POST':
        username_to_follow = request.form['username']
        conn, c = create_connection()
        # Get the IDs of the logged-in user and the user to follow
        c.execute("SELECT id FROM users WHERE username=?", (session.get('username'),))
        follower_id = c.fetchone()[0]
        c.execute("SELECT id FROM users WHERE username=?", (username_to_follow,))
        followed_id = c.fetchone()[0]
        # Check if the logged-in user is already following the user
        c.execute("SELECT * FROM follows WHERE follower_id=? AND followed_id=?", (follower_id, followed_id))
        if c.fetchone():
            return "You are already following this user"
        else:
            c.execute("INSERT INTO follows (follower_id, followed_id) VALUES (?, ?)", (follower_id, followed_id))
            conn.commit()
            conn.close()
            return redirect(url_for('profile', username=username_to_follow))  # Redirect to the profile page
    else:
        return "Method Not Allowed", 405  # Return method not allowed status if the request method is not POST

# Route to unfollow a user
@app.route('/unfollow_user', methods=['POST'])
def unfollow_user():
    if request.method == 'POST':
        username_to_unfollow = request.form['username']
        conn, c = create_connection()
        # Get the IDs of the logged-in user and the user to unfollow
        c.execute("SELECT id FROM users WHERE username=?", (session.get('username'),))
        follower_id = c.fetchone()[0]
        c.execute("SELECT id FROM users WHERE username=?", (username_to_unfollow,))
        followed_id = c.fetchone()[0]
        # Check if the logged-in user is following the user
        c.execute("SELECT * FROM follows WHERE follower_id=? AND followed_id=?", (follower_id, followed_id))
        if not c.fetchone():
            return "You are not following this user"
        else:
            c.execute("DELETE FROM follows WHERE follower_id=? AND followed_id=?", (follower_id, followed_id))
            conn.commit()
            conn.close()
            return redirect(url_for('profile', username=username_to_unfollow))  # Redirect to the profile page
    else:
        return "Method Not Allowed", 405  # Return method not allowed status if the request method is not POST


if __name__ == '__main__':
    app.run(debug=True)
