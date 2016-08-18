import os
from flask import Flask, request, jsonify
from jose import jwt
from jwt import encode, decode
from jose.exceptions import JWSError
import json


app = Flask(__name__)


@app.route('/', methods=['GET'])
def info():
    return "Try POST to /login or /code"


@app.route('/login', methods=['POST'])
def login():
    user = request.get_json()

    if user and ("email" in user):
        token = encode({"email": user["email"], "respondent_id": "123"})
        return jsonify({"token": token})
    else:
        return known_error("Please provide a Json message with 'email' and 'password' fields.")


@app.route('/code', methods=['POST'])
def code():
    access_code = request.get_json()

    if access_code and ("code" in access_code):
        token = encode({"code": access_code["code"], "respondent_id": "123"})
        return jsonify({"token": token})
    else:
        return known_error("Please provide a Json message with a 'code' field.")


@app.route('/profile', methods=['GET'])
def profile():
    token = request.headers.get("token")
    data = validate_token(token)

    if data and "respondent_id" in data:
        # We have a verified respondent id:
        if data["respondent_id"] == "123":
            return jsonify({"name": "Florence Nightingale"})
        else:
            return jsonify({"name": "Rob DeBank", "status": "enforcement"})


@app.route('/respondent_units', methods=['GET'])
def respondent_units():
    token = request.headers.get("token")
    data = validate_token(token)

    if data and "respondent_id" in data:
        # We have a verified respondent id:
        result = {"respondent_id": data["respondent_id"], "respondent_units": []}
        respondent_unit = {}
        if data["respondent_id"] == "123":
            respondent_unit = {"name": "Nursing Ltd.", "reference": "abc"}
        else:
            respondent_unit = {"name": "Morgan Stanley", "reference": "$$$"}
        result["respondent_units"].append(respondent_unit)
        data["respondent_units"] = result["respondent_units"]
        result["token"] = encode(data)
        return jsonify(result)
    return known_error("Please provide a 'token' header containing a JWT with a respondent_id value.")


@app.route('/questionnaires', methods=['GET'])
def questionnaires():
    token = request.headers.get("token")
    data = validate_token(token)
    reference = request.args.get('reference')
    print(reference)
    print(repr(data))

    if data and "respondent_id" in data and "respondent_units" in data:
        for respondent_unit in data["respondent_units"]:
            print(respondent_unit["reference"] + " == " + reference)
            if respondent_unit["reference"] == reference:
                questionnaire = {"name": "Monthly Commodities Inquiry", }
                respondent_unit["questionnaires"] = [questionnaire]
                return jsonify({"questionnaires": respondent_unit["questionnaires"], token: encode(data)})
    return known_error("Please provide a 'token' header containing a JWT with a respondent_id value "
                "and one or more respondent_unit entries "
                "and a query parameter 'reference' identifying the unit you wish to retrieve questionnaires for.")


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
