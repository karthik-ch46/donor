from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "blood_donor_project_secret_key"

DATABASE = "database.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

def init_db():
    conn = get_db()

    # Users who login with mobile number
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mobile TEXT UNIQUE NOT NULL
        )
    """)

    # User profile
    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            mobile TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES app_users(id)
        )
    """)

    # Blood donors
    conn.execute("""
        CREATE TABLE IF NOT EXISTS blood_donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            mobile TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            pincode TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            available TEXT DEFAULT 'Yes',
            FOREIGN KEY (user_id) REFERENCES app_users(id)
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# PAGE ACCESS CONTROL
# =========================================================

def login_required():
    return "user_id" in session


def profile_required():
    if "user_id" not in session:
        return False

    conn = get_db()

    profile = conn.execute(
        "SELECT * FROM profiles WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return profile is not None


def donor_required():
    if "user_id" not in session:
        return False

    conn = get_db()

    donor = conn.execute(
        "SELECT * FROM blood_donors WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return donor is not None


# =========================================================
# LANDING PAGE
# =========================================================

@app.route("/")
def index():
    return render_template("index.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    # Already logged in
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":

        mobile = request.form.get("mobile", "").strip()

        if not mobile:
            return render_template(
                "login.html",
                error="Please enter your mobile number."
            )

        if not mobile.isdigit():
            return render_template(
                "login.html",
                error="Mobile number must contain only numbers."
            )

        if len(mobile) != 10:
            return render_template(
                "login.html",
                error="Please enter a valid 10-digit mobile number."
            )

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM app_users WHERE mobile = ?",
            (mobile,)
        ).fetchone()

        if user is None:

            cursor = conn.execute(
                "INSERT INTO app_users (mobile) VALUES (?)",
                (mobile,)
            )

            user_id = cursor.lastrowid
            conn.commit()

        else:
            user_id = user["id"]

        conn.close()

        session["user_id"] = user_id
        session["mobile"] = mobile

        # Login successful → Dashboard
        return redirect(url_for("home"))

    return render_template("login.html")


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()

    existing_profile = conn.execute(
        "SELECT * FROM profiles WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        age = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        mobile = request.form.get("mobile", "").strip()

        if not name or not age or not gender or not mobile:

            conn.close()

            return render_template(
                "profile.html",
                error="Please fill all the fields.",
                profile=existing_profile
            )

        try:
            age_value = int(age)

        except ValueError:

            conn.close()

            return render_template(
                "profile.html",
                error="Age must be a number.",
                profile=existing_profile
            )

        if age_value < 18 or age_value > 100:

            conn.close()

            return render_template(
                "profile.html",
                error="Please enter a valid age between 18 and 100.",
                profile=existing_profile
            )

        if not mobile.isdigit() or len(mobile) != 10:

            conn.close()

            return render_template(
                "profile.html",
                error="Please enter a valid 10-digit mobile number.",
                profile=existing_profile
            )

        if existing_profile:

            conn.execute("""
                UPDATE profiles
                SET name = ?, age = ?, gender = ?, mobile = ?
                WHERE user_id = ?
            """, (
                name,
                age_value,
                gender,
                mobile,
                session["user_id"]
            ))

        else:

            conn.execute("""
                INSERT INTO profiles
                (user_id, name, age, gender, mobile)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session["user_id"],
                name,
                age_value,
                gender,
                mobile
            ))

        conn.commit()
        conn.close()

        session["profile_completed"] = True

        return redirect(url_for("register"))

    conn.close()

    return render_template(
        "profile.html",
        profile=existing_profile
    )


# =========================================================
# DONOR REGISTRATION
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if not login_required():
        return redirect(url_for("login"))

    if not profile_required():
        return redirect(url_for("profile"))

    conn = get_db()

    existing_donor = conn.execute(
        "SELECT * FROM blood_donors WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()

    profile = conn.execute(
        "SELECT * FROM profiles WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        age = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        mobile = request.form.get("mobile", "").strip()
        blood_group = request.form.get("blood_group", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        pincode = request.form.get("pincode", "").strip()

        latitude = request.form.get("latitude", "").strip()
        longitude = request.form.get("longitude", "").strip()

        if not all([
            name,
            age,
            gender,
            mobile,
            blood_group,
            address,
            city,
            pincode
        ]):

            conn.close()

            return render_template(
                "register.html",
                error="Please fill all required fields.",
                profile=profile,
                donor=existing_donor
            )

        try:
            age_value = int(age)

        except ValueError:

            conn.close()

            return render_template(
                "register.html",
                error="Age must be a number.",
                profile=profile,
                donor=existing_donor
            )

        if not mobile.isdigit() or len(mobile) != 10:

            conn.close()

            return render_template(
                "register.html",
                error="Please enter a valid 10-digit mobile number.",
                profile=profile,
                donor=existing_donor
            )

        # Convert location values
        lat_value = None
        lon_value = None

        try:

            if latitude:
                lat_value = float(latitude)

            if longitude:
                lon_value = float(longitude)

        except ValueError:

            lat_value = None
            lon_value = None

        if existing_donor:

            conn.execute("""
                UPDATE blood_donors
                SET name = ?,
                    age = ?,
                    gender = ?,
                    mobile = ?,
                    blood_group = ?,
                    address = ?,
                    city = ?,
                    pincode = ?,
                    latitude = ?,
                    longitude = ?
                WHERE user_id = ?
            """, (
                name,
                age_value,
                gender,
                mobile,
                blood_group,
                address,
                city,
                pincode,
                lat_value,
                lon_value,
                session["user_id"]
            ))

        else:

            conn.execute("""
                INSERT INTO blood_donors
                (
                    user_id,
                    name,
                    age,
                    gender,
                    mobile,
                    blood_group,
                    address,
                    city,
                    pincode,
                    latitude,
                    longitude,
                    available
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Yes')
            """, (
                session["user_id"],
                name,
                age_value,
                gender,
                mobile,
                blood_group,
                address,
                city,
                pincode,
                lat_value,
                lon_value
            ))

        conn.commit()
        conn.close()

        session["donor_completed"] = True

        return redirect(url_for("search"))

    conn.close()

    # Pre-fill donor form using profile information
    if existing_donor:
        donor_data = existing_donor
    else:
        donor_data = profile

    return render_template(
        "register.html",
        profile=profile,
        donor=donor_data
    )


# =========================================================
# SEARCH BLOOD GROUP
# =========================================================

@app.route("/search", methods=["GET", "POST"])
def search():

    if not login_required():
        return redirect(url_for("login"))

    if not profile_required():
        return redirect(url_for("profile"))

    if not donor_required():
        return redirect(url_for("register"))

    if request.method == "POST":

        blood_group = request.form.get(
            "blood_group",
            ""
        ).strip()

        if not blood_group:

            return render_template(
                "search.html",
                error="Please select a blood group."
            )

        session["required_blood_group"] = blood_group

        return redirect(url_for("matching"))

    return render_template("search.html")


# =========================================================
# AI MATCHING
# =========================================================

@app.route("/matching")
def matching():

    if not login_required():
        return redirect(url_for("login"))

    if not profile_required():
        return redirect(url_for("profile"))

    if not donor_required():
        return redirect(url_for("register"))

    blood_group = session.get("required_blood_group")

    if not blood_group:
        return redirect(url_for("search"))

    conn = get_db()

    donors = conn.execute("""
        SELECT *
        FROM blood_donors
        WHERE blood_group = ?
        AND available = 'Yes'
        ORDER BY city ASC, name ASC
    """, (blood_group,)).fetchall()

    conn.close()

    return render_template(
        "matching.html",
        donors=donors,
        blood_group=blood_group
    )


# =========================================================
# ALL AVAILABLE DONORS
# =========================================================

@app.route("/donors")
def donors():

    if not login_required():
        return redirect(url_for("login"))

    if not profile_required():
        return redirect(url_for("profile"))

    if not donor_required():
        return redirect(url_for("register"))

    conn = get_db()

    all_donors = conn.execute("""
        SELECT *
        FROM blood_donors
        WHERE available = 'Yes'
        ORDER BY name ASC
    """).fetchall()

    conn.close()

    return render_template(
        "donors.html",
        donors=all_donors
    )


# =========================================================
# HOME DASHBOARD
# =========================================================

@app.route("/home")
def home():

    # User must be logged in
    if not login_required():
        return redirect(url_for("login"))

    # Directly show dashboard
    return render_template("home.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    # After logout → Landing Page
    return redirect(url_for("index"))


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )