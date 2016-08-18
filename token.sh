#!/bin/bash

echo User:
curl -v -X POST -H "Content-Type: application/json" \
    -d '{"email": "user@example.com"}' \
    https://sdc-login-user.herokuapp.com/login # http://localhost:5000/login

echo ---
echo Code:
curl -v -X POST -H "Content-Type: application/json" \
    -d '{"code": "abc123"}' \
    https://sdc-login-user.herokuapp.com/login # http://localhost:5000/code
