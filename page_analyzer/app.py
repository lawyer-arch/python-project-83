import os

from dotenv import load_dotenv
from flask import Flask

from page_analyzer.routes import routes

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

app.register_blueprint(routes)

if __name__ == '__main__':
    app.run(debug=True)
    