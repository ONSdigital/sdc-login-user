import os
from flask import Flask, request, jsonify
from jwt import encode, decode
from jose.exceptions import JWSError


app = Flask(__name__)

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
        "questionnaire_id": "aaa"
    },
    {
        "code": "def456",
        "questionnaire_id": "bbb"
    },
    {
        "code": "ghi789",
        "questionnaire_id": "ccc"
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

questionnaires = [
    {
        "response_id": "801",
        "name": "Monthly Commodities Inquiry",
        "survey_id": "023",
        "form_type": "0203",
        "period": "0816",
        "respondent_unit": "222"
    },
    {
        "response_id": "802",
        "name": "Monthly Commodities Inquiry",
        "survey_id": "023",
        "form_type": "0203",
        "period": "0816",
        "respondent_unit": "223"
    },
    {
        "response_id": "803",
        "name": "Monthly Commodities Inquiry",
        "survey_id": "023",
        "form_type": "0203",
        "period": "0816",
        "respondent_unit": "224"
    },
    {
        "response_id": "804",
        "name": "Retail Sales Inquiry",
        "survey_id": "023",
        "form_type": "0102",
        "period": "0816",
        "respondent_unit": "222"
    },
    {
        "response_id": "805",
        "name": "Retail Sales Inquiry",
        "survey_id": "023",
        "form_type": "0102",
        "period": "0816",
        "respondent_unit": "223"
    },
    {
        "response_id": "806",
        "name": "Retail Sales Inquiry",
        "survey_id": "023",
        "form_type": "0102",
        "period": "0816",
        "respondent_unit": "224"
    }
]


@app.route('/', methods=['GET'])
def info():
    return "Try POST to /login or /code"


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


@app.route('/questionnaires', methods=['GET'])
def questionnaire_entries():
    token = request.headers.get("token")
    data = validate_token(token)
    reference = request.args.get('reference')
    # print(reference)
    # print(repr(data))

    if data and "respondent_id" in data and "respondent_units" in data:
        for respondent_unit in data["respondent_units"]:
            # print(respondent_unit["reference"] + " == " + reference)
            if respondent_unit["reference"] == reference:
                respondent_unit["questionnaires"] = []
                for questionnaire in questionnaires:
                    if questionnaire["respondent_unit"] == reference:
                        respondent_unit["questionnaires"].append(questionnaire)
                return jsonify({"questionnaires": respondent_unit["questionnaires"], "token": encode(data)})
            else:
                return unauthorized("Unable to find respondent unit for " + reference)
    return known_error("Please provide a 'token' header containing a JWT with a respondent_id value "
                       "and one or more respondent_unit entries "
                       "and a query parameter 'reference' identifying the unit you wish to get questionnaires for.")


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
