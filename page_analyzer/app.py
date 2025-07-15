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
                flash('URL успешно добавлен', 'success')
                return redirect(url_for('show_url', id=url_id))
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
            cur.execute('''
                SELECT 
                    urls.id,
                    urls.name,
                    urls.created_at,
                    MAX(url_checks.created_at) AS last_check_date
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
                flash('URL не найден', 'danger')
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
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            # Получаем URL по id
            cur.execute("SELECT name FROM urls WHERE id = %s", (id,))
            url_data = cur.fetchone()
            if not url_data:
                flash('URL не найден', 'danger')
                return redirect(url_for('urls'))

            url = url_data[0]
            try:
                response = requests.get(url)
                response.raise_for_status()  # проверяем статус

                # Для отладки — посмотреть первые 1000 символов ответа
                print(response.text[:1000])

                # Парсим HTML
                soup = BeautifulSoup(response.text, 'html.parser')

                h1 = soup.h1.string.strip() if soup.h1 and soup.h1.string else ''
                title = soup.title.string.strip() if soup.title and soup.title.string else ''

                description_tag = soup.find('meta', attrs={'name': 'description'})
                description = description_tag['content'].strip() if description_tag and 'content' in description_tag.attrs else ''

                # Вставляем данные проверки в базу
                cur.execute(
                    '''INSERT INTO url_checks (url_id, status_code, h1, title, description, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s)''',
                    (id, response.status_code, h1, title, description, datetime.now())
                )
                flash('Проверка успешно добавлена', 'success')

            except requests.RequestException:
                flash('Произошла ошибка при проверке URL', 'danger')

    return redirect(url_for('show_url', id=id))