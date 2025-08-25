from flask import Flask, render_template, request, redirect, session, url_for, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import html

app = Flask(__name__, template_folder='templates')
app.secret_key = "azka_secret"

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="azkadb"
    )

# ==================== FORM LOGIN & REGISTER ====================
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        action = request.form["action"]
        username = html.escape(request.form["username"])
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if action == "login":
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user["password"], password):
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                flash("Login berhasil!", "success")
                return redirect(url_for("form_belanja"))
            else:
                flash("Login gagal. Username atau password salah.", "danger")

        elif action == "register":
            hashed_pw = generate_password_hash(password)
            try:
                cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pw))
                conn.commit()
                flash("Registrasi berhasil! Silakan login.", "success")
            except mysql.connector.errors.IntegrityError:
                flash("Username sudah digunakan!", "danger")

        cursor.close()
        conn.close()

    return render_template("auth.html")

# ==================== LOGOUT ====================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ==================== FORM BELANJA ====================
@app.route("/form", methods=["GET", "POST"])
def form_belanja():
    if "user_id" not in session:
        return redirect(url_for("home"))
    return render_template("index.html")

@app.route("/proses", methods=["POST"])
def proses():
    if "user_id" not in session:
        return redirect(url_for("home"))

    # Validasi dan Escape Input
    AzkaPelanggan = html.escape(request.form['AzkaPelanggan'])
    AzkaBarang = html.escape(request.form['AzkaBarang'])
    AzkaHarga = int(request.form['AzkaHarga'])
    AzkaJumlah = int(request.form['AzkaJumlah'])
    AzkaStatus = html.escape(request.form['AzkaStatus'])
    AzkaMetode = html.escape(request.form['AzkaMetode'])

    AzkaTotalBarang = AzkaHarga * AzkaJumlah
    AzkaDiskon = int(AzkaTotalBarang * 0.2) if AzkaStatus == "Gold" else int(AzkaTotalBarang * 0.1) if AzkaStatus == "Silver" else 0
    AzkaAdmin = 2500 if AzkaMetode == "Transfer" else 0
    AzkaTotalBelanja = AzkaTotalBarang - AzkaDiskon + AzkaAdmin
    AzkaVocher = "Anda Mendapatkan Vocher Bonus" if AzkaTotalBelanja > 500000 and AzkaStatus == "Gold" else ""

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transaksi (
            user_id, pelanggan, barang, harga, jumlah, status, metode,
            total_barang, diskon, admin, total_belanja, vocher
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        session["user_id"], AzkaPelanggan, AzkaBarang, AzkaHarga, AzkaJumlah, AzkaStatus,
        AzkaMetode, AzkaTotalBarang, AzkaDiskon, AzkaAdmin,
        AzkaTotalBelanja, AzkaVocher
    ))
    conn.commit()
    cursor.close()
    conn.close()

    return render_template("hasil.html",
                           AzkaPelanggan=AzkaPelanggan,
                           AzkaBarang=AzkaBarang,
                           AzkaJumlah=AzkaJumlah,
                           AzkaStatus=AzkaStatus,
                           AzkaMetode=AzkaMetode,
                           AzkaAdmin=AzkaAdmin,
                           AzkaHarga=AzkaHarga,
                           AzkaTotalBelanja=AzkaTotalBelanja,
                           AzkaTotalBarang=AzkaTotalBarang,
                           AzkaDiskon=AzkaDiskon,
                           AzkaVocher=AzkaVocher)

if __name__ == '__main__':
    app.run(debug=True)
