import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse
import validators
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def add_url(url: str):
    if not validators.url(url) or len(url) > 255:
        raise ValueError("Невалидный URL")

    parsed = urlparse(url)
    normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
            if cur.fetchone():
                return False  # URL уже есть

            cur.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, %s)",
                (normalized_url, datetime.now())
            )
    conn.close()
    return True


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url_input = request.form.get('url')
        try:
            success = add_url(url_input)
            if success:
                flash('URL успешно добавлен', 'success')
            else:
                flash('Этот URL уже добавлен', 'warning')
        except ValueError as e:
            flash(str(e), 'danger')
        return redirect(url_for('index'))

    return render_template('index.html')


@app.route('/urls')
def urls():
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM urls ORDER BY created_at DESC")
            urls_list = cur.fetchall()
    return render_template('urls.html', urls=urls_list)


@app.route('/urls/<int:id>')
def url_detail(id):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (id,))
            url_data = cur.fetchone()
    if url_data is None:
        flash('URL не найден', 'danger')
        return redirect(url_for('urls'))
    return render_template('url.html', url=url_data)
