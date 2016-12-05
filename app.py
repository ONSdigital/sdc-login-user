import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from jwt import encode, decode
from jose.exceptions import JWSError
from passlib.context import CryptContext
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String

from typing import Dict
import typing

# service name (initially used for sqlite file name and schema name)
SERVICE_NAME = 'sdc-login-user'
ENVIRONMENT_NAME = os.getenv('ENVIRONMENT_NAME', 'dev')
PORT = int(os.environ.get('PORT', 5009))

app = Flask(__name__)

# Enable cross-origin requests
CORS(app)

# Set up the database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:////tmp/{}.db'.format(SERVICE_NAME))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
SCHEMA_NAME = None if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite') else '{}_{}'.format(ENVIRONMENT_NAME, SERVICE_NAME)

if os.getenv('SQL_DEBUG') == 'true':
    import logging
    import sys
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)


# User model
class User(db.Model):
    __table_args__ = {'schema': SCHEMA_NAME}
    # Columns
    id = Column(Integer, primary_key=True)
    respondent_id = Column(String(10))
    name = Column(String(255))
    email = Column(String(255), unique=True)
    password_hash = Column(String(255))

    # Password handling
    # "PBKDF2 is probably the best for portability"
    #  http://pythonhosted.org/passlib/new_app_quickstart.html
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], default="pbkdf2_sha256")

    def __init__(self, respondent_id=None, name=None, email=None):
        self.respondent_id = respondent_id
        self.name = name
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.name

    def as_dict(self) -> Dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name not in ['id', 'password_hash']}

    def set_password(self, password):
        self.password_hash = None
        if password is not None:
            self.password_hash = self.pwd_context.encrypt(password)

    def verify_password(self, password):
        """ Users can't log in until a password is set. """
        return self.password_hash is not None and self.pwd_context.verify(password, self.password_hash)


@app.route('/', methods=['GET'])
def info():
    return """
        </ul>
            <li>Try POST to <a href="/login">/login</a></li>
            <li>Valid email addresses are:
            florence.nightingale@example.com,
            chief.boyce@example.com,
            fireman.sam@example.com and
            rob.dabank@example.com
            </li>
            <li>Valid internet access codes are:
            abc123,
            def456,
            ghi789,
            jkl012,
            mno345 and
            pqr678
            </li>
            <li>Make a note of the returned token and pass it in a "token" header for other requests.</li>
            <li>Try GET or POST to <a href="/profile">/profile</a></li>
            <li>Then try GET to <a href="/reporting_units">/reporting_units</a> to see the RUs the respondent is associated with.</li>
            <li>Make a note of the expanded token</li>
            <li>Then try GET to
            <a href="/respondents">/respondents</a>
            with a ?reference=... query parameter
            containing the RU ref to retrieve the lists of
            other respondents associated with the specified RU</li>
            <li>Then head over to
            <a href="https://sdc-questionnaires.herokuapp.com/">https://sdc-questionnaires.herokuapp.com/</a>
            to query information about assigned questionnaires.</li>
        </ul>
        """


@app.route('/loaderio-1cda968ab7d7bf9ca31e6e1d6950cc0d/')
def loader_id():
    return "loaderio-1cda968ab7d7bf9ca31e6e1d6950cc0d"


@app.route('/login', methods=['POST'])
def login():
    credentials = request.get_json()

    if credentials and ("email" in credentials) and ("password" in credentials):
        respondent = User.query.filter_by(email=credentials["email"]).first()
        if respondent is not None:
            if respondent.verify_password(credentials["password"]):
                token = encode(respondent.as_dict())
                return jsonify({"token": token})
        return unauthorized("Access denied")
    else:
        return unauthorized("Please provide a Json message with 'email' and 'password' fields.")


@app.route('/profile', methods=['GET'])
def profile():
    token = request.headers.get("token")
    data = validate_token(token)

    if data and "respondent_id" in data:
        # We have a verified respondent id:
        respondent = User.query.filter_by(respondent_id=data["respondent_id"]).first()
        if respondent is not None:
            return jsonify(respondent.as_dict())
        return known_error('Respondent ID {} not found.'.format(data['respondent_id']))
    return unauthorized("Please provide a token header that includes a respondent_id.")


@app.route('/profile', methods=['POST'])
def profile_update():
    token = request.headers.get("token")
    data = validate_token(token)
    json = request.get_json()

    if data and "respondent_id" in data:
        # We have a verified respondent id:
        respondent = User.query.filter_by(respondent_id=data["respondent_id"]).first()
        if respondent is not None:
            if "name" in json:
                respondent.name = json["name"]
                db.session.commit()
            return jsonify(respondent.as_dict())
        return known_error('Respondent ID {} not found.'.format(data['respondent_id']))
    return unauthorized("Please provide a token header that includes a respondent_id.")


@app.route('/profiles', methods=['GET'])
def profiles():
    token = request.headers.get('token')
    if validate_token(token) is not None:

        respondent_ids = request.args.get('respondent_ids', '').split(',')

        if respondent_ids:
            # We have verified respondent ids:
            respondents = User.query.filter(User.respondent_id.in_(respondent_ids)).all()
            result = {'respondents': [a.as_dict() for a in respondents]}
            return jsonify(result)

        return unauthorized("Please provide a respondent_ids query string arg.")

    return unauthorized("Please provide a 'token' header containing a valid JWT.")


@app.errorhandler(401)
def unauthorized(error=None):
    app.logger.error("Unauthorized: '{}'".format(request.data.decode('UTF8')))
    message = {'message': '{}: {}'.format(error, request.url)}
    resp = jsonify(message)
    resp.status_code = 401
    return resp


@app.errorhandler(400)
def known_error(error=None):
    app.logger.error("Bad request: '{}'".format(request.data.decode('UTF8')))
    message = {'message': '{}: {}'.format(error, request.url)}
    resp = jsonify(message)
    resp.status_code = 400
    return resp


@app.errorhandler(500)
def unknown_error(error=None):
    app.logger.error("Error: '{}'".format(request.data.decode('UTF8')))
    message = {'message': 'Internal server error: {}'.format(error)}
    resp = jsonify(message)
    resp.status_code = 500
    return resp


def validate_token(token):
    try:
        return decode(token)
    except Exception:
        return None


def recreate_database():
    if SCHEMA_NAME:
        sql = ('DROP SCHEMA IF EXISTS "{0}" CASCADE;'
               'CREATE SCHEMA IF NOT EXISTS "{0}"'.format(SCHEMA_NAME))
        db.engine.execute(sql)
    else:
        db.drop_all()
    db.create_all()


def create_users():
    """
    # Set up users
    respondents = [
        {
            "respondent_id": "101",
            "email": "florence.nightingale@example.com",
            "name": "Florence Nightingale",
        },
        {
            "respondent_id": "102",
            "email": "chief.boyce@example.com",
            "name": "Chief Fire Officer Boyce",
        },
        {
            "respondent_id": "103",
            "email": "fireman.sam@example.com",
            "name": "Fireman Sam",
        },
        {
            "respondent_id": "104",
            "email": "rob.dabank@example.com",
            "name": "Robert DaBank",
        }
    ]
    """
    # Set up users
    respondents = [
        {
            "respondent_id": "1",
            "email": "james.smith@example.com",
            "name": "James Smith",
        },
        {
            "respondent_id": "2",
            "email": "john.johnson@example.com",
            "name": "John Johnson",
        },
        {
            "respondent_id": "3",
            "email": "robert.williams@example.com",
            "name": "Robert Williams",
        },
        {
            "respondent_id": "4",
            "email": "michael.jones@example.com",
            "name": "Michael Jones",
        },
        {
            "respondent_id": "5",
            "email": "mary.brown@example.com",
            "name": "Mary Brown",
        }
    ]
    for respondent in respondents:
        if User.query.filter_by(respondent_id=respondent["respondent_id"]).first() is None:
            user = User(respondent_id=respondent['respondent_id'], email=respondent['email'], name=respondent['name'])
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
            print(user)

    # Just to see that test users are present
    print(User.query.all())


if __name__ == '__main__':
    # create and populate db only if in main process (Werkzeug also spawns a child process)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        recreate_database()
        create_users()

    # Start server
    app.run(debug=True, host='0.0.0.0', port=PORT, threaded=True)

