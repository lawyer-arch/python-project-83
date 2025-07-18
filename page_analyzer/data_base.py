import os
from datetime import datetime
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from page_analyzer.url_validator import is_valid_url, normalize_url

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def add_url(url: str) -> tuple[int, bool]:
    if len(url) > 255 or not is_valid_url(url):
        raise ValueError("Произошла ошибка при проверке")

    normalized_url = normalize_url(url)
    
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM urls WHERE name = %s", 
                        (normalized_url,))
            existing = cur.fetchone()
            if existing:
                return existing[0], False

            cur.execute(
                '''INSERT INTO urls (name, created_at) 
                   VALUES (%s, %s) RETURNING id''',
                   (normalized_url, datetime.now())
            )
            new_id = cur.fetchone()[0]
    conn.close()
    return new_id, True


def get_all_urls():
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
            return cur.fetchall()


def get_url_with_checks(id: int):
    conn = get_connection()
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute('SELECT * FROM urls WHERE id = %s', (id,))
            url = cur.fetchone()
            if not url:
                return None, []

            cur.execute('''
                SELECT id, status_code, h1, title, description, created_at
                FROM url_checks
                WHERE url_id = %s
                ORDER BY id DESC
            ''', (id,))
            checks = cur.fetchall()
    return url, checks


def insert_check_result(id, status_code, h1, title, description):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO url_checks (
                    url_id, status_code, h1, title, description, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ''',
                (id, status_code, h1, title, description, datetime.now())
            )