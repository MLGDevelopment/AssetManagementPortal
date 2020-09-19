import logging
import os
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
# from app.scripts import wan_writer
# import socket
# socket.getaddrinfo('localhost', 8080)

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname( __file__ ), 'data', 'tmp'))

application = app = Flask(__name__)
app.config['SECRET_KEY'] = '2f64884026723dad15ab1beeaff018fcd1bf29747ad79a2b'
# app.config['SECRET_KEY'] = os.urandom(32)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# TODO: ONE FOR TESTING, ONE FOR PROD. SET CAREFULLY
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5432/MLGCapital'
#app.config['SERVER_NAME'] = 'internalmlg:5000'
#app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

# TODO: IMPLEMENT SOCKETS
# socketio = SocketIO(app)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)
csrf.init_app(app)


def build_logger():
    """
    Function for building a logger
    :return:
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    handler = logging.FileHandler('scraper.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('INITIALIZING')
    return logger


logger = build_logger()
import routes

