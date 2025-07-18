import requests
from flask import Blueprint, flash, redirect, render_template, request, url_for
from page_analyzer.parser import parse_html
from page_analyzer.data_base import (
    add_url,
    get_all_urls,
    get_connection,
    get_url_with_checks,
    insert_check_result,
)


routes = Blueprint('routes', __name__)


@routes.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url_input = request.form.get('url')
        try:
            url_id, is_new = add_url(url_input)
            if is_new:
                flash('Страница успешно добавлена', 'success')
            else:
                flash('Страница уже существует', 'warning')
            return redirect(url_for('routes.show_url', id=url_id))
        except ValueError:
            flash("Некорректный URL", 'danger')
        except Exception:
            flash("Произошла ошибка при проверке", 'danger')
        return redirect(url_for('routes.index'))
    return render_template('index.html')


@routes.route('/urls')
def urls():
    urls_list = get_all_urls()
    return render_template('urls.html', urls=urls_list)


@routes.route('/urls/<int:id>')
def show_url(id):
    url, checks = get_url_with_checks(id)
    if not url:
        flash('Страница не найдена', 'danger')
        return redirect(url_for('routes.urls'))
    return render_template('url.html', url=url, checks=checks)


@routes.route('/urls/<int:id>/checks', methods=['POST'])
def check_url(id):
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM urls WHERE id = %s", (id,))
                row = cur.fetchone()
                if not row:
                    flash('URL не найден', 'danger')
                    return redirect(url_for('routes.urls'))
                url = row[0]

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            h1, title, description = parse_html(response.text)
            insert_check_result(
                                id,
                                response.status_code,
                                h1,
                                title,
                                description
            )
            
            flash('Страница успешно проверена', 'success')
        except requests.RequestException as e:
            status_code = getattr(e.response, 'status_code', 0)
            insert_check_result(id, status_code, None, None, None)
            flash('Произошла ошибка при проверке', 'danger')

    except Exception:
        flash('Произошла ошибка при проверке', 'danger')

    return redirect(url_for('routes.show_url', id=id))