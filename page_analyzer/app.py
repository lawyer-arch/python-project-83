import requests
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
from urllib.parse import urlparse
import validators
from datetime import datetime
from bs4 import BeautifulSoup

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
            existing = cur.fetchone()
            if existing:
                return existing[0]

            cur.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
                (normalized_url, datetime.now())
            )
            new_id = cur.fetchone()[0]
    conn.close()
    return new_id 


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url_input = request.form.get('url')
        try:
            url_id = add_url(url_input)
            if url_id:
                flash('Страница успешно проверена', 'success')
                return redirect(url_for('show_url', id=url_id))
            else:
                flash('Страница уже существует', 'warning')
        except ValueError as e:
            flash(str(e), 'danger')
        return redirect(url_for('index'))

    return render_template('index.html')


@app.route('/urls')
def urls():
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT 
                    urls.id,
                    urls.name,
                    urls.created_at,
                    MAX(url_checks.created_at) AS last_check_date,
                    MAX(url_checks.status_code) AS last_status_code
                FROM urls
                LEFT JOIN url_checks ON urls.id = url_checks.url_id
                GROUP BY urls.id
                ORDER BY urls.id DESC
            ''')
            urls_list = cur.fetchall()
    return render_template('urls.html', urls=urls_list)


@app.route('/urls/<int:id>')
def show_url(id):
    conn = get_connection()
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute('SELECT * FROM urls WHERE id = %s', (id,))
            url = cur.fetchone()
            if not url:
                flash('Страница не найдена', 'danger')
                return redirect(url_for('urls'))

            cur.execute('''
                SELECT id, status_code, h1, title, description, created_at
                FROM url_checks
                WHERE url_id = %s
                ORDER BY id DESC
            ''', (id,))
            checks = cur.fetchall()

    return render_template('url.html', url=url, checks=checks)


@app.route('/urls/<int:id>/checks', methods=['POST'])
def check_url(id):
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM urls WHERE id = %s", (id,))
                url_data = cur.fetchone()
                if not url_data:
                    flash('URL не найден', 'danger')
                    return redirect(url_for('urls'))

                url = url_data[0]
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    
                  
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                 
                    h1 = soup.find('h1')
                    title = soup.find('title')
                    description = soup.find('meta', attrs={'name': 'description'})
                    
                    h1_text = h1.text.strip() if h1 else None
                    title_text = title.text.strip() if title else None
                    description_text = description['content'].strip() if description else None
                    
                    cur.execute(
                        '''INSERT INTO url_checks (url_id, status_code, h1, title, description, created_at)
                           VALUES (%s, %s, %s, %s, %s, %s)''',
                        (id, response.status_code, h1_text, title_text, description_text, datetime.now())
                    )
                    flash('Проверка успешно проверена', 'success')

                except requests.exceptions.HTTPError as e:
                    if 500 <= response.status_code < 600:
                        flash('Произошла ошибка при проверке', 'danger')
                    else:
                        raise
                except requests.RequestException:
                    flash('Произошла ошибка при проверке', 'danger')
    except Exception as e:
        flash('Произошла ошибка при проверке', 'danger')

    return redirect(url_for('show_url', id=id))
