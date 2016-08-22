import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from jwt import encode, decode
from jose.exceptions import JWSError


app = Flask(__name__)
CORS(app)

respondents = [
    {
        "respondent_id": "101",
        "email": "florence.nightingale@example.com",
        "name": "Florence Nightingale"
    },
    {
        "respondent_id": "102",
        "email": "chief.boyce@example.com",
        "name": "Chief Fire Officer Boyce"
    },
    {
        "respondent_id": "103",
        "email": "fireman.sam@example.com",
        "name": "Fireman Sam"
    },
    {
        "respondent_id": "104",
        "email": "rob.dabank@example.com",
        "name": "Robert DaBank"
    }
]

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

respondent_units = [
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
            <li>Then try GET to <a href="/respondent_units">/respondent_units</a> to see the RUs the respondent is associated with.</li>
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


@app.route('/login', methods=['POST'])
def login():
    user = request.get_json()

    if user and ("email" in user):
        for respondent in respondents:
            if respondent["email"] == user["email"]:
                token = encode(respondent)
                return jsonify({"token": token})
        return unauthorized("Access denied")
    else:
        return known_error("Please provide a Json message with 'email' and 'password' fields.")


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
        return known_error("Please provide a Json message with a 'code' field.")


@app.route('/profile', methods=['GET'])
def profile():
    token = request.headers.get("token")
    data = validate_token(token)

    if data and "respondent_id" in data:
        # We have a verified respondent id:
        for respondent in respondents:
            if respondent["respondent_id"] == data["respondent_id"]:
                print(jsonify(respondent))
                return jsonify(respondent)
        return known_error("Respondent ID " + str(data["respondent_id"]) + " not found.")
    return unauthorized("Please provide a token header that includes a respondent_id.")


@app.route('/profile', methods=['POST'])
def profile_update():
    token = request.headers.get("token")
    data = validate_token(token)
    json = request.get_json()

    if data and "respondent_id" in data:
        # We have a verified respondent id:
        for respondent in respondents:
            if respondent["respondent_id"] == data["respondent_id"]:
                if "name" in json:
                    respondent["name"] = json["name"]
                return jsonify(respondent)
        return known_error("Respondent ID " + str(data["respondent_id"]) + " not found.")
    return unauthorized("Please provide a token header that includes a respondent_id.")


@app.route('/respondent_units', methods=['GET'])
def respondent_unit_associations():
    token = request.headers.get("token")
    data = validate_token(token)

    if data and "respondent_id" in data:
        # We have a verified respondent id:
        result = {"respondent_id": data["respondent_id"], "respondent_units": []}
        for respondent_unit in respondent_units:
            for respondent_id in respondent_unit["respondents"]:
                if respondent_id == data["respondent_id"]:
                    result["respondent_units"].append(respondent_unit)
        data["respondent_units"] = result["respondent_units"]
        result["token"] = encode(data)
        return jsonify(result)
    return known_error("Please provide a 'token' header containing a JWT with a respondent_id value.")


@app.route('/respondents', methods=['GET'])
def respondent_profiles():
    token = request.headers.get("token")
    data = validate_token(token)
    reference = request.args.get('reference')

    if data and "respondent_id" in data and "respondent_units" in data:
        for respondent_unit in data["respondent_units"]:
            # print(respondent_unit["reference"] + " == " + reference)
            if respondent_unit["reference"] == reference:
                result = []
                for respondent_id in respondent_unit["respondents"]:
                    for respondent in respondents:
                        if respondent["respondent_id"] == respondent_id:
                            result.append(respondent)
                return jsonify(result)
            else:
                return unauthorized("Unable to find respondent unit for " + reference)
    return known_error("Please provide a 'token' header containing a JWT with a respondent_id value "
                       "and one or more respondent_unit entries "
                       "and a query parameter 'reference' identifying the unit you wish to get questionnaires for.")


@app.errorhandler(401)
def unauthorized(error=None):
    app.logger.error("Unauthorized: '%s'", request.data.decode('UTF8'))
    message = {
        'status': 401,
        'message': "{}: {}".format(error, request.url),
    }
    resp = jsonify(message)
    resp.status_code = 401

    return resp


@app.errorhandler(400)
def known_error(error=None):
    app.logger.error("Bad request: '%s'", request.data.decode('UTF8'))
    message = {
        'status': 400,
        'message': "{}: {}".format(error, request.url),
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


@app.errorhandler(500)
def unknown_error(error=None):
    app.logger.error("Error: '%s'", request.data.decode('UTF8'))
    message = {
        'status': 500,
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


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
