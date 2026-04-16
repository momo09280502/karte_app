from flask import Flask, render_template, request, redirect, send_from_directory
import sqlite3

app = Flask(__name__)

from PIL import Image
import numpy as np

def get_dominant_color(image_path):
    img = Image.open(image_path)
    img = img.resize((100, 100))  # 軽くする

    data = np.array(img)
    data = data.reshape((-1, 3))

    avg_color = data.mean(axis=0)
    return f"({int(avg_color[0])}, {int(avg_color[1])}, {int(avg_color[2])})"
    
import os

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            date TEXT,
            color TEXT,
            memo TEXT,
            image_path TEXT
        )
    ''')

    conn.commit()
    conn.close()

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM customers')
    customers = c.fetchall()
    conn.close()
    return render_template('index.html', customers=customers)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

@app.route('/add_record/<int:customer_id>', methods=['GET', 'POST'])
def add_record(customer_id):
    if request.method == 'POST':
        date = request.form['date']
        color = request.form['color']
        memo = request.form['memo']

        file = request.files.get('image')

        if file and file.filename != "":
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            dominant_color = get_dominant_color(filepath)
        else:
            dominant_color = "(0, 0, 0)"
            filepath = ""

        combined_color = f"{color} / {dominant_color}"

        # ←ここで初めてDB接続
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute(
            'INSERT INTO records (customer_id, date, color, memo, image_path) VALUES (?, ?, ?, ?, ?)',
            (customer_id, date, combined_color, memo, filepath)
        )

        conn.commit()
        conn.close()

        return redirect(f'/customer/{customer_id}')

    return render_template('add_record.html', customer_id=customer_id)

@app.route('/customer/<int:customer_id>')
def customer_detail(customer_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('SELECT * FROM customers WHERE id=?', (customer_id,))
    customer = c.fetchone()

    c.execute('SELECT * FROM records WHERE customer_id=?', (customer_id,))
    records = c.fetchall()

    conn.close()
    return render_template('customer.html', customer=customer, records=records)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)