from flask import Flask, render_template, request, redirect, send_from_directory
import sqlite3
from PIL import Image
import numpy as np
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_dominant_color(image_path):
    img = Image.open(image_path)
    img = img.resize((100, 100))
    data = np.array(img)
    data = data.reshape((-1, 3))
    avg_color = data.mean(axis=0)
    return f"({int(avg_color[0])}, {int(avg_color[1])}, {int(avg_color[2])})"

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


@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM customers')
    customers = c.fetchall()
    conn.close()
    return render_template('index.html', customers=customers)

@app.route('/add', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        name = request.form['name']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('INSERT INTO customers (name) VALUES (?)', (name,))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('add_customer.html')

@app.route('/customer/<int:customer_id>')
def customer_detail(customer_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('SELECT * FROM customers WHERE id=?', (customer_id,))
    customer = c.fetchone()

    c.execute('SELECT * FROM records WHERE customer_id=? ORDER BY id DESC', (customer_id,))
    records = c.fetchall()

    conn.close()
    return render_template('customer.html', customer=customer, records=records)

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

@app.route('/delete_record/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('SELECT customer_id FROM records WHERE id=?', (record_id,))
    record = c.fetchone()

    if record:
        customer_id = record[0]
        c.execute('DELETE FROM records WHERE id=?', (record_id,))
        conn.commit()
        conn.close()
        return redirect(f'/customer/{customer_id}')

    conn.close()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)