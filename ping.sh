#!/bin/bash

url=https://sdc-login-user.herokuapp.com

while [ true ]
do

  echo ---
  echo User:
  curl -i -X POST -H "Content-Type: application/json" \
    -d '{"email": "user@example.com"}' \
    ${url}/login

  echo ---
  echo Code:
  curl -i -X POST -H "Content-Type: application/json" \
    -d '{"code": "abc123"}' \
    ${url}/code

    sleep 1
done
