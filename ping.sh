#!/bin/bash

while [ true ]
do
    curl -i \
    -H "Content-Type: application/json" \
    -X POST -d '{"username":"xyz","password":"xyz"}' \
    http://localhost:5000/profile
    
    sleep 1
done
