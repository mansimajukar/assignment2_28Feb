from flask import Flask, render_template, request, redirect, session
import sqlite3
import json

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("students.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            roll TEXT UNIQUE,
            total REAL,
            average REAL,
            grade TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS admin(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    c.execute("INSERT OR IGNORE INTO admin (username, password) VALUES (?, ?)",
              ("admin", "admin123"))

    conn.commit()
    conn.close()

init_db()

# ---------------- GRADE ----------------
def calculate_grade(avg):
    if avg >= 90:
        return "A"
    elif avg >= 75:
        return "B"
    elif avg >= 60:
        return "C"
    elif avg >= 50:
        return "D"
    else:
        return "F"

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("students.db")
        c = conn.cursor()
        c.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["admin"] = username
            return redirect("/dashboard")
        else:
            return "Invalid Credentials!"

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/")

    conn = sqlite3.connect("students.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM students")
    total = c.fetchone()[0]

    c.execute("SELECT average FROM students")
    averages = [row[0] for row in c.fetchall()]

    c.execute("SELECT total FROM students")
    totals = [row[0] for row in c.fetchall()]

    conn.close()

    avg = round(sum(averages)/len(averages), 2) if averages else 0
    highest = max(totals) if totals else 0
    lowest = min(totals) if totals else 0

    return render_template("dashboard.html",
                           total=total,
                           avg=avg,
                           highest=highest,
                           lowest=lowest)

# ---------------- ADD STUDENT ----------------
@app.route("/add", methods=["GET", "POST"])
def add_student():
    if "admin" not in session:
        return redirect("/")

    if request.method == "POST":
        name = request.form["name"]
        roll = request.form["roll"]
        marks = [float(request.form[f"mark{i}"]) for i in range(1, 6)]

        total = sum(marks)
        avg = total / 5
        grade = calculate_grade(avg)

        try:
            conn = sqlite3.connect("students.db")
            c = conn.cursor()
            c.execute("INSERT INTO students (name, roll, total, average, grade) VALUES (?, ?, ?, ?, ?)",
                      (name, roll, total, avg, grade))
            conn.commit()
            conn.close()
        except:
            return "Roll Number Already Exists!"

        return redirect("/view")

    return render_template("add_student.html")

# ---------------- VIEW ----------------
@app.route("/view")
def view_students():
    if "admin" not in session:
        return redirect("/")

    conn = sqlite3.connect("students.db")
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    students = c.fetchall()
    conn.close()

    return render_template("view_students.html", students=students)

# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete_student(id):
    conn = sqlite3.connect("students.db")
    c = conn.cursor()
    c.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/view")

# ---------------- GRAPH ----------------
@app.route("/stats")
def stats():
    if "admin" not in session:
        return redirect("/")

    conn = sqlite3.connect("students.db")
    c = conn.cursor()
    c.execute("SELECT name, total FROM students")
    data = c.fetchall()
    conn.close()

    names = []
    totals = []

    for row in data:
        names.append(row[0])
        totals.append(row[1])

    # Convert to JSON safely
    names_json = json.dumps(names)
    totals_json = json.dumps(totals)

    return render_template("stats.html",
                           names=names_json,
                           totals=totals_json)

if __name__ == "__main__":
    app.run(debug=True)