import os
from flask import Flask, request, jsonify
from jose import jwt
from jwt import encode, decode
import json


app = Flask(__name__)


@app.route('/login', methods=['POST'])
def login():
    user = request.get_json()

    if user and ("email" in user):
        token = encode({"email": user["email"]})
        return jsonify({"token": token})
    else:
        return known_error("Request payload was empty")


@app.route('/code', methods=['POST'])
def code():
    access_code = request.get_json()

    if access_code and ("code" in access_code):
        token = encode({"code": access_code["code"]})
        return jsonify({"token": token})
    else:
        return known_error("Request payload was empty")


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
        data = decode(token)
        return data
    else:
        return ""


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
