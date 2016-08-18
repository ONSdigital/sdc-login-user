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


# curl localhost:5000
# curl -X POST localhost:5000/login
# curl -X POST -H "content-type: application/json" -d '{"email": "bob@example.com"}' localhost:5000/login
# curl -H "token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZXNwb25kZW50X2lkIjoiMTIzIiwiZW1haWwiOiJib2JAZXhhbXBsZS5jb20ifQ.MrqSCt_PLIP0XOVKQgSvdXEFZ0QdpTcSajPIPdo9Cfw" \
#      localhost:5000/profile
# curl -H "token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZXNwb25kZW50X2lkIjoiMTIzIiwiZW1haWwiOiJib2JAZXhhbXBsZS5jb20ifQ.MrqSCt_PLIP0XOVKQgSvdXEFZ0QdpTcSajPIPdo9Cfw" \
#      localhost:5000/respondent_units
# curl -H "token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZXNwb25kZW50X3VuaXRzIjpbeyJyZWZlcmVuY2UiOiJhYmMiLCJuYW1lIjoiTnVyc2luZyBMdGQuIn1dLCJyZXNwb25kZW50X2lkIjoiMTIzIiwiZW1haWwiOiJib2JAZXhhbXBsZS5jb20ifQ.Jh9dQiZMFrkouBVR7by9L7BkGagqKmflIKpTUPQ0zMg" \
#      localhost:5000/questionnaires?reference=abc