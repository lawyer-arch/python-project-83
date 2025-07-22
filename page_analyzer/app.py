import os

from dotenv import load_dotenv
from flask import Flask

from page_analyzer.error_handlers import register_error_handlers
from page_analyzer.routes import routes

load_dotenv()

app = Flask(__name__)  # NOSONAR

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # NOSONAR

register_error_handlers(app)
app.register_blueprint(routes)

if __name__ == '__main__':
    app.run()
    