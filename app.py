import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from jwt import encode, decode
from jose.exceptions import JWSError
from passlib.context import CryptContext
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String


app = Flask(__name__)

# Enable cross-origin requests
CORS(app)

# Set up the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/users.db'
db = SQLAlchemy(app)


# User model
class User(db.Model):

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

    def json(self):
        return {"respondent_id": self.respondent_id,
                "name": self.name,
                "email": self.email}

    def set_password(self, password):
        self.password_hash = None
        if password is not None:
            self.password_hash = self.pwd_context.encrypt(password)

    def verify_password(self, password):
        """ Users can't log in until a password is set. """
        return self.password_hash is not None and \
            self.pwd_context.verify(password, self.password_hash)


access_codes = [
    {
        "code": "abc123",
        "response_id": "801"
    },
    {
        "code": "def456",
        "response_id": "802"
    },
    {
        "code": "ghi789",
        "response_id": "803"
    },
    {
        "code": "jkl012",
        "response_id": "804"
    },
    {
        "code": "mno345",
        "response_id": "805"
    },
    {
        "code": "pqr678",
        "response_id": "806"
    }
]

reporting_units = [
    {
        "reference": "222",
        "name": "Nursing Ltd.",
        "respondents": [
            "101"
        ]
    },
    {
        "reference": "223",
        "name": "Pontypandy fire station.",
        "respondents": [
            "102", "103"
        ]
    },
    {
        "reference": "224",
        "name": "Morgan Stanley",
        "respondents": [
            "104"
        ]
    }
]


@app.route('/', methods=['GET'])
def info():
    return """
        </ul>
            <li>Try POST to <a href="/login">/login</a> or <a href="/code">/code</a></li>
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
                token = encode(respondent.json())
                return jsonify({"token": token})
        return unauthorized("Access denied")
    else:
        return unauthorized("Please provide a Json message with 'email' and 'password' fields.")


@app.route('/code', methods=['POST'])
def code():
    json = request.get_json()

    if json and ("code" in json):
        for access_code in access_codes:
            if access_code["code"] == json["code"]:
                token = encode(access_code)
                return jsonify({"token": token})
        return unauthorized("Access denied for code " + json["code"])
    else:
        return unauthorized("Please provide a Json message with a 'code' field.")


@app.route('/profile', methods=['GET'])
def profile():
    token = request.headers.get("token")
    data = validate_token(token)

    if data and "respondent_id" in data:
        # We have a verified respondent id:
        respondent = User.query.filter_by(respondent_id=data["respondent_id"]).first()
        if respondent is not None:
            return jsonify(respondent.json())
        return known_error("Respondent ID " + str(data["respondent_id"]) + " not found.")
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
            return jsonify(respondent.json())
        return known_error("Respondent ID " + str(data["respondent_id"]) + " not found.")
    return unauthorized("Please provide a token header that includes a respondent_id.")


@app.errorhandler(401)
def unauthorized(error=None):
    app.logger.error("Unauthorized: '%s'", request.data.decode('UTF8'))
    message = {
        'message': "{}: {}".format(error, request.url),
    }
    resp = jsonify(message)
    resp.status_code = 401

    return resp


@app.errorhandler(400)
def known_error(error=None):
    app.logger.error("Bad request: '%s'", request.data.decode('UTF8'))
    message = {
        'message': "{}: {}".format(error, request.url),
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


@app.errorhandler(500)
def unknown_error(error=None):
    app.logger.error("Error: '%s'", request.data.decode('UTF8'))
    message = {
        'message': "Internal server error: " + repr(error),
    }
    resp = jsonify(message)
    resp.status_code = 500

    return resp


def validate_token(token):

    if token:
        try:
            return decode(token)
        except JWSError:
            return ""


def create_database():

    #db.drop_all()
    db.create_all()


def create_users():

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
    for respondent in respondents:
        if User.query.filter_by(respondent_id=respondent["respondent_id"]).first() is None:
            user = User(
                respondent_id=respondent["respondent_id"],
                email=respondent["email"],
                name=respondent["name"]
            )
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
            print(user)

    # Just to see that test users are present
    print(User.query.all())


if __name__ == '__main__':

    # Create database
    create_database()
    create_users()

    # Start server
    port = int(os.environ.get('PORT', 5009))
    app.run(debug=True, host='0.0.0.0', port=port, threaded=True)

