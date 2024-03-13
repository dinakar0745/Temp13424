from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configurations
mysql_config = {
    'host': 'localhost',
    'user': 'dp',
    'password': 'Welcome987*',
    'database': 'issue_tracker_db'
}

# Connect to MySQL database
conn = mysql.connector.connect(**mysql_config)
cursor = conn.cursor()

# Email configurations
email_config = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'smtp_username': '2210030004@klh.edu.in',
    'smtp_password': 'msrh wjur lvaf gwio'
}

# Function to send email
def send_email(sender_email, recipient_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
    server.starttls()
    server.login(email_config['smtp_username'], email_config['smtp_password'])
    server.sendmail(sender_email, recipient_email, msg.as_string())
    server.quit()
    
# Database table structure for issues
# Assume we have a table named 'issues' with columns: id, title, description, status, assigned_user
# You should adjust this according to your actual database structure
def create_issues_table():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(50),
            assigned_user VARCHAR(50)
        )
    """)
    conn.commit()

# Function to fetch all issues from the database
def get_all_issues():
    cursor.execute("SELECT * FROM issues")
    issues = cursor.fetchall()
    return issues

# Create issues table if not exists
create_issues_table()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Query database to check user credentials
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and user[2] == password:
            # Successful login, store username in session
            session['username'] = username
            return redirect(url_for('dashboard'))  # Redirect to dashboard or any other page after login
        else:
            # Invalid credentials, reload login page with error message
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if 'username' in session:
        issues = get_all_issues()
        return render_template("dashboard.html", issues=issues)
    else:
        return redirect(url_for('login'))

@app.route("/create_issue", methods=["GET", "POST"])
def create_issue():
    if 'username' in session:
        if request.method == "POST":
            title = request.form.get("title")
            description = request.form.get("description")
            status = request.form.get("status")
            assigned_user = request.form.get("assigned_user")

            # Insert issue into the database
            cursor.execute("INSERT INTO issues (title, description, status, assigned_user) VALUES (%s, %s, %s, %s)", (title, description, status, assigned_user))
            conn.commit()

            # Fetch email of the assigned user
            cursor.execute("SELECT email FROM users WHERE username = %s", (assigned_user,))
            assigned_user_email = cursor.fetchone()[0]

            sender_email = email_config['smtp_username']  # Using the configured sender email
            send_email(sender_email, assigned_user_email, "New Issue Created", f"A new issue has been created.\nTitle: {title}\nDescription: {description}")

            return redirect(url_for('dashboard'))  # Redirect to the dashboard after creating the issue

        else:
            cursor.execute("SELECT username FROM users")
            users = [user[0] for user in cursor.fetchall()]  # Extract usernames from fetchall result
            return render_template("create_issue.html", users=users)

    else:
        return redirect(url_for('login'))

        

@app.route("/issue_details/<int:issue_id>")
def issue_details(issue_id):
    if 'username' in session:
        cursor.execute("SELECT * FROM issues WHERE id = %s", (issue_id,))
        issue = cursor.fetchone()
        
        if issue:
            return render_template("issue_details.html", issue=issue)
        else:
            return "Issue not found."
    else:
        return redirect(url_for('login'))

def update_issue_status(issue_id, new_status):
    conn = mysql.connector.connect(**mysql_config)  # Connect to MySQL using the configuration
    cursor = conn.cursor()
    cursor.execute("UPDATE issues SET status = %s WHERE id = %s", (new_status, issue_id))
    conn.commit()
    conn.close()

@app.route("/update_status/<int:issue_id>", methods=["POST"])
def update_status(issue_id):
    if 'username' in session:
        if request.method == "POST":
            new_status = request.form.get("status")
            update_issue_status(issue_id, new_status)
            return redirect(url_for('issue_details', issue_id=issue_id))
        else:
            return "Method Not Allowed", 405
    else:
        return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
