#!/bin/bash
curl -v -X POST -H "Content-Type: application/json" \
    -d '{"email": "user@example.com"}' \
    https://sdc-login-user.herokuapp.com/login # http://localhost:5000/login
